#!/usr/bin/env python3
"""
build_ground_truth.py — генерирует ground_truth.jsonl по принципу (c):
  • 7 override-рёбер (label=1, эталоны из ADR-0004)
  • 5-7 cross-file рёбер с высоким recall_score (label=1, не override)
  • 10 фоновых рёбер с низким recall_score (label=0, T3)

Это не «золотая» ручная разметка, а стартовая правдоподобная выборка
для A/B калибровки формул. После прогона A/B GT пополняется вручную.
"""
import json
import random
from pathlib import Path

REPO = Path("/home/workspace")
SRC = REPO / "graphify-out" / "inferred_clean.enriched.jsonl"
OUT = REPO / "graphify-out" / "ground_truth.jsonl"

random.seed(42)

with open(SRC) as f:
    edges = [json.loads(line) for line in f if line.strip()]

override = [e for e in edges if e.get("override_applied")]
print(f"override-рёбер: {len(override)} (label=1)")

# cross-file = source_path != target_path (разные файлы)
def is_cross_file(e):
    return (e.get("source_path") or "").strip() != (e.get("target_path") or "").strip()

cross = [
    e for e in edges
    if e.get("tier") == "T1"
    and not e.get("override_applied")
    and is_cross_file(e)
]
cross_sorted = sorted(cross, key=lambda x: x.get("recall_score", 0), reverse=True)
cross_top = cross_sorted[:7]
print(f"cross-file T1 (не override): {len(cross)}; взято top-7 по recall_score")
print(f"  диапазон recall_score: "
      f"{cross_top[-1]['recall_score']:.3f} … {cross_top[0]['recall_score']:.3f}")

# фон: T3 (forced decay 0.05), случайные 10
background = [e for e in edges if e.get("tier") == "T3"]
print(f"T3-рёбер в выборке: {len(background)}")
background_pick = random.sample(background, 10)

gt = []
for e in override:
    gt.append({
        "source_node_id": e["source_node_id"],
        "target_node_id": e["target_node_id"],
        "relation": e.get("relation"),
        "label": 1,
        "kind": "override",
    })
for e in cross_top:
    gt.append({
        "source_node_id": e["source_node_id"],
        "target_node_id": e["target_node_id"],
        "relation": e.get("relation"),
        "label": 1,
        "kind": "cross_file_top",
        "recall_score": e.get("recall_score"),
    })
for e in background_pick:
    gt.append({
        "source_node_id": e["source_node_id"],
        "target_node_id": e["target_node_id"],
        "relation": e.get("relation"),
        "label": 0,
        "kind": "background_T3",
    })

with open(OUT, "w") as f:
    for item in gt:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

label_dist = {}
kind_dist = {}
for g in gt:
    label_dist[g["label"]] = label_dist.get(g["label"], 0) + 1
    kind_dist[g["kind"]] = kind_dist.get(g["kind"], 0) + 1

print(f"\n✅ {OUT.relative_to(REPO)} создан: {len(gt)} записей")
print(f"   label distribution: {label_dist}")
print(f"   kind distribution:  {kind_dist}")
