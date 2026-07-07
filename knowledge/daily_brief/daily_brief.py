#!/usr/bin/env python3
"""
Daily Brief — Parse email summaries and suggest ATOM ideas.

Usage:
    python knowledge/daily_brief/daily_brief.py --latest        # Show latest brief
    python knowledge/daily_brief/daily_brief.py --list         # List all briefs
    python knowledge/daily_brief/daily_brief.py --ideas         # Generate ATOM ideas
    python knowledge/daily_brief/daily_brief.py --parse FILE   # Parse specific file
"""

from __future__ import annotations
import argparse
import re
from datetime import datetime, timedelta
from pathlib import Path

BRIEF_DIR = Path(__file__).parent
BRIEF_GLOB = "brief_????-??-??.md"
DAYS_TO_KEEP = 30


def get_latest_brief():
    """Find most recent brief file."""
    briefs = sorted(BRIEF_DIR.glob(BRIEF_GLOB), reverse=True)
    if not briefs:
        return None
    return briefs[0]


def list_briefs():
    """List all stored briefs."""
    briefs = sorted(BRIEF_DIR.glob(BRIEF_GLOB), reverse=True)
    if not briefs:
        print("No briefs stored.")
        return []
    print(f"\n=== Stored Briefs ({len(briefs)} found) ===")
    for b in briefs:
        stat = b.stat()
        dt = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        print(f"  {b.name}  (modified: {dt})")
    return briefs


def parse_brief_content(content: str) -> dict:
    """Parse brief markdown into structured sections."""
    result = {"date": None, "items": [], "raw": content}

    # Extract date from subject or first heading
    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", content)
    if date_match:
        result["date"] = date_match.group(1)

    # Extract bullet points (## Item, ### Item, or **Item**)
    item_pattern = re.compile(r"^\s*[-*•]\s*(.+?)(?:\n|$)", re.MULTILINE)
    items = []
    for m in item_pattern.finditer(content):
        text = m.group(1).strip()
        if len(text) > 20:  # Filter short noise
            items.append(text)
    result["items"] = items

    return result


def generate_ideas(brief_content: str) -> list:
    """Generate ATOM improvement ideas from brief content."""
    ideas = []

    # Detect patterns in brief
    has_tool_release = any(kw in brief_content.lower() for kw in ["github", "release", "tool", "framework"])
    has_research = any(kw in brief_content.lower() for kw in ["arxiv", "paper", "research", "study"])
    has_community = any(kw in brief_content.lower() for kw in ["reddit", "hacker news", "discussion", "forum"])

    if has_tool_release:
        ideas.append(
            {
                "category": "TOOL_ADOPTION",
                "prompt": "Рассмотреть возможность интеграции нового инструмента из сводки в AstroFinSentinelV5. Проверить: совместимость с существующей архитектурой, необходимость ATOM-карточки.",
            }
        )

    if has_research:
        ideas.append(
            {
                "category": "RESEARCH_INTEGRATION",
                "prompt": "Найдены новые исследования. Оценить применимость для: (1) улучшения reward function, (2) новых фичей в агентах, (3) оптимизации KARL-цикла.",
            }
        )

    if has_community:
        ideas.append(
            {
                "category": "COMMUNITY_SENTIMENT",
                "prompt": "Обсуждения сообщества указывают на тренды. Проанализировать sentiment: какие проблемы пользователей можно решить через новые ATOM-карточки?",
            }
        )

    # Always suggest something
    ideas.append(
        {
            "category": "CONTINUOUS_IMPROVEMENT",
            "prompt": "Использовать данные сводки для обновления ATOM-KARL backlog. Добавить новые ideas в knowledge/ATOM_BACKLOG.md.",
        }
    )

    return ideas


def ideas_to_tracker(ideas: list, source: str = "daily_brief"):
    """Import ideas into idea_tracker."""
    try:
        from knowledge.daily_brief.idea_tracker import (
            IdeaStatus,
            create_idea,
            load_ideas,
            save_idea,
        )

        imported = 0
        skipped = 0

        existing = load_ideas()
        existing_texts = {i.text for i in existing}

        for idea_data in ideas:
            text = idea_data.get("prompt", idea_data.get("text", ""))
            category = idea_data.get("category", "GENERAL")

            if text in existing_texts:
                skipped += 1
                continue

            idea = create_idea(text, source, category)
            save_idea(idea)
            imported += 1

        return imported, skipped
    except ImportError as e:
        print(f"Warning: idea_tracker not available: {e}")
        return 0, 0


def show_brief(path: Path):
    """Display brief content."""
    content = path.read_text()
    parsed = parse_brief_content(content)

    print(f"\n{'=' * 60}")
    print(f"  Brief: {path.name}")
    print(f"{'=' * 60}\n")

    # Show items
    if parsed["items"]:
        print("### Key Items\n")
        for i, item in enumerate(parsed["items"], 1):
            print(f"  {i}. {item[:100]}{'...' if len(item) > 100 else ''}")
        print()

    # Show ideas
    ideas = generate_ideas(content)
    if ideas:
        print("### Suggested ATOM Ideas\n")
        for idea in ideas:
            print(f"  [{idea['category']}]")
            print(f"    → {idea['prompt']}\n")


def garbage_collect():
    """Remove briefs older than DAYS_TO_KEEP."""
    cutoff = datetime.now() - timedelta(days=DAYS_TO_KEEP)
    removed = 0
    for path in BRIEF_DIR.glob(BRIEF_GLOB):
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        if mtime < cutoff:
            path.unlink()
            removed += 1
    return removed


def main():
    parser = argparse.ArgumentParser(description="Daily Brief CLI")
    parser.add_argument("--latest", action="store_true", help="Show latest brief")
    parser.add_argument("--list", action="store_true", help="List all briefs")
    parser.add_argument("--ideas", action="store_true", help="Generate ATOM ideas from latest")
    parser.add_argument("--parse", type=str, help="Parse specific brief file")
    parser.add_argument("--gc", action="store_true", help="Garbage collect old briefs")
    parser.add_argument("--save", type=str, help="Save brief content (for webhook/email)")
    parser.add_argument("--track", action="store_true", help="Import ideas into idea_tracker")

    args = parser.parse_args()

    # Garbage collect old briefs
    if args.gc:
        removed = garbage_collect()
        print(f"Removed {removed} old briefs.")
        return

    if args.save:
        # Save new brief
        today = datetime.now().strftime("%Y-%m-%d")
        path = BRIEF_DIR / f"brief_{today}.md"
        path.write_text(args.save)

        # Update symlink
        latest = BRIEF_DIR / "brief_latest.md"
        if latest.exists():
            latest.unlink()
        latest.symlink_to(path.name)

        print(f"Saved: {path}")
        return

    if args.parse:
        path = Path(args.parse)
        if not path.is_absolute():
            path = BRIEF_DIR / path
        if path.exists():
            show_brief(path)
        else:
            print(f"File not found: {path}")
        return

    if args.latest or args.ideas:
        path = get_latest_brief()
        if path:
            show_brief(path)
            if args.ideas:
                ideas = generate_ideas(path.read_text())
                print("\n### ATOM Ideas for This Brief\n")
                for idea in ideas:
                    print(f"  [{idea['category']}]")
                    print(f"    → {idea['prompt']}\n")
        else:
            print("No briefs found. Run with --gc to clean up or wait for next daily email.")
        return

    if args.list:
        list_briefs()
        return

    # Default: show latest
    path = get_latest_brief()
    if path:
        show_brief(path)
    else:
        print("No briefs stored. Use --save to add one.")


if __name__ == "__main__":
    main()
