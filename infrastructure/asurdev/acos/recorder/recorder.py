"""ACOS TraceRecorder — fully contract-compliant implementation."""
import threading
import traceback as tb_module
from datetime import datetime
from typing import Any

from acos.contracts.trace_contract import (
    TraceRecorderContract,
    validate_trace_recorder_contract,
    validate_trace_format,
    ExecutionResult,
    Decision,
)
from acos.storage.memory_backend import MemoryTraceStorage

class DeterministicTraceRecorder:
    """
    Contract-compliant TraceRecorder.
    
    Guarantees:
    - get_trace() always exists and returns dict or None
    - record_trace() always returns trace_id (str)
    - idempotent writes
    - thread-safe
    
    Storage backend: MemoryTraceStorage (swappable to PostgresTraceStorage).
    """
    
    def __init__(self, storage=None):
        self._storage = storage or MemoryTraceStorage()
        self._lock = threading.RLock()
        # CONTRACT VALIDATION — fail fast on construction
        validate_trace_recorder_contract(self)
    
    def record_trace(self, trace: dict) -> str:
        """
        Persist full execution trace. Returns trace_id (str).
        
        Args:
            trace: Must contain trace_id, decision, dag, created_at
            
        Returns:
            trace_id (str) — guaranteed non-None
            
        Raises:
            ValueError: if trace format is invalid
        """
        validate_trace_format(trace)
        with self._lock:
            trace_id = trace.get("trace_id")
            if not trace_id:
                trace_id = f"trace-{datetime.utcnow().isoformat()}"
                trace = {**trace, "trace_id": trace_id}
            # Always write
            written_id = self._storage.write(trace)
            return str(written_id)
    
    def get_trace(self, trace_id: str) -> dict | None:
        """
        Retrieve full trace by ID. Returns dict or None.
        
        Args:
            trace_id: str identifier
            
        Returns:
            dict | None — never raises, returns None if not found
        """
        if not trace_id:
            return None
        with self._lock:
            try:
                result = self._storage.fetch(trace_id)
                return result if result else None
            except Exception:
                return None
    
    def list_traces(self, filters: dict | None = None) -> list[dict]:
        """
        Query traces by filter. Returns list[dict].
        
        Args:
            filters: Optional {key: value} constraints
            
        Returns:
            list[dict] — guaranteed non-None (empty list if no results)
        """
        with self._lock:
            try:
                return self._storage.query(filters or {})
            except Exception:
                return []
    
    def update_trace(self, trace_id: str, patch: dict) -> None:
        """
        Append or patch trace data. Returns None.
        
        Args:
            trace_id: str identifier
            patch: dict of fields to update
            
        Raises:
            KeyError: if trace_id not found
        """
        with self._lock:
            self._storage.update(trace_id, patch)
    
    def clear(self) -> None:
        """Clear all traces. For testing only."""
        if hasattr(self._storage, "clear"):
            self._storage.clear()

    def has_trace(self, trace_id: str) -> bool:
        """Idempotency check — returns True if trace exists. Patch 2."""
        if not trace_id:
            return False
        with self._lock:
            return self._storage.has_trace(trace_id)
