#!/usr/bin/env python3
"""PG watchdog — supervision for PostgreSQL cluster 15/main (127.0.0.1:5432).

Runs as a Zo user service (mode=process). Every INTERVAL seconds:
  1. probes readiness with pg_isready
  2. if down and restart budget allows -> pg_ctlcluster 15 main start, then waits for ready
     (before the start a stale .s.PGSQL.<port>.lock left over from a sandbox restart is moved
     to a quarantine dir — see clear_stale_lock; the file is never deleted in place)
  3. verifies append-only ledger row count never decreases (integrity tripwire)
  4. emits one JSON line per event to /dev/shm/pg-watchdog.log (collected by Promtail -> Loki)
     and keeps last state in /dev/shm/pg-watchdog-state.json

No DDL/DML is ever executed against the database: the only SQL is a read-only
SELECT count(*) FROM ledger_entries.
"""

from __future__ import annotations

import datetime
import json
import os
import shutil
import socket
import subprocess
import sys
import time

PORT = 5432
CLUSTER = "15"
INTERVAL = 30
RESTART_BUDGET_PER_HOUR = 5
READY_TIMEOUT_S = 60
# F1: осиротевший .s.PGSQL.<port>.lock после рестарта песочницы не даёт кластеру стартовать.
# Пути и порт — параметры clear_stale_lock, чтобы матрицу можно было прогнать на временном
# кластере, не касаясь боевого 5432.
SOCKET_DIR = "/var/run/postgresql"
SOCKET_PATH = os.path.join(SOCKET_DIR, f".s.PGSQL.{PORT}")
LOCK_PATH = SOCKET_PATH + ".lock"
DATA_DIR = "/var/lib/postgresql/15/main"
QUARANTINE_ROOT = SOCKET_DIR
QUARANTINE_KEEP = 10
# Метка владения: ротация трогает только карантины этого скрипта. Ручные каталоги
# (quarantine-20260927T…, quarantine-20261012T…) метки не имеют и не удаляются.
QUARANTINE_MARKER = ".pg-watchdog-quarantine"
# F2: исчерпанный бюджет не должен превращать сторожа в молчащий цикл.
BUDGET_SLOWDOWN = 4  # период проб при исчерпанном бюджете: INTERVAL × 4
BUDGET_ALERT_PERIOD_S = 3600  # pg_down_budget_exceeded — не чаще раза в час
# R3: state и журнал — на persistent-пути (/dev/shm теряется при перезапуске
# песочницы). История рестартов обязана переживать рестарт.
STATE_DIR = "/var/lib/pg-watchdog"
STATE_PATH = os.path.join(STATE_DIR, "state.json")
LOG_PATH = os.path.join(STATE_DIR, "watchdog.log")  # журнал событий, с ротацией
LOG_MAX_BYTES = 1_000_000  # 1 MB → watchdog.log.1
PSQL = [
    "/usr/sbin/runuser",
    "-u",
    "postgres",
    "--",
    "/usr/bin/psql",
    "-h",
    "/var/run/postgresql",
    "-p",
    str(PORT),
    "-d",
    "roma",
    "-tAc",
]


def now_iso() -> str:
    return (
        datetime.datetime.now(datetime.timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def emit(**fields) -> None:
    line = json.dumps({"ts": now_iso(), **fields}, ensure_ascii=False)
    print(line, flush=True)  # stdout → супервизор → Loki (/dev/shm/pg-watchdog.log)
    try:  # R3: durable-копия на persistent-пути, переживает рестарт песочницы
        os.makedirs(STATE_DIR, exist_ok=True)
        if os.path.exists(LOG_PATH) and os.path.getsize(LOG_PATH) >= LOG_MAX_BYTES:
            os.replace(LOG_PATH, LOG_PATH + ".1")
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception as exc:  # журнал не должен ронять супервизию
        print(
            json.dumps(
                {
                    "ts": now_iso(),
                    "event": "log_write_failed",
                    "error": type(exc).__name__,
                }
            ),
            flush=True,
        )


def pg_is_ready() -> bool:
    try:
        return (
            subprocess.run(
                ["/usr/bin/pg_isready", "-h", "127.0.0.1", "-p", str(PORT), "-q"],
                capture_output=True,
                timeout=15,
            ).returncode
            == 0
        )
    except Exception:
        return False


def read_state() -> dict:
    try:
        with open(STATE_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def write_state(state: dict) -> None:
    os.makedirs(STATE_DIR, exist_ok=True)
    state["updated_at"] = now_iso()
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, STATE_PATH)


def prune_restarts(restarts: list[str]) -> list[str]:
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
    keep = []
    for ts in restarts:
        try:
            if datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")) >= cutoff:
                keep.append(ts)
        except Exception:
            continue
    return keep


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except Exception:
        return False


def _pid_comm(pid: int) -> str | None:
    try:
        with open(f"/proc/{pid}/comm", encoding="utf-8") as fh:
            return fh.read().strip()
    except Exception:
        return None


def _read_pid(path: str) -> int | None:
    """PID из первой строки lock/postmaster.pid; None — если там не число."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        first = fh.readline().strip()
    return int(first) if first.isdigit() else None


def _port_listening(port: int, host: str = "127.0.0.1", timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _budget_alert_due(state: dict) -> bool:
    last = state.get("budget_alerted_at")
    if not last:
        return True
    try:
        ts = datetime.datetime.fromisoformat(str(last).replace("Z", "+00:00"))
    except Exception:
        return True
    age = (datetime.datetime.now(datetime.timezone.utc) - ts).total_seconds()
    return age >= BUDGET_ALERT_PERIOD_S


def _rotate_quarantine(root: str, keep: int) -> list[str]:
    """Удалить старейшие карантины ЭТОГО скрипта (по метке); чужие каталоги не трогаем."""
    try:
        own = [
            name
            for name in os.listdir(root)
            if name.startswith("quarantine-")
            and os.path.isfile(os.path.join(root, name, QUARANTINE_MARKER))
        ]
    except Exception:
        return []
    removed = []
    for name in sorted(own)[: max(0, len(own) - keep)]:
        try:
            shutil.rmtree(os.path.join(root, name))
            removed.append(name)
        except Exception:
            continue
    return removed


def clear_stale_lock(
    *,
    port: int = PORT,
    socket_path: str | None = None,
    lock_path: str | None = None,
    data_dir: str | None = None,
    quarantine_root: str | None = None,
    keep: int = QUARANTINE_KEEP,
) -> tuple[bool, str, str | None]:
    """Перенести осиротевший .s.PGSQL.<port>.lock в карантин → (cleared, reason, quarantine).

    Fail-closed: при любом сомнении файл НЕ трогаем. Порядок проверок:
      1. сокет существует              -> кластер жив, отказ
      2. порт слушается               -> на порту кто-то есть, отказ
      3. lock отсутствует             -> чистить нечего
      4. lock нечитаем                -> отказ
      5. PID из lock — живой postgres -> отказ
      6. postmaster.pid — живой postgres -> отказ (два postmaster на один data dir)
    Иначе lock (и stale postmaster.pid) переносятся в quarantine-<ts>/, карантин ротируется.
    """
    socket_path = socket_path or os.path.join(SOCKET_DIR, f".s.PGSQL.{port}")
    lock_path = lock_path or socket_path + ".lock"
    data_dir = data_dir or DATA_DIR
    quarantine_root = quarantine_root or QUARANTINE_ROOT

    if os.path.exists(socket_path):
        return False, "socket_present", None
    if _port_listening(port):
        return False, "port_listening", None
    if not os.path.exists(lock_path):
        return False, "no_lock", None
    try:
        pid = _read_pid(lock_path)
    except Exception:
        return False, "lock_unreadable", None
    if pid is not None and _pid_alive(pid) and _pid_comm(pid) == "postgres":
        return False, "lock_owner_is_postgres", None

    postmaster_pid = os.path.join(data_dir, "postmaster.pid")
    stale_postmaster = os.path.exists(postmaster_pid)
    if stale_postmaster:
        try:
            pm_pid = _read_pid(postmaster_pid)
        except Exception:
            return False, "postmaster_unreadable", None
        if pm_pid is not None and _pid_alive(pm_pid) and _pid_comm(pm_pid) == "postgres":
            return False, "postmaster_running", None

    quarantine = os.path.join(
        quarantine_root,
        "quarantine-"
        + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
    )
    try:
        os.makedirs(quarantine, exist_ok=True)
        with open(os.path.join(quarantine, QUARANTINE_MARKER), "w", encoding="utf-8") as fh:
            fh.write(now_iso() + "\n")
        os.replace(lock_path, os.path.join(quarantine, os.path.basename(lock_path)))
        if stale_postmaster:
            os.replace(postmaster_pid, os.path.join(quarantine, "postmaster.pid"))
    except Exception:
        return False, "quarantine_failed", quarantine
    _rotate_quarantine(quarantine_root, keep)
    return True, "stale_lock_cleared", quarantine


def ledger_rows() -> int | None:
    try:
        out = subprocess.run(
            PSQL + ["SELECT count(*) FROM ledger_entries"],
            capture_output=True,
            timeout=20,
        )
        if out.returncode != 0:
            return None
        return int(out.stdout.decode().strip())
    except Exception:
        return None


def start_cluster() -> bool:
    try:
        res = subprocess.run(
            ["/usr/bin/pg_ctlcluster", CLUSTER, "main", "start"],
            capture_output=True,
            timeout=120,
        )
        return res.returncode == 0
    except Exception:
        return False


def wait_ready(timeout_s: int) -> float | None:
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout_s:
        if pg_is_ready():
            return round(time.monotonic() - t0, 2)
        time.sleep(2)
    return None


def main() -> int:
    state = read_state()
    state.setdefault("restarts", [])
    state.setdefault("restarts_total", 0)
    if "ledger_baseline" not in state:
        state["ledger_baseline"] = ledger_rows()
    emit(
        event="watchdog_start",
        pid=os.getpid(),
        port=PORT,
        interval_s=INTERVAL,
        budget_per_hour=RESTART_BUDGET_PER_HOUR,
        ledger_baseline=state["ledger_baseline"],
    )

    while True:
        state["restarts"] = prune_restarts(state.get("restarts", []))
        up = pg_is_ready()
        state["pg_up"] = int(up)
        state["last_check"] = now_iso()
        state["restarts_last_hour"] = len(state["restarts"])

        sleep_s = INTERVAL
        if up:
            if state.get("was_down"):
                state["was_down"] = False
                state["budget_exceeded"] = False
                state["budget_alerted_at"] = None
                emit(
                    event="pg_recovered",
                    pg_up=1,
                    restarts_last_hour=len(state["restarts"]),
                )
        else:
            state["was_down"] = True
            if len(state["restarts"]) >= RESTART_BUDGET_PER_HOUR:
                state["budget_exceeded"] = True
                # F2: пробы продолжаются, но реже; ERROR — не чаще раза в час, чтобы
                # ручной разбор не терялся в потоке одинаковых строк.
                sleep_s = INTERVAL * BUDGET_SLOWDOWN
                if _budget_alert_due(state):
                    state["budget_alerted_at"] = now_iso()
                    emit(
                        event="pg_down_budget_exceeded",
                        level="ERROR",
                        hint="manual_intervention_required",
                        pg_up=0,
                        restarts_last_hour=len(state["restarts"]),
                        action="none",
                    )
            else:
                emit(event="pg_down", pg_up=0, action="pg_ctlcluster_start")
                cleared, reason, quarantine = clear_stale_lock()
                if cleared:
                    emit(event="stale_lock_cleared", reason=reason, quarantine=quarantine)
                elif reason != "no_lock":
                    emit(event="stale_lock_skipped", reason=reason)
                # F2: бюджет расходуется на ЛЮБОЙ попытке, а не только на удачной —
                # иначе безуспешно стартующего сторожа не остановить.
                state["restarts"].append(now_iso())
                state["restarts_total"] = state.get("restarts_total", 0) + 1
                state["restarts_last_hour"] = len(state["restarts"])
                t0 = time.monotonic()
                started = start_cluster()
                recovery = wait_ready(READY_TIMEOUT_S)
                if recovery is not None:
                    state["last_restart_at"] = now_iso()
                    state["last_recovery_s"] = recovery
                    state["budget_exceeded"] = False
                    emit(
                        event="pg_restart_ok",
                        pg_up=1,
                        started=started,
                        recovery_s=round(time.monotonic() - t0, 2),
                        restarts_total=state["restarts_total"],
                        restarts_last_hour=len(state["restarts"]),
                    )
                else:
                    emit(
                        event="pg_restart_failed",
                        pg_up=0,
                        started=started,
                        timeout_s=READY_TIMEOUT_S,
                        action="pg_ctlcluster_start",
                        recovery_s=None,
                    )

        rows = ledger_rows()
        if rows is not None:
            state["ledger_rows"] = rows
            baseline = state.get("ledger_baseline")
            if baseline is None:
                state["ledger_baseline"] = rows
            elif rows < baseline:
                emit(
                    event="ledger_integrity_violation",
                    pg_up=int(state["pg_up"]),
                    ledger_rows=rows,
                    ledger_baseline=baseline,
                )
            else:
                state["ledger_baseline"] = max(baseline, rows)

        write_state(state)
        time.sleep(sleep_s)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
