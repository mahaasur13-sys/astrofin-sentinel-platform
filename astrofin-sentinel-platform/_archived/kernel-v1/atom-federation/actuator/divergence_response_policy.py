"""
Divergence Response Policy — v7.4
Threshold-driven intervention policy: decides WHEN and HOW to respond to divergence.

This is the "brain" of the actuator layer:
  given a divergence field state → choose the appropriate response action.

Design philosophy:
  - Reactive  (threshold breached)  vs  Proactive  (drift predicted)
  - Minimal sufficient intervention
  - No action if system is self-correcting
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto


class InterventionLevel(Enum):
    NONE = auto()          # coherence fine, no action
    WATCH = auto()         # approaching threshold, monitor only
    LIGHT = auto()         # minor intervention, single worker
    MODERATE = auto()      # multi-worker, moderate structural change
    AGGRESSIVE = auto()    # strong intervention, rebalancing
    EMERGENCY = auto()     # divergence critical, immediate hard reset


class ResponseAction(Enum):
    NO_ACTION = auto()
    INCREASE_OBSERVATION_FREQUENCY = auto()
    MICRO_CORRECTION = auto()
    REPROJECT_WORKER = auto()
    REBALANCE_AXIS = auto()
    PARTIAL_RESET = auto()
    FULL_RESET = auto()
    ISOLATE_WORKER = auto()       # quarantine misbehaving node
    EMERGENCY_SYNC = auto()       # force full state sync across workers


@dataclass
class ThresholdConfig:
    """
    Configurable thresholds for intervention levels.
    All coherence values are 0..1.
    """
    watch_coherence: float = 0.90
    light_coherence: float = 0.80
    moderate_coherence: float = 0.65
    aggressive_coherence: float = 0.45
    emergency_coherence: float = 0.25

    # Rate-of-change thresholds
    drift_rate_watch: float = 0.05   # per second
    drift_rate_alarm: float = 0.15   # per second

    # Divergence flux thresholds
    max_acceptable_flux: float = 0.3


@dataclass
class ResponseDecision:
    """
    A decision made by the policy engine.
    """
    level: InterventionLevel
    primary_action: ResponseAction
    secondary_actions: list[ResponseAction]
    target_workers: list[str]
    target_axes: list[str]
    reasoning: str
    override: bool  # True if this is an emergency override
    timestamp_ms: int


@dataclass
class DivergenceResponsePolicy:
    """
    Threshold-driven policy engine for swarm divergence response.

    Maps divergence field state → InterventionLevel → ResponseAction(s).

    The policy can use:
      1. Absolute thresholds (coherence level)
      2. Rate-of-change (drift velocity)
      3. Predictive model (optional predictor function)

    The policy does NOT execute actions — it DECIDES what to do.
    Execution is handled by CausalActuationEngine.
    """
    thresholds: ThresholdConfig = field(default_factory=ThresholdConfig)

    # Optional predictive model: given last N coherence values,
    # predict if breach will happen within prediction_horizon_seconds
    _coherence_history: list[float] = field(default_factory=list, init=False)
    _history_timestamps: list[int] = field(default_factory=list, init=False)
    _last_decision: ResponseDecision | None = field(default=None, init=False)
    _cooldown_ms: int = 5000  # minimum ms between decisions

    def evaluate(
        self,
        global_coherence: float,
        axis_coherences: dict[str, float],
        field_severity: str,
        most_divergent_axis: str,
        most_divergent_worker: str,
        timestamp_ms: int | None = None,
        predictor_fn: Callable[[list[float]], bool] | None = None,
    ) -> ResponseDecision:
        """
        Main evaluation entry point.

        Args:
            global_coherence: overall swarm coherence 0..1
            axis_coherences: per-axis coherence values
            field_severity: string name of FieldSeverity
            most_divergent_axis: axis with highest divergence
            most_divergent_worker: worker with highest individual divergence
            timestamp_ms: current time (optional, uses time.time_ns() if None)
            predictor_fn: optional (coherence_history → bool) for proactive decisions

        Returns:
            ResponseDecision with InterventionLevel, ResponseAction(s), targets.
        """
        ts = timestamp_ms or int(time.time() * 1000)

        # Cooldown check
        if (
            self._last_decision is not None
            and ts - self._last_decision.timestamp_ms < self._cooldown_ms
        ):
            return self._last_decision

        # Record history
        self._coherence_history.append(global_coherence)
        self._history_timestamps.append(ts)
        if len(self._coherence_history) > 60:
            self._coherence_history = self._coherence_history[-60:]
            self._history_timestamps = self._history_timestamps[-60:]

        # 1. Determine intervention level from absolute coherence
        level = self._level_from_coherence(global_coherence)

        # 2. Check rate-of-change (drift velocity)
        drift_rate = self._compute_drift_rate(ts)
        if drift_rate >= self.thresholds.drift_rate_alarm and level.value < InterventionLevel.MODERATE.value:
            level = InterventionLevel.MODERATE

        # 3. Check predictive breach (proactive)
        proactive = False
        if predictor_fn is not None and len(self._coherence_history) >= 5:
            proactive = predictor_fn(self._coherence_history)
            if proactive and level.value < InterventionLevel.LIGHT.value:
                level = InterventionLevel.LIGHT

        # 4. Override for CRITICAL field severity
        override = field_severity == "CRITICAL"
        if override:
            level = InterventionLevel.EMERGENCY

        # 5. Map level → actions
        primary, secondaries = self._actions_for_level(level)

        # 6. Target workers and axes
        targets = self._targets_for_level(
            level, most_divergent_worker, most_divergent_axis, axis_coherences
        )

        decision = ResponseDecision(
            level=level,
            primary_action=primary,
            secondary_actions=secondaries,
            target_workers=targets["workers"],
            target_axes=targets["axes"],
            reasoning=self._reasoning_string(level, global_coherence, drift_rate, proactive),
            override=override,
            timestamp_ms=ts,
        )

        self._last_decision = decision
        return decision

    def _level_from_coherence(self, coherence: float) -> InterventionLevel:
        t = self.thresholds
        if coherence >= t.watch_coherence:
            return InterventionLevel.NONE
        elif coherence >= t.light_coherence:
            return InterventionLevel.WATCH
        elif coherence >= t.moderate_coherence:
            return InterventionLevel.LIGHT
        elif coherence >= t.aggressive_coherence:
            return InterventionLevel.MODERATE
        elif coherence >= t.emergency_coherence:
            return InterventionLevel.AGGRESSIVE
        else:
            return InterventionLevel.EMERGENCY

    def _compute_drift_rate(self, now_ms: int) -> float:
        """
        Compute rate of coherence change (per second).
        Uses last 2 data points if available.
        """
        if len(self._coherence_history) < 2:
            return 0.0
        dt_s = (now_ms - self._history_timestamps[-2]) / 1000.0
        if dt_s <= 0:
            return 0.0
        dC = self._coherence_history[-1] - self._coherence_history[-2]
        return abs(dC / dt_s)

    def _actions_for_level(
        self, level: InterventionLevel
    ) -> tuple[ResponseAction, list[ResponseAction]]:
        mapping = {
            InterventionLevel.NONE: (ResponseAction.NO_ACTION, []),
            InterventionLevel.WATCH: (
                ResponseAction.INCREASE_OBSERVATION_FREQUENCY,
                [ResponseAction.MICRO_CORRECTION],
            ),
            InterventionLevel.LIGHT: (
                ResponseAction.MICRO_CORRECTION,
                [ResponseAction.REPROJECT_WORKER],
            ),
            InterventionLevel.MODERATE: (
                ResponseAction.REBALANCE_AXIS,
                [ResponseAction.MICRO_CORRECTION, ResponseAction.REPROJECT_WORKER],
            ),
            InterventionLevel.AGGRESSIVE: (
                ResponseAction.PARTIAL_RESET,
                [ResponseAction.REBALANCE_AXIS],
            ),
            InterventionLevel.EMERGENCY: (
                ResponseAction.FULL_RESET,
                [ResponseAction.ISOLATE_WORKER, ResponseAction.EMERGENCY_SYNC],
            ),
        }
        return mapping.get(level, (ResponseAction.NO_ACTION, []))

    @staticmethod
    def _targets_for_level(
        level: InterventionLevel,
        most_divergent_worker: str,
        most_divergent_axis: str,
        axis_coherences: dict[str, float],
    ) -> dict[str, list[str]]:
        """
        Determine which workers and axes to target based on intervention level.
        """
        if level == InterventionLevel.NONE or level == InterventionLevel.WATCH:
            return {"workers": [], "axes": []}
        elif level == InterventionLevel.LIGHT:
            return {
                "workers": [most_divergent_worker],
                "axes": [most_divergent_axis],
            }
        elif level == InterventionLevel.MODERATE:
            # All workers on the most divergent axis + any axis below threshold
            axes = [k for k, v in axis_coherences.items() if v < 0.7]
            if not axes:
                axes = [most_divergent_axis]
            return {"workers": [most_divergent_worker], "axes": axes}
        elif level == InterventionLevel.AGGRESSIVE:
            axes = list(axis_coherences.keys())
            return {"workers": [most_divergent_worker], "axes": axes}
        else:  # EMERGENCY
            axes = list(axis_coherences.keys())
            # All workers implicated — would need swarm-wide context
            return {"workers": [most_divergent_worker], "axes": axes}

    @staticmethod
    def _reasoning_string(
        level: InterventionLevel,
        coherence: float,
        drift_rate: float,
        proactive: bool,
    ) -> str:
        parts = [f"coherence={coherence:.3f}", f"level={level.name}"]
        if drift_rate > 0:
            parts.append(f"drift={drift_rate:.4f}/s")
        if proactive:
            parts.append("proactive=true")
        return "; ".join(parts)

    def should_act(self, decision: ResponseDecision) -> bool:
        """Helper: returns True if decision warrants actuation."""
        return decision.level != InterventionLevel.NONE

    def reset_history(self) -> None:
        """Clear coherence history (e.g., after a reset)."""
        self._coherence_history.clear()
        self._history_timestamps.clear()
        self._last_decision = None
