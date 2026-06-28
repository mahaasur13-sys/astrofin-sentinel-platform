#!/usr/bin/env python3
"""diagnose_relations.py — relation-type & same-file breakdown for the current ingest.

Run:
    python3 graphify-out/diagnose_relations.py
    python3 graphify-out/diagnose_relations.py graphify-out/inferred_clean.jsonl
"""

import json
import sys
from collections import Counter
from pathlib import Path

DEFAULT = Path("graphify-out/inferred_clean.jsonl")
path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT

edges = []
with path.open("r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            edges.append(json.loads(line))

print(f"Файл:           {path}")
print(f"Всего рёбер:    {len(edges)}")

print("\nРаспределение 'relation':")
for rel, count in Counter(e.get("relation") for e in edges).most_common():
    print(f"  {str(rel):25} : {count:4} ({count / len(edges) * 100:5.1f}%)")

print("\nРаспределение 'verdict':")
for v, count in Counter(e.get("verdict") for e in edges).most_common():
    print(f"  {str(v):25} : {count:4} ({count / len(edges) * 100:5.1f}%)")

print("\nРаспределение 'tier':")
for t, count in Counter(e.get("tier") for e in edges).most_common():
    print(f"  {str(t):25} : {count:4} ({count / len(edges) * 100:5.1f}%)")

print("\nSame-file vs Cross-file (по source_path == target_path):")
same = sum(1 for e in edges if e.get("source_path") == e.get("target_path"))
cross = len(edges) - same
print(f"  Same-file  : {same:4} ({same / len(edges) * 100:5.1f}%)")
print(f"  Cross-file : {cross:4} ({cross / len(edges) * 100:5.1f}%)")

if cross > 0:
    print("\nCross-file relation breakdown:")
    cross_edges = [e for e in edges if e.get("source_path") != e.get("target_path")]
    for rel, count in Counter(e.get("relation") for e in cross_edges).most_common():
        print(f"  {str(rel):25} : {count:4}")
