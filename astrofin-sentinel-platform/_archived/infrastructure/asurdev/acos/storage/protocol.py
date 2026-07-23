"""TraceStoreProtocol (refactor §3.2: protocol-based abstraction).

`TraceStoreProtocol` is the God-Node-free abstraction over the trace
storage layer. Concrete impls live in `impl.py` and downstream
backend files (e.g. `memory_backend.py`, `postgres_backend.py`).
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from .types import TraceRecord


@runtime_checkable
class TraceStoreProtocol(Protocol):
    """Storage-agnostic trace contract.

    Implementations: `DeterministicTraceStore` (in-memory,
    replay-safe), `PostgresBackend`, `MemoryBackend`. Callers depend
    only on this protocol — no God-Node imports required.
    """

    def write(self, record: TraceRecord) -> None: ...
    def read(self, trace_id: str) -> TraceRecord | None: ...
    def list(self, limit: int | None = None) -> list[TraceRecord]: ...
