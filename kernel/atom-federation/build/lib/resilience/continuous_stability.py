"""
ContinuousStabilityEngine v6.5 — Proactive 1Hz stability tick loop.

Problem:
  v6.4's StabilityMetricsEngine is event-triggered (passive).
  The cluster needs continuous proactive measurement.

Solution:
  ContinuousStabilityEngine runs at 1Hz (TICK_MS=1000):
    tick → measure → score → arbitrate → act → log → repeat

Key difference:
  v6.4: event → react → heal           (reactive, waits for events)
  v6.5: tick(1Hz) → measure → act      (proactive, never waits)

Usage:
    engine = ContinuousStabilityEngine(ctrl=closed_loop_ctrl)
    engine.start()

    # or synchronous:
    engine.tick()  # single shot
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

__all__ = ["ContinuousStabilityEngine", "TickResult"]


# ── Tick result ────────────────────────────────────────────────────────────────

@dataclass
class TickResult:
    tick_num: int
    ts: float
    duration_ms: float
    stability_score: float
    is_healthy: bool
    is_critical: bool
    actions_taken: list[str]
    slo_violations: list[str]
    convergence_detected: bool
    panic: bool = False

    def to_dict(self) -> dict:
        return {
            "tick_num": self.tick_num,
            "ts": round(self.ts, 4),
            "duration_ms": round(self.duration_ms, 4),
            "stability_score": round(self.stability_score, 4),
            "is_healthy": self.is_healthy,
            "is_critical": self.is_critical,
            "actions_taken": self.actions_taken,
            "slo_violations": self.slo_violations,
            "convergence_detected": self.convergence_detected,
            "panic": self.panic,
        }


# ── SLO definitions ────────────────────────────────────────────────────────────

SLO_LATENCY_MS = 100.0
SLO_LOSS_RATE = 0.05
SLO_STABILITY_MIN = 0.70
SLO_VIOLATIONS_PER_MIN = 10


# ── ContinuousStabilityEngine ─────────────────────────────────────────────────

class ContinuousStabilityEngine:
    """
    Runs stability evaluation every TICK_MS milliseconds.

    This is the "heartbeat" of the closed-loop system in v6.5+.
    It ensures the system never waits for an event — it continuously
    measures, decides, and acts.

    The tick loop:
      1. Snapshot all subsystem states (metrics, router, healer)
      2. Check SLO violations
      3. If SLO violated → inject into ClosedLoopResilienceController
      4. If convergence detected → signal partition healed
      5. If stability degraded 2 ticks in a row → trigger self-heal
      6. Log tick result
    """

    TICK_MS: float = 1000.0  # 1 second cadence

    def __init__(
        self,
        ctrl,  # ClosedLoopResilienceController
        tick_ms: float = 1000.0,
    ):
        self.ctrl = ctrl
        self.TICK_MS = tick_ms
        self._running = False
        self._thread: threading.Thread | None = None
        self._tick_count = 0
        self._last_score: float = 1.0
        self._consecutive_degraded_ticks = 0
        self._last_violation_count = 0
        self._tick_results: list[TickResult] = []
        self._on_tick_callbacks: list[Callable[[TickResult], None]] = []
        self._panic_state = False

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._tick_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
            self._thread = None

    def is_running(self) -> bool:
        return self._running

    # ── Single tick (sync — for testing and single-shot use) ───────────────

    def tick(self) -> TickResult:
        """
        Execute one stability tick synchronously.
        Returns TickResult for the tick.
        """
        return self._do_tick()

    # ── Internal ──────────────────────────────────────────────────────────

    def _tick_loop(self) -> None:
        while self._running:
            tick_start = time.monotonic()
            self._do_tick()
            elapsed_ms = (time.monotonic() - tick_start) * 1000
            sleep_s = max(0, (self.TICK_MS - elapsed_ms) / 1000)
            time.sleep(sleep_s)

    def _do_tick(self) -> TickResult:
        self._tick_count += 1
        tick_start = time.monotonic()
        actions_taken: list[str] = []
        slo_violations: list[str] = []
        panic = False

        try:
            # 1. Collect all subsystem states
            snapshot = self.ctrl.get_snapshot()
            router_state = self.ctrl.get_all_routes()
            heal_state = self.ctrl.healer.state() if hasattr(self.ctrl.healer, "state") else {}
            score = snapshot.stability_score

            # 2. SLO checks
            slo_violations = self._check_slos(snapshot, router_state)
            if slo_violations:
                for violation in slo_violations:
                    self.ctrl.on_sbs_violation([violation], violation_type="WARNING")
                    actions_taken.append(f"slo_violation:{violation}")

            # 3. Convergence detection: if score improved significantly → partition healed
            convergence_detected = (
                score > self._last_score + 0.1
                and self._last_violation_count > 0
                and snapshot.violation_count_60s < self._last_violation_count
            )
            if convergence_detected:
                healed = self.ctrl.get_healthy_peers()
                if healed:
                    self.ctrl.on_partition_healed(list(set(healed + self.ctrl.peers)))
                    actions_taken.append("partition_healed")

            # 4. Stability degradation detection: 2 ticks in a row → self-heal
            if score < SLO_STABILITY_MIN:
                self._consecutive_degraded_ticks += 1
                if self._consecutive_degraded_ticks >= 2:
                    if hasattr(self.ctrl, "reactor") and hasattr(self.ctrl.reactor, "on_action"):
                        actions_taken.append("degraded_2_ticks_self_heal_triggered")
            else:
                self._consecutive_degraded_ticks = 0

            # 5. If critical → trigger alert
            if score < 0.30 and not self._panic_state:
                self.ctrl.on_sbs_violation(
                    [{"type": "CRITICAL", "node": self.ctrl.node_id}],
                    violation_type="CRITICAL",
                )
                actions_taken.append("critical_score_alert")
                self._panic_state = True

            # 6. If recovered → clear panic
            if score > 0.60 and self._panic_state:
                self._panic_state = False

            # 7. Feed DRL metrics from router state
            for peer, state in router_state.items():
                if isinstance(state, dict):
                    lat = state.get("latency_ema", 0.0)
                    loss = state.get("loss_rate_ema", 0.0)
                    ok = not state.get("violating_slo", False)
                    self.ctrl.on_drl_latency(peer, lat, SLO_LATENCY_MS, ok)
                    if loss > 0:
                        self.ctrl.on_drl_loss(peer, loss, SLO_LOSS_RATE)

            # 8. Log to history
            self._last_score = score
            self._last_violation_count = snapshot.violation_count_60s

        except Exception as exc:
            actions_taken.append(f"ERROR:{exc}")
            panic = True

        duration_ms = (time.monotonic() - tick_start) * 1000
        result = TickResult(
            tick_num=self._tick_count,
            ts=time.monotonic(),
            duration_ms=duration_ms,
            stability_score=self._last_score,
            is_healthy=self._last_score >= SLO_STABILITY_MIN,
            is_critical=self._last_score < 0.30,
            actions_taken=actions_taken,
            slo_violations=slo_violations,
            convergence_detected=convergence_detected,
            panic=panic,
        )
        self._tick_results.append(result)
        if len(self._tick_results) > 300:
            self._tick_results = self._tick_results[-300:]

        for cb in self._on_tick_callbacks:
            try:
                cb(result)
            except Exception:
                pass

        return result

    def _check_slos(
        self,
        snapshot,
        router_state: dict,
    ) -> list[str]:
        violations = []
        if snapshot.stability_score < SLO_STABILITY_MIN:
            violations.append(f"stability:{snapshot.stability_score:.3f}<{SLO_STABILITY_MIN}")
        if snapshot.violation_count_60s > SLO_VIOLATIONS_PER_MIN:
            violations.append(f"violations:{snapshot.violation_count_60s}>{SLO_VIOLATIONS_PER_MIN}")
        if snapshot.recovery_rate < 0.50:
            violations.append(f"recovery_rate:{snapshot.recovery_rate:.3f}<0.50")
        for peer, state in router_state.items():
            if isinstance(state, dict) and state.get("violating_slo"):
                violations.append(f"peer:{peer}:slo_violated")
        return violations

    # ── Callbacks ─────────────────────────────────────────────────────────

    def on_tick(self, cb: Callable[[TickResult], None]) -> None:
        self._on_tick_callbacks.append(cb)

    # ── Introspection ───────────────────────────────────────────────────

    def get_recent_ticks(self, last_n: int = 10) -> list[TickResult]:
        return self._tick_results[-last_n:]

    def get_avg_tick_duration_ms(self) -> float:
        if not self._tick_results:
            return 0.0
        return sum(t.duration_ms for t in self._tick_results) / len(self._tick_results)

    def dump(self) -> dict:
        return {
            "tick_count": self._tick_count,
            "is_running": self._running,
            "tick_ms": self.TICK_MS,
            "last_score": round(self._last_score, 4),
            "consecutive_degraded_ticks": self._consecutive_degraded_ticks,
            "panic_state": self._panic_state,
            "avg_tick_duration_ms": round(self.get_avg_tick_duration_ms(), 2),
            "recent_ticks": [t.to_dict() for t in self.get_recent_ticks(5)],
        }
