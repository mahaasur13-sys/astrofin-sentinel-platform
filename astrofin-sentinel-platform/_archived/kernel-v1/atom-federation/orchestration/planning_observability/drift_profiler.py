"""
drift_profiler.py — planning_observability layer
Detects and reports planning degradation over time.

Detects:
  - oscillating plans (replanning without progress)
  - unstable goals (goal drift between replans)
  - unstable evaluation weights (weight adjustments growing)
  - structural DAG drift (graph structure changing significantly)

Invariant (v8.0 Phase A):
  planning_degradation = f(oscillation, goal_drift, weight_drift, DAG_drift)
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum


class DriftType(Enum):
    OSCILLATING_PLAN = "oscillating_plan"
    UNSTABLE_GOAL = "unstable_goal"
    UNSTABLE_WEIGHTS = "unstable_weights"
    STRUCTURAL_DAG_DRIFT = "structural_dag_drift"
    COHERENCE_COLLAPSE = "coherence_collapse"
    SCORE_HYSTERESIS = "score_hysteresis"


@dataclass
class DriftEpisode:
    drift_type: DriftType
    start_tick: int
    end_tick: int
    severity: float            # 0..1
    description: str
    evidence: dict             # raw metrics that triggered detection


@dataclass
class OscillationProfile:
    """Profile of plan oscillation."""
    plan_id: str
    replan_count: int
    avg_coherence_delta: float
    coherence_variance: float
    is_oscillating: bool
    oscillation_frequency: float


@dataclass
class GoalDriftProfile:
    """Profile of goal drift between replans."""
    plan_id: str
    drift_magnitude: float     # how much goal changed
    drift_velocity: float      # drift per tick
    drift_acceleration: float # drift acceleration (2nd derivative)
    is_drift_detected: bool


@dataclass
class WeightDriftProfile:
    """Profile of evaluation weight instability."""
    avg_weight_adjustment: float
    weight_adjustment_variance: float
    sources_with_negative_growth: list[str]
    is_weight_instability_detected: bool


@dataclass
class DAGDriftProfile:
    """Profile of structural DAG drift."""
    structural_similarity: float   # 0..1 (1 = identical structure)
    node_count_delta: int
    depth_delta: int
    branching_factor_delta: float
    is_drift_detected: bool


class DriftProfiler:
    """
    Detects and profiles planning degradation patterns.

    Uses sliding windows and statistical tests to identify:
      1. Oscillating plans — replans that don't improve coherence
      2. Goal drift — goal changes between replans
      3. Weight instability — growing weight adjustments
      4. Structural DAG drift — graph structure changes over time

    All detection is based on observable trace + graph data.
    No internal state beyond detection thresholds.
    """

    def __init__(
        self,
        oscillation_window: int = 10,
        drift_window: int = 20,
        weight_window: int = 30,
        dag_snapshot_interval: int = 5,
        coherence_drop_threshold: float = 0.10,
        weight_variance_threshold: float = 0.05,
        structural_similarity_threshold: float = 0.70,
    ) -> None:
        self.oscillation_window = oscillation_window
        self.drift_window = drift_window
        self.weight_window = weight_window
        self.dag_snapshot_interval = dag_snapshot_interval
        self.coherence_drop_threshold = coherence_drop_threshold
        self.goal_drift_threshold: float = 0.10  # used in scan(); separate from oscillation threshold
        self.weight_variance_threshold = weight_variance_threshold
        self.structural_similarity_threshold = structural_similarity_threshold

        # DAG structure snapshots for drift detection
        self._dag_snapshots: list[dict] = []
        self._last_snapshot_tick: int = -1

    # ─── oscillation detection ─────────────────────────────────────────────────

    def detect_oscillation(
        self,
        coherence_trajectory: list[float],
        replan_count: int,
        tick: int,
        plan_id: str,
    ) -> OscillationProfile:
        """
        Detect oscillating replan pattern.

        Oscillation = replans that consistently fail to improve coherence
        (or worsen it), measured by coherence variance and delta sign changes.
        """
        if len(coherence_trajectory) < 3 or replan_count < 2:
            return OscillationProfile(
                plan_id=plan_id,
                replan_count=replan_count,
                avg_coherence_delta=0.0,
                coherence_variance=0.0,
                is_oscillating=False,
                oscillation_frequency=0.0,
            )

        # Coherence deltas between consecutive points
        deltas = [
            coherence_trajectory[i] - coherence_trajectory[i - 1]
            for i in range(1, len(coherence_trajectory))
        ]
        avg_delta = sum(deltas) / len(deltas)
        mean = sum(deltas) / len(deltas)
        variance = sum((d - mean) ** 2 for d in deltas) / len(deltas)
        coherence_variance = math.sqrt(variance)

        # Oscillation detected if:
        # 1. Average coherence change is near zero (no progress)
        # 2. Variance is high (direction flips frequently)
        sign_changes = sum(
            1 for i in range(1, len(deltas))
            if (deltas[i] >= 0) != (deltas[i - 1] >= 0)
        )
        sign_change_rate = sign_changes / max(1, len(deltas) - 1)

        is_oscillating = (
            abs(avg_delta) < self.coherence_drop_threshold
            and coherence_variance > self.coherence_drop_threshold
            and sign_change_rate > 0.4
        )

        return OscillationProfile(
            plan_id=plan_id,
            replan_count=replan_count,
            avg_coherence_delta=avg_delta,
            coherence_variance=coherence_variance,
            is_oscillating=is_oscillating,
            oscillation_frequency=sign_change_rate,
        )

    # ─── goal drift detection ───────────────────────────────────────────────────

    def detect_goal_drift(
        self,
        coherence_at_replans: list[float],
        tick: int,
        plan_id: str,
        goal_drift_threshold: float = 0.10,
    ) -> GoalDriftProfile:
        """
        Detect goal drift across replans.

        Goal drift = consistent directional change in coherence at replan points.
        Detected by measuring drift magnitude, velocity, and acceleration.
        """
        if len(coherence_at_replans) < 3:
            return GoalDriftProfile(
                plan_id=plan_id,
                drift_magnitude=0.0,
                drift_velocity=0.0,
                drift_acceleration=0.0,
                is_drift_detected=False,
            )

        # Drift magnitude = range of coherence values
        drift_magnitude = (
            max(coherence_at_replans) - min(coherence_at_replans)
        )

        # Drift velocity = avg change per tick
        n = len(coherence_at_replans)
        ticks_span = max(1, n - 1)
        drift_velocity = drift_magnitude / ticks_span

        # Drift acceleration = change in velocity
        deltas = [
            coherence_at_replans[i] - coherence_at_replans[i - 1]
            for i in range(1, n)
        ]
        if len(deltas) >= 2:
            delta_deltas = [
                deltas[i] - deltas[i - 1]
                for i in range(1, len(deltas))
            ]
            drift_acceleration = sum(delta_deltas) / len(delta_deltas)
        else:
            drift_acceleration = 0.0

        is_drift_detected = drift_velocity > goal_drift_threshold

        return GoalDriftProfile(
            plan_id=plan_id,
            drift_magnitude=drift_magnitude,
            drift_velocity=drift_velocity,
            drift_acceleration=drift_acceleration,
            is_drift_detected=is_drift_detected,
        )

    # ─── weight instability detection ─────────────────────────────────────────

    def detect_weight_instability(
        self,
        weight_adjustments: list[float],
    ) -> WeightDriftProfile:
        """
        Detect unstable evaluation weights.

        Weight instability = growing variance in weight adjustments
        over time, suggesting the evaluator is "hunting" for stable weights.
        """
        if len(weight_adjustments) < 3:
            return WeightDriftProfile(
                avg_weight_adjustment=0.0,
                weight_adjustment_variance=0.0,
                sources_with_negative_growth=[],
                is_weight_instability_detected=False,
            )

        avg_adjustment = sum(weight_adjustments) / len(weight_adjustments)
        mean = sum(weight_adjustments) / len(weight_adjustments)
        variance = sum((w - mean) ** 2 for w in weight_adjustments) / len(weight_adjustments)

        is_instability_detected = math.sqrt(variance) > self.weight_variance_threshold

        return WeightDriftProfile(
            avg_weight_adjustment=avg_adjustment,
            weight_adjustment_variance=math.sqrt(variance),
            sources_with_negative_growth=[],
            is_weight_instability_detected=is_instability_detected,
        )

    # ─── DAG structural drift ─────────────────────────────────────────────────

    def _dag_structural_fingerprint(self, nodes: list[dict]) -> dict:
        """Generate a structural fingerprint of a DAG snapshot."""
        node_ids = sorted([n["node_id"] for n in nodes])
        child_counts = sorted([len(n.get("children_ids", [])) for n in nodes])
        return {
            "node_ids": node_ids,
            "child_counts": tuple(child_counts),
            "node_count": len(nodes),
        }

    @staticmethod
    def _jaccard_similarity(set_a: set, set_b: set) -> float:
        """Jaccard similarity between two sets."""
        if not set_a and not set_b:
            return 1.0
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        if union == 0:
            return 1.0
        return intersection / union

    def record_dag_snapshot(self, nodes: list[dict], tick: int) -> None:
        """Record a DAG snapshot for drift detection."""
        if tick - self._last_snapshot_tick < self.dag_snapshot_interval:
            return
        fp = self._dag_structural_fingerprint(nodes)
        self._dag_snapshots.append({**fp, "tick": tick})
        self._last_snapshot_tick = tick

    def detect_dag_drift(self, current_nodes: list[dict]) -> DAGDriftProfile:
        """
        Detect structural drift between current DAG and recent snapshots.

        Similarity = Jaccard on node IDs + correlation on child count distributions.
        """
        if len(self._dag_snapshots) < 2:
            return DAGDriftProfile(
                structural_similarity=1.0,
                node_count_delta=0,
                depth_delta=0,
                branching_factor_delta=0.0,
                is_drift_detected=False,
            )

        current_fp = self._dag_structural_fingerprint(current_nodes)
        prev_fp = self._dag_snapshots[-1]

        # Node ID similarity
        id_sim = self._jaccard_similarity(
            set(current_fp["node_ids"]),
            set(prev_fp["node_ids"]),
        )

        # Child count distribution similarity (normalized)
        current_cc = current_fp["child_counts"]
        prev_cc = prev_fp["child_counts"]
        max_len = max(len(current_cc), len(prev_cc))
        if max_len > 0:
            min_len = min(len(current_cc), len(prev_cc))
            cc_sim = sum(
                1 for i in range(min_len)
                if current_cc[i] == prev_cc[i]
            ) / max_len
        else:
            cc_sim = 1.0

        structural_similarity = (id_sim + cc_sim) / 2.0

        node_count_delta = (
            current_fp["node_count"] - prev_fp["node_count"]
        )
        current_avg_children = (
            sum(current_cc) / len(current_cc) if current_cc else 0.0
        )
        prev_avg_children = (
            sum(prev_cc) / len(prev_cc) if prev_cc else 0.0
        )
        branching_factor_delta = current_avg_children - prev_avg_children

        is_drift_detected = (
            structural_similarity < self.structural_similarity_threshold
            or node_count_delta > 5
        )

        return DAGDriftProfile(
            structural_similarity=structural_similarity,
            node_count_delta=node_count_delta,
            depth_delta=0,  # depth tracking requires node depth data
            branching_factor_delta=branching_factor_delta,
            is_drift_detected=is_drift_detected,
        )

    # ─── full drift scan ────────────────────────────────────────────────────────

    def scan(
        self,
        tick: int,
        plan_id: str,
        coherence_trajectory: list[float],
        replan_count: int,
        coherence_at_replans: list[float],
        weight_adjustments: list[float],
        current_nodes: list[dict],
    ) -> list[DriftEpisode]:
        """
        Run full drift detection scan.

        Returns list of detected drift episodes with severity and evidence.
        """
        episodes: list[DriftEpisode] = []

        # Oscillation detection
        osc = self.detect_oscillation(
            coherence_trajectory, replan_count, tick, plan_id
        )
        if osc.is_oscillating:
            episodes.append(DriftEpisode(
                drift_type=DriftType.OSCILLATING_PLAN,
                start_tick=tick - self.oscillation_window,
                end_tick=tick,
                severity=min(1.0, osc.coherence_variance * 2),
                description=(
                    f"Plan {plan_id}: oscillating (freq={osc.oscillation_frequency:.2f}, "
                    f"replans={osc.replan_count}, avg_delta={osc.avg_coherence_delta:.3f})"
                ),
                evidence={"oscillation_profile": {
                    "replan_count": osc.replan_count,
                    "coherence_variance": osc.coherence_variance,
                    "oscillation_frequency": osc.oscillation_frequency,
                    "avg_coherence_delta": osc.avg_coherence_delta,
                }},
            ))

        # Goal drift detection
        gdp = self.detect_goal_drift(coherence_at_replans, tick, plan_id, self.goal_drift_threshold)
        if gdp.is_drift_detected:
            severity = min(1.0, gdp.drift_magnitude)
            episodes.append(DriftEpisode(
                drift_type=DriftType.UNSTABLE_GOAL,
                start_tick=tick - self.drift_window,
                end_tick=tick,
                severity=severity,
                description=(
                    f"Plan {plan_id}: goal drift detected "
                    f"(magnitude={gdp.drift_magnitude:.3f}, "
                    f"velocity={gdp.drift_velocity:.3f})"
                ),
                evidence={"goal_drift_profile": {
                    "drift_magnitude": gdp.drift_magnitude,
                    "drift_velocity": gdp.drift_velocity,
                    "drift_acceleration": gdp.drift_acceleration,
                }},
            ))

        # Weight instability detection
        wdp = self.detect_weight_instability(weight_adjustments)
        if wdp.is_weight_instability_detected:
            episodes.append(DriftEpisode(
                drift_type=DriftType.UNSTABLE_WEIGHTS,
                start_tick=tick - self.weight_window,
                end_tick=tick,
                severity=min(1.0, wdp.weight_adjustment_variance * 5),
                description=(
                    f"Weight instability detected "
                    f"(variance={wdp.weight_adjustment_variance:.3f})"
                ),
                evidence={"weight_drift_profile": {
                    "avg_adjustment": wdp.avg_weight_adjustment,
                    "variance": wdp.weight_adjustment_variance,
                }},
            ))

        # DAG structural drift
        dag_dp = self.detect_dag_drift(current_nodes)
        self.record_dag_snapshot(current_nodes, tick)
        if dag_dp.is_drift_detected:
            episodes.append(DriftEpisode(
                drift_type=DriftType.STRUCTURAL_DAG_DRIFT,
                start_tick=tick - self.drift_window,
                end_tick=tick,
                severity=1.0 - dag_dp.structural_similarity,
                description=(
                    f"DAG structural drift detected "
                    f"(similarity={dag_dp.structural_similarity:.3f}, "
                    f"node_delta={dag_dp.node_count_delta})"
                ),
                evidence={"dag_drift_profile": {
                    "structural_similarity": dag_dp.structural_similarity,
                    "node_count_delta": dag_dp.node_count_delta,
                    "branching_factor_delta": dag_dp.branching_factor_delta,
                }},
            ))

        return episodes
