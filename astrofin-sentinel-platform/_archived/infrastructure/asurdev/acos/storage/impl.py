"""Concrete trace store impl (refactor §3.1 + §3.6: deterministic clock).

Replaces `datetime.utcnow()` from the old `schema.py` with the
injectable `common.deterministic.utc_now_deterministic()` helper.
This is the single entry point used by callers — God Nodes no
longer need a direct clock import.
"""
from __future__ import annotations

from datetime import datetime as _datetime

from common.deterministic import utc_now_deterministic

from .types import TraceRecord


class DeterministicTraceStore:
    """In-memory trace store that fills `created_at` from the
    global deterministic clock.

    Implements `TraceStoreProtocol` without inheriting from it
    (structural typing — God-Node-free).
    """

    def __init__(self) -> None:
        self._records: dict[str, TraceRecord] = {}

    def write(self, record: TraceRecord) -> None:
        # Fill `created_at` from deterministic clock when caller passed None.
        if record.created_at is None:
            record.created_at = utc_now_deterministic()
        self._records[record.trace_id] = record

    def read(self, trace_id: str) -> TraceRecord | None:
        return self._records.get(trace_id)

    def list(self, limit: int | None = None) -> list[TraceRecord]:
        items = list(self._records.values())
        items.sort(key=lambda r: r.created_at or _MIN)
        return items[: limit if limit is not None else len(items)]

    def clear(self) -> None:
        """Reset store state. Useful for replay tests."""
        self._records.clear()


_MIN = _datetime.min
