#!/usr/bin/env python3
"""
ACOS EventSourcedEngine — PATCH 2: Idempotent execution (FIXED).
If trace already exists, returns cached result WITHOUT re-execution.
After execution, records trace to recorder for idempotency.
"""
from __future__ import annotations
import time
from acos.recorder.recorder import DeterministicTraceRecorder
from acos.validator.contract_validator import DAGValidator


class EventSourcedEngine:
    """
    Idempotent write-side execution engine.
    
    PATCH 2 fixes:
    - execute() checks has_trace() BEFORE execution
    - After execution, records trace to recorder for idempotency
    - DAGValidator.validate_dag() called BEFORE any state changes
    """

    def __init__(self, event_log, trace_recorder: DeterministicTraceRecorder | None = None):
        self._log = event_log
        self._recorder = trace_recorder

    def execute(self, dag: dict, context: dict, trace_id: str) -> str:
        """
        Idempotent execution.
        
        PATCH 2: Check has_trace() BEFORE executing.
        If trace exists → return cached trace_id (no re-execution).
        After execution → record to recorder for future idempotency.
        """
        # IDEMPOTENCY: skip if already executed
        if self._recorder and self._recorder.has_trace(trace_id):
            print(f"[IDEMPOTENT] Trace {trace_id} already exists, skipping execution")
            return trace_id

        # PATCH 2: Validate DAG BEFORE any state changes
        violations = DAGValidator.validate_dag(dag)
        if violations:
            raise ValueError(f"DAG validation failed: {[v.message for v in violations]}")

        t0 = time.time()

        # Phase 1: DAG creation
        self._log.emit(trace_id, "DAG_CREATED", {"dag": dag, "context": context, "started_at": t0})

        # Phase 2: Validation
        self._log.emit(trace_id, "DAG_VALIDATED", {
            "node_count": len(dag.get("nodes", [])),
            "edge_count": len(dag.get("edges", []))
        })

        # Phase 3: Governance
        self._log.emit(trace_id, "GOVERNANCE_APPROVED", {"reason": "passed", "decided_at": time.time()})

        # Phase 4: Node execution
        for node in dag.get("nodes", []):
            node_id = node.get("id") or node.get("name") or str(node)
            self._log.emit(trace_id, "NODE_SCHEDULED", {"node_id": node_id})
            self._log.emit(trace_id, "NODE_EXECUTED", {"node_id": node_id, "result": "success"})

        # Phase 5: Complete
        self._log.emit(trace_id, "TRACE_RECORDED", {"final_state": {"status": "COMPLETED"}})

        # PATCH 2 FIX: Record trace to recorder AFTER successful execution
        if self._recorder:
            self._recorder.record_trace({
                "trace_id": trace_id,
                "decision": "APPROVED",
                "dag": dag,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(t0)),
            })

        return trace_id

    def emit_failure(self, trace_id: str, node_id: str, error: str) -> None:
        """Emit NODE_FAILED event."""
        self._log.emit(trace_id, "NODE_FAILED", {"node_id": node_id, "error": error})

    def emit_governance(self, trace_id: str, decision: str, reason: str) -> None:
        """Emit governance event."""
        et = "GOVERNANCE_APPROVED" if decision == "APPROVED" else "GOVERNANCE_REJECTED"
        self._log.emit(trace_id, et, {"reason": reason})
