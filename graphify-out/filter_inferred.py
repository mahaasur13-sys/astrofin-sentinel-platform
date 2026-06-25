#!/usr/bin/env python3
"""filter_inferred.py — exclude INFERRED edges whose source_file is a
.markdown/.md file or points under _archived/. Such edges are parser
artifacts (docs parsed as 'containers') rather than real code links.

Reads:  graphify-out/inferred_clean.jsonl   (JSONL stream)
Writes: graphify-out/inferred_clean_filtered.jsonl

The script is deterministic and side-effect-free outside the output file.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

WORKSPACE = Path("/home/workspace")
INPUT = WORKSPACE / "graphify-out" / "inferred_clean.jsonl"
OUTPUT = WORKSPACE / "graphify-out" / "inferred_clean_filtered.jsonl"

# Files whose source_file should not generate INFERRED edges.
# - README.md, CLAUDE.md, etc. parse as "containers" of every symbol in the repo.
# - _archived/ holds dead/superseded code that the validator correctly tags outdated.
SKIP_SOURCE_PATH_SUBSTRINGS = ("/_archived/", "_archived/")
SKIP_SOURCE_PATH_SUFFIXES = (".md", ".markdown")


def keep(edge: dict) -> bool:
    src = edge.get("source_path") or edge.get("source_file") or ""
    if not src:
        return False
    if any(s in src for s in SKIP_SOURCE_PATH_SUBSTRINGS):
        return False
    if src.endswith(SKIP_SOURCE_PATH_SUFFIXES):
        return False
    return True


def main() -> None:
    edges = [json.loads(line) for line in INPUT.open() if line.strip()]
    before = len(edges)
    kept = [e for e in edges if keep(e)]
    after = len(kept)

    with OUTPUT.open("w") as f:
        for e in kept:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    print(f"read    : {before}")
    print(f"written : {after}")
    print(f"dropped : {before - after} ({100*(before-after)/before:.1f}%)")
    print(f"output  : {OUTPUT}")


if __name__ == "__main__":
    main()