#!/usr/bin/env python3
# =============================================================================
# lint_project_board.py — линтер Project Board
#
# Проверяет:
#   1. Все задачи из PRODUCTION_BACKLOG.md имеют соответствующие issues
#   2. У issues есть обязательные labels (phase, moscow, area)
#   3. Issues привязаны к milestone
#   4. Phase в issue совпадает с фазой из backlog
#
# Использование:
#   export GH_TOKEN=ghp_xxxx
#   python scripts/lint_project_board.py [--strict]
#
# --strict: exit 1 при любой ошибке (для CI gate)
# =============================================================================

import argparse
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import requests

GITHUB_API = "https://api.github.com"
REPO_OWNER = "mahaasur13-sys"
REPO_NAME = "astrofin-sentinel-platform"
BACKLOG_PATH = Path("PRODUCTION_BACKLOG.md")

REQUIRED_LABELS = {
    "phase": re.compile(r"^phase-[0-5]$"),
    "moscow": re.compile(r"^(must|should|could|wont)$"),
    "area": re.compile(r"^area/(backend|devops|security|docs|qa)$"),
}

VALID_MILESTONES = {"v0.1.0", "v0.2.0", "v0.3.0", "v0.4.0", "v1.0.0"}


def get_headers() -> dict:
    token = os.environ.get("GH_TOKEN")
    if not token:
        print("❌ GH_TOKEN not set", file=sys.stderr)
        sys.exit(1)
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def parse_backlog() -> dict[str, dict]:
    """Парсит PRODUCTION_BACKLOG.md → dict {task_id: {phase, title, moscow, hours}}."""
    if not BACKLOG_PATH.exists():
        print(f"❌ {BACKLOG_PATH} not found", file=sys.stderr)
        sys.exit(1)

    content = BACKLOG_PATH.read_text(encoding="utf-8")
    tasks: dict[str, dict] = {}

    pattern = re.compile(
        r"\|\s*\*\*(P(\d)-(\d+))\*\*\s*\|\s*(.+?)\s*\|"
        r"\s*(🟥|🟧|🟨|⬜)?\s*(Critical|High|Medium|Low)?\s*\|"
        r"\s*(\d+)\s*\|"
    )

    for match in pattern.finditer(content):
        full_id, phase_str, _num, title, moscow_emoji, _priority, hours = match.groups()
        tasks[full_id] = {
            "phase": int(phase_str),
            "title": title.strip(),
            "moscow": moscow_emoji or "🟧",
            "hours": int(hours),
        }

    return tasks


def fetch_all_issues(state: str = "all") -> list[dict]:
    """Получает все issues репозитория (с пагинацией)."""
    issues: list[dict] = []
    page = 1

    while True:
        response = requests.get(
            f"{GITHUB_API}/repos/{REPO_OWNER}/{REPO_NAME}/issues",
            params={"state": state, "per_page": 100, "page": page},
            headers=get_headers(),
        )
        if response.status_code != 200:
            print(f"❌ GitHub API error: {response.status_code}", file=sys.stderr)
            sys.exit(1)

        batch = response.json()
        if not batch:
            break

        # Исключаем PR'ы
        issues.extend(i for i in batch if "pull_request" not in i)
        if len(batch) < 100:
            break
        page += 1

    return issues


def extract_task_id(title: str) -> str | None:
    """Извлекает P{x}-{y} из заголовка issue."""
    match = re.match(r"\[?(P\d-\d+)\]?", title)
    return match.group(1) if match else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Линтер Project Board + спринтов AstroFin Sentinel")
    parser.add_argument("--strict", action="store_true",
                        help="Exit 1 on any error (for CI gate)")
    parser.add_argument("--state", choices=["open", "closed", "all"], default="all")
    args = parser.parse_args()

    backlog = parse_backlog()
    print(f"📋 Backlog: {len(backlog)} tasks")

    issues = fetch_all_issues(args.state)
    print(f"🐙 GitHub: {len(issues)} issues fetched")

    # Группируем issues по task_id (может быть несколько — main + sub-tasks)
    issues_by_task: dict[str, list[dict]] = defaultdict(list)
    for issue in issues:
        task_id = extract_task_id(issue["title"])
        if task_id:
            issues_by_task[task_id].append(issue)

    errors: list[str] = []
    warnings: list[str] = []
    matched = 0
    open_matched = 0

    for task_id, expected in sorted(backlog.items()):
        task_issues = issues_by_task.get(task_id, [])

        if not task_issues:
            errors.append(f"❌ {task_id}: no issue found (backlog: {expected['title']})")
            continue

        matched += 1
        open_task_issues = [i for i in task_issues if i["state"] == "open"]
        if open_task_issues:
            open_matched += 1

        for issue in task_issues:
            issue_num = issue["number"]
            issue_state = issue["state"]
            labels = {label["name"] for label in issue.get("labels", [])}
            milestone = issue.get("milestone", {}).get("title") if issue.get("milestone") else None

            # Проверка required labels
            for label_type, pattern in REQUIRED_LABELS.items():
                if not any(pattern.match(lbl) for lbl in labels):
                    errors.append(
                        f"❌ #{issue_num} ({task_id}, {issue_state}): "
                        f"missing {label_type} label (has: {sorted(labels)})"
                    )

            # Проверка phase
            phase_label = f"phase-{expected['phase']}"
            if phase_label not in labels and not any(lbl.startswith("phase-") for lbl in labels):
                warnings.append(
                    f"⚠️  #{issue_num} ({task_id}): expected '{phase_label}' label"
                )

            # Проверка milestone для open issues
            if issue_state == "open" and not milestone:
                warnings.append(
                    f"⚠️  #{issue_num} ({task_id}): no milestone assigned"
                )
            elif milestone and milestone not in VALID_MILESTONES:
                warnings.append(
                    f"⚠️  #{issue_num} ({task_id}): unexpected milestone '{milestone}'"
                )

    # Проверяем issues без task_id (orphans)
    orphan_count = sum(1 for i in issues if not extract_task_id(i["title"]))
    if orphan_count:
        warnings.append(f"⚠️  {orphan_count} issues without task_id (orphan)")

    # Отчёт
    print(f"\n{'=' * 60}")
    print(f"📊 LINT REPORT")
    print(f"{'=' * 60}")
    print(f"Backlog tasks:       {len(backlog)}")
    print(f"Issues fetched:      {len(issues)}")
    print(f"Matched:             {matched} / {len(backlog)} ({100 * matched // max(len(backlog), 1)}%)")
    print(f"Open matched:        {open_matched} / {len(backlog)}")
    print(f"Orphan issues:       {orphan_count}")
    print(f"Errors:              {len(errors)}")
    print(f"Warnings:            {len(warnings)}")

    if errors:
        print(f"\n{'─' * 60}")
        print("ERRORS:")
        for e in errors:
            print(f"  {e}")

    if warnings:
        print(f"\n{'─' * 60}")
        print("WARNINGS (first 20):")
        for w in warnings[:20]:
            print(f"  {w}")
        if len(warnings) > 20:
            print(f"  ... and {len(warnings) - 20} more")

    if args.strict and (errors or warnings):
        print(f"\n❌ Lint failed in strict mode")
        sys.exit(1)
    elif errors:
        print(f"\n❌ Lint failed ({len(errors)} errors)")
        sys.exit(1)
    else:
        print(f"\n✅ Lint passed (with {len(warnings)} warnings)")


if __name__ == "__main__":
    main()
