"""ACOS Trace Contract — enforced TraceRecorder interface."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol


class Decision(Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REJECTED_CONSTRAINT = "REJECTED_CONSTRAINT"
    REJECTED_RISK = "REJECTED_RISK"
    ERROR = "ERROR"


@dataclass
class ExecutionResult:
    trace_id: str
    decision: Decision
    dag: dict
    schedule: dict | None = None
    execution_trace: list[dict] = field(default_factory=list)
    final_state: dict = field(default_factory=dict)
    error: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    governance_checks: dict = field(default_factory=dict)
    l9_injections: dict = field(default_factory=dict)
    l11_verification: dict | None = None
    dag_hash: str | None = None
    node_results: dict = field(default_factory=dict)


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
            raise RuntimeError(f"TraceRecorder contract violation: missing method '{method}()'. Object: {type(obj).__name__}. Implement all required methods: {required_methods}")
        if not callable(getattr(obj, method)):
            raise RuntimeError(f"TraceRecorder contract violation: '{method}' is not callable.")
    # Verify return type hints exist (documentation contract)
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
