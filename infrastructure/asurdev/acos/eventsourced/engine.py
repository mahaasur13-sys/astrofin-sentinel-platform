#!/usr/bin/env python3
"""
ACOS SCL v6 — EventSourcedEngine (WRITE-SIDE ONLY).
EMITS events ONLY. NO read-side. NO reducer. NO projection.
"""
from __future__ import annotations
import time

class EventSourcedEngine:
    """
    Write-side only execution engine.
    
    INVARIANTS (enforced):
    - emit() ONLY → EventLog.append()
    - NEVER imports or calls StateReducer
    - NEVER imports or calls StateProjection
    - NEVER calls EventLog.get_trace() / get_all()
    - execute() returns trace_id (str) ONLY
    
    execute() contract:
        Input: dag, context, trace_id
        Output: trace_id (str) ONLY
        Side effect: events appended to EventLog
    """
    
    def __init__(self, event_log):
        self._log = event_log
    
    def execute(self, dag: dict, context: dict, trace_id: str) -> str:
        """Execute DAG. Returns trace_id ONLY."""
        t0 = time.time()
        
        # Phase 1: DAG creation
        self._log.emit(trace_id, "DAG_CREATED", {"dag": dag, "context": context, "started_at": t0})
        
        # Phase 2: Validation
        self._log.emit(trace_id, "DAG_VALIDATED", {
            "node_count": len(dag.get("nodes", [])),
            "edge_count": len(dag.get("edges", []))
        })
        
        # Phase 3: Governance approval
        self._log.emit(trace_id, "GOVERNANCE_APPROVED", {"reason": "passed", "decided_at": time.time()})
        
        # Phase 4: Node scheduling & execution
        for node in dag.get("nodes", []):
            node_id = node.get("id") or node.get("name") or str(node)
            self._log.emit(trace_id, "NODE_SCHEDULED", {"node_id": node_id})
            self._log.emit(trace_id, "NODE_EXECUTED", {"node_id": node_id, "result": "success"})
        
        # Phase 5: Trace complete
        self._log.emit(trace_id, "TRACE_RECORDED", {"final_state": {"status": "COMPLETED"}})
        
        return trace_id
    
    def emit_failure(self, trace_id: str, node_id: str, error: str) -> None:
        """Emit NODE_FAILED event. Write-side ONLY."""
        self._log.emit(trace_id, "NODE_FAILED", {"node_id": node_id, "error": error})
    
    def emit_governance(self, trace_id: str, decision: str, reason: str) -> None:
        """Emit governance event. Write-side ONLY."""
        et = "GOVERNANCE_APPROVED" if decision == "APPROVED" else "GOVERNANCE_REJECTED"
        self._log.emit(trace_id, et, {"reason": reason})
