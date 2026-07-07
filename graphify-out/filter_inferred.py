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
import os
from pathlib import Path

# Resolve workspace from $WORKSPACE or $ASTROFIN_WORKSPACE, fall back to CWD.
# CWD is the canonical fallback because this script is invoked from the repo
# root (e.g. CI: `python graphify-out/filter_inferred.py`). Using
# ~/workspace would silently point at a non-existent dir in containers/agents
# whose $HOME is /root.
WORKSPACE = Path(
    os.environ.get("WORKSPACE")
    or os.environ.get("ASTROFIN_WORKSPACE")
    or Path.cwd()
).resolve()
INPUT = WORKSPACE / "graphify-out" / "inferred_clean.jsonl"
OUTPUT = WORKSPACE / "graphify-out" / "inferred_clean_filtered.jsonl"

# Files whose source_file should not generate INFERRED edges.
# - README.md, CLAUDE.md, etc. parse as "containers" of every symbol in the repo.
# - _archived/ holds dead/superseded code that the validator correctly tags outdated.
SKIP_SOURCE_PATH_SUBSTRINGS = ("/_archived/", "_archived/")
SKIP_SOURCE_PATH_SUFFIXES = (".md", ".markdown")


def keep(edge: dict) -> bool:
    """Decide whether an inferred edge should be kept.

    An edge is dropped if EITHER ``source_path`` or ``source_file``:
      - is missing/empty,
      - contains ``_archived/`` substring,
      - ends with ``.md`` or ``.markdown``.

    These represent parser artifacts (markdown docs parsed as containers
    of every repo symbol, or dead/superseded code) rather than real code links.
    """
    sources = (edge.get("source_path") or "", edge.get("source_file") or "")
    if not any(sources):
        return False
    for src in sources:
        if not src:
            continue
        if any(sub in src for sub in SKIP_SOURCE_PATH_SUBSTRINGS):
            return False
        if src.endswith(SKIP_SOURCE_PATH_SUFFIXES):
            return False
    return True


def main() -> None:
    """Stream the inferred edges, filter via :func:`keep`, write the survivors.

    Reads JSONL from :data:`INPUT`, writes JSONL to :data:`OUTPUT`, and prints
    ``read`` / ``written`` / ``dropped`` counters plus the output path. The
    drop percentage is guarded against zero-division on an empty input.
    """
    edges = [json.loads(line) for line in INPUT.open() if line.strip()]
    before = len(edges)
    kept = [e for e in edges if keep(e)]
    after = len(kept)
    drop_pct = (100.0 * (before - after) / before) if before > 0 else 0.0

    with OUTPUT.open("w") as f:
        for e in kept:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    print(f"read    : {before}")
    print(f"written : {after}")
    print(f"dropped : {before - after} ({drop_pct:.1f}%)")
    print(f"output  : {OUTPUT}")


if __name__ == "__main__":
    main()
