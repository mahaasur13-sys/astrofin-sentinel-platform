#!/usr/bin/env python3
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class ExecutionState:
    trace_id: str = ""
    status: str = "INIT"
    governance_decision: str | None = None
    dag: dict = field(default_factory=dict)
    node_states: dict[str, str] = field(default_factory=dict)
    scheduled_count: int = 0
    executed_count: int = 0
    failed_count: int = 0
    events_emitted: list[str] = field(default_factory=list)

def _payload_to_dict(p) -> dict:
    if isinstance(p, dict): return p
    if isinstance(p, tuple): return dict(p)
    return {}

class StateReducer:
    def __init__(self, event_log):
        self._log = event_log

    def reduce(self, trace_id: str) -> ExecutionState:
        events = self._log.get_trace(trace_id)
        state = ExecutionState(trace_id=trace_id)
        for event in sorted(events, key=lambda e: e.timestamp):
            state = self._apply(state, event)
        return state

    def rebuild(self, trace_id: str) -> dict[str, Any]:
        s = self.reduce(trace_id)
        return {
            "trace_id": s.trace_id, "status": s.status,
            "governance_decision": s.governance_decision,
            "scheduled_count": s.scheduled_count,
            "executed_count": s.executed_count,
            "failed_count": s.failed_count,
            "dag": s.dag, "node_states": s.node_states,
        }

    def _apply(self, state: ExecutionState, event) -> ExecutionState:
        et = event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type)
        p = _payload_to_dict(event.payload)
        if et == "DAG_CREATED":
            state.status = "CREATED"; state.dag = p.get("dag", {})
        elif et == "DAG_VALIDATED": state.status = "VALIDATED"
        elif et == "DAG_INVALID": state.status = "INVALID"
        elif et == "GOVERNANCE_APPROVED":
            state.status = "APPROVED"; state.governance_decision = "APPROVED"
        elif et == "GOVERNANCE_REJECTED":
            state.status = "REJECTED"; state.governance_decision = "REJECTED"
        elif et == "NODE_SCHEDULED":
            nid = p.get("node_id", ""); 
            if nid:
                state.node_states[nid] = "SCHEDULED"
                state.scheduled_count += 1
                state.events_emitted.append("NODE_SCHEDULED")
        elif et == "NODE_EXECUTED":
            nid = p.get("node_id", ""); 
            if nid:
                state.node_states[nid] = "EXECUTED"
                state.executed_count += 1
                state.events_emitted.append("NODE_EXECUTED")
                dag_nodes = state.dag.get("nodes", [])
                if dag_nodes:
                    nids = {n.get("id", n.get("name", str(n))) if isinstance(n, dict) else str(n) for n in dag_nodes}
                    if all(state.node_states.get(n) == "EXECUTED" for n in nids):
                        state.status = "COMPLETED"
        elif et == "NODE_FAILED":
            nid = p.get("node_id", ""); 
            if nid:
                state.node_states[nid] = "FAILED"
                state.failed_count += 1
                state.status = "FAILED"
        elif et == "SCHEDULER_TIMEOUT": state.status = "TIMEOUT"
        elif et == "TRACE_RECORDED": pass
        return state
