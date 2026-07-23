"""
plan_evaluator.py — v8.0 Phase 2
Evaluates plan quality using persistence-grounded IntegrationReport.
"""
from __future__ import annotations

from dataclasses import dataclass

from meta_control.integration.persistence_bridge import IntegrationReport


@dataclass
class PlanEvaluation:
    plan_id: str
    tick: int

    # Raw coherence scores
    base_coherence: float
    enriched_coherence: float
    coherence_gain: float

    # Stability signals
    global_trend: float
    window_depth: int
    source_count: int
    coherent_sources: list[str]

    # Gain quality
    global_gain_multiplier: float
    unstable_sources: list[str]

    # Weight quality
    avg_weight_adjustment: float
    sources_with_negative_history: list[str]

    # Composite scores
    stability_score: float      # f(trend, depth, source_count)
    coherence_score: float      # f(enriched_coherence, coherence_gain)
    gain_score: float           # f(gain_multiplier, unstable)
    weight_score: float        # f(avg_weight, negative_history)

    overall: float             # weighted composite


@dataclass
class PlanScoreWeights:
    stability: float = 0.25
    coherence: float = 0.30
    gain: float = 0.25
    weight: float = 0.20


class PlanEvaluator:
    """
    Evaluates a plan (represented as IntegrationReport + metadata)
    against persistence-grounded truth.

    Inputs:
      - IntegrationReport from PersistenceBridge
      - StabilityLedger source_statuses
      - DecisionMemory outcome_stats

    Produces:
      - PlanEvaluation with per-dimension scores + composite overall
    """

    def __init__(self, weights: PlanScoreWeights | None = None) -> None:
        self.weights = weights or PlanScoreWeights()

    def evaluate(
        self,
        plan_id: str,
        report: IntegrationReport,
        source_statuses: dict[str, dict],
        unstable_threshold: float = 0.65,
    ) -> PlanEvaluation:
        tick = report.tick

        # Coherence
        base_c = report.coherence.base_coherence
        enriched_c = report.coherence.enriched_coherence
        coherence_gain = enriched_c - base_c

        # Stability
        trend = report.coherence.trend
        depth = report.coherence.window_depth
        src_count = report.coherence.source_count
        coherent_srcs = report.coherence.coherence_sources

        # Gain
        global_mult = 1.0
        unstable_srcs: list[str] = []
        for adj in report.gain_adjustments:
            if adj.source == "__global__":
                global_mult = adj.multiplier
            elif source_statuses.get(adj.source, {}).get("is_coherent", True) is False:
                unstable_srcs.append(adj.source)

        # Weight
        avg_weight = 0.0
        neg_history: list[str] = []
        if report.weight_deltas:
            avg_weight = sum(w.priority_adjustment for w in report.weight_deltas) / len(report.weight_deltas)
            for w in report.weight_deltas:
                if w.avg_outcome_score < 0.4:
                    neg_history.append(w.source)

        # Per-dimension scores (0..1, higher = better)
        stability_score = self._stability_score(trend, depth, src_count)
        coherence_score = self._coherence_score(coherence_gain, enriched_c)
        gain_score = self._gain_score(global_mult, unstable_srcs)
        weight_score = self._weight_score(avg_weight, neg_history)

        # Composite
        w = self.weights
        overall = (
            w.stability * stability_score
            + w.coherence * coherence_score
            + w.gain * gain_score
            + w.weight * weight_score
        )

        return PlanEvaluation(
            plan_id=plan_id,
            tick=tick,
            base_coherence=base_c,
            enriched_coherence=enriched_c,
            coherence_gain=coherence_gain,
            global_trend=trend,
            window_depth=depth,
            source_count=src_count,
            coherent_sources=coherent_srcs,
            global_gain_multiplier=global_mult,
            unstable_sources=unstable_srcs,
            avg_weight_adjustment=avg_weight,
            sources_with_negative_history=neg_history,
            stability_score=stability_score,
            coherence_score=coherence_score,
            gain_score=gain_score,
            weight_score=weight_score,
            overall=overall,
        )

    @staticmethod
    def _stability_score(trend: float, depth: int, source_count: int) -> float:
        trend_part = (trend + 1.0) / 2.0  # -1..1 → 0..1
        depth_part = min(1.0, depth / max(1, source_count * 2))
        return 0.6 * trend_part + 0.4 * depth_part

    @staticmethod
    def _coherence_score(gain: float, enriched: float) -> float:
        gain_part = min(1.0, max(0.0, gain))
        level_part = min(1.0, enriched)
        return 0.5 * gain_part + 0.5 * level_part

    @staticmethod
    def _gain_score(multiplier: float, unstable: list[str]) -> float:
        mult_part = min(1.5, max(0.0, multiplier)) / 1.5
        stab_part = 1.0 - (len(unstable) / max(1, 10))
        return 0.5 * mult_part + 0.5 * stab_part

    @staticmethod
    def _weight_score(avg_delta: float, neg_history: list[str]) -> float:
        delta_part = min(1.0, max(-1.0, avg_delta))
        history_part = 1.0 - (len(neg_history) / max(1, 5))
        return 0.5 * (delta_part + 0.5) + 0.5 * history_part
