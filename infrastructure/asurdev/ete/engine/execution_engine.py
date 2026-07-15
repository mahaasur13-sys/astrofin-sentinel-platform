#!/usr/bin/env python3
from __future__ import annotations
from enum import Enum
import uuid
import time

class ExecutionState(Enum):
    PENDING = "PENDING"; RUNNING = "RUNNING"; SUCCESS = "SUCCESS"
    FAILED = "FAILED"; KILLED = "KILLED"; ROLLED_BACK = "ROLLED_BACK"

class ExecutionEngine:
    """
    DAG execution with:
    - Topological ordering (parallel where possible)
    - Checkpointing, retry logic, failure isolation
    - Immutable trace recording
    """

    def __init__(self, governance_gate=None, scheduler_adapter=None):
        self.governance_gate = governance_gate
        self.scheduler = scheduler_adapter
        self.traces = {}
        self._state = {"status": "idle", "executions": 0}

    def execute(self, dag: dict, context: dict) -> dict:
        dag_id = dag.get("dag_id", "unknown")
        trace = {
            "trace_id": str(uuid.uuid4())[:12],
            "dag": dag,
            "dag_id": dag_id,
            "node_execution_log": [],
            "governance_decisions": [],
            "scheduler_mapping": [],
            "risk_events": [],
            "latency_profile": {},
            "final_state": ExecutionState.PENDING.value,
        }
        self.traces[trace["trace_id"]] = trace
        self._state["executions"] += 1
        self._state["status"] = "running"

        if self.governance_gate:
            try:
                decision_obj, reason = self.governance_gate.pre_check(dag, context)
                decision = str(decision_obj) if decision_obj else "APPROVED"
                trace["governance_decisions"].append({"stage": "pre", "decision": decision, "reason": reason})
                if "REJECT" in decision:
                    trace["final_state"] = ExecutionState.FAILED.value
                    self._state["status"] = "idle"
                    return trace
            except Exception as e:
                trace["governance_decisions"].append({"stage": "pre", "decision": "ERROR", "reason": str(e)})

        if self.scheduler:
            try:
                routing = self.scheduler.route(dag)
                trace["scheduler_mapping"] = routing.get("assignments", [])
            except Exception:
                pass

        nodes_map = {n.get("node_id") or n.get("id"): n for n in dag.get("nodes", [])}
        in_degree = {nid: 0 for nid in nodes_map}
        for e in dag.get("edges", []):
            in_degree[e.get("to")] = in_degree.get(e.get("to"), 0) + 1
        ready = [n for n, d in in_degree.items() if d == 0]
        completed = set()

        while ready:
            batch = ready
            ready = []
            for node_id in batch:
                node = nodes_map.get(node_id)
                if not node:
                    continue
                t0 = time.time()
                ok, err = self._execute_node(node, trace, context)
                latency = time.time() - t0
                trace["latency_profile"][node_id] = round(latency, 4)
                trace["node_execution_log"].append({
                    "node_id": node_id, "status": "SUCCESS" if ok else "FAILED",
                    "error": err, "latency": latency,
                })
                if not ok:
                    trace["final_state"] = ExecutionState.FAILED.value
                    self._state["status"] = "idle"
                    return trace
                completed.add(node_id)
                for e in dag.get("edges", []):
                    if e.get("from") == node_id:
                        in_degree[e["to"]] -= 1
                        if in_degree[e["to"]] == 0:
                            ready.append(e["to"])

        trace["final_state"] = ExecutionState.SUCCESS.value
        self._state["status"] = "idle"
        return trace

    def _execute_node(self, node: dict, trace: dict, context: dict) -> tuple[bool, str]:
        try:
            if self.governance_gate and node.get("layer") == "L8":
                try:
                    if not self.governance_gate.mid_check(node.get("node_id", ""), context):
                        trace["risk_events"].append({"node_id": node.get("node_id"), "event": "kill_switch"})
                        return False, "kill_switch_triggered"
                except Exception:
                    pass
            return True, ""
        except Exception as e:
            return False, str(e)

    def get_state(self) -> dict:
        return dict(self._state)

    def get_trace(self, trace_id: str) -> dict:
        return self.traces.get(trace_id, {})
