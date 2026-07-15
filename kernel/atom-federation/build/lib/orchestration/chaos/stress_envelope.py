"""
stress_envelope.py — chaos layer
Stability Envelope: formal working range for the autonomous planning system.

Transforms the system from heuristic-driven to constraint-driven control:
  metrics → envelope violation → severity (ground truth) → drift/chaos feedback

Bounds definition:
  - plan_stability_index:   0.6..1.0   (below 0.6 = degraded planning)
  - coherence_drop_rate:    0.0..0.15  (above 0.15 = rapid coherence loss)
  - replanning_frequency:   0.0..0.4   (above 0.4 = thrashing)
  - oscillation_index:      0.0..0.3   (above 0.3 = oscillation instability)
  - dag_structural_drift:   0.0..0.3   (above 0.3 = structural instability)

Envelope states (classify):
  STABLE   — all metrics within bounds
  WARNING  — 1-2 bounds violated, no critical thresholds breached
  CRITICAL — 3+ bounds violated OR any single bound > 2x upper limit
  COLLAPSE — system has entered incoherent state (coherence_drop_rate > 0.4
             OR plan_stability_index < 0.2 OR oscillation_index > 0.8)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

# ─── Envelope state classification ─────────────────────────────────────────────

class EnvelopeState(Enum):
    STABLE   = "stable"
    WARNING  = "warning"
    CRITICAL = "critical"
    COLLAPSE = "collapse"


# ─── Bound definitions ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class MetricBound:
    """Immutable bound for a single metric."""
    lower: float
    upper: float

    def is_violated(self, value: float) -> bool:
        return value < self.lower or value > self.upper

    def violation_magnitude(self, value: float) -> float:
        """How far outside bounds (0 if within)."""
        if value < self.lower:
            return self.lower - value
        if value > self.upper:
            return value - self.upper
        return 0.0


@dataclass
class EnvelopeBounds:
    """
    Complete set of stability bounds.

    Defaults calibrated for autonomous planning systems:
      - plan_stability_index:   planning coherence must stay above 0.6
      - coherence_drop_rate:    drops faster than 15% per tick indicate instability
      - replanning_frequency:   more than 40% of ticks with replans = thrashing
      - oscillation_index:      oscillation frequency above 0.3 = unstable
      - dag_structural_drift:   structural similarity below 0.7 = degraded graph
    """
    plan_stability_index:   MetricBound = field(
        default_factory=lambda: MetricBound(lower=0.6, upper=1.0)
    )
    coherence_drop_rate:    MetricBound = field(
        default_factory=lambda: MetricBound(lower=0.0, upper=0.15)
    )
    replanning_frequency:   MetricBound = field(
        default_factory=lambda: MetricBound(lower=0.0, upper=0.4)
    )
    oscillation_index:      MetricBound = field(
        default_factory=lambda: MetricBound(lower=0.0, upper=0.3)
    )
    dag_structural_drift:   MetricBound = field(
        default_factory=lambda: MetricBound(lower=0.0, upper=0.3)
    )

    @classmethod
    def from_dict(cls, data: dict) -> EnvelopeBounds:
        """Build bounds from dict of {metric_name: (lower, upper)}."""
        instance = cls()
        for name, (lower, upper) in data.items():
            if hasattr(instance, name) and isinstance((lower, upper), tuple):
                setattr(instance, name, MetricBound(lower=lower, upper=upper))
        return instance


# ─── Envelope violation record ─────────────────────────────────────────────────

@dataclass
class ViolationRecord:
    metric: str
    value: float
    bound: MetricBound
    magnitude: float   # distance outside bounds
    severity: float   # normalized 0..1 (magnitude relative to bound width)

    def __repr__(self) -> str:
        return (
            f"ViolationRecord(metric={self.metric}, value={self.value:.3f}, "
            f"bound=({self.bound.lower:.3f},{self.bound.upper:.3f}), "
            f"magnitude={self.magnitude:.3f}, severity={self.severity:.3f})"
        )


# ─── Core StabilityEnvelope ───────────────────────────────────────────────────

class StabilityEnvelope:
    """
    Formal stability boundary for the autonomous planning system.

    Provides:
      is_within(metrics)         — boolean: all metrics inside bounds?
      violation_score(metrics)   — float 0..1: aggregate violation severity
      classify(metrics)          — EnvelopeState: STABLE / WARNING / CRITICAL / COLLAPSE
      violations(metrics)        — list[ViolationRecord]: per-metric breakdown

    Designed to integrate with:
      - DriftProfiler    (drift episodes → envelope violation)
      - ChaosBridge      (impact score → envelope violation)
      - Governor         (block rate → envelope contribution)
      - CircuitBreaker   (envelope state → circuit open/close)
    """

    def __init__(
        self,
        bounds: EnvelopeBounds | None = None,
        critical_multiplier: float = 2.0,
        collapse_thresholds: dict | None = None,
    ) -> None:
        self.bounds = bounds or EnvelopeBounds()
        self.critical_multiplier = critical_multiplier  # 2x upper → CRITICAL
        self._collapse_thresholds = collapse_thresholds or {
            "coherence_drop_rate":    0.40,
            "plan_stability_index":   0.20,
            "oscillation_index":      0.80,
        }
        self._violation_history: list[list[ViolationRecord]] = []
        self._max_history: int = 100

    # ─── core API ─────────────────────────────────────────────────────────────

    def is_within(self, metrics: dict) -> bool:
        """True if ALL metrics are within their bounds."""
        violations = self.violations(metrics)
        return len(violations) == 0

    def violations(self, metrics: dict) -> list[ViolationRecord]:
        """Return per-metric violation records (empty = all within bounds)."""
        records: list[ViolationRecord] = []
        for metric_key, bound in self._bound_fields():
            if metric_key not in metrics:
                continue
            value = float(metrics[metric_key])
            if bound.is_violated(value):
                magnitude = bound.violation_magnitude(value)
                bound_width = bound.upper - bound.lower
                severity = magnitude / bound_width if bound_width > 0 else 0.0
                records.append(ViolationRecord(
                    metric=metric_key,
                    value=value,
                    bound=bound,
                    magnitude=magnitude,
                    severity=severity,
                ))
        return records

    def violation_score(self, metrics: dict) -> float:
        """
        Aggregate violation score 0..1.

        Uses max-severity across bounds: any single bound massively violated
        yields score near 1.0. Capped at 1.0.
        """
        records = self.violations(metrics)
        if not records:
            return 0.0
        return min(1.0, max(r.severity for r in records))

    def classify(self, metrics: dict) -> EnvelopeState:
        """
        Classify system into EnvelopeState.

        COLLAPSE check (highest priority):
          - Any single metric beyond collapse threshold → COLLAPSE
        CRITICAL check:
          - 3+ violations OR any violation with severity > 2.0 → CRITICAL
        WARNING check:
          - 1-2 violations → WARNING
        STABLE:
          - No violations → STABLE
        """
        # COLLAPSE: absolute thresholds breached
        # Lower-bound metrics (lower value = worse): collapse when value <= threshold
        # Upper-bound metrics (higher value = worse): collapse when value >= threshold
        _lower_collapse = {"plan_stability_index"}
        for metric, threshold in self._collapse_thresholds.items():
            if metric not in metrics:
                continue
            value = float(metrics[metric])
            if metric in _lower_collapse:
                if value <= threshold:
                    return EnvelopeState.COLLAPSE
            else:
                if value >= threshold:
                    return EnvelopeState.COLLAPSE

        # Count violations
        records = self.violations(metrics)
        violation_count = len(records)
        any_severe = any(r.severity > self.critical_multiplier for r in records)

        if violation_count >= 3 or any_severe:
            return EnvelopeState.CRITICAL
        if violation_count >= 1:
            return EnvelopeState.WARNING
        return EnvelopeState.STABLE

    def violation_score_from_episodes(
        self,
        drift_episodes: list,   # list[DriftEpisode]
        tick: int,
    ) -> float:
        """
        Compute envelope violation score from DriftProfiler episodes.

        Maps drift episode types → envelope metrics:
          - OSCILLATING_PLAN   → oscillation_index, replanning_frequency
          - UNSTABLE_GOAL      → plan_stability_index
          - UNSTABLE_WEIGHTS   → plan_stability_index
          - STRUCTURAL_DAG_DRIFT → dag_structural_drift
          - COHERENCE_COLLAPSE  → coherence_drop_rate (triggers COLLAPSE)
        """
        if not drift_episodes:
            return 0.0

        # Build synthetic metrics from episodes
        metrics: dict[str, float] = {
            "oscillation_index":    0.0,
            "replanning_frequency": 0.0,
            "plan_stability_index": 1.0,
            "coherence_drop_rate":  0.0,
            "dag_structural_drift": 0.0,
        }

        osc_count = 0
        goal_drift_mag = 0.0
        dag_drift = 0.0
        coherence_collapse = False

        for ep in drift_episodes:
            from orchestration.planning_observability.drift_profiler import DriftType
            dt = ep.drift_type
            severity = float(ep.severity)

            if dt == DriftType.OSCILLATING_PLAN:
                osc_count += 1
                metrics["oscillation_index"] = max(
                    metrics["oscillation_index"],
                    min(1.0, severity * 2)
                )
            elif dt == DriftType.UNSTABLE_GOAL:
                metrics["plan_stability_index"] = min(
                    metrics["plan_stability_index"],
                    max(0.5 - severity * 0.5, 0.3)
                )
            elif dt == DriftType.UNSTABLE_WEIGHTS:
                metrics["plan_stability_index"] = min(
                    metrics["plan_stability_index"],
                    1.0 - (severity * 0.5)
                )
            elif dt == DriftType.STRUCTURAL_DAG_DRIFT:
                metrics["dag_structural_drift"] = max(
                    metrics["dag_structural_drift"],
                    severity
                )
            elif dt == DriftType.COHERENCE_COLLAPSE:
                metrics["coherence_drop_rate"] = max(
                    metrics["coherence_drop_rate"],
                    min(1.0, severity * 2)
                )
                coherence_collapse = True
            # SCORE_HYSTERESIS — treated as oscillation
            elif dt.value == "score_hysteresis":
                metrics["oscillation_index"] = max(
                    metrics["oscillation_index"],
                    min(1.0, severity)
                )

        # replanning_frequency from oscillation count
        if len(drift_episodes) > 0:
            metrics["replanning_frequency"] = min(
                1.0,
                osc_count / max(1, len(drift_episodes))
            )

        # COLLAPSE detection from episodes
        if coherence_collapse and metrics["coherence_drop_rate"] >= self._collapse_thresholds["coherence_drop_rate"]:
            return 1.0  # immediate collapse

        return self.violation_score(metrics)

    # ─── history & diagnostics ────────────────────────────────────────────────

    def record_violations(self, metrics: dict) -> None:
        """Store violation records for trend analysis."""
        records = self.violations(metrics)
        self._violation_history.append(records)
        if len(self._violation_history) > self._max_history:
            self._violation_history.pop(0)

    def recent_violation_trend(self, window: int = 10) -> float:
        """
        Compute violation trend over recent window.

        Returns avg violation_score across last `window` observations.
        Returns NaN if no history.
        """
        if not self._violation_history:
            return float("nan")
        windowed = self._violation_history[-window:]
        scores = []
        for records in windowed:
            if not records:
                scores.append(0.0)
            else:
                bound_count = len(self._bound_fields())
                total = sum(r.severity for r in records)
                scores.append(min(1.0, total / bound_count))
        return sum(scores) / len(scores) if scores else float("nan")

    def explain(self, metrics: dict) -> dict:
        """Full diagnostic output for a metrics snapshot."""
        state = self.classify(metrics)
        records = self.violations(metrics)
        score = self.violation_score(metrics)
        return {
            "state": state.value,
            "violation_score": score,
            "violation_count": len(records),
            "violations": [
                {
                    "metric": r.metric,
                    "value": round(r.value, 4),
                    "lower": round(r.bound.lower, 4),
                    "upper": round(r.bound.upper, 4),
                    "magnitude": round(r.magnitude, 4),
                    "severity": round(r.severity, 4),
                }
                for r in records
            ],
            "is_within": len(records) == 0,
            "trend": round(self.recent_violation_trend(), 4) if not math.isnan(self.recent_violation_trend()) else None,
        }

    # ─── internal helpers ──────────────────────────────────────────────────────

    def _bound_fields(self):
        """Yield (name, bound) for all defined bounds."""
        return [
            ("plan_stability_index",   self.bounds.plan_stability_index),
            ("coherence_drop_rate",    self.bounds.coherence_drop_rate),
            ("replanning_frequency",   self.bounds.replanning_frequency),
            ("oscillation_index",      self.bounds.oscillation_index),
            ("dag_structural_drift",   self.bounds.dag_structural_drift),
        ]
