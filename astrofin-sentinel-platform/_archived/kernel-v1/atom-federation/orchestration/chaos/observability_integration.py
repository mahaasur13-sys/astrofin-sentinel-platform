"""
chaos/observability_integration.py — HARDENING-2 MVP

Chaos ↔ Drift Correlation + Impact Scoring + Feedback Controller.

Minimal viable layer that closes the loop:
  chaos_event → attach_to_drift → compute_impact → feedback → tune intensity

Classes (MVP):
  DriftCorrelation        — correlation record between chaos and drift
  ImpactScorer           — deterministic weighted impact scoring
  ChaosFeedbackController — adjusts chaos intensity based on impact
  ChaosObservabilityBridge — unified API, owns correlation store

Edge cases handled:
  - zero/missing signals → return safe defaults
  - empty correlation list → no-op on feedback
  - tick/time tracking for lag computation
  - governor integration point for circuit breaker
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

# ─── drift correlation record ──────────────────────────────────────────────────

class DriftType(Enum):
    """Mirrors DriftType from drift_profiler.py (local re-export for this module)."""
    OSCILLATING_PLAN = "oscillating_plan"
    UNSTABLE_GOAL = "unstable_goal"
    UNSTABLE_WEIGHTS = "unstable_weights"
    STRUCTURAL_DAG_DRIFT = "structural_dag_drift"
    COHERENCE_COLLAPSE = "coherence_collapse"
    SCORE_HYSTERESIS = "score_hysteresis"


@dataclass
class DriftCorrelation:
    """
    Records a causal link between a chaos event and a detected drift episode.
    """
    chaos_event_id: str
    drift_type: DriftType
    lag_ticks: int
    severity: float          # 0..1
    correlation_id: str = field(default_factory=lambda: f"corr_{id(object())}")


@dataclass
class ChaosEvent:
    """
    Minimal chaos event record for correlation tracking.
    """
    event_id: str
    event_type: str
    intensity: float          # 0..1
    tick_injected: int


# ─── impact scorer ─────────────────────────────────────────────────────────────

@dataclass
class ImpactWeights:
    """Tunable weights for ImpactScorer. Must sum to 1.0."""
    w_oscillation: float = 0.25
    w_coherence_drop: float = 0.25
    w_governor_block_rate: float = 0.30
    w_recovery_time: float = 0.20


class ImpactScorer:
    """
    Deterministic weighted impact scorer.

    impact = w1*oscillation + w2*coherence_drop
           + w3*governor_block_rate + w4*recovery_time

    All inputs normalised to [0, 1]. No ML, no randomness.
    """

    def __init__(self, weights: ImpactWeights | None = None):
        self.weights = weights or ImpactWeights()
        total = (
            self.weights.w_oscillation
            + self.weights.w_coherence_drop
            + self.weights.w_governor_block_rate
            + self.weights.w_recovery_time
        )
        if not math.isclose(total, 1.0, abs_tol=0.01):
            raise ValueError(f"ImpactWeights must sum to 1.0, got {total}")

    def score(
        self,
        oscillation: float,
        coherence_drop: float,
        governor_block_rate: float,
        recovery_time: float,
    ) -> float:
        impact = (
            self.weights.w_oscillation * min(1.0, max(0.0, oscillation))
            + self.weights.w_coherence_drop * min(1.0, max(0.0, coherence_drop))
            + self.weights.w_governor_block_rate * min(1.0, max(0.0, governor_block_rate))
            + self.weights.w_recovery_time * min(1.0, max(0.0, recovery_time))
        )
        return round(min(1.0, max(0.0, impact)), 4)

    def explain(
        self,
        oscillation: float,
        coherence_drop: float,
        governor_block_rate: float,
        recovery_time: float,
    ) -> str:
        """Human-readable breakdown of impact components."""
        w = self.weights
        return (
            f"impact={self.score(oscillation, coherence_drop, governor_block_rate, recovery_time):.4f}\n"
            f"  oscillation={w.w_oscillation * oscillation:.4f} (w={w.w_oscillation})\n"
            f"  coherence_drop={w.w_coherence_drop * coherence_drop:.4f} (w={w.w_coherence_drop})\n"
            f"  governor_block_rate={w.w_governor_block_rate * governor_block_rate:.4f} (w={w.w_governor_block_rate})\n"
            f"  recovery_time={w.w_recovery_time * recovery_time:.4f} (w={w.w_recovery_time})"
        )


# ─── chaos feedback controller ────────────────────────────────────────────────

@dataclass
class ControllerConfig:
    """Tunable parameters for ChaosFeedbackController."""
    impact_high: float = 0.70
    impact_low: float = 0.30
    reduction_factor: float = 0.20
    increase_factor: float = 1.15
    min_intensity: float = 0.05
    max_intensity: float = 1.00


class ChaosFeedbackController:
    """
    Stateless deterministic controller.

    impact > impact_high  → reduce intensity (multiply by reduction_factor)
    impact < impact_low   → increase intensity (multiply by increase_factor)
    otherwise            → hold
    """

    def __init__(self, config: ControllerConfig | None = None):
        self.config = config or ControllerConfig()
        cfg = self.config
        if not (0 <= cfg.impact_low < cfg.impact_high <= 1.0):
            raise ValueError("impact_low must be < impact_high and both in [0, 1]")
        if not (0 < cfg.reduction_factor < 1.0 < cfg.increase_factor):
            raise ValueError("reduction_factor must be < 1.0 < increase_factor")

    def feedback(self, current_intensity: float, impact: float) -> float:
        cfg = self.config
        if impact > cfg.impact_high:
            new_intensity = current_intensity * cfg.reduction_factor
        elif impact < cfg.impact_low:
            new_intensity = current_intensity * cfg.increase_factor
        else:
            new_intensity = current_intensity

        return round(
            min(cfg.max_intensity, max(cfg.min_intensity, new_intensity)),
            4,
        )

    def explain(self, current_intensity: float, impact: float) -> str:
        cfg = self.config
        action = "HOLD"
        if impact > cfg.impact_high:
            action = "REDUCE"
        elif impact < cfg.impact_low:
            action = "INCREASE"
        new_intensity = self.feedback(current_intensity, impact)
        return f"[{action}] impact={impact:.4f} | current={current_intensity:.4f} → new={new_intensity:.4f}"


# ─── chaos-observability bridge ────────────────────────────────────────────────

class ChaosObservabilityBridge:
    """
    Unified API: owns correlation store, provides full chaos↔drift integration.

    Responsibilities:
      1. record_chaos_event  — register a chaos injection event
      2. attach_to_drift     — link a drift episode to a chaos event
      3. compute_impact      — score current system impact
      4. feedback            — tune chaos intensity from impact
      5. correlation_summary — report all active correlations
    """

    def __init__(
        self,
        scorer: ImpactScorer | None = None,
        controller: ChaosFeedbackController | None = None,
        max_correlations: int = 200,
    ):
        self.scorer = scorer or ImpactScorer()
        self.controller = controller or ChaosFeedbackController()
        self.max_correlations = max_correlations

        self._correlations: list[DriftCorrelation] = []
        self._chaos_events: dict[str, ChaosEvent] = {}
        self._governor_blocks: list[bool] = []
        self._governor_window: int = 20
        self._current_intensity: float = 0.50

    # ── chaos event recording ─────────────────────────────────────────────────

    def record_chaos_event(
        self,
        event_id: str,
        event_type: str,
        intensity: float,
        tick_injected: int,
    ) -> ChaosEvent:
        event = ChaosEvent(
            event_id=event_id,
            event_type=event_type,
            intensity=intensity,
            tick_injected=tick_injected,
        )
        self._chaos_events[event_id] = event
        return event

    # ── drift correlation ──────────────────────────────────────────────────────

    def attach_to_drift(
        self,
        chaos_event_id: str,
        drift_type: DriftType,
        lag_ticks: int,
        severity: float,
    ) -> DriftCorrelation:
        corr = DriftCorrelation(
            chaos_event_id=chaos_event_id,
            drift_type=drift_type,
            lag_ticks=lag_ticks,
            severity=severity,
            correlation_id=f"corr_{len(self._correlations)}",
        )
        self._correlations.append(corr)

        # Prune if over capacity
        if len(self._correlations) > self.max_correlations:
            self._correlations = self._correlations[-self.max_correlations:]

        return corr

    # ── governor block rate tracking ─────────────────────────────────────────

    def record_governor_decision(self, blocked: bool) -> None:
        self._governor_blocks.append(blocked)
        if len(self._governor_blocks) > self._governor_window:
            self._governor_blocks = self._governor_blocks[-self._governor_window:]

    def governor_block_rate(self) -> float:
        if not self._governor_blocks:
            return 0.0
        blocked_count = sum(1 for b in self._governor_blocks if b)
        return round(blocked_count / len(self._governor_blocks), 4)

    # ── impact computation ─────────────────────────────────────────────────────

    def compute_impact(
        self,
        oscillation: float,
        coherence_drop: float,
        recovery_time: float,
    ) -> float:
        block_rate = self.governor_block_rate()
        return self.scorer.score(
            oscillation=oscillation,
            coherence_drop=coherence_drop,
            governor_block_rate=block_rate,
            recovery_time=recovery_time,
        )

    # ── feedback loop ─────────────────────────────────────────────────────────

    def feedback(self, impact: float) -> float:
        new_intensity = self.controller.feedback(self._current_intensity, impact)
        self._current_intensity = new_intensity
        return new_intensity

    @property
    def current_intensity(self) -> float:
        return self._current_intensity

    @property
    def correlations(self) -> list[DriftCorrelation]:
        return list(self._correlations)

    def correlation_summary(self) -> dict:
        if not self._correlations:
            return {"total": 0, "by_type": {}, "avg_lag": 0.0, "avg_severity": 0.0}

        by_type: dict[str, int] = {}
        total_severity = 0.0
        total_lag = 0

        for corr in self._correlations:
            key = corr.drift_type.value
            by_type[key] = by_type.get(key, 0) + 1
            total_severity += corr.severity
            total_lag += corr.lag_ticks

        n = len(self._correlations)
        return {
            "total": n,
            "by_type": by_type,
            "avg_lag": round(total_lag / n, 2),
            "avg_severity": round(total_severity / n, 4),
        }

    def explain(self, impact: float) -> str:
        lines = [
            "ChaosObservabilityBridge state:",
            f"  intensity={self._current_intensity:.4f}",
            f"  impact={impact:.4f}",
            f"  governor_block_rate={self.governor_block_rate():.4f}",
            f"  correlations={len(self._correlations)}",
            f"  feedback: {self.controller.explain(self._current_intensity, impact)}",
        ]
        return "\n".join(lines)
