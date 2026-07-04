#!/usr/bin/env python3
# =============================================================================
# seed_project_board.py — заполнение GitHub Project V2 задачами из бэклога
#
# Использование:
#   export GH_TOKEN=ghp_xxxx
#   python scripts/seed_project_board.py --project 1 --milestone v1.0.0 --dry-run
#
# Что делает:
#   1. Парсит PRODUCTION_BACKLOG.md, извлекает задачи формата P{phase}-{id}
#   2. Для каждой задачи создаёт issue через REST API с правильными labels
#   3. Добавляет issue в Project V2 через GraphQL mutation
#
# Опции:
#   --dry-run      только показать, что будет создано (без реальных изменений)
#   --project N    номер Project V2 (default: 1)
#   --milestone    целевой milestone (default: v1.0.0)
#   --phase        фильтр по фазе (0-5), default: все
#   --limit N      создать максимум N задач (default: без лимита)
# =============================================================================

import argparse
import os
import re
import sys
from pathlib import Path

import requests

GITHUB_API = "https://api.github.com"
REPO_OWNER = "mahaasur13-sys"
REPO_NAME = "astrofin-sentinel-platform"
BACKLOG_PATH = Path("PRODUCTION_BACKLOG.md")

# Маппинг фаз на цветовые labels
PHASE_LABELS = {
    0: ("phase-0", "5319E7"),
    1: ("phase-1", "1D76DB"),
    2: ("phase-2", "0075CA"),
    3: ("phase-3", "0E8A16"),
    4: ("phase-4", "BFD4F2"),
    5: ("phase-5", "D93F0B"),
}

# MoSCoW emoji → label
MOSCOW_LABELS = {
    "🟥": "must",
    "🟧": "should",
    "🟨": "could",
    "⬜": "wont",
}


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


def parse_backlog(phase_filter: int | None = None) -> list[dict]:
    """Парсит PRODUCTION_BACKLOG.md и возвращает список задач."""
    if not BACKLOG_PATH.exists():
        print(f"❌ {BACKLOG_PATH} not found", file=sys.stderr)
        sys.exit(1)

    content = BACKLOG_PATH.read_text(encoding="utf-8")
    tasks: list[dict] = []

    # Паттерн: | **P1-03** | **Название** | 🟧 High | 8 | ... |
    pattern = re.compile(
        r"\|\s*\*\*(P(\d)-(\d+))\*\*\s*\|\s*(.+?)\s*\|"
        r"\s*(🟥|🟧|🟨|⬜)?\s*(Critical|High|Medium|Low)?\s*\|"
        r"\s*(\d+)\s*\|"
    )

    for match in pattern.finditer(content):
        full_id, phase_str, num, title, moscow_emoji, _priority, hours = match.groups()
        phase = int(phase_str)

        if phase_filter is not None and phase != phase_filter:
            continue

        tasks.append({
            "id": full_id,
            "phase": phase,
            "title": title.strip(),
            "moscow": MOSCOW_LABELS.get(moscow_emoji or "🟧", "should"),
            "hours": int(hours),
        })

    return tasks


def graphql(query: str, variables: dict | None = None) -> dict:
    response = requests.post(
        f"{GITHUB_API}/graphql",
        json={"query": query, "variables": variables or {}},
        headers=get_headers(),
    )
    if response.status_code != 200:
        print(f"❌ GraphQL error: {response.status_code}", file=sys.stderr)
        print(response.text, file=sys.stderr)
        sys.exit(1)
    return response.json()


def get_project_id(project_number: int) -> str:
    """Получает global ID Project V2."""
    query = """
    query($owner: String!, $repo: String!, $number: Int!) {
      repository(owner: $owner, name: $repo) {
        projectV2(number: $number) { id }
      }
    }
    """
    data = graphql(query, {
        "owner": REPO_OWNER,
        "repo": REPO_NAME,
        "number": project_number,
    })
    project = data.get("data", {}).get("repository", {}).get("projectV2")
    if not project:
        print(f"❌ Project V2 #{project_number} not found in {REPO_OWNER}/{REPO_NAME}",
              file=sys.stderr)
        sys.exit(1)
    return project["id"]


def issue_exists(task_id: str) -> bool:
    """Проверяет, существует ли уже issue с таким task ID."""
    response = requests.get(
        f"{GITHUB_API}/search/issues",
        params={"q": f"repo:{REPO_OWNER}/{REPO_NAME} {task_id} in:title"},
        headers=get_headers(),
    )
    if response.status_code != 200:
        return False
    return response.json().get("total_count", 0) > 0


def create_issue(task: dict, milestone: str | None) -> int | None:
    """Создаёт issue и возвращает её номер."""
    phase_label, _ = PHASE_LABELS.get(task["phase"], ("phase-?", None))
    labels = ["production", phase_label, task["moscow"]]

    body = (
        f"## {task['id']}: {task['title']}\n\n"
        f"**Phase:** {task['phase']}  \n"
        f"**MoSCoW:** {task['moscow']}  \n"
        f"**Estimate:** {task['hours']} ч\n\n"
        f"### Definition of Done\n"
        f"- [ ] Код реализован\n"
        f"- [ ] Тесты добавлены / обновлены\n"
        f"- [ ] CI зелёный\n"
        f"- [ ] PR смёржен\n\n"
        f"_Auto-created from PRODUCTION_BACKLOG.md by `scripts/seed_project_board.py`_"
    )

    payload = {"title": f"[{task['id']}] {task['title']}", "body": body, "labels": labels}
    if milestone:
        payload["milestone"] = milestone

    response = requests.post(
        f"{GITHUB_API}/repos/{REPO_OWNER}/{REPO_NAME}/issues",
        json=payload,
        headers=get_headers(),
    )
    if response.status_code != 201:
        print(f"❌ Failed to create {task['id']}: {response.status_code}",
              file=sys.stderr)
        print(response.text, file=sys.stderr)
        return None
    return response.json()["number"]


def add_to_project(project_id: str, issue_node_id: str) -> bool:
    """Добавляет issue в Project V2."""
    mutation = """
    mutation($projectId: ID!, $contentId: ID!) {
      addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
        item { id }
      }
    }
    """
    data = graphql(mutation, {
        "projectId": project_id,
        "contentId": issue_node_id,
    })
    return "errors" not in data


def get_issue_node_id(issue_number: int) -> str | None:
    """Получает global node ID по номеру issue."""
    response = requests.get(
        f"{GITHUB_API}/repos/{REPO_OWNER}/{REPO_NAME}/issues/{issue_number}",
        headers=get_headers(),
    )
    if response.status_code != 200:
        return None
    return response.json().get("node_id")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--project", type=int, default=1, help="Project V2 number")
    parser.add_argument("--milestone", default="v1.0.0", help="Target milestone")
    parser.add_argument("--phase", type=int, choices=[0, 1, 2, 3, 4, 5],
                        help="Filter by phase (0-5)")
    parser.add_argument("--limit", type=int, help="Max issues to create")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be created without making changes")
    args = parser.parse_args()

    tasks = parse_backlog(phase_filter=args.phase)
    print(f"📋 Parsed {len(tasks)} tasks from PRODUCTION_BACKLOG.md")
    if args.phase is not None:
        print(f"   (filtered to Phase {args.phase})")

    if args.dry_run:
        print("\n--- DRY RUN MODE — no changes will be made ---\n")
        for t in tasks[:args.limit] if args.limit else tasks:
            exists = issue_exists(t["id"])
            status = "⏭️  EXISTS" if exists else "✨ WOULD CREATE"
            print(f"{status}: [{t['id']}] {t['title']} "
                  f"({t['hours']}ч, {t['moscow']})")
        return

    project_id = get_project_id(args.project)
    print(f"✅ Project V2 #{args.project} ID: {project_id}")

    created = 0
    skipped = 0
    failed = 0

    for t in tasks if not args.limit else tasks[:args.limit]:
        if issue_exists(t["id"]):
            print(f"⏭️  {t['id']}: already exists, skipping")
            skipped += 1
            continue

        print(f"✨ Creating {t['id']}: {t['title']}...")
        issue_number = create_issue(t, args.milestone)
        if not issue_number:
            failed += 1
            continue

        node_id = get_issue_node_id(issue_number)
        if not node_id:
            print(f"⚠️  Created issue #{issue_number} but failed to get node_id",
                  file=sys.stderr)
            failed += 1
            continue

        if add_to_project(project_id, node_id):
            created += 1
        else:
            failed += 1

    print(f"\n📊 Summary: {created} created, {skipped} skipped, {failed} failed")


if __name__ == "__main__":
    main()
