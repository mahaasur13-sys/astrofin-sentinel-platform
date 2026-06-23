#!/usr/bin/env python3
"""
build_balanced_sample.py

Constructs a balanced, deterministic subsample of INFERRED edges from
graphify-out/inferred_clean.jsonl, suitable for manual relation analysis.

Design:
  - Read all edges from inferred_clean.jsonl
  - Group by (relation, same_file_flag)
  - Stratified sample: cap each (relation, same_file) group at MAX_PER_BUCKET
  - Optionally seed-deterministic via --seed
  - Emit JSONL to stdout or --out path

This is the tool referenced in the previous session's recommendations:
"Build a balanced sample of 500 INFERRED edges, max N per (relation, same-file) bucket."

Usage:
  python3 build_balanced_sample.py \\
      --in graphify-out/inferred_clean.jsonl \\
      --out graphify-out/inferred_sample_balanced.jsonl \\
      --max-per-bucket 50 \\
      --seed 42
"""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path


def is_same_file(edge: dict) -> bool:
    """Same-file means source_path == target_path AND both lines parse as int."""
    sp = edge.get("source_path") or ""
    tp = edge.get("target_path") or ""
    if sp != tp or not sp:
        return False
    sl = edge.get("source_line") or ""
    tl = edge.get("target_line") or ""
    try:
        int(sl)
        int(tl)
    except (TypeError, ValueError):
        return False
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--in",
        dest="inp",
        default="graphify-out/inferred_clean.jsonl",
        help="Path to inferred_clean.jsonl",
    )
    ap.add_argument(
        "--out",
        default="",
        help="Output path. If empty, write JSONL to stdout.",
    )
    ap.add_argument(
        "--max-per-bucket",
        type=int,
        default=50,
        help="Cap on edges per (relation, same_file) bucket (default: 50)",
    )
    ap.add_argument(
        "--seed",
        type=int,
        default=42,
        help="RNG seed for deterministic sampling (default: 42)",
    )
    ap.add_argument(
        "--max-total",
        type=int,
        default=0,
        help="Optional hard cap on total edges (0 = no cap).",
    )
    args = ap.parse_args()

    inp = Path(args.inp)
    if not inp.exists():
        raise SystemExit(f"missing input: {inp}")

    rng = random.Random(args.seed)
    buckets: dict[tuple[str, bool], list[dict]] = defaultdict(list)

    with inp.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                edge = json.loads(line)
            except json.JSONDecodeError:
                continue
            relation = edge.get("relation") or "unknown"
            same = is_same_file(edge)
            buckets[(relation, same)].append(edge)

    sampled: list[dict] = []
    bucket_stats: dict[tuple[str, bool], dict] = {}

    for key, edges in buckets.items():
        rng.shuffle(edges)
        cap = min(args.max_per_bucket, len(edges))
        pick = edges[:cap]
        sampled.extend(pick)
        bucket_stats[key] = {
            "available": len(edges),
            "sampled": len(pick),
        }

    rng.shuffle(sampled)
    if args.max_total and len(sampled) > args.max_total:
        sampled = sampled[: args.max_total]

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            for e in sampled:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
        print(f"wrote {len(sampled)} edges to {out_path}")
    else:
        for e in sampled:
            print(json.dumps(e, ensure_ascii=False))

    summary = {
        "total_sampled": len(sampled),
        "max_per_bucket": args.max_per_bucket,
        "seed": args.seed,
        "buckets": {
            f"{rel}|same={sf}": stats
            for (rel, sf), stats in sorted(bucket_stats.items())
        },
    }
    print("---SAMPLE_STATS---")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
