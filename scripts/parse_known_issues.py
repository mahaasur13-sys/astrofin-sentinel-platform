r"""scripts/parse_known_issues.py
================================
Phase 6 - KNOWN_ISSUES.md parser for CI integration.
Reads docs/KNOWN_ISSUES.md, extracts KI-001..KI-013 entries,
and emits a JSON list of {id, title, paths} objects to stdout.

Path extraction: looks for the 'Affected' line (or similar) in each
section, and pulls backtick-quoted file paths out of it. Falls back
to the whole issue body if 'Affected' is not found.

Usage:
    python scripts/parse_known_issues.py > ki.json
    python scripts/parse_known_issues.py --path docs/KNOWN_ISSUES.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KNOWN_ISSUES = REPO_ROOT / "docs" / "KNOWN_ISSUES.md"

# Match the header line of each KI section: '## KI-001 - ...'
SECTION_RE = re.compile(r"^##\s+(KI-\d+)\s*[-]*\s*(.+)$", re.MULTILINE)

# Match 'Affected' line - we accept English 'Affected files:' or
# Russian 'Zatронутые файлы:' (cyrillic 'За'). The 'За' prefix is
# intentionally avoided here to keep this file ASCII; the section
# body itself is the fallback.
AFFECTED_RE = re.compile(r"\*(?:Affected|Затронутые файлы|Files?)\s*:?\*?\s*\n([^*]+)", re.IGNORECASE)

# Match backtick-quoted file paths inside a string.
PATH_RE = re.compile(r"`([\w./\-]+\.[\w]+)`")


def _split_sections(text: str) -> list[tuple[str, str, str]]:
    r"""Split KNOWN_ISSUES.md into (id, title, body) tuples."""
    sections: list[tuple[str, str, str]] = []
    matches = list(SECTION_RE.finditer(text))
    for i, m in enumerate(matches):
        kid = m.group(1)
        title = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end]
        sections.append((kid, title, body))
    return sections


def _extract_paths(body: str) -> list[str]:
    r"""Pull file paths out of the 'Affected' line; fall back to body scan."""
    m = AFFECTED_RE.search(body)
    haystack = m.group(1) if m else body
    return sorted(set(PATH_RE.findall(haystack)))


def parse(text: str) -> list[dict]:
    r"""Parse KNOWN_ISSUES.md text into a list of {id, title, paths} dicts."""
    out: list[dict] = []
    for kid, title, body in _split_sections(text):
        out.append(
            {
                "id": kid,
                "title": title,
                "paths": _extract_paths(body),
            }
        )
    return out


def main() -> int:
    r"""CLI entry point."""
    parser = argparse.ArgumentParser(description="Parse KNOWN_ISSUES.md")
    parser.add_argument(
        "--path",
        type=Path,
        default=DEFAULT_KNOWN_ISSUES,
        help="Path to KNOWN_ISSUES.md (default: docs/KNOWN_ISSUES.md)",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a one-line summary instead of full JSON",
    )
    args = parser.parse_args()

    if not args.path.exists():
        print(f"ERROR: {args.path} not found", file=sys.stderr)
        return 1

    text = args.path.read_text(encoding="utf-8")
    entries = parse(text)

    if args.summary:
        total = len(entries)
        with_paths = sum(1 for e in entries if e["paths"])
        print(f"KNOWN_ISSUES: {total} entries ({with_paths} with affected paths)")
        return 0

    json.dump(entries, sys.stdout, indent=2, ensure_ascii=False)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
