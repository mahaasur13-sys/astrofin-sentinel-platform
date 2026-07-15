#!/usr/bin/env python3
"""
ATOM-R-042: Daily Digest Log

Tracks all processed digests and their outcomes.
Format: Date | Source | Key Ideas | Status | Linked ATOMs

Usage:
    python knowledge/daily_digest/daily_digest_log.py --log 2026-03-29 --ideas "Pressure Field, CrewAI"
    python knowledge/daily_digest/daily_digest_log.py --list --limit 10
    python knowledge/daily_digest/daily_digest_log.py --status PROPOSED
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class DigestStatus(Enum):
    PROCESSED = "PROCESSED"
    ANALYZED = "ANALYZED"
    PROPOSED = "PROPOSED"
    ACCEPTED = "ACCEPTED"
    IMPLEMENTED = "IMPLEMENTED"
    REJECTED = "REJECTED"


@dataclass
class DigestEntry:
    """A single digest log entry."""

    date: str
    source: str  # email, webhook, file
    key_ideas: list  # Top 3 ideas from digest
    status: str = DigestStatus.PROCESSED.value
    linked_atoms: list = field(default_factory=list)
    notes: str = ""
    processed_at: str = field(default_factory=lambda: datetime.now().isoformat())


class DigestLog:
    """Tracks digest processing history."""

    LOG_FILE = Path(__file__).parent / "daily_digest_log.md"

    # Markdown table header
    TABLE_HEADER = """| Date | Source | Key Ideas | Status | Linked ATOMs |
|-------|--------|-----------|--------|--------------|
"""

    def __init__(self):
        self.entries: list[DigestEntry] = []
        self._load()

    def _load(self):
        """Load entries from markdown file."""
        if not self.LOG_FILE.exists():
            self.entries = []
            return

        content = self.LOG_FILE.read_text()

        # Parse markdown table
        entries = []
        for line in content.split("\n"):
            if (
                line.startswith("|")
                and not line.startswith("|--")
                and "Date" not in line
            ):
                parts = [p.strip() for p in line.split("|")[1:-1]]
                if len(parts) >= 4:
                    entry = DigestEntry(
                        date=parts[0],
                        source=parts[1],
                        key_ideas=parts[2].split(", ") if parts[2] else [],
                        status=parts[3],
                        linked_atoms=(
                            parts[4].split(", ") if len(parts) > 4 and parts[4] else []
                        ),
                    )
                    entries.append(entry)

        self.entries = entries

    def _save(self):
        """Save entries to markdown file."""
        lines = [
            "# Daily Digest Log",
            "",
            f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            self.TABLE_HEADER.strip(),
        ]

        for e in sorted(self.entries, key=lambda x: x.date, reverse=True):
            ideas_str = ", ".join(e.key_ideas[:3])
            atoms_str = ", ".join(e.linked_atoms) if e.linked_atoms else "—"
            lines.append(
                f"| {e.date} | {e.source} | {ideas_str} | {e.status} | {atoms_str} |"
            )

        self.LOG_FILE.write_text("\n".join(lines), encoding="utf-8")

    def add_entry(
        self, date: str, source: str, key_ideas: list, status: str = None
    ) -> DigestEntry:
        """Add a new digest entry."""
        # Check if entry for date exists
        for e in self.entries:
            if e.date == date:
                # Update existing
                e.source = source
                e.key_ideas = key_ideas
                if status:
                    e.status = status
                e.processed_at = datetime.now().isoformat()
                self._save()
                return e

        entry = DigestEntry(
            date=date,
            source=source,
            key_ideas=key_ideas,
            status=status or DigestStatus.PROCESSED.value,
        )
        self.entries.append(entry)
        self._save()
        return entry

    def update_status(self, date: str, status: str, linked_atoms: list = None):
        """Update status for an entry."""
        for e in self.entries:
            if e.date == date:
                e.status = status
                if linked_atoms:
                    e.linked_atoms.extend(linked_atoms)
                e.processed_at = datetime.now().isoformat()
                self._save()
                return e
        return None

    def get_by_status(self, status: str) -> list[DigestEntry]:
        """Get entries by status."""
        return [e for e in self.entries if e.status == status]

    def get_by_date(self, date: str) -> DigestEntry | None:
        """Get entry by date."""
        for e in self.entries:
            if e.date == date:
                return e
        return None

    def list_entries(self, limit: int = 50, status_filter: str = None):
        """List entries."""
        entries = self.entries
        if status_filter:
            entries = [e for e in entries if e.status == status_filter]

        entries = sorted(entries, key=lambda x: x.date, reverse=True)[:limit]

        if not entries:
            print("No entries found.")
            return

        print(f"\n{'=' * 80}")
        print(f"  📔 DAILY DIGEST LOG — {len(entries)} entries")
        print(f"{'=' * 80}\n")
        print(f"{'Date':<12} {'Source':<12} {'Status':<12} {'Key Ideas':<35} {'ATOMs'}")
        print("-" * 80)

        for e in entries:
            ideas = ", ".join(e.key_ideas[:2])[:33]
            atoms = ", ".join(e.linked_atoms) if e.linked_atoms else "—"
            print(f"{e.date:<12} {e.source:<12} {e.status:<12} {ideas:<35} {atoms}")

        print(f"\nTotal: {len(entries)} entries")

    def get_stats(self) -> dict:
        """Get statistics."""
        if not self.entries:
            return {}

        status_counts = {}
        for e in self.entries:
            status_counts[e.status] = status_counts.get(e.status, 0) + 1

        return {
            "total": len(self.entries),
            "by_status": status_counts,
            "dates_processed": [e.date for e in self.entries],
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Daily Digest Log")
    parser.add_argument("--log", type=str, help="Add log entry for date")
    parser.add_argument(
        "--source", type=str, default="email", help="Source (email, webhook, file)"
    )
    parser.add_argument("--ideas", type=str, help="Comma-separated key ideas")
    parser.add_argument("--status", type=str, help="Set status for --log")
    parser.add_argument("--list", action="store_true", help="List all entries")
    parser.add_argument("--limit", type=int, default=50, help="Limit for --list")
    parser.add_argument("--filter", type=str, help="Filter by status")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--update", type=str, help="Update status for date")
    parser.add_argument("--atoms", type=str, help="Linked ATOMs for --update")

    args = parser.parse_args()

    log = DigestLog()

    if args.log:
        ideas = []
        if args.ideas:
            ideas = [i.strip() for i in args.ideas.split(",")]

        entry = log.add_entry(args.log, args.source, ideas, args.status)
        print(f"Logged: {entry.date} [{entry.status}]")
        return

    if args.update:
        atoms = []
        if args.atoms:
            atoms = [a.strip() for a in args.atoms.split(",")]

        entry = log.update_status(args.update, args.status or "PROCESSED", atoms)
        if entry:
            print(f"Updated: {entry.date} → {entry.status}")
        else:
            print(f"Entry not found: {args.update}")
        return

    if args.stats:
        stats = log.get_stats()
        print(f"\n{'=' * 50}")
        print("  📊 DIGEST LOG STATISTICS")
        print(f"{'=' * 50}")
        print(f"  Total digests: {stats.get('total', 0)}")
        print("\n  By status:")
        for status, count in stats.get("by_status", {}).items():
            print(f"    {status}: {count}")
        return

    if args.list:
        log.list_entries(limit=args.limit, status_filter=args.filter)
        return

    # Default: show recent
    log.list_entries(limit=args.limit)


if __name__ == "__main__":
    main()
