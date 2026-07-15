#!/usr/bin/env python3
"""ACOS SCL v6 - EventLog (append-only, O(1) trace index)."""
from __future__ import annotations
from acos.events.event import Event

class EventLog:
    """Append-only log with O(1) trace index."""
    def __init__(self):
        self._in_memory: list[Event] = []
        self._traces: dict[str, list[Event]] = {}  # O(1) index
        self._last_hash: str = "0" * 64

    def append(self, event: Event) -> Event:
        object.__setattr__(event, 'prev_hash', self._last_hash)
        object.__setattr__(event, 'event_hash', event._compute_hash())
        self._in_memory.append(event)
        self._traces.setdefault(event.trace_id, []).append(event)
        self._last_hash = event.event_hash
        return event

    def emit(self, trace_id: str, event_type: str, payload: dict | None = None, actor: str = "engine") -> Event:
        from acos.events.types import EventType
        if isinstance(event_type, str): event_type = EventType(event_type)
        event = Event(trace_id=trace_id, event_type=event_type,
                      payload=dict(payload) if payload else {}, actor=actor)
        return self.append(event)

    def get_trace(self, trace_id: str) -> list[Event]:
        return list(self._traces.get(trace_id, []))

    def get_all(self) -> list[Event]:
        return list(self._in_memory)

    def get_last_hash(self) -> str:
        return self._last_hash

    def get_event_count(self) -> int:
        return len(self._in_memory)

    def verify_chain(self, trace_id: str | None = None) -> bool:
        events = self.get_trace(trace_id) if trace_id else self._in_memory
        prev = "0" * 64
        for e in sorted(events, key=lambda x: x.timestamp):
            if e.prev_hash != prev: return False
            if e.event_hash != e._compute_hash(): return False
            prev = e.event_hash
        return True
