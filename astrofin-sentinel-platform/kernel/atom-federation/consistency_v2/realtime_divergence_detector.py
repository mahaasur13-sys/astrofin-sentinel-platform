"""
realtime_divergence_detector.py
===============================
Detects three classes of continuous divergence that I1-I4 snapshot checks miss:

    1. TEMPORAL WINDOW DIVERGENCE
       sI1-sI4 verify state equality at discrete ticks.
       But: execution_state(t) == replay_state(t) doesn't guarantee
            the DERIVATIVE is identical: d/dt exec ≠ d/dt replay.

    2. NON-REPLAYABLE NONDETERMINISM
       Sources: external IO, async scheduler variance, K8s timing, GC pauses.
       These cause: logically correct replay, temporally wrong execution.

    3. COHERENCE TRAJECTORY DRIFT
       drift_score changes at different rates in exec vs replay.

Classes:
    DivergenceType       — enum of divergence categories
    TransitionRecord     — timestamped state transition
    TemporalDriftEntry  — temporal divergence between two domains
    NonReplayableMarker  — flags events that are unreplayable by nature
    RealtimeDivergenceDetector  — main detection engine
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

# ── Types ────────────────────────────────────────────────────────────────────

class DivergenceType(Enum):
    TEMPORAL_DRIFT = auto()
    RATE_DIVERGENCE = auto()
    NONDETERMINISTIC_EVENT = auto()
    COHERENCE_TRAJECTORY_DRIFT = auto()
    CAUSAL_GAP = auto()


@dataclass
class NonReplayableMarker:
    event_id: str
    source: str
    reason: str
    wallclock_ts_ns: int


@dataclass
class TransitionRecord:
    state_hash: str
    wallclock_ns: int
    logical_ts_ns: int
    domain: str
    node_id: str


@dataclass
class TemporalDriftEntry:
    state_hash: str
    exec_wallclock_ns: int
    replay_wallclock_ns: int
    drift_ms: float
    severity: str
    ts_ns: int = field(default_factory=lambda: time.time_ns())

    def to_dict(self) -> dict[str, Any]:
        return {
            "state_hash": self.state_hash,
            "drift_ms": self.drift_ms,
            "severity": self.severity,
        }


@dataclass
class DivergenceEvent:
    divergence_type: DivergenceType
    details: str
    severity: str
    exec_value: Any
    replay_value: Any
    drift: float
    can_self_heal: bool
    ts_ns: int = field(default_factory=lambda: time.time_ns())

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.divergence_type.name,
            "details": self.details,
            "severity": self.severity,
            "drift": self.drift,
            "can_self_heal": self.can_self_heal,
        }


@dataclass
class DivergenceReport:
    events: list[DivergenceEvent]
    temporal_drift_entries: list[TemporalDriftEntry]
    nondeterministic_markers: list[NonReplayableMarker]
    total_checks: int
    divergent_checks: int
    all_consistent: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_checks": self.total_checks,
            "divergent_checks": self.divergent_checks,
            "all_consistent": self.all_consistent,
            "temporal_drifts": [e.to_dict() for e in self.temporal_drift_entries],
            "events": [e.to_dict() for e in self.events],
        }


# ── State hasher ─────────────────────────────────────────────────────────────

def _state_hash(state: dict, depth: int = 3) -> str:
    """Compact fingerprint of a cluster state, excluding wallclock-dependent fields."""
    def _stable_view(d: dict, dpt: int) -> dict:
        if dpt <= 0:
            return {}
        return {
            k: (_stable_view(v, dpt - 1) if isinstance(v, dict)
                else (float(v) if isinstance(v, (int, float)) else v))
            for k, v in d.items()
            if k not in ("wallclock_ns", "ts_ns", "last_updated_ns", "latency_ns")
        }
    view = _stable_view(state, depth)
    payload = json.dumps(view, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


# ── RealtimeDivergenceDetector ─────────────────────────────────────────────

class RealtimeDivergenceDetector:
    """
    Detects continuous (streaming) divergence classes that I1-I4 miss.
    """

    _TEMPORAL_WARNING_MS = 100.0
    _TEMPORAL_CRITICAL_MS = 500.0
    _COHERENCE_DRIFT_WARNING = 0.05
    _COHERENCE_DRIFT_CRITICAL = 0.15
    _RATE_WARNING = 0.2
    _RATE_CRITICAL = 0.5

    def __init__(
        self,
        exec_state_fn: Callable[[], dict],
        replay_state_fn: Callable[[], dict],
        exec_events_fn: Callable[[], list] | None = None,
        replay_events_fn: Callable[[], list] | None = None,
        get_coherence_drift_fn: Callable[[dict], dict[str, float]] | None = None,
        temporal_drift_threshold_ms: float = 500.0,
        nondeterministic_sources: list[str] | None = None,
        max_transition_history: int = 1000,
    ):
        self._exec_state_fn = exec_state_fn
        self._replay_state_fn = replay_state_fn
        self._exec_events_fn = exec_events_fn or (lambda: [])
        self._replay_events_fn = replay_events_fn or (lambda: [])
        self._coherence_fn = get_coherence_drift_fn or (lambda _: {})
        self._temporal_threshold_ms = temporal_drift_threshold_ms
        self._nondet_sources = set(nondeterministic_sources or [])

        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None

        self._transitions_exec: list[TransitionRecord] = []
        self._transitions_replay: list[TransitionRecord] = []
        self._max_history = max_transition_history

        self._tick_count = 0
        self._divergence_count = 0
        self._last_report: DivergenceReport | None = None

        self._prev_exec_coherence: dict[str, float] = {}
        self._prev_replay_coherence: dict[str, float] = {}

        self._exec_transition_timestamps: list[int] = []
        self._replay_transition_timestamps: list[int] = []

    def _record_transition(
        self,
        state: dict,
        domain: str,
    ) -> TransitionRecord | None:
        """Record a state transition if the state actually changed."""
        curr_hash = _state_hash(state)
        wallclock_ns = state.get("wallclock_ns", time.time_ns())
        logical_ns = state.get("logical_ts_ns", wallclock_ns)
        node_id = state.get("node_id", "cluster")

        transitions = self._transitions_exec if domain == "exec" else self._transitions_replay
        timestamps = self._exec_transition_timestamps if domain == "exec" else self._replay_transition_timestamps

        if transitions and transitions[-1].state_hash == curr_hash:
            return None

        record = TransitionRecord(
            state_hash=curr_hash,
            wallclock_ns=wallclock_ns,
            logical_ts_ns=logical_ns,
            domain=domain,
            node_id=node_id,
        )
        transitions.append(record)
        timestamps.append(wallclock_ns)

        if len(transitions) > self._max_history:
            transitions.pop(0)
        if len(timestamps) > self._max_history:
            timestamps.pop(0)

        return record

    def _check_temporal_drift(self, exec_state: dict, replay_state: dict) -> list[DivergenceEvent]:
        """Check if identical state was reached at different wall-clock times."""
        events = []
        exec_hash = _state_hash(exec_state)
        replay_hash = _state_hash(replay_state)

        if exec_hash != replay_hash:
            return events

        exec_ns = exec_state.get("wallclock_ns", time.time_ns())
        replay_ns = replay_state.get("wallclock_ns", time.time_ns())
        drift_ms = abs(exec_ns - replay_ns) / 1e6

        if drift_ms > self._TEMPORAL_CRITICAL_MS:
            severity = "critical"
            can_heal = False
        elif drift_ms > self._TEMPORAL_WARNING_MS:
            severity = "warning"
            can_heal = True
        else:
            return events

        events.append(DivergenceEvent(
            divergence_type=DivergenceType.TEMPORAL_DRIFT,
            details=f"identical state at drift={drift_ms:.2f}ms",
            severity=severity,
            exec_value=exec_ns,
            replay_value=replay_ns,
            drift=drift_ms,
            can_self_heal=can_heal,
        ))
        return events

    def _check_rate_divergence(self) -> list[DivergenceEvent]:
        """Compare transition rates between exec and replay over 60s window."""
        events = []
        now_ns = time.time_ns()
        window_ns = 60 * 1e9

        cutoff = now_ns - int(window_ns)
        exec_recent = [t for t in self._exec_transition_timestamps if t >= cutoff]
        replay_recent = [t for t in self._replay_transition_timestamps if t >= cutoff]

        if len(exec_recent) < 2 or len(replay_recent) < 2:
            return events

        exec_rate = len(exec_recent) / (window_ns / 60 * 1e9)
        replay_rate = len(replay_recent) / (window_ns / 60 * 1e9)
        max_rate = max(exec_rate, replay_rate, 0.001)
        rate_drift = abs(exec_rate - replay_rate) / max_rate

        if rate_drift > self._RATE_CRITICAL:
            severity = "critical"
            can_heal = False
        elif rate_drift > self._RATE_WARNING:
            severity = "warning"
            can_heal = True
        else:
            return events

        events.append(DivergenceEvent(
            divergence_type=DivergenceType.RATE_DIVERGENCE,
            details=f"exec={exec_rate:.2f}/min, replay={replay_rate:.2f}/min, diff={rate_drift:.2%}",
            severity=severity,
            exec_value=exec_rate,
            replay_value=replay_rate,
            drift=rate_drift,
            can_self_heal=can_heal,
        ))
        return events

    def _check_coherence_trajectory(self, exec_state: dict, replay_state: dict) -> list[DivergenceEvent]:
        """Track coherence drift_score rate of change in both domains."""
        events = []
        curr_exec_coh = self._coherence_fn(exec_state)
        curr_replay_coh = self._coherence_fn(replay_state)

        if not curr_exec_coh or not curr_replay_coh:
            return events

        all_nodes = set(curr_exec_coh) | set(curr_replay_coh)
        max_coh_drift = 0.0
        worst_node = None

        for node_id in all_nodes:
            prev_e = self._prev_exec_coherence.get(node_id, 0.0)
            prev_r = self._prev_replay_coherence.get(node_id, 0.0)
            curr_e = curr_exec_coh.get(node_id, 0.0)
            curr_r = curr_replay_coh.get(node_id, 0.0)

            delta_e = abs(curr_e - prev_e)
            delta_r = abs(curr_r - prev_r)
            max_delta = max(delta_e, delta_r, 0.001)
            coh_drift = abs(delta_e - delta_r) / max_delta

            if coh_drift > max_coh_drift:
                max_coh_drift = coh_drift
                worst_node = node_id

        self._prev_exec_coherence = dict(curr_exec_coh)
        self._prev_replay_coherence = dict(curr_replay_coh)

        if max_coh_drift > self._COHERENCE_DRIFT_CRITICAL:
            severity = "critical"
            can_heal = False
        elif max_coh_drift > self._COHERENCE_DRIFT_WARNING:
            severity = "warning"
            can_heal = True
        else:
            return events

        events.append(DivergenceEvent(
            divergence_type=DivergenceType.COHERENCE_TRAJECTORY_DRIFT,
            details=f"node={worst_node}: {max_coh_drift:.2%}",
            severity=severity,
            exec_value=curr_exec_coh.get(worst_node),
            replay_value=curr_replay_coh.get(worst_node),
            drift=max_coh_drift,
            can_self_heal=can_heal,
        ))
        return events

    def _tick(self) -> DivergenceReport:
        """Run one detection tick and return report."""
        exec_state = self._exec_state_fn()
        replay_state = self._replay_state_fn()
        self._exec_events_fn()
        self._replay_events_fn()

        self._record_transition(exec_state, "exec")
        self._record_transition(replay_state, "replay")

        all_events: list[DivergenceEvent] = []
        all_events.extend(self._check_temporal_drift(exec_state, replay_state))
        all_events.extend(self._check_rate_divergence())
        all_events.extend(self._check_coherence_trajectory(exec_state, replay_state))

        self._tick_count += 1
        if all_events:
            self._divergence_count += 1

        report = DivergenceReport(
            events=all_events,
            temporal_drift_entries=[],
            nondeterministic_markers=[],
            total_checks=self._tick_count,
            divergent_checks=self._divergence_count,
            all_consistent=len(all_events) == 0,
        )

        with self._lock:
            self._last_report = report

        return report

    def start(self, interval_sec: float = 1.0) -> None:
        """Start continuous detection in background thread."""
        self._running = True

        def loop():
            while self._running:
                try:
                    self._tick()
                except Exception as e:
                    import sys
                    print(f"[RealtimeDivergenceDetector] tick error: {e}", file=sys.stderr)
                time.sleep(interval_sec)

        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)

    def get_report(self) -> DivergenceReport | None:
        with self._lock:
            return self._last_report

    def verify(self) -> DivergenceReport:
        """Synchronous one-shot verification."""
        return self._tick()
