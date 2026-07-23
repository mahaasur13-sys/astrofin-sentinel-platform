"""
evaluation_metrics.py — planning_observability layer
Metrics for measuring planning quality as a system (not individual plan quality).

Key metrics:
  - plan_stability_index
  - evaluation_entropy
  - replanning_frequency
  - coherence_drop_rate
  - dag_complexity_growth

Invariant (v8.0 Phase A):
  planning_health = f(stability, evaluation_entropy, replanning_rate, DAG_drift)
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class EvaluationMetrics:
    """
    Snapshot of planning system health at a given tick.
    """
    tick: int

    # Score distribution metrics
    plan_stability_index: float       # 0..1 (1 = perfectly stable trajectory)
    evaluation_entropy: float        # bits (higher = more chaotic evaluation)
    coherence_entropy: float         # bits (coherence score distribution entropy)

    # Replanning metrics
    replanning_frequency: float      # replans / plan (per-plan rate)
    replanning_burst_ratio: float    # fraction of ticks with replan (burst detection)

    # Coherence metrics
    coherence_drop_rate: float       # drops / tick (coherence degradation speed)
    coherence_recovery_rate: float   # recoveries / tick (bounce-back speed)

    # DAG complexity
    dag_complexity: float            # nodes / depth ratio at this tick
    dag_branching_factor: float     # avg children per node
    dag_depth: int                  # longest path length
    dag_growth_rate: float           # nodes added per tick

    # Score trend
    score_trend: float              # slope of overall score over recent ticks


@dataclass
class MetricsConfig:
    entropy_window: int = 20
    score_trend_window: int = 10
    coherence_drop_threshold: float = 0.05
    dag_growth_window: int = 50


class EvaluationMetricsCollector:
    """
    Computes planning health metrics from trace logger and plan graph data.

    All metrics are computed from observable data (trace events + DAG state).
    No internal state beyond config and rolling windows.
    """

    def __init__(self, config: MetricsConfig | None = None) -> None:
        self.config = config or MetricsConfig()

    # ─── score stability ───────────────────────────────────────────────────────

    @staticmethod
    def plan_stability_index(score_trajectory: list[float]) -> float:
        """
        1 - (stddev / range) of recent overall scores.
        1.0 = perfectly stable trajectory, 0.0 = chaotic.
        """
        if len(score_trajectory) < 2:
            return 1.0
        mean = sum(score_trajectory) / len(score_trajectory)
        variance = sum((s - mean) ** 2 for s in score_trajectory) / len(score_trajectory)
        stddev = math.sqrt(variance)
        score_range = max(score_trajectory) - min(score_trajectory)
        if score_range < 1e-9:
            return 1.0
        return max(0.0, 1.0 - stddev / score_range)

    @staticmethod
    def _shannon_entropy(values: list[float], bins: int = 10) -> float:
        """Shannon entropy of a distribution (bits)."""
        if not values:
            return 0.0
        min_v, max_v = min(values), max(values)
        if max_v - min_v < 1e-9:
            return 0.0
        counts = [0] * bins
        for v in values:
            bin_idx = min(bins - 1, int((v - min_v) / (max_v - min_v) * bins))
            counts[bin_idx] += 1
        total = len(values)
        entropy = 0.0
        for c in counts:
            if c > 0:
                p = c / total
                entropy -= p * math.log2(p)
        return entropy

    def evaluation_entropy(
        self,
        stability_scores: list[float],
        gain_scores: list[float],
        weight_scores: list[float],
    ) -> float:
        """Combined entropy of 4D score components."""
        st_ent = self._shannon_entropy(stability_scores)
        co_ent = self._shannon_entropy([s for s in stability_scores])
        ga_ent = self._shannon_entropy(gain_scores)
        we_ent = self._shannon_entropy(weight_scores)
        return (st_ent + co_ent + ga_ent + we_ent) / 4.0

    # ─── replanning ────────────────────────────────────────────────────────────

    @staticmethod
    def replanning_frequency(
        total_replans: int,
        total_plans: int,
    ) -> float:
        """Replans per plan."""
        if total_plans == 0:
            return 0.0
        return total_replans / total_plans

    @staticmethod
    def replanning_burst_ratio(
        replan_ticks: list[int],
        total_ticks: int,
    ) -> float:
        """Fraction of ticks with at least one replan."""
        if total_ticks == 0:
            return 0.0
        unique_ticks = len(set(replan_ticks))
        return unique_ticks / total_ticks

    # ─── coherence ─────────────────────────────────────────────────────────────

    @staticmethod
    def coherence_drop_rate(
        coherence_trajectory: list[float],
        drop_threshold: float = 0.05,
    ) -> float:
        """
        Average number of coherence drops per tick.
        A drop = consecutive decrease > threshold.
        """
        if len(coherence_trajectory) < 2:
            return 0.0
        drops = sum(
            1 for i in range(1, len(coherence_trajectory))
            if coherence_trajectory[i] - coherence_trajectory[i - 1] < -drop_threshold
        )
        return drops / (len(coherence_trajectory) - 1)

    @staticmethod
    def coherence_recovery_rate(
        coherence_trajectory: list[float],
        recovery_threshold: float = 0.03,
    ) -> float:
        """
        Average number of coherence recoveries per tick.
        A recovery = consecutive increase > threshold.
        """
        if len(coherence_trajectory) < 2:
            return 0.0
        recoveries = sum(
            1 for i in range(1, len(coherence_trajectory))
            if coherence_trajectory[i] - coherence_trajectory[i - 1] > recovery_threshold
        )
        return recoveries / (len(coherence_trajectory) - 1)

    # ─── DAG complexity ────────────────────────────────────────────────────────

    @staticmethod
    def dag_complexity(
        total_nodes: int,
        max_depth: int,
    ) -> float:
        """Nodes / depth ratio. High = wide shallow DAG, low = deep narrow DAG."""
        if max_depth == 0:
            return 0.0
        return total_nodes / max_depth

    @staticmethod
    def dag_branching_factor(
        nodes_with_children: list[int],
        total_nodes: int,
    ) -> float:
        """Average children per node."""
        if total_nodes == 0:
            return 0.0
        return sum(nodes_with_children) / total_nodes

    @staticmethod
    def dag_growth_rate(
        node_counts_per_tick: list[int],
    ) -> float:
        """
        Linear slope of node count growth over ticks.
        Positive = plan graph is expanding.
        """
        n = len(node_counts_per_tick)
        if n < 2:
            return 0.0
        ticks = list(range(n))
        mean_t = sum(ticks) / n
        mean_c = sum(node_counts_per_tick) / n
        numerator = sum((ticks[i] - mean_t) * (node_counts_per_tick[i] - mean_c) for i in range(n))
        denominator = sum((ticks[i] - mean_t) ** 2 for i in range(n))
        if denominator < 1e-9:
            return 0.0
        return numerator / denominator

    # ─── score trend ────────────────────────────────────────────────────────────

    @staticmethod
    def score_trend(
        score_trajectory: list[float],
    ) -> float:
        """Linear slope of overall score over recent ticks."""
        n = len(score_trajectory)
        if n < 2:
            return 0.0
        ticks = list(range(n))
        mean_t = sum(ticks) / n
        mean_s = sum(score_trajectory) / n
        numerator = sum((ticks[i] - mean_t) * (score_trajectory[i] - mean_s) for i in range(n))
        denominator = sum((ticks[i] - mean_t) ** 2 for i in range(n))
        if denominator < 1e-9:
            return 0.0
        return numerator / denominator

    # ─── full snapshot ─────────────────────────────────────────────────────────

    def compute_snapshot(
        self,
        tick: int,
        score_trajectory: list[float],
        stability_scores: list[float],
        coherence_scores: list[float],
        gain_scores: list[float],
        weight_scores: list[float],
        coherence_trajectory: list[float],
        total_replans: int,
        total_plans: int,
        replan_ticks: list[int],
        total_ticks: int,
        total_nodes: int,
        max_depth: int,
        nodes_with_children: list[int],
        node_counts_per_tick: list[int],
    ) -> EvaluationMetrics:
        """
        Compute full metrics snapshot from trace + graph data.
        """
        return EvaluationMetrics(
            tick=tick,
            plan_stability_index=self.plan_stability_index(score_trajectory),
            evaluation_entropy=self.evaluation_entropy(
                stability_scores, gain_scores, weight_scores
            ),
            coherence_entropy=self._shannon_entropy(coherence_scores),
            replanning_frequency=self.replanning_frequency(total_replans, total_plans),
            replanning_burst_ratio=self.replanning_burst_ratio(replan_ticks, total_ticks),
            coherence_drop_rate=self.coherence_drop_rate(coherence_trajectory),
            coherence_recovery_rate=self.coherence_recovery_rate(coherence_trajectory),
            dag_complexity=self.dag_complexity(total_nodes, max_depth),
            dag_branching_factor=self.dag_branching_factor(nodes_with_children, total_nodes),
            dag_depth=max_depth,
            dag_growth_rate=self.dag_growth_rate(node_counts_per_tick),
            score_trend=self.score_trend(score_trajectory),
        )

    # ─── health score ──────────────────────────────────────────────────────────

    @staticmethod
    def planning_health_score(metrics: EvaluationMetrics) -> float:
        """
        Composite planning health score (0..1).

        Combines:
          - plan_stability_index (weight: 0.30)
          - replanning_burst_ratio (neg: weight 0.20)
          - coherence_drop_rate (neg: weight 0.25)
          - evaluation_entropy (neg: weight 0.15)
          - dag_growth_rate (neg: weight 0.10)
        """
        stability = metrics.plan_stability_index
        replan_burst = min(1.0, metrics.replanning_burst_ratio)
        coherence_drop = min(1.0, metrics.coherence_drop_rate)
        entropy = min(1.0, metrics.evaluation_entropy / 4.0)  # normalize to 0..1
        dag_growth = min(1.0, abs(metrics.dag_growth_rate))

        health = (
            0.30 * stability
            + 0.20 * (1.0 - replan_burst)
            + 0.25 * (1.0 - coherence_drop)
            + 0.15 * (1.0 - entropy)
            + 0.10 * (1.0 - dag_growth)
        )
        return max(0.0, min(1.0, health))
