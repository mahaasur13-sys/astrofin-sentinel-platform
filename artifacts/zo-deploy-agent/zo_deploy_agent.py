#!/usr/bin/env python3
"""ROMA deploy-agent — pull-based CD для машины Zo. Класс G-ZO-DEPLOY-RED.

Зачем перевёрнуто направление потока: конвейер «Deploy to Zo» ходил ИЗ раннера
GitHub Actions НА машину Zo по SSH. У раннера нет ни маршрута, ни DNS до Zo —
`ssh: Could not resolve hostname ... Temporary failure in name resolution`, exit 255.
Инбаунд-канал до машины отсутствует (Zo достигается снаружи только через свой http-прокси),
поэтому выкат делает сама машина: она тянет master, когда CI по этому SHA зелёный,
а раннеру остаётся вердикт — дождаться commit status `deploy/zo`, который ставит агент.

Цикл (INTERVAL, по умолчанию 60 с):
  1. `git ls-remote origin <branch>` → remote_sha
  2. remote_sha == deployed_sha → тишина (ни одного лишнего действия)
  3. remote_sha ∈ failed       → тишина (отказ зафиксирован, повторов нет)
  4. CI-гейт: запуск workflow "ROMA CI" по этому SHA завершён и success
  5. выкат: fetch → fast-forward → compileall-предпроверка → миграции → рестарт → /health
  6. вердикт: commit status `deploy/zo` на SHA (pending → success/failure/error)

Сознательные ограничения (не «недоделки», а защита):
  * fast-forward only — разошедшаяся история = отказ, дерево не трогаем;
  * грязное дерево = отказ: изменённые tracked-файлы (`git status --porcelain
    --untracked-files=no`) блокируют fast-forward — чужой незакоммиченный труд не сносится
    молча (класс G-PHANTOM-ENTRY-WRITE); новые untracked-файлы выкат не блокируют;
  * инвариант «HEAD == то, что исполняет сервис»: любой отказ ПОСЛЕ fast-forward
    откатывает дерево к последнему рабочему SHA;
  * память об отказе постоянна (по SHA) — повторов нет; снятие памяти `--retry-all`;
    первый алерт об отказе уходит сразу, стоячий — раз в сутки и не раньше часа после отказа;
    плюс один напоминающий алерт в сутки, пока выкат стоит;
  * миграции ДО рестарта и с самопроверкой: если после `run_migrations.py` в
    schema_migrations остались неотмеченные файлы, выкат блокируется — код не поднимается,
    прод продолжает жить на старом. Молчаливый no-op миграций (например, .env не читается
    в env-only режиме) так ловится, а не прощается;
  * рестартится ровно один сервис (roma-execution-bridge); чужое не трогаем;
  * авто-откат выключен по умолчанию (`--rollback-on-unhealthy`) — отказ регистрируется,
    алертится и лечится человеком; авто-перезапись без GO в этом проекте не делается;
  * состояние и журнал — на persistent-пути (/var/lib/roma-deploy-agent), потому что
    /dev/shm теряется при рестарте песочницы, а память о выкате обязана переживать рестарт;
  * один писатель: flock; два экземпляра не выкатывают одновременно.

CLI:
    zo_deploy_agent.py                  # цикл (режим сервиса)
    zo_deploy_agent.py --once           # один цикл
    zo_deploy_agent.py --dry-run        # план без изменений
    zo_deploy_agent.py --status         # состояние, без действий
    zo_deploy_agent.py --retry-all      # снять память об отказах и продолжить
"""

from __future__ import annotations

import argparse
import datetime
import fcntl
import json
import os
import pathlib
import signal
import subprocess
import sys
import time
import urllib.request

REPO = pathlib.Path(os.environ.get("ROMA_REPO_DIR", "/home/workspace/roma-execution-bridge"))
STATE_DIR = pathlib.Path(os.environ.get("ROMA_DEPLOY_STATE_DIR", "/var/lib/roma-deploy-agent"))
STATE_PATH = STATE_DIR / "state.json"
LOG_PATH = STATE_DIR / "deploy-agent.log"
LOCK_PATH = STATE_DIR / "deploy-agent.lock"
LOG_MAX_BYTES = 1_000_000

BRANCH = os.environ.get("ROMA_DEPLOY_BRANCH", "master")
CI_WORKFLOW = os.environ.get("ROMA_DEPLOY_CI_WORKFLOW", "ci.yml")
SERVICE = os.environ.get("ROMA_DEPLOY_SERVICE", "roma-execution-bridge")
SUPERVISOR_CONF = os.environ.get("ZO_SUPERVISOR_CONF", "/etc/zo/supervisord-user.conf")
HEALTH_URL = os.environ.get("ROMA_HEALTH_URL", "http://127.0.0.1:8900/health")
STATUS_CONTEXT = os.environ.get("ROMA_DEPLOY_STATUS_CONTEXT", "deploy/zo")
RELAY_URL = os.environ.get("ROMA_ALERT_RELAY_URL", "http://127.0.0.1:8099/notify")
PG_DSN_DB = os.environ.get("ROMA_PG_DB", "roma")

INTERVAL = int(os.environ.get("ROMA_DEPLOY_INTERVAL", "60"))
HEALTH_TIMEOUT_S = int(os.environ.get("ROMA_DEPLOY_HEALTH_TIMEOUT", "90"))
GIT_TIMEOUT_S = 180
MIGRATE_TIMEOUT_S = 300
HEARTBEAT_CYCLES = 30
FAILED_NOTICE_INTERVAL_S = 3600
PYTHON = sys.executable or "/usr/local/bin/python3"

_STOP = False


def _handle_stop(signum, _frame):  # noqa: ANN001
    global _STOP
    _STOP = True
    emit("stop_requested", signal=signum)


def now_iso() -> str:
    return (
        datetime.datetime.now(datetime.timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _age_s(iso: str) -> float:
    """Возраст отметки времени в секундах (для «не будить повторно»)."""
    if not iso:
        return 0.0
    try:
        seen = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except Exception:  # noqa: BLE001
        return 0.0
    return (datetime.datetime.now(datetime.timezone.utc) - seen).total_seconds()


def emit(event: str, **fields) -> None:
    line = json.dumps({"ts": now_iso(), "event": event, **fields}, ensure_ascii=False)
    print(line, flush=True)  # stdout → супервизор → Loki (/dev/shm/roma-deploy-agent.log)
    try:  # durable-копия: /dev/shm теряется при рестарте песочницы
        os.makedirs(STATE_DIR, exist_ok=True)
        if LOG_PATH.exists() and LOG_PATH.stat().st_size >= LOG_MAX_BYTES:
            os.replace(LOG_PATH, LOG_PATH.with_suffix(".log.1"))
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception as exc:  # журнал не имеет права ронять выкат
        print(json.dumps({"ts": now_iso(), "event": "log_write_failed", "error": type(exc).__name__}), flush=True)


def alert(title: str, summary: str, status: str = "firing") -> None:
    payload = {
        "title": title,
        "status": status,
        "alerts": [
            {
                "status": status,
                "labels": {"alertname": "ZoDeployAgent"},
                "annotations": {"summary": summary[:900]},
            }
        ],
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(RELAY_URL, data=data, method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            emit("alert_sent", title=title, http=resp.status)
    except Exception as exc:  # канал алертов — не причина отменять вердикт
        emit("alert_failed", title=title, error=f"{type(exc).__name__}: {exc}")


def run(cmd: list[str], *, timeout: int, cwd: pathlib.Path = REPO) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
        return proc.returncode, (proc.stdout or "").strip(), (proc.stderr or "").strip()
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout after {timeout}s: {' '.join(cmd)}"
    except Exception as exc:  # noqa: BLE001
        return 125, "", f"{type(exc).__name__}: {exc}"


def load_state() -> dict:
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"deployed_sha": "", "failed": {}, "history": []}
    except Exception as exc:  # noqa: BLE001
        emit("state_unreadable", error=type(exc).__name__)
        return {"deployed_sha": "", "failed": {}, "history": []}


def save_state(state: dict) -> None:
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        state["updated_at"] = now_iso()
        tmp = STATE_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(tmp, STATE_PATH)
    except Exception as exc:  # noqa: BLE001
        emit("state_write_failed", error=type(exc).__name__)


def remote_sha() -> str:
    rc, out, err = run(["git", "ls-remote", "origin", f"refs/heads/{BRANCH}"], timeout=60)
    if rc != 0 or not out:
        emit("remote_unresolved", rc=rc, error=err[:300])
        return ""
    return out.split()[0]


def ci_state(sha: str) -> tuple[str, str]:
    """green | pending | red | unknown — состояние workflow CI по конкретному SHA."""
    rc, out, err = run(
        ["gh", "run", "list", "--workflow", CI_WORKFLOW, "--branch", BRANCH, "--limit", "30", "--json", "headSha,status,conclusion"],
        timeout=60,
    )
    if rc != 0:
        return "unknown", err[:200]
    try:
        runs = json.loads(out or "[]")
    except Exception as exc:  # noqa: BLE001
        return "unknown", f"json: {type(exc).__name__}"
    for item in runs:
        if item.get("headSha") == sha:
            if item.get("status") != "completed":
                return "pending", "run in progress"
            return ("green", "ci success") if item.get("conclusion") == "success" else ("red", str(item.get("conclusion")))
    return "pending", "no run for this sha yet"


def tree_dirty() -> str:
    """Изменённые tracked-файлы. Незакоммиченные новые файлы (untracked) выкат не блокируют."""
    rc, out, err = run(["git", "status", "--porcelain", "--untracked-files=no"], timeout=30)
    if rc != 0:
        return f"git_status_failed:{err[:120]}"
    return out


def notice_due(state: dict, key: str, interval_s: int = FAILED_NOTICE_INTERVAL_S) -> bool:
    """Троттлинг одинаковых уведомлений: одно в час, а не каждый цикл."""
    notices = state.setdefault("notices", {})
    last = notices.get(key, "")
    due = True
    if last:
        try:
            seen = datetime.datetime.fromisoformat(last.replace("Z", "+00:00"))
            due = (datetime.datetime.now(datetime.timezone.utc) - seen).total_seconds() >= interval_s
        except Exception:  # noqa: BLE001
            due = True
    if due:
        notices[key] = now_iso()
    return due


def ff_possible(sha: str) -> tuple[bool, str]:
    rc, _, _ = run(["git", "merge-base", "--is-ancestor", "HEAD", sha], timeout=30)
    if rc == 0:
        return True, ""
    return False, "HEAD не предок remote — история разошлась"


def applied_migrations() -> set[str]:
    rc, out, err = run(
        [
            "/usr/sbin/runuser", "-u", "postgres", "--", "/usr/bin/psql",
            "-h", "/var/run/postgresql", "-p", "5432", "-d", PG_DSN_DB, "-tAc",
            "select filename from schema_migrations",
        ],
        timeout=30,
    )
    if rc != 0:
        emit("migration_ledger_unreadable", rc=rc, error=err[:200])
        return set()
    return {line.strip() for line in out.splitlines() if line.strip()}


def pending_migrations() -> tuple[list[str], bool]:
    """(список неприменённых файлов, удалось ли прочитать ledger)."""
    applied = applied_migrations()
    if not applied:
        return [], False
    files = sorted(p.name for p in (REPO / "migrations").glob("*.sql"))
    return [name for name in files if name not in applied], True


def remote_migration_files(sha: str) -> list[str]:
    """Файлы migrations/*.sql в удалённом дереве этого SHA — по gh api, без fetch.

    Нужны, чтобы план выката показывал миграции, которые ещё лежат в удалённом коммите:
    дерево на машине их ещё не содержит (`git ls-tree` без fetch их не увидит).
    """
    repo = repo_owner_name()
    if not repo:
        return []
    rc, out, err = run(
        ["gh", "api", f"/repos/{repo}/contents/migrations?ref={sha}", "--jq", ".[].name"],
        timeout=60,
    )
    if rc != 0:
        emit("remote_migrations_unreadable", sha=sha[:8], error=err[:200])
        return []
    return sorted(n.strip() for n in out.splitlines() if n.strip().endswith(".sql"))


def repo_owner_name() -> str:
    rc, out, _ = run(["git", "remote", "get-url", "origin"], timeout=30)
    if rc != 0:
        return ""
    url = out.strip().removesuffix(".git")
    if url.startswith("https://github.com/"):
        return url[len("https://github.com/") :]
    if url.startswith("git@github.com:"):
        return url[len("git@github.com:") :]
    return ""


def post_status(sha: str, state: str, description: str, target_url: str = "") -> None:
    repo = repo_owner_name()
    if not repo:
        emit("status_post_skipped", reason="remote_owner_unresolved")
        return
    cmd = [
        "gh", "api", "-X", "POST", f"/repos/{repo}/statuses/{sha}",
        "-f", f"state={state}",
        "-f", f"context={STATUS_CONTEXT}",
        "-f", f"description={description[:130]}",
    ]
    if target_url:
        cmd += ["-f", f"target_url={target_url}"]
    rc, _, err = run(cmd, timeout=60)
    emit("status_posted", sha=sha[:8], state=state, rc=rc, error=err[:200] if rc else "")


def health_ok() -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=6) as resp:
            body = resp.read().decode("utf-8", "replace")
            if resp.status != 200:
                return False, f"http={resp.status}"
            payload = json.loads(body)
            if payload.get("status") != "ok":
                return False, f"status={payload.get('status')}"
            if payload.get("pg") is not True:
                return False, "pg=false"
            return True, "ok"
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


def wait_healthy() -> tuple[bool, str]:
    deadline = time.time() + HEALTH_TIMEOUT_S
    last = "not probed"
    while time.time() < deadline:
        ok, last = health_ok()
        if ok:
            return True, last
        time.sleep(3)
    return False, last


def restart_service() -> tuple[bool, str]:
    rc, out, err = run(["supervisorctl", "-c", SUPERVISOR_CONF, "restart", SERVICE], timeout=90)
    detail = (out or err or "").strip().replace("\n", " ")[:200]
    if rc != 0:
        return False, f"rc={rc} {detail}"
    return True, detail


def plan(sha: str, state: dict) -> dict:
    applied = applied_migrations()
    local_files = sorted(p.name for p in (REPO / "migrations").glob("*.sql"))
    if sha and sha != (state.get("deployed_sha") or ""):
        files = remote_migration_files(sha) or local_files
    else:
        files = local_files
    return {
        "sha": sha,
        "deployed_sha": state.get("deployed_sha") or "",
        "commits": ahead_by(state.get("deployed_sha") or "", sha) if state.get("deployed_sha") else None,
        "pending_migrations": [n for n in files if n not in applied],
        "migration_ledger_readable": bool(applied),
        "branch": BRANCH,
        "service": SERVICE,
    }


def ahead_by(base: str, head: str) -> int | None:
    """Сколько коммитов между base и head — по gh api compare.

    Локальный `git rev-list base..head` не годится: выкатываемый коммит ещё не скачан.
    """
    repo = repo_owner_name()
    if not repo or not base:
        return None
    rc, out, err = run(
        ["gh", "api", f"/repos/{repo}/compare/{base}...{head}", "--jq", ".ahead_by"],
        timeout=60,
    )
    if rc != 0 or not out.strip().isdigit():
        return count_commits(base, head) if base else None
    return int(out.strip())


def count_commits(base: str, head: str) -> int | None:
    rc, out, _ = run(["git", "rev-list", "--count", f"{base}..{head}"], timeout=30)
    if rc != 0 or not out.isdigit():
        return None
    return int(out)


def fail(state: dict, sha: str, reason: str, detail: str, *, notified: bool = True) -> None:
    state.setdefault("failed", {})[sha] = {"reason": reason, "detail": detail[:500], "ts": now_iso()}
    state["last_failed_notice"] = now_iso()
    emit("deploy_failed", sha=sha[:8], reason=reason, detail=detail[:300])
    if notified:
        alert(
            "ROMA deploy-agent: выкат не состоялся",
            f"SHA {sha[:8]} причина={reason}\n{detail[:400]}\nЖурнал: {LOG_PATH}",
        )
    save_state(state)  # память об отказе обязана пережить рестарт агента


def rollback_tree(previous: str, state: dict) -> None:
    """Вернуть дерево к последнему рабочему SHA после отказа ПОСЛЕ fast-forward.

    Инвариант: HEAD рабочего дерева всегда равен коду, который исполняет сервис.
    Иначе рестарт песочницы поднял бы новый код без его миграций — прод ушёл бы
    в состояние «новый писатель против старой схемы» без единого сигнала.
    """
    if not previous:
        emit("tree_not_rolled_back", reason="previous_unknown")
        return
    rc, _, err = run(["git", "reset", "--hard", previous], timeout=60)
    emit("tree_rolled_back", to=previous[:8], rc=rc, error=err[:200] if rc else "")


def do_deploy(sha: str, state: dict, *, dry_run: bool, rollback_on_unhealthy: bool) -> bool:
    previous = state.get("deployed_sha") or ""
    steps: list[str] = []

    if dry_run:
        emit("dry_run_plan", **plan(sha, state))
        return True

    post_status(sha, "pending", "машина Zo тянет master")
    emit("deploy_start", sha=sha[:8], previous=previous[:8], commits=ahead_by(previous, sha) if previous else None)

    rc, _, err = run(["git", "fetch", "--prune", "origin", BRANCH], timeout=GIT_TIMEOUT_S)
    if rc != 0:
        fail(state, sha, "fetch_failed", err)
        post_status(sha, "failure", "git fetch не удался")
        return False
    steps.append("fetch")

    ok, why = ff_possible(sha)  # проверяем ПОСЛЕ fetch: до него объект remote-коммита не существует
    if not ok:
        fail(state, sha, "history_diverged", why)
        post_status(sha, "error", "история разошлась, fast-forward невозможен")
        return False

    rc, out, err = run(["git", "merge", "--ff-only", sha], timeout=60)
    if rc != 0:
        fail(state, sha, "ff_failed", (out or err)[:300])
        post_status(sha, "failure", "fast-forward не удался")
        return False
    steps.append("ff")

    rc, _, err = run(
        [PYTHON, "-m", "compileall", "-q", "-x", r"(\.venv|\.git|node_modules|__pycache__|tests)", "."],
        timeout=180,
    )
    if rc != 0:
        fail(state, sha, "compile_failed", err or "compileall")
        rollback_tree(previous, state)
        post_status(sha, "failure", "предпроверка синтаксиса провалилась")
        return False
    steps.append("compile")

    pending_before, ledger_ok = pending_migrations()
    if not ledger_ok:
        fail(state, sha, "migration_ledger_unreadable", "не читается schema_migrations — вердикт по миграциям невозможен")
        rollback_tree(previous, state)
        post_status(sha, "error", "ledger миграций не читается")
        return False
    if pending_before:
        rc, out, err = run([PYTHON, "scripts/run_migrations.py"], timeout=MIGRATE_TIMEOUT_S)
        emit("migrations_run", rc=rc, pending_before=len(pending_before), out=(out or err)[-300:])
        if rc != 0:
            fail(state, sha, "migration_failed", (err or out or "run_migrations rc!=0")[:300])
            rollback_tree(previous, state)
            post_status(sha, "failure", "миграции не применились")
            return False
        pending_after, _ = pending_migrations()
        if pending_after:
            fail(state, sha, "migration_not_applied", "не отмечены: " + ",".join(pending_after[:6]))
            rollback_tree(previous, state)
            post_status(sha, "failure", "миграции не отмечены в ledger")
            return False
        steps.append(f"migrate:{len(pending_before)}")
    else:
        steps.append("migrate:none")

    ok, detail = restart_service()
    if not ok:
        fail(state, sha, "restart_failed", detail)
        rollback_tree(previous, state)
        post_status(sha, "failure", "рестарт сервиса не удался")
        return False
    steps.append("restart")

    healthy, hdetail = wait_healthy()
    if not healthy:
        emit("health_failed", sha=sha[:8], detail=hdetail)
        if rollback_on_unhealthy and previous:
            rc, _, err = run(["git", "reset", "--hard", previous], timeout=60)
            emit("rollback", rc=rc, to=previous[:8], error=err[:200])
            ok2, det2 = restart_service()
            h2, hd2 = wait_healthy() if ok2 else (False, "restart failed")
            alert(
                "ROMA deploy-agent: выкат откачен",
                f"SHA {sha[:8]} не поднялся ({hdetail}); откат на {previous[:8]} → health={hd2}",
            )
            fail(state, sha, "health_failed_rolled_back", f"{hdetail} | rollback health={hd2}")
            post_status(sha, "failure", "выкат откачен: сервис не поднялся")
            return False
        alert(
            "ROMA deploy-agent: сервис не поднялся после выката",
            f"SHA {sha[:8]} health={hdetail}\nСмотри /dev/shm/{SERVICE}_err.log. Авто-откат выключен.",
        )
        fail(state, sha, "health_failed", hdetail)
        post_status(sha, "failure", "сервис не поднялся после выката")
        return False
    steps.append("health")

    state["deployed_sha"] = sha
    state["last_success"] = now_iso()
    state.setdefault("history", []).append({"sha": sha, "at": now_iso(), "steps": steps, "commits": ahead_by(previous, sha) if previous else None})
    state["history"] = state["history"][-30:]
    state.get("failed", {}).pop(sha, None)
    save_state(state)
    emit("deploy_success", sha=sha[:8], previous=previous[:8], steps=steps, health=hdetail)
    post_status(sha, "success", "выкат на машину Zo выполнен, /health ok")
    alert("ROMA deploy-agent: выкат выполнен", f"SHA {sha[:8]} шаги={'+'.join(steps)} /health ok", status="resolved")
    return True


def cycle(state: dict, *, dry_run: bool, rollback_on_unhealthy: bool, heartbeat_due: bool) -> dict:
    sha = remote_sha()
    if not sha:
        return state
    deployed = state.get("deployed_sha") or ""
    if sha == deployed:
        if heartbeat_due:
            emit("heartbeat", deployed_sha=deployed[:8], remote_sha=sha[:8], in_sync=True)
        return state
    if sha in state.get("failed", {}):
        # первый алерт об отказе уже ушёл в момент отказа; стоячий — не раньше часа спустя,
        # иначе владелец получает два сообщения об одном и том же в течение минуты.
        stale = _age_s(state.get("last_failed_notice") or state["failed"][sha].get("ts") or "") >= 3600
        if stale and notice_due(state, "failed_memory:" + sha, 86400):
            entry = state["failed"][sha]
            alert(
                "ROMA deploy-agent: выкат стоит",
                f"SHA {sha[:8]} причина={entry.get('reason')}\n{(entry.get('detail') or '')[:300]}\n"
                "Выкат не повторяется, пока не позовут (--retry-all) — это не зависание, а память.",
            )
            save_state(state)
        if heartbeat_due:
            emit("heartbeat", deployed_sha=deployed[:8], remote_sha=sha[:8], in_sync=False, skipped="failed_memory", reason=state["failed"][sha].get("reason"))
        return state

    status, detail = ci_state(sha)
    if status == "pending":
        if heartbeat_due:
            emit("heartbeat", deployed_sha=deployed[:8], remote_sha=sha[:8], skipped="ci_pending")
        return state
    if status == "unknown":
        emit("ci_gate_unknown", sha=sha[:8], detail=detail)
        return state
    if status == "red":
        emit("ci_gate_red", sha=sha[:8], detail=detail)
        fail(state, sha, "ci_red", f"CI по SHA завершился: {detail}")
        post_status(sha, "error", f"CI красный ({detail}) — выкат не начат")
        save_state(state)
        return state

    if dry_run:
        emit("ci_gate_green", sha=sha[:8])
        emit("dry_run_plan", **plan(sha, state), tree_modified=tree_dirty()[:300])
        return state

    dirty = tree_dirty()
    if dirty:
        # чужой незакоммиченный труд не сносится молча; повторим, когда дерево очистят
        emit("tree_modified", detail=dirty[:300])
        if notice_due(state, "tree_modified"):
            alert(
                "ROMA deploy-agent: выкат придержан",
                f"SHA {sha[:8]}: в дереве есть изменённые tracked-файлы, fast-forward отменён.\n{dirty[:400]}",
            )
            save_state(state)
        return state

    do_deploy(sha, state, dry_run=False, rollback_on_unhealthy=rollback_on_unhealthy)
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description="ROMA pull-based deploy agent (Zo)")
    parser.add_argument("--once", action="store_true", help="один цикл и выход")
    parser.add_argument("--dry-run", action="store_true", help="показать план, ничего не менять")
    parser.add_argument("--status", action="store_true", help="показать состояние")
    parser.add_argument("--interval", type=int, default=INTERVAL, help="период цикла, сек")
    parser.add_argument("--rollback-on-unhealthy", action="store_true", help="авто-откат при неподнявшемся сервисе")
    parser.add_argument("--retry-all", action="store_true", help="снять память об отказах (после устранения причины)")
    args = parser.parse_args()

    state = load_state()
    if args.retry_all:
        cleared = sorted(state.get("failed", {}))
        state["failed"] = {}
        state.pop("notices", None)
        save_state(state)
        emit("retry_memory_cleared", shas=[c[:8] for c in cleared])
        return 0
    if args.status:
        pending, ledger_ok = pending_migrations()
        print(json.dumps({**state, "remote_sha": remote_sha(), "pending_migrations": pending, "migration_ledger_readable": ledger_ok}, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    os.makedirs(STATE_DIR, exist_ok=True)
    signal.signal(signal.SIGTERM, _handle_stop)
    signal.signal(signal.SIGINT, _handle_stop)

    if not state.get("deployed_sha"):
        # Первый запуск: код, который сейчас держит порт, лежит в HEAD рабочего дерева —
        # это и есть фактически выкаченное состояние. Иначе агент считал бы выкатом
        # коммит, которого на машине никогда не было, и терял бы счёт «насколько отстали».
        rc, out, _ = run(["git", "rev-parse", "HEAD"], timeout=30)
        if rc == 0 and out.strip():
            state["deployed_sha"] = out.strip()
            state["deployed_sha_source"] = "inferred_from_head"
            save_state(state)
            emit("bootstrap_deployed_sha", sha=out.strip()[:8], source="inferred_from_head")

    lock_fh = open(LOCK_PATH, "w")  # noqa: SIM115
    try:
        fcntl.flock(lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        emit("lock_busy", detail="другой экземпляр держит аренду выката")
        return 0

    emit(
        "agent_start",
        pid=os.getpid(),
        repo=str(REPO),
        branch=BRANCH,
        interval=args.interval,
        dry_run=args.dry_run,
        rollback_on_unhealthy=args.rollback_on_unhealthy,
        deployed_sha=(state.get("deployed_sha") or "")[:8],
        lease="held",
    )

    cycles = 0
    while not _STOP:
        cycles += 1
        heartbeat_due = cycles % HEARTBEAT_CYCLES == 0
        try:
            state = cycle(state, dry_run=args.dry_run, rollback_on_unhealthy=args.rollback_on_unhealthy, heartbeat_due=heartbeat_due)
        except Exception as exc:  # цикл не имеет права умереть от одной ошибки
            emit("cycle_error", error=f"{type(exc).__name__}: {exc}")
        if args.once or args.dry_run:
            break
        for _ in range(args.interval):
            if _STOP:
                break
            time.sleep(1)

    emit("agent_stop", cycles=cycles, deployed_sha=(state.get("deployed_sha") or "")[:8])
    return 0


if __name__ == "__main__":
    sys.exit(main())
