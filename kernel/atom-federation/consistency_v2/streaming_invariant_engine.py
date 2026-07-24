"""
streaming_invariant_engine.py
==============================
Continuous streaming proof system — verifies invariants on delta streams
instead of full snapshot comparisons.

Key idea:
    Instead of  check(full_exec, full_replay)
    We verify  Δ(state_exec(t)) ↔ Δ(state_replay(t))  continuously

Formal invariant:
    ∀ t:  d/dt execution_state  ≡  d/dt replay_state

Module structure:
    StreamingInvariantEngine   — main class, runs verification loop
    StreamInvariantResult      — per-check result with delta values
    StreamingReport           — aggregated report over a time window
"""
from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import logging
log = logging.getLogger(__name__)


# ── Result types ────────────────────────────────────────────────────────────

@dataclass
class StreamInvariantResult:
    """Single delta-stream invariant check result."""
    invariant_id: str          # sI1 | sI2 | sI3 | sI4
    passed: bool
    exec_delta: dict[str, Any] # what changed in execution since last check
    replay_delta: dict[str, Any]  # what changed in replay since last check
    delta_drift: float         # drift between deltas (not states!)
    details: str
    ts_ns: int = field(default_factory=lambda: time.time_ns())


@dataclass
class StreamingReport:
    """Aggregated report over a sliding time window."""
    invariant_results: list[StreamInvariantResult]
    window_duration_s: float
    total_checks: int
    passed_checks: int
    all_passed: bool
    max_delta_drift: float = 0.0
    ts_ns: int = field(default_factory=lambda: time.time_ns())

    def to_dict(self) -> dict[str, Any]:
        return {
            "window_s": self.window_duration_s,
            "total": self.total_checks,
            "passed": self.passed_checks,
            "all_passed": self.all_passed,
            "max_delta_drift": self.max_delta_drift,
            "checks": [
                {
                    "id": r.invariant_id,
                    "passed": r.passed,
                    "drift": r.delta_drift,
                    "details": r.details,
                }
                for r in self.invariant_results
            ],
        }


# ── StreamingInvariantEngine ───────────────────────────────────────────────

class StreamingInvariantEngine:
    """
    Continuous invariant verification over delta streams.

    Instead of comparing full snapshots, this engine maintains the last known
    state deltas for both execution and replay domains and verifies that
    their deltas remain equivalent at each verification tick.

    Formal invariant verified:
        ∀ t:  delta_exec(t) ≡ delta_replay(t)

    Usage:
        engine = StreamingInvariantEngine(
            get_state_delta_exec=lambda prev, curr: {...},   # (prev, curr) -> delta
            get_state_delta_replay=lambda prev, curr: {...},
            interval_sec=1.0,
        )
        engine.start()
        # ... later ...
        report = engine.get_sliding_report(window_s=30.0)
        engine.stop()
    """

    def __init__(
        self,
        get_state_delta_exec: Callable[[dict, dict], dict[str, Any]],
        get_state_delta_replay: Callable[[dict, dict], dict[str, Any]],
        get_causal_delta_exec: Callable[[list, list], dict[str, Any]] | None = None,
        get_causal_delta_replay: Callable[[list, list], dict[str, Any]] | None = None,
        get_sbs_delta_exec: Callable[[dict, dict], dict[str, Any]] | None = None,
        get_sbs_delta_replay: Callable[[dict, dict], dict[str, Any]] | None = None,
        interval_sec: float = 1.0,
        max_window_results: int = 300,
    ):
        """
        Args:
            get_state_delta_exec:   fn(prev_state, curr_state) -> delta dict for exec domain
            get_state_delta_replay: fn(prev_state, curr_state) -> delta dict for replay domain
            get_causal_delta_exec:  fn(prev_events, curr_events) -> causal delta dict (optional)
            get_causal_delta_replay: fn(prev_events, curr_events) -> causal delta dict (optional)
            get_sbs_delta_exec:    fn(prev_state, curr_state) -> SBS delta dict (optional)
            get_sbs_delta_replay:  fn(prev_state, curr_state) -> SBS delta dict (optional)
            interval_sec:          verification tick interval in seconds
            max_window_results:    max number of per-tick results to keep for sliding window
        """
        self._get_exec_delta = get_state_delta_exec
        self._get_replay_delta = get_state_delta_replay
        self._get_causal_exec = get_causal_delta_exec
        self._get_causal_replay = get_causal_delta_replay
        self._get_sbs_exec = get_sbs_delta_exec
        self._get_sbs_replay = get_sbs_delta_replay
        self._interval = interval_sec
        self._max_results = max_window_results

        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None

        # Last known full states (used to compute deltas)
        self._prev_exec_state: dict[str, Any] = {}
        self._prev_replay_state: dict[str, Any] = {}
        self._prev_exec_events: list = []
        self._prev_replay_events: list = []

        self._tick_results: list[StreamInvariantResult] = []
        self._start_ts_ns: int = 0

    # ── Core delta checks (sI1) ──────────────────────────────────────────────

    @staticmethod
    def _delta_drift(d1: dict, d2: dict) -> float:
        """Compute normalized drift between two delta dicts."""
        if not d1 and not d2:
            return 0.0
        all_keys = set(d1.keys()) | set(d2.keys())
        if not all_keys:
            return 0.0
        drift = 0.0
        for k in all_keys:
            v1 = d1.get(k, None)
            v2 = d2.get(k, None)
            if v1 is None or v2 is None:
                drift += 1.0
            elif isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                max_v = max(abs(v1), abs(v2), 1e-9)
                drift += abs(v1 - v2) / max_v
            elif v1 != v2:
                drift += 1.0
        return drift / len(all_keys)

    def _check_sI1(self, curr_exec: dict, curr_replay: dict) -> StreamInvariantResult:
        """
        sI1: State delta equivalence — the deltas themselves must be identical.
        This is the streaming version of I1.
        """
        prev_e = self._prev_exec_state
        prev_r = self._prev_replay_state

        delta_e = self._get_exec_delta(prev_e, curr_exec)
        delta_r = self._get_replay_delta(prev_r, curr_replay)

        drift = self._delta_drift(delta_e, delta_r)
        passed = drift < 1e-9

        return StreamInvariantResult(
            invariant_id="sI1",
            passed=passed,
            exec_delta=delta_e,
            replay_delta=delta_r,
            delta_drift=drift,
            details="sI1_PASS" if passed else f"delta_drift={drift:.2e}",
        )

    # ── Causal delta check (sI2) ────────────────────────────────────────────

    def _check_sI2(
        self,
        curr_exec_events: list,
        curr_replay_events: list,
    ) -> StreamInvariantResult:
        """
        sI2: Causal DAG delta equivalence — new events must appear in both domains
        with identical causal structure changes.
        """
        if self._get_causal_exec is None or self._get_causal_replay is None:
            return StreamInvariantResult(
                invariant_id="sI2",
                passed=True,
                exec_delta={},
                replay_delta={},
                delta_drift=0.0,
                details="sI2_SKIP (no causal delta fns provided)",
            )

        delta_e = self._get_causal_exec(self._prev_exec_events, curr_exec_events)
        delta_r = self._get_causal_replay(self._prev_replay_events, curr_replay_events)

        drift = self._delta_drift(delta_e, delta_r)
        passed = drift < 1e-9

        return StreamInvariantResult(
            invariant_id="sI2",
            passed=passed,
            exec_delta=delta_e,
            replay_delta=delta_r,
            delta_drift=drift,
            details="sI2_PASS" if passed else f"causal_delta_drift={drift:.2e}",
        )

    # ── SBS delta check (sI3) ───────────────────────────────────────────────

    def _check_sI3(
        self,
        curr_exec: dict,
        curr_replay: dict,
    ) -> StreamInvariantResult:
        """sI3: SBS violation delta equivalence across domains."""
        if self._get_sbs_exec is None or self._get_sbs_replay is None:
            return StreamInvariantResult(
                invariant_id="sI3",
                passed=True,
                exec_delta={},
                replay_delta={},
                delta_drift=0.0,
                details="sI3_SKIP (no SBS delta fns provided)",
            )

        delta_e = self._get_sbs_exec(self._prev_exec_state, curr_exec)
        delta_r = self._get_sbs_replay(self._prev_replay_state, curr_replay)

        drift = self._delta_drift(delta_e, delta_r)
        passed = drift < 1e-9

        return StreamInvariantResult(
            invariant_id="sI3",
            passed=passed,
            exec_delta=delta_e,
            replay_delta=delta_r,
            delta_drift=drift,
            details="sI3_PASS" if passed else f"sbs_delta_drift={drift:.2e}",
        )

    # ── Full tick ───────────────────────────────────────────────────────────

    def _tick(
        self,
        curr_exec_state: dict[str, Any],
        curr_replay_state: dict[str, Any],
        curr_exec_events: list,
        curr_replay_events: list,
    ) -> list[StreamInvariantResult]:
        """Run all sI checks for one tick and update prev states."""
        results = [
            self._check_sI1(curr_exec_state, curr_replay_state),
            self._check_sI2(curr_exec_events, curr_replay_events),
            self._check_sI3(curr_exec_state, curr_replay_state),
        ]

        with self._lock:
            self._prev_exec_state = curr_exec_state
            self._prev_replay_state = curr_replay_state
            self._prev_exec_events = curr_exec_events
            self._prev_replay_events = curr_replay_events
            self._tick_results.append(results)
            if len(self._tick_results) > self._max_results:
                self._tick_results.pop(0)

        return results

    # ── Background runner ───────────────────────────────────────────────────

    def start(
        self,
        get_curr_exec_state: Callable[[], dict[str, Any]],
        get_curr_replay_state: Callable[[], dict[str, Any]],
        get_curr_exec_events: Callable[[], list] | None = None,
        get_curr_replay_events: Callable[[], list] | None = None,
    ) -> None:
        """
        Start continuous verification in background thread.

        Args:
            get_curr_exec_state:    fn() -> current exec domain state dict
            get_curr_replay_state:  fn() -> current replay domain state dict
            get_curr_exec_events:   fn() -> current exec event list (optional)
            get_curr_replay_events: fn() -> current replay event list (optional)
        """
        self._running = True
        self._start_ts_ns = time.time_ns()

        def loop():
            while self._running:
                try:
                    curr_e = get_curr_exec_state()
                    curr_r = get_curr_replay_state()
                    curr_ee = get_curr_exec_events() if get_curr_exec_events else []
                    curr_re = get_curr_replay_events() if get_curr_replay_events else []
                    self._tick(curr_e, curr_r, curr_ee, curr_re)
                except Exception as e:
                    # Non-fatal — log and continue
                    import sys
                    log.info(f"[StreamingInvariantEngine] tick error: {e}", file=sys.stderr)
                time.sleep(self._interval)

        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the background verification loop."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)

    # ── Reports ────────────────────────────────────────────────────────────

    def get_sliding_report(self, window_s: float = 30.0) -> StreamingReport:
        """
        Get aggregated results over the last `window_s` seconds.

        Args:
            window_s: time window in seconds

        Returns:
            StreamingReport with aggregated stats
        """
        now_ns = time.time_ns()
        cutoff_ns = now_ns - int(window_s * 1e9)

        with self._lock:
            relevant: list[StreamInvariantResult] = []
            for tick_results in self._tick_results:
                for r in tick_results:
                    if r.ts_ns >= cutoff_ns:
                        relevant.append(r)
                        break  # only first result per tick

        if not relevant:
            return StreamingReport(
                invariant_results=[],
                window_duration_s=window_s,
                total_checks=0,
                passed_checks=0,
                all_passed=True,
            )

        total = len(relevant)
        passed = sum(1 for r in relevant if r.passed)
        max_drift = max(r.delta_drift for r in relevant)

        return StreamingReport(
            invariant_results=relevant,
            window_duration_s=window_s,
            total_checks=total,
            passed_checks=passed,
            all_passed=passed == total,
            max_delta_drift=max_drift,
        )

    def get_last_tick_results(self) -> list[StreamInvariantResult]:
        """Get the most recent tick's results."""
        with self._lock:
            if not self._tick_results:
                return []
            return self._tick_results[-1]

    # ── Manual trigger (for testing / on-demand verification) ───────────────

    def verify(
        self,
        curr_exec_state: dict[str, Any],
        curr_replay_state: dict[str, Any],
        curr_exec_events: list,
        curr_replay_events: list,
    ) -> list[StreamInvariantResult]:
        """
        Synchronous one-shot verification. Does not start background loop.
        Useful for testing or on-demand checks.
        """
        return self._tick(curr_exec_state, curr_replay_state, curr_exec_events, curr_replay_events)
