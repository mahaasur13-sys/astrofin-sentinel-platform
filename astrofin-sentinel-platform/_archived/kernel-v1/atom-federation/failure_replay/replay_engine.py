"""
Replay Engine v7.0 — Deterministic event replay for distributed OS debugging.

Provides:
  - Deterministic replay from event store (replay events in exact ts order)
  - Speed control (1x, 10x, 100x, realtime)
  - Selective replay (by node_id, event_type, time range)
  - State reconstruction (rebuild node state from event sequence)
  - Replay → divergence detection (compare replay vs actual run)

Key invariant:
  Two replays of the same event sequence from the same initial state
  MUST produce identical node states.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from enum import Enum
from typing import Any

from observability.core.event_schema import Event


class ReplaySpeed(Enum):
    REALTIME = 1.0
    FAST10X = 10.0
    FAST100X = 100.0
    FAST1000X = 1000.0
    MAX = 0.0  # as fast as possible


@dataclass
class ReplayConfig:
    from_ts: int
    to_ts: int | None = None
    node_ids: list[str] | None = None
    event_types: list[str] | None = None
    speed: ReplaySpeed = ReplaySpeed.REALTIME
    stop_on_event_types: list[str] | None = None
    start_paused: bool = False


@dataclass
class ReplayState:
    """Mutable state during replay."""
    events_replayed: int = 0
    events_skipped: int = 0
    last_event_ts: int = 0
    paused: bool = False
    stopped: bool = False
    error: str | None = None


class ReplayEngine:
    """
    Deterministic event replay engine.

    Usage:
        engine = ReplayEngine(event_store=store)
        engine.load_config(ReplayConfig(from_ts=ts0))

        # Option A: Iterate events
        for event in engine.replay():
            apply_event(event)

        # Option B: Subscribe to events (replay as stream)
        def handler(event: Event):
            apply_event(event)
        engine.replay(handler=handler)
    """

    def __init__(
        self,
        event_store: Any,  # EventStore instance
        initial_state_provider: Callable[[str], dict] | None = None,
    ):
        """
        Args:
            event_store: EventStore instance to read from
            initial_state_provider: fn(node_id) -> initial state dict for replay
        """
        self._store = event_store
        self._provider = initial_state_provider
        self._config: ReplayConfig | None = None
        self._state = ReplayState()
        self._lock = threading.Lock()
        self._paused_event = threading.Event()
        self._stop_event = threading.Event()
        self._subscribers: list[Callable[[Event], None]] = []
        self._speed = ReplaySpeed.REALTIME

    def load_config(self, config: ReplayConfig) -> None:
        """Load replay configuration. Resets replay state."""
        with self._lock:
            self._config = config
            self._state = ReplayState()
            self._paused_event.set()
            self._stop_event.clear()
            self._speed = config.speed

    def pause(self) -> None:
        with self._lock:
            self._state.paused = True
            self._paused_event.clear()

    def resume(self) -> None:
        with self._lock:
            self._state.paused = False
            self._paused_event.set()

    def stop(self) -> None:
        with self._lock:
            self._state.stopped = True
            self._stop_event.set()
            self._paused_event.set()  # unblock if paused

    def add_subscriber(self, handler: Callable[[Event], None]) -> None:
        """Add an event handler called for each replayed event."""
        self._subscribers.append(handler)

    def remove_subscriber(self, handler: Callable[[Event], None]) -> None:
        self._subscribers.remove(handler)

    def replay(self) -> Iterator[Event]:
        """
        Generator that yields events in deterministic order.
        Respects pause/resume/stop. Emits at configured speed.
        """
        if self._config is None:
            raise RuntimeError("No replay config loaded. Call load_config() first.")

        self._replay_start_wallclock = time.monotonic()
        self._first_event_ts: int | None = None
        cursor = self._store.replay_cursor(
            from_ts=self._config.from_ts,
            to_ts=self._config.to_ts,
            event_types=self._config.event_types,
            node_ids=self._config.node_ids,
        )

        for event in cursor:
            # Fix first_event_ts anchor for deterministic relative timing
            if self._first_event_ts is None:
                self._first_event_ts = event.ts

            # Check stop signal
            if self._stop_event.is_set():
                break

            # Handle pause
            self._paused_event.wait()

            # Handle stop-on types
            if (
                self._config.stop_on_event_types
                and event.event_type in self._config.stop_on_event_types
            ):
                yield event
                break

            # Rate limiting (speed control)
            if self._speed != ReplaySpeed.MAX:
                elapsed_real = time.monotonic() - self._replay_start_wallclock
                event_elapsed_s = (event.ts - self._first_event_ts) / 1e9
                target_elapsed = event_elapsed_s / self._speed.value
                sleep_time = target_elapsed - elapsed_real
                if sleep_time > 0:
                    time.sleep(sleep_time)

            self._state.events_replayed += 1
            self._state.last_event_ts = event.ts

            # Compute replay lag (ms) for observability
            lag_ms = 0.0
            if self._first_event_ts is not None and self._speed != ReplaySpeed.MAX:
                elapsed_real = time.monotonic() - self._replay_start_wallclock
                event_elapsed_s = (event.ts - self._first_event_ts) / 1e9
                target_elapsed = event_elapsed_s / self._speed.value
                lag_ms = max(0.0, (target_elapsed - elapsed_real) * 1000.0)

            # Dispatch to subscribers (passes lag_ms via event context)
            for sub in self._subscribers:
                try:
                    sub(event, lag_ms=lag_ms, speed=self._speed.value)
                except TypeError:
                    sub(event)

            yield event

    def replay_until(
        self,
        until_event_type: str,
        handler: Callable[[Event], None] | None = None,
    ) -> Event | None:
        """
        Replay events until a specific event type is encountered.
        Returns the event that triggered stop, or None if not found.
        """
        self._config.stop_on_event_types = [until_event_type]
        for event in self.replay():
            if handler:
                handler(event)
            if event.event_type == until_event_type:
                return event
        return None

    def replay_as_thread(
        self,
        handler: Callable[[Event], None],
    ) -> threading.Thread:
        """Start replay in a background thread."""
        t = threading.Thread(target=self._replay_thread_body, args=(handler,))
        t.daemon = True
        t.start()
        self._replay_start_wallclock = time.monotonic()
        return t

    def _replay_thread_body(self, handler: Callable[[Event], None]) -> None:
        try:
            for event in self.replay():
                handler(event)
        except Exception as e:
            with self._lock:
                self._state.error = str(e)

    def get_state(self) -> ReplayState:
        """Return current replay state snapshot."""
        with self._lock:
            return ReplayState(
                events_replayed=self._state.events_replayed,
                events_skipped=self._state.events_skipped,
                last_event_ts=self._state.last_event_ts,
                paused=self._state.paused,
                stopped=self._state.stopped,
                error=self._state.error,
            )

    def get_stats(self) -> dict:
        """Return replay statistics."""
        s = self.get_state()
        duration_ns = s.last_event_ts - (self._config.from_ts if self._config else 0)
        return {
            "events_replayed": s.events_replayed,
            "events_skipped": s.events_skipped,
            "duration_ns": duration_ns,
            "duration_s": duration_ns / 1e9,
            "paused": s.paused,
            "stopped": s.stopped,
            "error": s.error,
        }


class StateReconstructor:
    """
    Rebuilds node/lattice/quorum state from an event sequence.

    Usage:
        reconstructor = StateReconstructor()
        for event in replay_engine.replay():
            reconstructor.apply(event)
        state = reconstructor.get_state()
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.node_states: dict[str, dict] = {}
        self.lattice_state: dict[str, Any] = {}
        self.quorum_state: dict[str, Any] = {}
        self.event_count: dict[str, int] = {}
        self._current_event: Event | None = None

    def apply(self, event: Event) -> None:
        """Apply a single event to rebuild state."""
        with self._lock:
            self._current_event = event
            handler = self._DISPATCH.get(event.event_type)
            if handler:
                handler(self, event)
            self.event_count[event.event_type] = (
                self.event_count.get(event.event_type, 0) + 1
            )

    def get_node_state(self, node_id: str) -> dict:
        return self.node_states.get(node_id, {})

    def get_lattice_state(self) -> dict:
        return dict(self.lattice_state)

    def get_quorum_state(self) -> dict:
        return dict(self.quorum_state)

    def get_state(self) -> dict:
        with self._lock:
            return {
                "nodes": {k: dict(v) for k, v in self.node_states.items()},
                "lattice": dict(self.lattice_state),
                "quorum": dict(self.quorum_state),
                "event_count": dict(self.event_count),
                "last_event_ts": self._current_event.ts if self._current_event else 0,
            }

    # ── Event handlers (match EventType enum values) ──────────────────────

    def _on_node_start(self, event: Event) -> None:
        self.node_states.setdefault(event.node_id, {}).update(
            status="active", first_seen_ts=event.ts
        )

    def _on_node_down(self, event: Event) -> None:
        self.node_states.setdefault(event.node_id, {}).update(
            status="down", down_since=event.ts
        )

    def _on_node_recovery(self, event: Event) -> None:
        self.node_states.setdefault(event.node_id, {}).update(
            status="active", last_recovery_ts=event.ts
        )

    def _on_sbs_violation(self, event: Event) -> None:
        ns = self.node_states.setdefault(event.node_id, {})
        ns["sbs_violations"] = ns.get("sbs_violations", 0) + 1
        ns["last_violation_ts"] = event.ts
        ns["last_violation_type"] = event.payload.get("violation_type", "unknown")

    def _on_coherence_drift(self, event: Event) -> None:
        ns = self.node_states.setdefault(event.node_id, {})
        ns["coherence_drift_score"] = event.payload.get("drift_score", 0.0)

    def _on_quorum_health_update(self, event: Event) -> None:
        self.quorum_state["health"] = event.payload.get("health", 1.0)
        self.quorum_state["members"] = event.payload.get("members", [])

    _DISPATCH: dict[str, Callable] = {
        "node.start": _on_node_start,
        "node.ready": _on_node_start,
        "node.down": _on_node_down,
        "node.recovery": _on_node_recovery,
        "sbs.violation": _on_sbs_violation,
        "coherence.drift.detected": _on_coherence_drift,
        "coherence.drift.resolved": _on_coherence_drift,
        "quorum.vote.granted": _on_quorum_health_update,
        "quorum.recovered": _on_quorum_health_update,
        "quorum.lost": _on_quorum_health_update,
    }
