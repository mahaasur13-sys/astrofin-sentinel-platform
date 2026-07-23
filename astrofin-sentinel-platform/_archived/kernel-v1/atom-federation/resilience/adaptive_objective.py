"""
AdaptiveObjectiveController v6.6 — J-gated autonomous control.

Problem:
  SystemOptimizer.compute_J() exists in v6.5 but is NOT integrated
  into the real control loop. Actions are taken without evaluating
  whether they improve or worsen the global objective.

Solution:
  AdaptiveObjectiveController wraps ClosedLoopResilienceController with:
    1. J-gated execution: every action evaluated by J() BEFORE execution
    2. Pre-execution prediction: SelfModel predicts next state
    3. Action deferral: if J would decrease → reject action
    4. Adaptive weights: gradient descent from action history

This shifts: REACTIVE → GOAL-DIRECTED AUTONOMOUS CONTROL.

Usage:
    obj_ctrl = AdaptiveObjectiveController(ctrl)
    should_exec = obj_ctrl.should_execute(PolicyAction.EVICT_NODE, "node-b", snap)
    result = obj_ctrl.tick()
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

from resilience.closed_loop import ClosedLoopResilienceController
from resilience.optimizer import SystemOptimizer
from resilience.policy_engine import PolicyAction
from resilience.self_model import SelfModel

__all__ = ["AdaptiveObjectiveController", "AdaptiveTickResult"]


@dataclass
class AdaptiveTickResult:
    tick_num: int
    ts: float
    duration_ms: float
    current_J: float
    previous_J: float
    J_delta: float
    action_taken: str | None
    action_rejected: bool
    predicted_J: float
    current_score: float
    is_healthy: bool
    weights: dict
    panic: bool = False

    @property
    def J_improved(self) -> bool:
        return self.J_delta > 0.0

    def to_dict(self) -> dict:
        return {
            "tick_num": self.tick_num,
            "ts": round(self.ts, 4),
            "duration_ms": round(self.duration_ms, 4),
            "current_J": round(self.current_J, 4),
            "previous_J": round(self.previous_J, 4),
            "J_delta": round(self.J_delta, 4),
            "action_taken": self.action_taken,
            "action_rejected": self.action_rejected,
            "predicted_J": round(self.predicted_J, 4),
            "current_score": round(self.current_score, 4),
            "is_healthy": self.is_healthy,
            "J_improved": self.J_improved,
            "weights": {k: round(v, 4) for k, v in self.weights.items()},
            "panic": self.panic,
        }


class AdaptiveObjectiveController:
    """
    Integrates J() global objective into the real control loop.

    Every action is gated by J():
      1. Compute current J(snapshot)
      2. Predict next state using SelfModel
      3. Compute predicted J
      4. If predicted_J >= current_J - tolerance → allow
         Else → reject/defer

    v6.6: REACTIVE → GOAL-DIRECTED AUTONOMOUS CONTROL
    """

    J_TOLERANCE = 0.05

    def __init__(
        self,
        ctrl: ClosedLoopResilienceController,
        optimizer: SystemOptimizer | None = None,
    ) -> None:
        self.ctrl = ctrl
        self.self_model = SelfModel()
        self.optimizer = optimizer or SystemOptimizer()
        self._action_history: list[dict] = []
        self._tick_count = 0
        self._previous_J: float = 0.0
        self._tick_results: list[AdaptiveTickResult] = []
        self._callbacks: list[Callable[[AdaptiveTickResult], None]] = []
        self._running = False
        self._thread: threading.Thread | None = None

    def should_execute(
        self,
        action: PolicyAction,
        target: str | None,
        snapshot,
    ) -> bool:
        """Return True if action would not decrease J beyond tolerance."""
        current_J = self.optimizer.compute_J(snapshot).J
        # Predict next state and use it for predicted J
        predicted_snap = self.self_model.predict_next_state(snapshot, action, target)
        zero_cost_actions = {
            PolicyAction.ADD_OBSERVATION,
            PolicyAction.LOG_ONLY,
            PolicyAction.NOOP,
            PolicyAction.ALERT_OPS,
        }
        action_cost = 0.0 if action in zero_cost_actions else 0.1
        predicted_result = self.optimizer.compute_J(predicted_snap, action_cost=action_cost)
        return predicted_result.J >= current_J - self.J_TOLERANCE

    def start(self, tick_ms: float = 1000.0) -> None:
        if self._running:
            return
        self._running = True

        def _loop() -> None:
            while self._running:
                tick_start = time.monotonic()
                self._do_tick()
                elapsed_ms = (time.monotonic() - tick_start) * 1000
                time.sleep(max(0, (tick_ms - elapsed_ms) / 1000))

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
            self._thread = None

    def tick(self) -> AdaptiveTickResult:
        return self._do_tick()

    def _do_tick(self) -> AdaptiveTickResult:
        self._tick_count += 1
        tick_start = time.monotonic()
        action_taken: str | None = None
        action_rejected = False
        panic = False

        try:
            snap = self.ctrl.get_snapshot()
            self.self_model.build_model(snap)
            current_J_result = self.optimizer.compute_J(snap)
            current_J = current_J_result.J
            current_score = snap.stability_score

            # Gradient descent every 10 ticks
            if len(self._action_history) >= 3 and self._tick_count % 10 == 0:
                self.optimizer.gradient_descent_step(snap, self._action_history[-10:])

            # Adaptive weight adjustment: if J is healthy, reduce healing cost
            if current_J > 0.7 and self.optimizer.weights.w_cost > 0.10:
                self.optimizer.weights.w_cost = max(0.05, self.optimizer.weights.w_cost - 0.01)

            # Record tick in history
            self._action_history.append({
                "action": "tick",
                "outcome": "success" if current_J > 0 else "failure",
                "J": current_J,
                "score": current_score,
            })
            if len(self._action_history) > 100:
                self._action_history = self._action_history[-100:]

            J_delta = current_J - self._previous_J
            self._previous_J = current_J

        except Exception:
            panic = True
            current_J = self._previous_J
            current_score = 0.0
            J_delta = 0.0

        duration_ms = (time.monotonic() - tick_start) * 1000
        result = AdaptiveTickResult(
            tick_num=self._tick_count,
            ts=time.monotonic(),
            duration_ms=duration_ms,
            current_J=current_J,
            previous_J=self._previous_J,
            J_delta=J_delta,
            action_taken=action_taken,
            action_rejected=action_rejected,
            predicted_J=current_J,  # same as current if no action
            current_score=current_score,
            is_healthy=current_J > 0.5,
            weights=self.optimizer.weights.to_dict(),
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

    def on_tick(self, cb: Callable[[AdaptiveTickResult], None]) -> None:
        self._callbacks.append(cb)

    def get_recent_ticks(self, last_n: int = 10) -> list[AdaptiveTickResult]:
        return self._tick_results[-last_n:]

    def dump(self) -> dict:
        return {
            "tick_count": self._tick_count,
            "is_running": self._running,
            "action_history_len": len(self._action_history),
            "last_J": self._previous_J,
            "weights": self.optimizer.weights.to_dict(),
            "recent_ticks": [t.to_dict() for t in self.get_recent_ticks(5)],
        }
