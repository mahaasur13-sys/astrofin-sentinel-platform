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
SAMPLE_BALANCED = REPO / "graphify-out" / "inferred_sample_balanced.jsonl"
SAMPLE_CLEAN = REPO / "graphify-out" / "inferred_sample_clean.jsonl"
SAMPLE_DROPPED = REPO / "graphify-out" / "inferred_sample_dropped.jsonl"

# c7 thresholds (ADR-0006 + CI gate). Tuned on 2026-06-25 clean sample:
# - valid rate must be >= 50% (otherwise our recall is broken)
# - false rate must be < 5% (otherwise false positives pollute memory)
# - sample size after filtering must be >= 200 (statistical power)
VALID_RATE_MIN = float(os.environ.get("HEALTHCHECK_VALID_MIN", "0.50"))
FALSE_RATE_MAX = float(os.environ.get("HEALTHCHECK_FALSE_MAX", "0.05"))
SAMPLE_MIN = int(os.environ.get("HEALTHCHECK_SAMPLE_MIN", "200"))


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


def filter_sample_by_existing_paths(in_path: Path, out_path: Path,
                                  dropped_path: Path) -> tuple:
    """Filter edges whose source_path/target_path exist as files in repo.

    Returns (n_in, n_out, n_drop, drop_reasons_counter, kept_relations_counter).
    """
    if not in_path.exists():
        return (0, 0, 0, Counter(), Counter())
    n_in = n_out = n_drop = 0
    drop_reasons = Counter()
    kept_relations = Counter()
    with in_path.open() as r, out_path.open("w") as w, dropped_path.open("w") as d:
        for line in r:
            if not line.strip():
                continue
            n_in += 1
            rec = json.loads(line)
            sp = rec.get("source_path") or ""
            tp = rec.get("target_path") or ""
            if not sp or not tp:
                drop_reasons["missing_path_field"] += 1
                d.write(line if line.endswith("\n") else line + "\n")
                n_drop += 1
                continue
            sp_abs = (REPO / sp).resolve()
            tp_abs = (REPO / tp).resolve()
            if not sp_abs.is_file():
                drop_reasons["source_missing"] += 1
                d.write(line if line.endswith("\n") else line + "\n")
                n_drop += 1
                continue
            if not tp_abs.is_file():
                drop_reasons["target_missing"] += 1
                d.write(line if line.endswith("\n") else line + "\n")
                n_drop += 1
                continue
            w.write(line if line.endswith("\n") else line + "\n")
            kept_relations[rec.get("relation", "unknown")] += 1
            n_out += 1
    return (n_in, n_out, n_drop, drop_reasons, kept_relations)


def _parse_validate_report(report: Path) -> dict:
    """Parse 'verdicts: {...}' line from docs/VALIDATION_REPORT.md header."""
    if not report.exists():
        return {}
    for line in report.read_text().splitlines()[:15]:
        line = line.strip()
        if (line.lower().startswith("verdict summary") or
            line.lower().startswith("verdict breakdown") or
            line.lower().lstrip("*").strip().startswith("verdict summary") or
            line.lower().lstrip("*").strip().startswith("verdict breakdown")):
            # Try parenthesized form first: "valid=X (Y%), ambiguous=..."
            import re
            m = re.findall(r"`(\w+)`\s*=\s*(\d+)", line)
            if m:
                return {k: int(v) for k, v in m}
    return {}


def check_validation_verdicts():
    # Ensure clean sample is up-to-date
    if not SAMPLE_BALANCED.exists():
        return False, "balanced sample missing (run build_sample.py first)"
    n_in, n_out, n_drop, reasons, kept = filter_sample_by_existing_paths(
        SAMPLE_BALANCED, SAMPLE_CLEAN, SAMPLE_DROPPED
    )
    if n_out < SAMPLE_MIN:
        return False, (
            f"clean sample too small: {n_out} < {SAMPLE_MIN} "
            f"(in={n_in}, drop={n_drop}, reasons={dict(reasons)})"
        )
    # Run validate_inferred.py
    import subprocess
    try:
        proc = subprocess.run(
            ["python3", str(REPO / "graphify-out" / "validate_inferred.py"),
             str(SAMPLE_CLEAN)],
            capture_output=True, text=True, timeout=300,
        )
    except subprocess.TimeoutExpired:
        return False, "validate_inferred.py timed out (>300s)"
    if proc.returncode != 0:
        return False, f"validate_inferred.py exit={proc.returncode}: {proc.stderr[-200:]}"
    report = REPO / "docs" / "VALIDATION_REPORT.md"
    verdicts = _parse_validate_report(report)
    if not verdicts:
        return False, "could not parse VALIDATION_REPORT.md verdict line"
    total = sum(verdicts.values())
    if total == 0:
        return False, "empty verdict counts"
    valid_rate = verdicts.get("valid", 0) / total
    false_rate = verdicts.get("false", 0) / total
    ok = valid_rate >= VALID_RATE_MIN and false_rate < FALSE_RATE_MAX
    msg = (
        f"verdicts={verdicts}, "
        f"valid_rate={valid_rate:.1%} (>= {VALID_RATE_MIN:.0%}), "
        f"false_rate={false_rate:.1%} (< {FALSE_RATE_MAX:.0%}), "
        f"sample={n_out}/{n_in}, types={len(kept)}"
    )
    return ok, msg


def check_health():
    checks = [
        ("c1: enriched file exists", lambda: check_file_exists(ENRICHED)),
        ("c2: clean file exists", lambda: check_file_exists(CLEAN)),
        ("c3: relation diversity >= 7", check_relations),
        ("c4: override 7/7", check_override),
        ("c5: tiers present + T1 spread", check_tiers),
        ("c6: recall_score range [0,1]", check_recall_score_range),
        ("c7: validation verdicts (valid>=50%, false<5%)", check_validation_verdicts),
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
