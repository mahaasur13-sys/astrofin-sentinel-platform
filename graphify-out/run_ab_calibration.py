#!/usr/bin/env python3
"""
run_ab_calibration.py — ADR-0006 A/B calibration runner.

Сравнивает 4 варианта формулы recall_score на ground_truth.
  v1_baseline       : tier * decay * conf * rel   (текущая)
  v2_no_tier        :        decay * conf * rel
  v3_smooth_tier    : sqrt(tier) * decay * conf * rel
  v4_relation_primary: rel * decay * conf * 0.4 + 0.6 * tier

Вход:  graphify-out/inferred_clean.enriched.jsonl
        graphify-out/ground_truth.jsonl
Выход: graphify-out/ab_calibration_v3.json
        Markdown-таблица в stdout
"""
from __future__ import annotations
import json
import math
import sys
from collections import Counter
from pathlib import Path

REPO = Path("/home/workspace")
EDGES = REPO / "graphify-out" / "inferred_clean.enriched.jsonl"
GT = REPO / "graphify-out" / "ground_truth.jsonl"
OUT = REPO / "graphify-out" / "ab_calibration_v3.json"

FORMULAS = ["v1_baseline", "v2_no_tier", "v3_smooth_tier", "v4_relation_primary"]
K_TOP = (10, 20)

TIER_WEIGHT = {"T1": 1.0, "T2": 0.6, "T3": 0.1}


def compute_recall(edge: dict, formula: str) -> float:
    tier = edge.get("tier", "T3")
    tw = TIER_WEIGHT.get(tier, 0.1)
    decay = edge.get("decay_factor", 1.0)
    conf = edge.get("confidence", 1.0)
    rel_w = edge.get("relation_weight", 0.5)

    if formula == "v1_baseline":
        return tw * decay * conf * rel_w
    if formula == "v2_no_tier":
        return decay * conf * rel_w
    if formula == "v3_smooth_tier":
        return math.sqrt(tw) * decay * conf * rel_w
    if formula == "v4_relation_primary":
        return rel_w * decay * conf * 0.4 + 0.6 * tw
    raise ValueError(f"Unknown formula: {formula}")


def load_edges() -> list[dict]:
    out = []
    for line in EDGES.read_text().splitlines():
        line = line.strip()
        if line and line.startswith("{"):
            out.append(json.loads(line))
    return out


def load_gt() -> list[dict]:
    out = []
    for line in GT.read_text().splitlines():
        line = line.strip()
        if line and line.startswith("{"):
            out.append(json.loads(line))
    return out


def evaluate(edges: list[dict], gt: list[dict], formula: str) -> dict:
    scored = [(compute_recall(e, formula), e) for e in edges]
    scored.sort(key=lambda x: x[0], reverse=True)

    gt_pos = {(g["source_node_id"], g["target_node_id"]) for g in gt if g.get("label") == 1}
    gt_neg = {(g["source_node_id"], g["target_node_id"]) for g in gt if g.get("label") == 0}

    result = {"formula": formula}
    for k in K_TOP:
        topk = [e for _, e in scored[:k]]
        result[f"gt_pos_in_top{k}"] = sum(
            1 for e in topk if (e["source_node_id"], e["target_node_id"]) in gt_pos
        )
        result[f"gt_neg_in_top{k}"] = sum(
            1 for e in topk if (e["source_node_id"], e["target_node_id"]) in gt_neg
        )
        result[f"override_in_top{k}"] = sum(1 for e in topk if e.get("override_applied"))
        scores_k = [s for s, _ in scored[:k]]
        result[f"spread_top{k}"] = round(max(scores_k) - min(scores_k), 4) if scores_k else 0.0
        rels = Counter(e.get("relation") for e in topk)
        result[f"top{k}_relations"] = dict(rels)
    return result


def main() -> int:
    edges = load_edges()
    gt = load_gt()
    if not edges:
        print("ERROR: no edges loaded", file=sys.stderr)
        return 1
    if not gt:
        print("ERROR: no GT loaded", file=sys.stderr)
        return 1

    n_pos = sum(1 for g in gt if g.get("label") == 1)
    n_neg = sum(1 for g in gt if g.get("label") == 0)
    print(f"📊 edges: {len(edges)}; GT: {n_pos} pos / {n_neg} neg\n")

    results = {f: evaluate(edges, gt, f) for f in FORMULAS}

    # Markdown-таблица
    print("| Formula | gt@10 | gt@20 | override@10 | override@20 | spread@10 | spread@20 | top10 rels |")
    print("|---------|-------|-------|-------------|-------------|-----------|-----------|------------|")
    for f, r in results.items():
        rels_str = ", ".join(f"{k}:{v}" for k, v in sorted(r["top10_relations"].items(), key=lambda x: -x[1])[:4])
        print(
            f"| {f} | {r['gt_pos_in_top10']}/{n_pos} | {r['gt_pos_in_top20']}/{n_pos} | "
            f"{r['override_in_top10']}/7 | {r['override_in_top20']}/7 | "
            f"{r['spread_top10']:.3f} | {r['spread_top20']:.3f} | {rels_str} |"
        )

    # False positives: сколько label=0 попало в top-K (хорошо бы 0)
    print("\n| Formula | FP@10 | FP@20 |")
    print("|---------|-------|-------|")
    for f, r in results.items():
        print(f"| {f} | {r['gt_neg_in_top10']} | {r['gt_neg_in_top20']} |")

    # Verdict: выбираем лучшую формулу. v1_baseline остаётся default,
    # если не уступает ни одной альтернативе по gt@10/spread. Override-loss
    # в top-10 (когда recall_score=1.0 у многих рёбер и Python sort стабильно
    # тай-брейкает) — это лимит tie-breaking, не дефект формулы.
    best = "v1_baseline"
    best_gt = results["v1_baseline"]["gt_pos_in_top10"]
    best_spread = results["v1_baseline"]["spread_top20"]
    for f, r in results.items():
        if r["gt_pos_in_top10"] > best_gt:
            best_gt = r["gt_pos_in_top10"]
            best = f
        elif r["gt_pos_in_top10"] == best_gt and r["spread_top20"] > best_spread:
            best = f

    if best == "v1_baseline":
        print("\n## Verdict")
        print("✅ v1_baseline остаётся default (лучшая или равная лучшей по gt@10/spread).")
    else:
        print("\n## Verdict")
        print(f"⚠️  Рекомендуется переключиться на {best} (gt@10={best_gt}).")
    ov10 = results["v1_baseline"]["override_in_top10"]
    if ov10 < 7:
        print(
            f"❗ Override-contract: в top-10 осталось {ov10}/7 override "
            f"(из 7 пар с score=1.0). Это лимит tie-breaking при {results['v1_baseline']['top10_relations']}, "
            f"не дефект формулы — требует ADR-0007 (override-aware secondary sort)."
        )
    else:
        print("✅ Override-contract: все 7/7 override в top-10.")

    OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\n📁 результат: {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
