#!/usr/bin/env python3
"""Healthcheck for the graphify-out inferred pipeline.

Verifies internal consistency of inferred_clean.enriched.jsonl:
  c1: enriched file exists
  c2: clean file exists
  c3: relation diversity (>= 7 types)
  c4: override contract (7/7 cross-file edges) - skips if memory_overrides.json absent
  c5: tiers present (T1, T2, T3) and T1 has recall_score spread
  c6: recall_score range [0, 1]
"""
import json
import os
import sys
from collections import Counter
from pathlib import Path

REPO = Path(os.environ.get("REPO_ROOT", Path(__file__).resolve().parents[1]))

ENRICHED = REPO / "graphify-out" / "inferred_clean.enriched.jsonl"
CLEAN = REPO / "graphify-out" / "inferred_clean.jsonl"
MEMORY_OVERRIDES = REPO / "memory_overrides.json"


def _load_edges(path):
    if not path.exists():
        return None
    out = []
    with open(path) as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return out


def check_file_exists(path):
    if not path.exists():
        return False, f"File not found: {path}"
    return True, "OK"


def check_relations():
    edges = _load_edges(ENRICHED)
    if edges is None:
        return False, "enriched file missing"
    c = Counter(e.get("relation") for e in edges)
    if len(c) < 7:
        return False, f"Only {len(c)} relation types, expected >= 7 ({dict(c)})"
    return True, f"{len(c)} relation types"


def check_override():
    if not MEMORY_OVERRIDES.exists():
        print("  [info] memory_overrides.json not found, skipping override contract check")
        return True, "skipped (no memory_overrides.json)"

    with open(MEMORY_OVERRIDES) as f:
        overrides_data = json.load(f)
    if isinstance(overrides_data, list):
        override_pairs = [(e.get("source"), e.get("target")) for e in overrides_data]
    elif isinstance(overrides_data, dict) and "overrides" in overrides_data:
        override_pairs = [(e.get("source"), e.get("target")) for e in overrides_data["overrides"]]
    else:
        return False, "unsupported memory_overrides.json format"

    edges = _load_edges(ENRICHED)
    if edges is None:
        return False, "enriched file missing"
    edge_set = {(e.get("source"), e.get("target")) for e in edges}
    missing = [f"({s}, {t})" for s, t in override_pairs if (s, t) not in edge_set]
    if missing:
        return False, f"missing override pairs: {', '.join(missing)}"
    return True, f"all {len(override_pairs)} override pairs present"


def check_tiers():
    edges = _load_edges(ENRICHED)
    if edges is None:
        return False, "enriched file missing"
    c = Counter(e.get("tier") for e in edges)
    for t in ("T1", "T2", "T3"):
        if t not in c:
            return False, f"missing tier {t}: {dict(c)}"
    t1_scores = [e.get("recall_score", 0) for e in edges if e.get("tier") == "T1"]
    spread = len(set(t1_scores))
    if spread < 2:
        return False, f"T1 has only {spread} unique recall_score values"
    return True, f"T1={c['T1']}, T2={c['T2']}, T3={c['T3']}, T1 spread={spread}"


def check_recall_score_range():
    edges = _load_edges(ENRICHED)
    if edges is None:
        return False, "enriched file missing"
    scores = [e.get("recall_score", 0) for e in edges]
    if min(scores) < 0 or max(scores) > 1.01:
        return False, f"recall_score out of [0,1]: min={min(scores)}, max={max(scores)}"
    return True, f"recall_score in [0,1] (min={min(scores):.3f}, max={max(scores):.3f})"


def check_health():
    checks = [
        ("c1: enriched file exists", lambda: check_file_exists(ENRICHED)),
        ("c2: clean file exists", lambda: check_file_exists(CLEAN)),
        ("c3: relation diversity >= 7", check_relations),
        ("c4: override 7/7", check_override),
        ("c5: tiers present + T1 spread", check_tiers),
        ("c6: recall_score range [0,1]", check_recall_score_range),
    ]
    all_passed = True
    for name, fn in checks:
        ok, msg = fn()
        print(f"{'PASS' if ok else 'FAIL'} {name}: {msg}")
        if not ok:
            all_passed = False
    return all_passed


if __name__ == "__main__":
    sys.exit(0 if check_health() else 1)
