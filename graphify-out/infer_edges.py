#!/usr/bin/env python3
"""
infer_edges.py — validated INFERRED-edge export for Hybrid Memory.

Implements the policy from docs/adr/ADR-0004-hybrid-memory-policy.md:
  - tier assignment by verdict + confidence:
      valid & conf >= 0.7  -> T1
      valid & conf <  0.7  -> T2
      ambiguous              -> T2
      false / outdated / moved -> T3
  - half_life by category:
      core: 180d, submodule: 60d, archived: 14d, trash: 14d
  - decay = max(0.05, exp(-delta_days / half_life))
  - manual overrides from config/memory_overrides.json
    keyed by (source_node_id, target_node_id)

Inputs:
  - /home/workspace/graphify-out/graph.json
  - /home/workspace/docs/VALIDATION_REPORT.md (regenerated each run)
  - /home/workspace/config/memory_overrides.json

Outputs:
  - JSONL: one edge per line, fields include tier, category, half_life,
    delta_days, decay_factor, weight, relation, source/target, etc.
  - JSON summary: counts of T1 / T2 / T3 and category breakdown.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path("/home/workspace")
GRAPH_JSON = REPO_ROOT / "graphify-out" / "graph.json"
VALIDATOR = REPO_ROOT / "graphify-out" / "validate_inferred.py"
REPORT_MD = REPO_ROOT / "docs" / "VALIDATION_REPORT.md"
OVERRIDES_JSON = REPO_ROOT / "config" / "memory_overrides.json"

KEEP = {"valid", "ambiguous", "false", "moved", "outdated"}

# Half-life by path category (ADR-0004)
HALF_LIFE_BY_CATEGORY = {
    "core": 180,
    "submodule": 60,
    "archived": 14,
    "trash": 14,
}

# Decay floor: never collapse below 5% influence
DECAY_FLOOR = 0.05
T3_FORCED_DECAY = 0.05  # T3 always sits at floor regardless of source age
TIER_WEIGHT = {"T1": 1.0, "T2": 0.6, "T3": 0.1}
# Tier weight is separate from recall_score because it must remain
# stable across decay, while decay varies with time.

# ADR-0005: relation-level weights. These reflect *semantic strength* of each
# relation type, independent of tier or decay. Hard dependencies (calls, imports,
# inherits) weigh more than transitive ones (references, re_exports).
RELATION_WEIGHTS = {
    "calls": 1.00,
    "contains": 0.95,
    "method": 0.90,
    "imports_from": 0.95,
    "inherits": 0.95,
    "imports": 0.90,
    "defines": 0.85,
    "rationale_for": 0.80,
    "uses": 0.75,
    "references": 0.65,
    "re_exports": 0.70,
}
DEFAULT_RELATION_WEIGHT = 0.50  # unknown / future relation types

_CATEGORY_PRIORITY = {"trash": 4, "archived": 3, "submodule": 2, "core": 1}
_SUBMODULE_PREFIXES = (
    "push/", "atom-federation-os/", "roma-execution-bridge/",
    "local-ai-stack/", "audit_repo/", "agent-runtime/",
    "acos-contracts/", "acos-core/", "sbs/",
)
_CORE_PREFIXES = (
    "core/", "agents/", "orchestration/", "meta_rl/", "ragservice/",
    "astra/", "astrology/", "domain/", "atom-core/", "AsurDev/",
)


def _categorize_one(path: str) -> str:
    p = path.lower()
    if "/trash/" in p or p.startswith("trash/"):
        return "trash"
    if "/_archived/" in p or "/archived/" in p:
        return "archived"
    if "/" not in p:
        return "submodule"
    if p.startswith(_SUBMODULE_PREFIXES):
        return "submodule"
    if p.startswith(_CORE_PREFIXES):
        return "core"
    return "submodule"


def categorize(src_path: str, tgt_path: str) -> tuple[str, int]:
    """Return (effective_category, half_life_days). The more aggressive
    category between source and target wins (archived beats core).
    """
    src_cat = _categorize_one(src_path)
    tgt_cat = _categorize_one(tgt_path)
    if _CATEGORY_PRIORITY[tgt_cat] > _CATEGORY_PRIORITY[src_cat]:
        effective = tgt_cat
    else:
        effective = src_cat
    return effective, HALF_LIFE_BY_CATEGORY[effective]


def load_overrides() -> dict:
    if not OVERRIDES_JSON.exists():
        return {}
    data = json.loads(OVERRIDES_JSON.read_text(encoding="utf-8"))
    out = {}
    for entry in data.get("overrides", []):
        key = (entry["source_node_id"], entry["target_node_id"])
        out[key] = entry
    return out


def tier_for(verdict: str, confidence: float) -> str:
    if verdict == "valid":
        return "T1" if confidence >= 0.7 else "T2"
    if verdict == "ambiguous":
        return "T2"
    if verdict in ("false", "moved", "outdated"):
        return "T3"
    return "T3"


_GIT_MTIME_CACHE: dict[str, int] = {}


def _git_mtime_days(path: str, as_of: datetime) -> int:
    """Return days since last git modification of `path`, or 0 if unknown."""
    if not path or path in _GIT_MTIME_CACHE:
        return _GIT_MTIME_CACHE.get(path, 0)
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", path],
            cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=5,
        )
        ts = int(out.stdout.strip())
        delta = max(0, int((as_of.timestamp() - ts) // 86400))
    except Exception:
        delta = 0
    _GIT_MTIME_CACHE[path] = delta
    return delta


def _normalize_line(s: str) -> str:
    """Strip the parser's accidental 'LL' duplication in source_location."""
    if s.startswith("LL"):
        return s[1:]
    return s


def _git_mtime_days(path: str, as_of) -> int | None:
    """Return days since path was last modified in git, or None if not tracked / unknown."""
    if not path:
        return None
    try:
        ts = subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "log", "-1", "--format=%ct", "--", path],
            stderr=subprocess.DEVNULL, text=True
        ).strip()
        if not ts:
            return None
        delta = (as_of - datetime.fromtimestamp(int(ts), tz=timezone.utc)).days
        return max(delta, 0)
    except Exception:
        return None


def load_graph():
    with GRAPH_JSON.open("r", encoding="utf-8") as f:
        return json.load(f)


def run_validator(sample_path: str = "/tmp/inferred_sample.json"):
    """Re-run validate_inferred.py against a known-good sample.

    The validator's CLI default is a stale /tmp/inferred_sample_500.json.
    We force it onto the fresh sample we just produced (see select_top_inferred.py
    and build_balanced_sample.py). This breaks the historical feedback loop
    where validate_inferred.py kept reading an old 500/'calls'-only sample and
    overwrote the diverse selection.
    """
    if not Path(sample_path).exists():
        raise SystemExit(f"run_validator: sample not found at {sample_path}")
    env = os.environ.copy()
    env["INFERRED_SAMPLE"] = str(sample_path)
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        capture_output=True, text=True, env=env,
    )
    if proc.returncode != 0:
        raise SystemExit(f"validator failed: {proc.stderr}")
    return proc.stdout.strip()


def parse_report():
    text = REPORT_MD.read_text(encoding="utf-8")
    verdicts = []
    current = None
    source = target = confidence = weight = relation = verdict = None
    for line in text.splitlines():
        if line.startswith("### INFERRED #"):
            if current and verdict in KEEP:
                verdicts.append(current)
            current = {}
            source = target = confidence = weight = relation = verdict = None
        elif line.startswith("- **Source:**"):
            source = _clean(line.split("**Source:**", 1)[1].strip())
        elif line.startswith("- **Target:**"):
            target = _clean(line.split("**Target:**", 1)[1].strip())
        elif line.startswith("- **Confidence:**"):
            tail = line.split("**Confidence:**", 1)[1].strip()
            parts = [p.strip() for p in tail.split("  ") if p.strip()]
            for p in parts:
                if p.startswith("**Weight:**"):
                    weight = p.split("**Weight:**", 1)[1].strip()
                elif p.startswith("**Relation:**"):
                    relation = p.split("**Relation:**", 1)[1].strip().strip("`")
                else:
                    confidence = p
        elif line.startswith("- **Verdict:**"):
            verdict = line.split("**Verdict:**", 1)[1].strip().strip("*")
            current = {
                "source": source,
                "target": target,
                "confidence": confidence,
                "weight": weight,
                "relation": relation,
                "verdict": verdict,
            }
    if current and verdict in KEEP:
        verdicts.append(current)
    return verdicts


def _clean(s: str) -> str:
    return s.replace("`", "").strip()


def split_source_target(row: dict):
    """Split 'file:L :: node_id' strings into (path, line, node_id)."""
    def _split(s: str):
        path_line, _, node_id = s.partition("::")
        node_id = node_id.strip()
        if ":" in path_line:
            path, _, line = path_line.rpartition(":")
        else:
            path, line = path_line, ""
        return path.strip(), line.strip(), node_id
    return _split(row["source"]), _split(row["target"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default="", help="Output file path")
    ap.add_argument("--fmt", choices=["jsonl", "json"], default="jsonl")
    ap.add_argument("--as-of", default="", help="ISO date for decay calc (default: now)")
    args = ap.parse_args()

    if not GRAPH_JSON.exists():
        raise SystemExit(f"missing {GRAPH_JSON}")

    run_validator("/tmp/inferred_sample.json")
    kept = parse_report()
    overrides = load_overrides()
    as_of = (datetime.fromisoformat(args.as_of) if args.as_of
             else datetime.now(timezone.utc))

    enriched = []
    tier_counts = {"T1": 0, "T2": 0, "T3": 0}
    cat_counts = {}
    override_hits = 0
    seen_pairs = set()

    g = load_graph()
    node_age_days = {}
    if "nodes" in g:
        for n in g["nodes"]:
            if "last_modified" in n and n["last_modified"]:
                try:
                    dt = datetime.fromisoformat(n["last_modified"].replace("Z", "+00:00"))
                    node_age_days[n["id"]] = (as_of - dt).days
                except Exception:
                    pass

    for row in kept:
        (src_path, src_line, src_node), (tgt_path, tgt_line, tgt_node) = split_source_target(row)
        if src_node == tgt_node:
            continue
        try:
            conf = float(row["confidence"])
        except Exception:
            conf = 0.0
        try:
            w = float(row["weight"])
        except Exception:
            w = 0.0

        key = (src_node, tgt_node)
        if key in overrides:
            ov = overrides[key]
            tier = ov.get("tier", "T3")
            half_life = int(ov.get("half_life", 60))
            cat = ov.get("category", "submodule")
            override_hits += 1
            print(
                f"[override] {src_node} -> {tgt_node} "
                f"tier={ov.get('tier')} hl={ov.get('half_life')}d "
                f"author={ov.get('author')} reason={ov.get('reason', '')[:60]}",
                file=sys.stderr,
            )
        else:
            cat, half_life = categorize(src_path, tgt_path)
            tier = tier_for(row["verdict"], conf)

        src_age = node_age_days.get(src_node)
        if src_age is None:
            src_age = _git_mtime_days(src_path, as_of)
        delta = max(int(src_age or 0), 0)  # None or negative → 0 (fresh)
        decay = max(DECAY_FLOOR, math.exp(-delta / half_life)) if half_life > 0 else DECAY_FLOOR
        if tier == "T3":
            decay = T3_FORCED_DECAY  # T3 never gets a normal decay curve

        pair_key = (src_node, tgt_node, row["verdict"])
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)

        tier_weight = TIER_WEIGHT[tier]
        rel_weight = RELATION_WEIGHTS.get(row["relation"], DEFAULT_RELATION_WEIGHT)
        recall_score = round(tier_weight * decay * conf * rel_weight, 4)

        enriched.append({
            "source_node_id": src_node,
            "source_path": src_path,
            "source_line": _normalize_line(src_line),
            "target_node_id": tgt_node,
            "target_path": tgt_path,
            "target_line": _normalize_line(tgt_line),
            "confidence": conf,
            "weight": w,
            "relation": row["relation"],
            "verdict": row["verdict"],
            "tier": tier,
            "category": cat,
            "half_life_days": half_life,
            "delta_days": delta,
            "decay_factor": round(decay, 4),
            "tier_weight": tier_weight,
            "relation_weight": rel_weight,
            "recall_score": recall_score,
            "override_applied": key in overrides,
        })
        tier_counts[tier] += 1
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    summary = {
        "as_of": as_of.isoformat(),
        "policy": "ADR-0004",
        "tier_counts": tier_counts,
        "category_counts": cat_counts,
        "override_hits": override_hits,
        "total_edges": len(enriched),
    }

    if args.fmt == "json":
        payload = {**summary, "edges": enriched}
        out = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        out = "\n".join(json.dumps(r, ensure_ascii=False) for r in enriched)

    if args.out:
        Path(args.out).write_text(out + ("\n" if out and not out.endswith("\n") else ""),
                                  encoding="utf-8")
        print(args.out)
    else:
        print(out)


if __name__ == "__main__":
    main()
