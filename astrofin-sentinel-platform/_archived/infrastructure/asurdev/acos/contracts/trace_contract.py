"""ACOS Trace Contract — DTOs re-exported from acos-contracts (S2 migration).

``Decision`` and ``ExecutionResult`` are owned by ``acos_contracts.events``
and re-exported here for backward compatibility with existing call sites
(``from acos.contracts.trace_contract import Decision, ExecutionResult``).

The recorder/storage protocol classes (``TraceRecorderContract``,
``StorageBackendContract``) and the runtime validators
(``validate_trace_recorder_contract``, ``validate_trace_format``) are
*not* part of acos-contracts yet — they remain local until the recorder
contract is promoted to the shared package.
"""
from __future__ import annotations

from typing import Any, Protocol

# DTOs lifted from acos-contracts.
from acos_contracts.events import Decision, ExecutionResult

__all__ = [
    "Decision",
    "ExecutionResult",
    "TraceRecorderContract",
    "StorageBackendContract",
    "validate_trace_recorder_contract",
    "validate_trace_format",
]


class TraceRecorderContract(Protocol):
    """ENFORCED contract for all TraceRecorder implementations."""

    def record_trace(self, trace: dict) -> str:
        """Persist full execution trace. MUST return trace_id (str)."""
        ...

    def get_trace(self, trace_id: str) -> dict | None:
        """Retrieve full trace by ID. MUST return dict or None."""
        ...

    def list_traces(self, filters: dict | None = None) -> list[dict]:
        """Query traces by filter. MUST return list[dict]."""
        ...

    def update_trace(self, trace_id: str, patch: dict) -> None:
        """Append or patch trace data. MUST return None."""
        ...


class StorageBackendContract(Protocol):
    """ENFORCED contract for all storage backends."""

    def write(self, trace: dict) -> str:
        """Write trace. MUST return trace_id (str)."""
        ...

    def fetch(self, trace_id: str) -> dict | None:
        """Fetch trace. MUST return dict or None."""
        ...

    def query(self, filters: dict) -> list[dict]:
        """Query traces. MUST return list[dict]."""
        ...


def validate_trace_recorder_contract(obj: Any) -> None:
    """FAIL FAST — raise if object violates TraceRecorderContract."""
    required_methods = ["record_trace", "get_trace", "list_traces", "update_trace"]
    for method in required_methods:
        if not hasattr(obj, method):
            raise RuntimeError(
                f"TraceRecorder contract violation: missing method '{method}()'. "
                f"Object: {type(obj).__name__}. "
                f"Implement all required methods: {required_methods}"
            )
        if not callable(getattr(obj, method)):
            raise RuntimeError(
                f"TraceRecorder contract violation: '{method}' is not callable."
            )
    doc = getattr(type(obj), "__doc__", "") or ""
    for method in required_methods:
        if method not in doc and method not in str(type(obj).__dict__):
            pass  # Acceptable — runtime check only


def validate_trace_format(trace: dict) -> None:
    """Validate trace has required fields."""
    required = ["trace_id", "decision", "dag", "created_at"]
    for field_name in required:
        if field_name not in trace:
            raise ValueError(f"Trace format violation: missing required field '{field_name}'")
    if not isinstance(trace.get("dag"), dict):
        raise ValueError("Trace format violation: 'dag' must be dict")
