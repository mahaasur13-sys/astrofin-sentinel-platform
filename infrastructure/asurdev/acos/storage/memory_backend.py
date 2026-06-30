#!/usr/bin/env python3
"""
ACOS Memory Storage Backend — with has_trace() for idempotency.
Patch 2: Added has_trace() method.
"""
import json
import threading
from datetime import datetime
from typing import Any


class MemoryTraceStorage:
    """Thread-safe in-memory storage with idempotency support."""

    def __init__(self):
        self._traces: dict[str, dict] = {}
        self._lock = threading.RLock()

    def write(self, trace: dict) -> str:
        with self._lock:
            trace_id = trace.get("trace_id") or f"mem-{len(self._traces)}"
            stored = {**trace, "trace_id": trace_id, "stored_at": datetime.utcnow().isoformat()}
            self._traces[trace_id] = stored
            return trace_id

    def fetch(self, trace_id: str) -> dict | None:
        with self._lock:
            return dict(self._traces.get(trace_id)) if trace_id in self._traces else None

    def query(self, filters: dict | None = None) -> list[dict]:
        with self._lock:
            if not filters:
                return [dict(t) for t in self._traces.values()]
            results = []
            for trace in self._traces.values():
                match = True
                for k, v in filters.items():
                    if trace.get(k) != v:
                        match = False
                        break
                if match:
                    results.append(dict(trace))
            return results

    def update(self, trace_id: str, patch: dict) -> None:
        with self._lock:
            if trace_id in self._traces:
                self._traces[trace_id].update(patch)
            else:
                raise KeyError(f"Trace {trace_id} not found")

    def has_trace(self, trace_id: str) -> bool:
        """Idempotency check — O(1) lookup. Patch 2."""
        with self._lock:
            return trace_id in self._traces

    def clear(self) -> None:
        with self._lock:
            self._traces.clear()
