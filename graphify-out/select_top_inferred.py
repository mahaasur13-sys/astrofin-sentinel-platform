#!/usr/bin/env python3
"""
select_top_inferred.py — primary selector of INFERRED edges from graph.json.

Reads /home/workspace/graphify-out/graph.json and writes a balanced top-N
selection to /home/workspace/graphify-out/inferred_clean.jsonl with **real
relation diversity** (the bug fixed by this script: the previous pipeline
collapsed everything to relation="calls" because no primary selector fed
graph.json → validator).

Design goals:
  - Stratified by `relation` so every relation that has ≥ MIN_PER_RELATION
    edges in the top window gets a slot.
  - Cross-file first: prefer edges where source_path != target_path so that
    cross-module contracts show up (ADR-0004 god-node contracts live here).
  - Deterministic via --seed.
  - Output schema matches what validate_inferred.py / infer_edges.py expect
    (inferred_clean.jsonl schema: source_node_id, target_node_id,
    source_path, source_line, target_path, target_line, confidence,
    weight, relation, context, source_file, source_location).

Usage:
  python3 select_top_inferred.py                    # defaults: 500 edges, max 100/relation, hard cap 200/relation
  python3 select_top_inferred.py --max 500 --max-per-relation 100 --hard-cap-per-relation 200 --seed 42

The hard cap exists because at large --max (e.g. 5000) a few large relation
buckets (calls/imports/uses/inherits) would otherwise dominate the entire
selection, collapsing diversity. The cap is enforced across anchor + min-floor
+ remainder + topup so every relation stays bounded.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path("/home/workspace")
GRAPH_JSON = REPO_ROOT / "graphify-out" / "graph.json"
DEFAULT_OUT = REPO_ROOT / "graphify-out" / "inferred_clean.jsonl"


def _load_override_pairs() -> set:
    """Load (source, target) pairs from config/memory_overrides.json.

    Override pairs are contractually required to be present in the inferred
    sample (ADR-0004), so we anchor them at the start of selection.
    """
    p = REPO_ROOT / "config" / "memory_overrides.json"
    if not p.exists():
        return set()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return set()
    out = set()
    for entry in data.get("overrides", []):
        s = entry.get("source_node_id") or entry.get("source")
        t = entry.get("target_node_id") or entry.get("target")
        if s and t:
            out.add((s, t))
    return out


def _conf(L: dict) -> float:
    v = L.get("confidence_score")
    if v is None:
        v = L.get("confidence")
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _w(L: dict) -> float:
    try:
        return float(L.get("weight") or 0)
    except (TypeError, ValueError):
        return 0.0


def is_cross_file(link: dict, nodes_by_id: dict) -> bool:
    sp = link.get("source_file") or ""
    tp_node = nodes_by_id.get(link.get("target", ""), {})
    tp = tp_node.get("source_file") or link.get("target_file") or ""
    if not sp or not tp:
        return False
    return sp != tp


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max", type=int, default=500, help="Total edges to select (default: 500).")
    ap.add_argument("--max-per-relation", type=int, default=100, help="Cap per relation bucket (default: 100).")
    ap.add_argument(
        "--min-per-relation",
        type=int,
        default=10,
        help="Floor per relation bucket when enough edges exist (default: 10).",
    )
    ap.add_argument(
        "--hard-cap-per-relation",
        type=int,
        default=200,
        help="Absolute ceiling per relation across ALL passes (default: 200). "
        "Defends against large --max (e.g. 5000) collapsing diversity "
        "when a few buckets (calls/imports/uses/inherits) dominate.",
    )
    ap.add_argument(
        "--cross-file-priority",
        action="store_true",
        default=True,
        help="Prefer cross-file edges inside each bucket (default: on).",
    )
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    # Clamp the per-relation soft knobs so they never exceed the hard cap.
    if args.max_per_relation > args.hard_cap_per_relation:
        args.max_per_relation = args.hard_cap_per_relation
    if args.min_per_relation > args.hard_cap_per_relation:
        args.min_per_relation = args.hard_cap_per_relation

    if not GRAPH_JSON.exists():
        raise SystemExit(f"missing {GRAPH_JSON}")

    g = json.load(GRAPH_JSON.open())
    nodes = g.get("nodes", [])
    links = g.get("links", [])
    nodes_by_id = {n["id"]: n for n in nodes}

    # Group all links by relation, sort by (weight desc, confidence desc).
    buckets: dict[str, list[dict]] = defaultdict(list)
    for link in links:
        rel = link.get("relation") or "unknown"
        buckets[rel].append(link)

    for rel in buckets:
        buckets[rel].sort(key=lambda L: (_w(L), _conf(L)), reverse=True)

    # Pass 0: anchor override pairs (ADR-0004 contract).
    # These 7 cross-file pairs MUST appear in the final selection regardless of
    # weight/confidence ranking, so the override mechanism in infer_edges.py is
    # end-to-end testable on every run.
    override_pairs = _load_override_pairs()
    link_index = {(l.get("source"), l.get("target")): l for l in links}  # noqa: E741
    anchored = []
    for s, t in sorted(override_pairs):
        link = link_index.get((s, t))
        if link is not None:
            anchored.append(link)
    selected: list[dict] = list(anchored)

    # Pass 1: enforce min-per-relation to guarantee diversity floor.
    for rel, items in sorted(buckets.items(), key=lambda kv: -len(kv[1])):
        if not items:
            continue
        take = min(args.min_per_relation, args.hard_cap_per_relation, len(items))
        selected.extend(items[:take])

    # Pass 2: fill remaining slots up to --max-per-relation with rest of buckets,
    # cross-file preferred, then sort key.
    remaining_slots = max(0, args.max - len(selected))
    if remaining_slots > 0:
        # Build a per-bucket "remainder" list excluding what we already took.
        already_taken_keys = {(e.get("source"), e.get("target")) for e in selected}
        # Track per-bucket count already in `selected` so we never exceed the hard cap.
        per_rel_count: dict[str, int] = Counter(e.get("relation", "unknown") for e in selected)
        for rel, items in buckets.items():
            remainder = [e for e in items if (e.get("source"), e.get("target")) not in already_taken_keys]
            if not remainder:
                continue
            if args.cross_file_priority:
                remainder.sort(key=lambda L: (not is_cross_file(L, nodes_by_id), -_w(L), -_conf(L)))
            # Hard cap is absolute across ALL passes; soft cap is per-pass.
            headroom = args.hard_cap_per_relation - per_rel_count.get(rel, 0)
            if headroom <= 0:
                continue
            soft_cap = min(args.max_per_relation - args.min_per_relation, len(remainder))
            cap = min(headroom, soft_cap)
            if cap <= 0:
                continue
            pick = remainder[:cap]
            selected.extend(pick)
            per_rel_count[rel] += len(pick)
            already_taken_keys.update((p.get("source"), p.get("target")) for p in pick)
            remaining_slots -= len(pick)
            if remaining_slots <= 0:
                break

    # Pass 3: if we still have slack, top up from largest buckets ignoring cap
    # BUT still respecting the hard absolute ceiling per relation.
    if remaining_slots > 0:
        already_taken_keys = {(e.get("source"), e.get("target")) for e in selected}
        per_rel_count = Counter(e.get("relation", "unknown") for e in selected)
        flat = []
        for items in buckets.values():
            flat.extend(items)
        flat.sort(key=lambda L: (_w(L), _conf(L)), reverse=True)
        for link in flat:
            key = (link.get("source"), link.get("target"))
            if key in already_taken_keys:
                continue
            rel = link.get("relation") or "unknown"
            if per_rel_count.get(rel, 0) >= args.hard_cap_per_relation:
                continue
            selected.append(link)
            already_taken_keys.add(key)
            per_rel_count[rel] += 1
            remaining_slots -= 1
            if remaining_slots <= 0:
                break

    # Trim if we overshot.
    if len(selected) > args.max:
        selected = selected[: args.max]

    # Map raw links → inferred_clean.jsonl schema.
    out_edges: list[dict] = []
    for link in selected:
        nodes_by_id.get(link.get("source", ""), {})
        tgt_node = nodes_by_id.get(link.get("target", ""), {})
        out_edges.append(
            {
                "source_node_id": link.get("source", ""),
                "source_path": link.get("source_file", ""),
                "source_line": link.get("source_location", ""),
                "target_node_id": link.get("target", ""),
                "target_path": (tgt_node.get("source_file") or link.get("target_file") or ""),
                "target_line": tgt_node.get("source_location", ""),
                "confidence": _conf(link),
                "weight": _w(link),
                "relation": link.get("relation", "unknown"),
                "context": link.get("context", ""),
                "source_file": link.get("source_file", ""),
                "source_location": link.get("source_location", ""),
            }
        )

    rng = random.Random(args.seed)
    rng.shuffle(out_edges)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for edge in out_edges:
            f.write(json.dumps(edge, ensure_ascii=False) + "\n")

    # Print summary so the caller sees diversity.
    rel_counter = Counter(e["relation"] for e in out_edges)
    cross = sum(1 for e in out_edges if e["source_path"] and e["target_path"] and e["source_path"] != e["target_path"])
    summary = {
        "total": len(out_edges),
        "cross_file": cross,
        "relation_distribution": dict(rel_counter.most_common()),
        "seed": args.seed,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"wrote {len(out_edges)} edges to {out_path}")


if __name__ == "__main__":
    main()
