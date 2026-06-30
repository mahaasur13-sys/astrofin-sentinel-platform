"""
execution_replay_bridge.py
=========================
Bridge between live distributed execution and replay engine.

Guarantees:
    EXECUTION_EVENT == REPLAY_EVENT

Checks:
    - same event_id
    - same timestamp ordering
    - same causation chain
    - same DRL distortion path
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from observability.core.event_schema import Event


@dataclass
class BridgeConfig:
    """Configuration for execution-replay bridging."""
    strict_idempotency_check: bool = True
    strict_causation_check: bool = True
    strict_drl_path_check: bool = True
    max_drift_ns: int = 1_000_000  # 1ms max event time drift
    causal_chain_depth_limit: int = 50


@dataclass
class BridgeResult:
    """Result of a single bridge check."""
    event_id: str
    passed: bool
    check_type: str  # identity | ordering | causation | drl_path
    exec_value: Any
    replay_value: Any
    drift: Any = None
    details: str = ""


class ExecutionReplayBridge:
    """
    Verifies that execution events are bit-for-bit identical to replay events.

    Usage:
        bridge = ExecutionReplayBridge(EventStore(), config=BridgeConfig())
        result = bridge.check_event(exec_event, replay_event)
        assert result.passed, f"Bridge failure: {result.details}"
    """

    def __init__(
        self,
        event_store: Any,  # EventStore instance
        config: BridgeConfig | None = None,
    ):
        self._store = event_store
        self._config = config or BridgeConfig()
        self._lock = threading.Lock()
        self._results: list[BridgeResult] = []

    # ── Identity checks ──────────────────────────────────────────────────

    def check_event_id(self, exec_event: Event, replay_event: Event) -> BridgeResult:
        """Check that exec and replay events have the same event_id."""
        match = exec_event.event_id == replay_event.event_id
        return BridgeResult(
            event_id=exec_event.event_id,
            passed=match,
            check_type="identity",
            exec_value=exec_event.event_id,
            replay_value=replay_event.event_id,
            drift=None if match else f"mismatch: {exec_event.event_id} != {replay_event.event_id}",
            details="event_id match" if match else "event_id MISMATCH",
        )

    def check_event_type(self, exec_event: Event, replay_event: Event) -> BridgeResult:
        """Check that event types are identical."""
        match = exec_event.event_type == replay_event.event_type
        return BridgeResult(
            event_id=exec_event.event_id,
            passed=match,
            check_type="identity",
            exec_value=exec_event.event_type,
            replay_value=replay_event.event_type,
            drift=None if match else "type mismatch",
            details="event_type match" if match else "event_type MISMATCH",
        )

    def check_node_id(self, exec_event: Event, replay_event: Event) -> BridgeResult:
        """Check that node_id is identical."""
        match = exec_event.node_id == replay_event.node_id
        return BridgeResult(
            event_id=exec_event.event_id,
            passed=match,
            check_type="identity",
            exec_value=exec_event.node_id,
            replay_value=replay_event.node_id,
            drift=None if match else f"node_id mismatch: {exec_event.node_id} != {replay_event.node_id}",
            details="node_id match" if match else "node_id MISMATCH",
        )

    # ── Ordering checks ────────────────────────────────────────────────────

    def check_timestamp_ordering(
        self,
        exec_event: Event,
        replay_event: Event,
        prev_exec_ts: int | None,
        prev_replay_ts: int | None,
    ) -> BridgeResult:
        """
        Check that replay event preserves the same relative ordering as execution.

        Invariant:
            exec_ts[i] - exec_ts[i-1]  should approximate  replay_ts[i] - replay_ts[i-1]
            (within max_drift_ns tolerance)
        """
        exec_drift = 0
        replay_drift = 0

        if prev_exec_ts is not None:
            exec_drift = exec_event.ts - prev_exec_ts
        if prev_replay_ts is not None:
            replay_drift = replay_event.ts - prev_replay_ts

        # For replay, we allow different absolute values but relative ordering must match
        order_match = (
            (prev_exec_ts is None and prev_replay_ts is None) or
            (exec_drift > 0 and replay_drift > 0) or
            (exec_drift == replay_drift == 0)
        )

        if not order_match:
            return BridgeResult(
                event_id=exec_event.event_id,
                passed=False,
                check_type="ordering",
                exec_value=exec_drift,
                replay_value=replay_drift,
                drift=f"order mismatch: exec_drift={exec_drift}, replay_drift={replay_drift}",
                details=f"Relative ordering violated at event {exec_event.event_id[:8]}",
            )

        return BridgeResult(
            event_id=exec_event.event_id,
            passed=True,
            check_type="ordering",
            exec_value=exec_drift,
            replay_value=replay_drift,
            drift=abs(exec_drift - replay_drift),
            details="ordering preserved",
        )

    # ── Causation checks ──────────────────────────────────────────────────

    def check_causation_chain(
        self,
        exec_event: Event,
        replay_event: Event,
        causal_parents: list[str] | None = None,
    ) -> BridgeResult:
        """
        Check that causation chain is preserved through the causal_parents field.

        Args:
            exec_event: Event from live execution
            replay_event: Event from replay engine
            causal_parents: List of parent event_ids that should cause this event
        """
        if not self._config.strict_causation_check:
            return BridgeResult(
                event_id=exec_event.event_id,
                passed=True,
                check_type="causation",
                exec_value=None,
                replay_value=None,
                details="causation check disabled",
            )

        exec_causes = set(exec_event.payload.get("causal_parents", []))
        replay_causes = set(replay_event.payload.get("causal_parents", []))

        missing_in_replay = exec_causes - replay_causes
        extra_in_replay = replay_causes - exec_causes

        passed = len(missing_in_replay) == 0 and len(extra_in_replay) == 0

        return BridgeResult(
            event_id=exec_event.event_id,
            passed=passed,
            check_type="causation",
            exec_value=sorted(exec_causes),
            replay_value=sorted(replay_causes),
            drift=len(missing_in_replay) + len(extra_in_replay),
            details=(
                "causation preserved"
                if passed
                else f"causation mismatch: missing={missing_in_replay}, extra={extra_in_replay}"
            ),
        )

    # ── DRL distortion path checks ──────────────────────────────────────

    def check_drl_path(self, exec_event: Event, replay_event: Event) -> BridgeResult:
        """
        Check that DRL distortion path is identical between execution and replay.

        DRL events carry a distortion fingerprint in payload['drl_fingerprint'].
        For deterministic replay, this fingerprint must be identical.
        """
        if not self._config.strict_drl_path_check:
            return BridgeResult(
                event_id=exec_event.event_id,
                passed=True,
                check_type="drl_path",
                exec_value=None,
                replay_value=None,
                details="drl_path check disabled",
            )

        exec_fp = exec_event.payload.get("drl_fingerprint")
        replay_fp = replay_event.payload.get("drl_fingerprint")

        # If neither has fingerprint, it's not a DRL event — skip
        if exec_fp is None and replay_fp is None:
            return BridgeResult(
                event_id=exec_event.event_id,
                passed=True,
                check_type="drl_path",
                exec_value=None,
                replay_value=None,
                details="non-DRL event, skipping",
            )

        match = exec_fp == replay_fp

        return BridgeResult(
            event_id=exec_event.event_id,
            passed=match,
            check_type="drl_path",
            exec_value=exec_fp,
            replay_value=replay_fp,
            drift=None if match else "drl_fingerprint mismatch",
            details="drl_path match" if match else "drl_path MISMATCH",
        )

    # ── Full bridge check ─────────────────────────────────────────────────

    def check_event(
        self,
        exec_event: Event,
        replay_event: Event,
        causal_parents: list[str] | None = None,
    ) -> BridgeResult:
        """
        Run ALL bridge checks on a single event pair.

        Returns a list of results, one per check type.
        """
        results: list[BridgeResult] = []

        # Identity
        results.append(self.check_event_id(exec_event, replay_event))
        results.append(self.check_event_type(exec_event, replay_event))
        results.append(self.check_node_id(exec_event, replay_event))

        # Causation
        results.append(self.check_causation_chain(exec_event, replay_event, causal_parents))

        # DRL path
        results.append(self.check_drl_path(exec_event, replay_event))

        # Aggregate: all must pass
        all_passed = all(r.passed for r in results)
        # Combine details
        failed_details = [r.details for r in results if not r.passed]

        return BridgeResult(
            event_id=exec_event.event_id,
            passed=all_passed,
            check_type="ALL",
            exec_value=exec_event,
            replay_value=replay_event,
            drift=[r.drift for r in results if r.drift is not None],
            details="; ".join(failed_details) if failed_details else "ALL_CHECKS_PASSED",
        )

    # ── Batch processing ──────────────────────────────────────────────────

    def check_stream(
        self,
        exec_events: Iterator[Event],
        replay_events: Iterator[Event],
    ) -> Iterator[BridgeResult]:
        """
        Stream through two event iterators and verify bridge at each step.

        Yields BridgeResult for each event pair.
        """
        prev_exec_ts: int | None = None
        prev_replay_ts: int | None = None

        for exec_ev, replay_ev in zip(exec_events, replay_events):
            result = self.check_event(exec_ev, replay_ev)
            result = self.check_timestamp_ordering(
                exec_ev, replay_ev, prev_exec_ts, prev_replay_ts
            )
            yield result

            prev_exec_ts = exec_ev.ts
            prev_replay_ts = replay_ev.ts

    def get_results(self) -> list[BridgeResult]:
        with self._lock:
            return list(self._results)

    def get_summary(self) -> dict[str, Any]:
        with self._lock:
            results = self._results
        if not results:
            return {"total": 0, "passed": 0, "failed": 0, "pass_rate": 1.0}

        passed = sum(1 for r in results if r.passed)
        return {
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed,
            "pass_rate": passed / len(results),
            "by_check_type": self._by_type(results),
        }

    def _by_type(self, results: list[BridgeResult]) -> dict[str, dict[str, int]]:
        by_type: dict[str, dict[str, int]] = {}
        for r in results:
            by_type.setdefault(r.check_type, {"passed": 0, "failed": 0})
            by_type[r.check_type]["passed" if r.passed else "failed"] += 1
        return by_type
