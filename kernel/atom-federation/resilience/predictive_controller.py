"""
PredictiveController v6.6 — Predictive pre-healing controller.

Problem:
  v6.5 is REACTIVE: heals after failure is detected.
  Need PREDICTIVE: heal BEFORE failure occurs.

Solution:
  PredictiveController wraps ClosedLoopResilienceController with:
    1. SelfModel integration — internal causal representation
    2. Forecast horizon — predict degradation N seconds ahead
    3. Pre-emptive healing — trigger heal before threshold breach

Key insight:
  v6.5: stability_score=0.3 → heal     (reactive, RTO-dependent)
  v6.6: score=0.7 but falling fast      → heal NOW (predictive, RTO→0)

Usage:
    predictor = PredictiveController(ctrl)
    result = predictor.tick()  # returns PredictiveTickResult
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

from resilience.closed_loop import ClosedLoopResilienceController
from resilience.healer import HealingAction
from resilience.self_model import SelfModel

__all__ = ["PredictiveController", "PredictiveTickResult"]


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class PredictiveTickResult:
    """
    Extended tick result with predictive fields.

    Adds to TickResult:
      - predicted_score: stability score forecast (horizon_s ahead)
      - predicted_change: expected delta from current score
      - pre_heal_triggered: whether pre-emptive heal fired
      - forecast_horizon_s: how far ahead we predicted
      - model_state: internal self-model summary
    """
    tick_num: int
    ts: float
    duration_ms: float
    current_score: float
    predicted_score: float
    predicted_change: float
    pre_heal_triggered: bool
    pre_heal_reason: str
    forecast_horizon_s: float
    actions_taken: list[str]
    model_built: bool
    panic: bool = False

    @property
    def is_stable(self) -> bool:
        return self.current_score >= 0.70

    @property
    def is_critical(self) -> bool:
        return self.current_score < 0.30

    @property
    def is_degraded(self) -> bool:
        return 0.30 <= self.current_score < 0.70

    @property
    def degradation_incoming(self) -> bool:
        """True if predicted score is significantly worse than current."""
        return self.predicted_change < -0.10

    def to_dict(self) -> dict:
        return {
            "tick_num": self.tick_num,
            "ts": round(self.ts, 4),
            "duration_ms": round(self.duration_ms, 4),
            "current_score": round(self.current_score, 4),
            "predicted_score": round(self.predicted_score, 4),
            "predicted_change": round(self.predicted_change, 4),
            "pre_heal_triggered": self.pre_heal_triggered,
            "pre_heal_reason": self.pre_heal_reason,
            "forecast_horizon_s": self.forecast_horizon_s,
            "actions_taken": self.actions_taken,
            "is_stable": self.is_stable,
            "is_critical": self.is_critical,
            "is_degraded": self.is_degraded,
            "degradation_incoming": self.degradation_incoming,
            "model_built": self.model_built,
            "panic": self.panic,
        }


# ── PredictiveController ───────────────────────────────────────────────────────

class PredictiveController:
    """
    Extends ClosedLoopResilienceController with predictive capabilities.

    The predictive loop:
      1. Build/update SelfModel from current snapshot
      2. Forecast stability score N seconds ahead
      3. If degradation exceeds threshold → pre-emptive heal
      4. Return PredictiveTickResult with prediction metadata

    This shifts the system from REACTIVE to PREDICTIVE control:
      - Reactive: wait for score to drop, then heal (late)
      - Predictive: detect falling trend, heal early (RTO → 0)
    """

    DEFAULT_HORIZON_S = 30.0
    DEFAULT_DEGRADATION_THRESHOLD = 0.15  # If score would drop >0.15 → pre-heal
    DEFAULT_PRE_HEAL_COOLDOWN_S = 10.0

    def __init__(
        self,
        ctrl: ClosedLoopResilienceController,
        forecast_horizon_s: float = DEFAULT_HORIZON_S,
        degradation_threshold: float = DEFAULT_DEGRADATION_THRESHOLD,
    ) -> None:
        self.ctrl = ctrl
        self.self_model = SelfModel()
        self.forecast_horizon_s = forecast_horizon_s
        self.degradation_threshold = degradation_threshold

        self._tick_count = 0
        self._last_score: float = 1.0
        self._pre_heal_cooldown_until: float = 0.0
        self._tick_results: list[PredictiveTickResult] = []
        self._callbacks: list[Callable[[PredictiveTickResult], None]] = []

        self._running = False
        self._thread: threading.Thread | None = None

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def start(self, tick_ms: float = 1000.0) -> None:
        if self._running:
            return
        self._running = True

        def _loop() -> None:
            while self._running:
                tick_start = time.monotonic()
                self._do_tick()
                elapsed_ms = (time.monotonic() - tick_start) * 1000
                sleep_s = max(0, (tick_ms - elapsed_ms) / 1000)
                time.sleep(sleep_s)

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
            self._thread = None

    def tick(self) -> PredictiveTickResult:
        """Synchronous single tick."""
        return self._do_tick()

    # ── Internal ────────────────────────────────────────────────────────

    def _do_tick(self) -> PredictiveTickResult:
        self._tick_count += 1
        tick_start = time.monotonic()
        actions_taken: list[str] = []
        pre_heal_triggered = False
        pre_heal_reason = ""
        model_built = False
        panic = False

        try:
            # 1. Collect snapshot
            snap = self.ctrl.get_snapshot()
            current_score = snap.stability_score

            # 2. Build self-model (reconstructs causal graph)
            self.self_model.build_model(snap)
            model_built = True

            # 3. Record score in trend for time-series
            self.self_model._state.record_score(current_score)

            # 4. Forecast stability N seconds ahead
            predicted_score = self.self_model.forecast_stability(
                snap, horizon_s=self.forecast_horizon_s
            )
            predicted_change = predicted_score - current_score

            # 5. Check degradation threshold — if falling fast, pre-heal
            if (
                current_score > 0.30  # not already critical
                and predicted_change < -self.degradation_threshold
                and time.monotonic() > self._pre_heal_cooldown_until
            ):
                pre_heal_triggered = True
                pre_heal_reason = (
                    f"Forecast: {current_score:.3f}→{predicted_score:.3f} "
                    f"(delta={predicted_change:.3f}) in {self.forecast_horizon_s}s. "
                    "Pre-emptive heal triggered."
                )
                actions_taken.append("pre_heal:RECONFIGURE_QUORUM")
                self.ctrl.healer.heal(HealingAction.RECONFIGURE_QUORUM)
                self._pre_heal_cooldown_until = (
                    time.monotonic() + self.DEFAULT_PRE_HEAL_COOLDOWN_S
                )

            # 6. If critical → standard reactive path
            if current_score < 0.30:
                self.ctrl.healer.heal(HealingAction.RECONFIGURE_QUORUM)
                actions_taken.append("critical:RECONFIGURE_QUORUM")

            # 7. Update DRL router metrics
            router_state = self.ctrl.get_all_routes()
            for peer, state in router_state.items():
                if isinstance(state, dict):
                    lat = state.get("latency_ema", 0.0)
                    ok = not state.get("violating_slo", False)
                    self.ctrl.on_drl_latency(peer, lat, 100.0, ok)

            self._last_score = current_score

        except Exception as exc:
            actions_taken.append(f"ERROR:{exc}")
            panic = True

        duration_ms = (time.monotonic() - tick_start) * 1000
        result = PredictiveTickResult(
            tick_num=self._tick_count,
            ts=time.monotonic(),
            duration_ms=duration_ms,
            current_score=self._last_score,
            predicted_score=predicted_score if model_built else self._last_score,
            predicted_change=predicted_change if model_built else 0.0,
            pre_heal_triggered=pre_heal_triggered,
            pre_heal_reason=pre_heal_reason,
            forecast_horizon_s=self.forecast_horizon_s,
            actions_taken=actions_taken,
            model_built=model_built,
            panic=panic,
        )

        self._tick_results.append(result)
        if len(self._tick_results) > 300:
            self._tick_results = self._tick_results[-300:]

        for cb in self._callbacks:
            try:
                cb(result)
            except Exception:
                pass

        return result

    # ── Callbacks ────────────────────────────────────────────────────────

    def on_tick(self, cb: Callable[[PredictiveTickResult], None]) -> None:
        self._callbacks.append(cb)

    # ── Introspection ───────────────────────────────────────────────────

    def get_recent_ticks(self, last_n: int = 10) -> list[PredictiveTickResult]:
        return self._tick_results[-last_n:]

    def get_pre_heal_count(self) -> int:
        return sum(1 for t in self._tick_results if t.pre_heal_triggered)

    def dump(self) -> dict:
        recent = self.get_recent_ticks(5)
        return {
            "tick_count": self._tick_count,
            "is_running": self._running,
            "forecast_horizon_s": self.forecast_horizon_s,
            "degradation_threshold": self.degradation_threshold,
            "pre_heal_count": self.get_pre_heal_count(),
            "last_score": round(self._last_score, 4),
            "recent_ticks": [t.to_dict() for t in recent],
            "self_model": self.self_model.dump(),
        }
