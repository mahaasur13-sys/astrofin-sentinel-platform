#!/usr/bin/env python3
"""
recall_test.py — ranking diagnostics for the Hybrid Memory ingestion output.

Reads /home/workspace/graphify-out/inferred_clean.jsonl and produces
ranked views that mirror how a downstream recall layer would use the
ingest: sort by recall_score (desc), allow filters by tier/category/
override_applied/keyword, print a compact table and a summary block.

Why this matters
----------------
Before wiring the ingest into Temporal Tree + KG, we want to know:
  1. Are the overrides actually pushing the right edges to the top?
  2. Is the decay curve penalising fresh-but-low-confidence edges too hard?
  3. Are T3 edges (parser noise) sitting at the bottom as expected?
  4. Which categories dominate the head of the ranking?

Usage
-----
  python3 graphify-out/recall_test.py                 # top-20 default
  python3 graphify-out/recall_test.py -n 50           # top-50
  python3 graphify-out/recall_test.py --tier T1       # filter by tier
  python3 graphify-out/recall_test.py --only-overrides
  python3 graphify-out/recall_test.py --keyword scheduler
  python3 graphify-out/recall_test.py --json          # machine-readable
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path("/home/workspace")
INGEST = REPO_ROOT / "graphify-out" / "inferred_clean.jsonl"


def load_edges():
    """Load the enriched edges written by infer_edges.py.

    If the ingest file lacks enriched fields (recall_score, tier, ...),
    invoke infer_edges.py to regenerate it. This keeps the script
    runnable as a one-shot ranking tool without manual orchestration.
    """
    if not INGEST.exists():
        raise SystemExit(f"missing {INGEST} — run `python3 graphify-out/infer_edges.py` first")
    edges = []
    needs_enrichment = False
    for line in INGEST.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        edges.append(json.loads(line))
        if "recall_score" not in edges[-1] or "tier" not in edges[-1]:
            needs_enrichment = True
    if needs_enrichment:
        import subprocess

        out_path = INGEST.with_suffix(".enriched.jsonl")
        subprocess.run(
            [sys.executable, str(REPO_ROOT / "graphify-out" / "infer_edges.py"), "-o", str(out_path)],
            check=True,
        )
        edges = []
        for line in out_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                edges.append(json.loads(line))
    return edges


def _mark_self_like(edges):
    for e in edges:
        e["self_like"] = e.get("source_path") == e.get("target_path")
    return edges


def apply_filters(edges, args):
    """Apply CLI filters in a predictable order."""
    out = edges
    if args.tier:
        out = [e for e in out if e["tier"] == args.tier]
    if args.category:
        out = [e for e in out if e["category"] == args.category]
    if args.only_overrides:
        out = [e for e in out if e["override_applied"]]
    if args.keyword:
        needle = args.keyword.lower()
        out = [e for e in out if needle in e["source_path"].lower() or needle in e["target_path"].lower() or needle in e["source_node_id"].lower() or needle in e["target_node_id"].lower()]
    if args.min_score is not None:
        out = [e for e in out if e["recall_score"] >= args.min_score]

    out = _mark_self_like(out)
    # ADR-0007: override is a contract (ADR-0004), not a hint. Override edges
    # must rank strictly above non-override edges whenever recall_score ties.
    # Final tie-break stays on (source_path, target_path, source_node_id,
    # target_node_id) so non-tied output is deterministic and identical to the
    # previous ranking modulo override promotion.
    out.sort(
        key=lambda e: (
            -int(e.get("override_applied", False)),
            -e["recall_score"],
            e["source_path"],
            e["target_path"],
            e["source_node_id"],
            e["target_node_id"],
        )
    )
    return out


def _short(path: str, maxlen: int = 50) -> str:
    """Compact file path for table display (no leading repo prefix)."""
    if len(path) <= maxlen:
        return path
    return "…" + path[-(maxlen - 1) :]


def _short_node(node_id: str, maxlen: int = 40) -> str:
    """Last 2 components of the node id — usually enough for disambiguation."""
    parts = node_id.rsplit("_", 2)
    if len(parts) >= 3 and len(parts[-1]) < 25:
        return "_".join(parts[-2:])
    return node_id[-maxlen:] if len(node_id) > maxlen else node_id


def render_table(edges, args):
    """Render a compact ASCII table to stdout."""
    rows = sorted(
        edges,
        key=lambda e: (
            -int(e.get("override_applied", False)),
            -e["recall_score"],
            e["source_path"],
            e["target_path"],
            e["source_node_id"],
            e["target_node_id"],
        ),
    )
    if args.limit:
        rows = rows[: args.limit]

    headers = ["rank", "score", "tier", "cat", "verdict", "ovr", "src → tgt"]
    print(" | ".join(headers))
    print("-" * 100)

    for rank, e in enumerate(rows, 1):
        src = _short(e["source_path"], 28)
        tgt = _short(e["target_path"], 28)
        arrow = f"{src} → {tgt}"
        ovr = "✓" if e["override_applied"] else " "
        print(
            " | ".join(
                [
                    f"{rank:>4}",
                    f"{e['recall_score']:.4f}",
                    f"{e['tier']:>3}",
                    f"{e['category'][:6]:<6}",
                    f"{e['verdict']:<10}",
                    f" {ovr}",
                    arrow,
                ]
            )
        )
    return rows


def render_summary(edges, total_population):
    """Print distribution stats to help spot rank composition."""
    if not edges:
        print("\n(no edges matched filters)")
        return

    by_tier = {}
    by_category = {}
    by_verdict = {}
    overridden = 0
    for e in edges:
        by_tier[e["tier"]] = by_tier.get(e["tier"], 0) + 1
        by_category[e["category"]] = by_category.get(e["category"], 0) + 1
        by_verdict[e["verdict"]] = by_verdict.get(e["verdict"], 0) + 1
        if e["override_applied"]:
            overridden += 1

    print("\n--- summary (after filters) ---")
    print(f"  matched/total: {len(edges)}/{total_population}")
    print(f"  by tier:       {by_tier}")
    print(f"  by category:   {by_category}")
    print(f"  by verdict:    {by_verdict}")
    print(f"  overridden:    {overridden}/{len(edges)}")

    scores = [e["recall_score"] for e in edges]
    scores_sorted = sorted(scores, reverse=True)
    print(f"  score range:   min={min(scores):.4f}  median={scores_sorted[len(scores_sorted) // 2]:.4f}  max={max(scores):.4f}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-n", "--limit", type=int, default=20, help="rows to show (default 20)")
    ap.add_argument("--tier", choices=["T1", "T2", "T3"], help="filter by tier")
    ap.add_argument("--category", choices=["core", "submodule", "archived", "trash"], help="filter by category")
    ap.add_argument("--verdict", choices=["valid", "ambiguous", "false", "moved", "outdated"], help="filter by verdict")
    ap.add_argument("--only-overrides", action="store_true", help="show only overridden edges")
    ap.add_argument("--keyword", help="substring match on paths/node_ids")
    ap.add_argument("--min-score", type=float, help="minimum recall_score")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of table")
    args = ap.parse_args()

    all_edges = load_edges()
    filtered = apply_filters(all_edges, args)

    if args.json:
        out = {
            "total_population": len(all_edges),
            "matched": len(filtered),
            "filters": {k: v for k, v in vars(args).items() if v is not None and k != "json"},
            "edges": filtered,
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        if args.only_overrides or args.tier or args.keyword or args.min_score:
            print(f"filters: {[(k, v) for k, v in vars(args).items() if v not in (None, False, 20)]}\n")
        render_table(filtered, args)
        render_summary(filtered, len(all_edges))


if __name__ == "__main__":
    main()
