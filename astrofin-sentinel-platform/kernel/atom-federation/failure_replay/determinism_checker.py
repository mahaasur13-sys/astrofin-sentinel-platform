"""
Determinism Checker v7.0 — Validates distributed OS determinism guarantees.

Provides:
  - Commutativity checks (are event pairs order-independent?)
  - Idempotency checks (does replaying events twice produce same state?)
  - Convergence verification (do two runs with same events converge to same state?)
  - Latency injection (test behavior under realistic network delays)
  - Divergence detection (detect when replay diverges from baseline)

This is the core tool for validating ATOMFederationOS correctness:
  "Two identical event sequences → identical node states"
"""

from __future__ import annotations

import random
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from observability.core.event_schema import Event


@dataclass
class DeterminismResult:
    """Result of a determinism check."""
    passed: bool
    check_type: str          # commutativity | idempotency | convergence
    event_pairs_checked: int
    divergent_pairs: int = 0
    details: list[str] = field(default_factory=list)
    duration_ns: int = 0
    ts: float = field(default_factory=time.time)


@dataclass
class DivergenceEvent:
    """A detected divergence during replay."""
    ts: int
    event_id: str
    event_type: str
    expected_state: dict
    actual_state: dict
    divergence_magnitude: float


class DeterminismChecker:
    """
    Verifies that the distributed OS obeys deterministic replay rules.

    Usage:
        checker = DeterminismChecker(state_equality_fn=my_node_eq)
        result = checker.check_commutativity(events)
        result = checker.check_idempotency(events)
        result = checker.check_convergence(baseline_events, test_events)

    The state_equality_fn must be provided by the caller because
    node state structure is application-specific.
    """

    def __init__(
        self,
        state_equality_fn: Callable[[dict, dict], bool] | None = None,
        divergence_threshold: float = 1e-9,
    ):
        """
        Args:
            state_equality_fn: fn(state_a, state_b) -> bool.
                               If None, uses deep equality.
            divergence_threshold: float comparison epsilon for state fields.
        """
        self._eq_fn = state_equality_fn or (lambda a, b: a == b)
        self._threshold = divergence_threshold
        self._lock = threading.Lock()
        self._divergences: list[DivergenceEvent] = []

    def check_commutativity(
        self,
        events: list[Event],
        state_transition_fn: Callable[[dict, Event], dict],
        initial_state: dict,
    ) -> DeterminismResult:
        """
        Check if event pairs commute: apply (A then B) vs (B then A).

        For a distributed OS to be deterministic, most events must commute.
        Non-commuting pairs identify critical ordering requirements.
        """
        start_ns = time.time_ns()
        checked = 0
        divergent = 0
        details = []

        # Sample pairs (n^2 check is expensive, sample first)
        sample_size = min(len(events), 500)
        sampled = random.sample(events, sample_size) if len(events) > sample_size else events

        for i, ev_a in enumerate(sampled):
            for ev_b in sampled[i + 1:]:
                # Apply A then B
                state_ab = state_transition_fn(initial_state, ev_a)
                state_ab = state_transition_fn(state_ab, ev_b)

                # Apply B then A
                state_ba = state_transition_fn(initial_state, ev_b)
                state_ba = state_transition_fn(state_ba, ev_a)

                checked += 1

                if not self._states_equal(state_ab, state_ba):
                    divergent += 1
                    details.append(
                        f"NON-COMMUTING: {ev_a.event_type} + {ev_b.event_type} "
                        f"(ids: {ev_a.event_id[:8]}, {ev_b.event_id[:8]})"
                    )

        duration_ns = time.time_ns() - start_ns
        passed = divergent == 0

        return DeterminismResult(
            passed=passed,
            check_type="commutativity",
            event_pairs_checked=checked,
            divergent_pairs=divergent,
            details=details[:50],  # cap details
            duration_ns=duration_ns,
        )

    def check_idempotency(
        self,
        events: list[Event],
        state_transition_fn: Callable[[dict, Event], dict],
        initial_state: dict,
    ) -> DeterminismResult:
        """
        Check if applying the same event sequence twice produces same state.
        Idempotency = applying events once OR twice should yield same result.
        """
        start_ns = time.time_ns()

        # Apply once
        state_once = initial_state
        for ev in events:
            state_once = state_transition_fn(state_once, ev)

        # Apply twice (duplicate events)
        state_twice = initial_state
        for ev in events:
            state_twice = state_transition_fn(state_twice, ev)
        for ev in events:
            state_twice = state_transition_fn(state_twice, ev)

        checked = len(events)
        divergent = 0
        details = []

        if not self._states_equal(state_once, state_twice):
            divergent = checked
            details.append("Idempotency violation: double-apply produced different state")

        duration_ns = time.time_ns() - start_ns

        return DeterminismResult(
            passed=divergent == 0,
            check_type="idempotency",
            event_pairs_checked=checked,
            divergent_pairs=divergent,
            details=details,
            duration_ns=duration_ns,
        )

    def check_convergence(
        self,
        baseline_events: list[Event],
        test_events: list[Event],
        state_transition_fn: Callable[[dict, Event], dict],
        initial_state: dict,
        max_drift_events: int = 100,
    ) -> DeterminismResult:
        """
        Check if two runs with same events converge to same final state.
        This is the core determinism property for replay.
        """
        start_ns = time.time_ns()

        # Run baseline
        state_baseline = initial_state
        for ev in baseline_events:
            state_baseline = state_transition_fn(state_baseline, ev)

        # Run test
        state_test = initial_state
        for ev in test_events:
            state_test = state_transition_fn(state_test, ev)

        checked = len(baseline_events)
        divergent = 0
        details = []

        if not self._states_equal(state_baseline, state_test):
            divergent = 1
            details.append(
                f"Convergence failure: baseline vs test states differ "
                f"(baseline_events={checked}, test_events={len(test_events)})"
            )

        duration_ns = time.time_ns() - start_ns

        return DeterminismResult(
            passed=divergent == 0,
            check_type="convergence",
            event_pairs_checked=checked,
            divergent_pairs=divergent,
            details=details,
            duration_ns=duration_ns,
        )

    def check_latency_injection(
        self,
        events: list[Event],
        state_transition_fn: Callable[[dict, Event], dict],
        initial_state: dict,
        latency_profile: Callable[[str], float],
    ) -> DeterminismResult:
        """
        Check if events remain correct under simulated network latency.
        Latency injection should NOT change correctness, only timing.
        """
        start_ns = time.time_ns()

        # Run with zero latency
        state_zero = initial_state
        for ev in events:
            state_zero = state_transition_fn(state_zero, ev)

        # Run with injected latency
        state_latency = initial_state
        for ev in events:
            latency = latency_profile(ev.event_type)
            if latency > 0:
                time.sleep(latency)
            state_latency = state_transition_fn(state_latency, ev)

        checked = len(events)
        divergent = 0
        details = []

        if not self._states_equal(state_zero, state_latency):
            divergent = checked
            details.append("Latency injection caused state divergence")

        duration_ns = time.time_ns() - start_ns

        return DeterminismResult(
            passed=divergent == 0,
            check_type="latency_injection",
            event_pairs_checked=checked,
            divergent_pairs=divergent,
            details=details,
            duration_ns=duration_ns,
        )

    def record_divergence(self, div: DivergenceEvent) -> None:
        """Record a divergence event for later analysis."""
        with self._lock:
            self._divergences.append(div)

    def get_divergences(self) -> list[DivergenceEvent]:
        with self._lock:
            return list(self._divergences)

    def _states_equal(self, a: dict, b: dict) -> bool:
        return self._eq_fn(a, b)


class ChaosToReplayBridge:
    """
    Bridge between Jepsen-style chaos results and ATOM event replay.

    Usage:
        bridge = ChaosToReplayBridge(chaos_result_dir="/tmp/jepsen_results")
        events = bridge.convert_chaos_to_events()
        # Then feed events to ReplayEngine
    """

    def __init__(self, chaos_result_dir: str):
        self.chaos_dir = chaos_result_dir

    def convert_chaos_to_events(self) -> list[Event]:
        """
        Parse Jepsen-style history and convert to ATOM events.

        This is a reference implementation. In practice, you'd implement
        the specific format of your chaos tool (Jepsen, Chaos Mesh, etc.)
        """
        import json
        import os

        events = []
        for filename in os.listdir(self.chaos_dir):
            if not filename.endswith(".json"):
                continue
            path = os.path.join(self.chaos_dir, filename)
            with open(path) as f:
                history = json.load(f)

            for entry in history:
                event_type = self._chaos_op_to_event_type(entry.get("type"))
                if event_type:
                    events.append(Event(
                        ts=int(entry.get("time", 0) * 1e9),  # convert s to ns
                        node_id=entry.get("node", "unknown"),
                        event_type=event_type,
                        payload={
                            "chaos_op": entry.get("op"),
                            "value": entry.get("value"),
                        },
                    ))

        return sorted(events, key=lambda e: e.ts)

    def _chaos_op_to_event_type(self, op: str) -> str | None:
        mapping = {
            "invoke": "rpc.request.send",
            "ok": "rpc.response.recv",
            "fail": "rpc.error",
            "info": "node.heartbeat",
            "timeout": "rpc.timeout",
        }
        return mapping.get(op)
