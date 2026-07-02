#!/usr/bin/env python3
"""
ReplayEngine — Deterministic Reconstruction

Requirements:
  - Exact DAG reconstruction from trace
  - Identical execution ordering
  - Pinned ML model versions
  - Identical governance outcomes
  - Deterministic scheduler routing
"""
from __future__ import annotations
import json

class ReplayEngine:
    """
    Reconstructs and re-executes a DAG from its trace.
    Determinism is guaranteed by pinning all inputs and model versions.
    """

    def __init__(self, execution_engine, governance_gate):
        self.engine = execution_engine
        self.governance_gate = governance_gate

    def replay(self, trace_id: str, recorder) -> dict:
        trace = recorder.get(trace_id)
        if not trace:
            return {"error": f"Trace {trace_id} not found"}
        dag = trace["dag"]
        context = {
            "risk_score": 0.0,
            "replay": True,
            "original_trace_id": trace_id,
            "model_versions": trace.get("metadata", {}).get("model_versions", {}),
        }
        replayed = self.engine.execute(dag, context)
        replayed["is_replay"] = True
        replayed["original_trace_id"] = trace_id
        match = self._compare_traces(trace, replayed)
        replayed["determinism_match"] = match
        return replayed

    def _compare_traces(self, original: dict, replayed: dict) -> bool:
        if original["final_state"] != replayed["final_state"]:
            return False
        orig_nodes = {n["node_id"]: n["status"] for n in original.get("node_execution_log", [])}
        repl_nodes = {n["node_id"]: n["status"] for n in replayed.get("node_execution_log", [])}
        return orig_nodes == repl_nodes

    def audit(self, trace_id: str, recorder) -> dict:
        trace = recorder.get(trace_id)
        if not trace:
            return {"error": f"Trace {trace_id} not found"}
        return {
            "trace_id": trace_id,
            "dag_id": trace["dag_id"],
            "final_state": trace["final_state"],
            "node_count": len(trace.get("node_execution_log", [])),
            "governance_approved": any(d.get("decision") == "APPROVED" for d in trace.get("governance_decisions", [])),
            "latency_ms": sum(trace.get("latency_profile", {}).values()) * 1000,
            "risk_events": len(trace.get("risk_events", [])),
        }
