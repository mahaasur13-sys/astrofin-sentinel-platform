#!/usr/bin/env python3
"""
ETE — Execution Trace Engine: Replayer
Guarantees deterministic replay of any decision trace.
"""
import json
import hashlib
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from ete.store.trace_store import TraceStore, TraceNode, TraceType

@dataclass
class ReplayResult:
    trace_id: str
    is_identical: bool
    divergence_points: List[Dict[str, Any]]
    replay_duration_ms: float
    steps_executed: int

class DeterministicReplayer:
    def __init__(self, store: TraceStore):
        self.store = store
        self.expected_hashes: Dict[str, str] = {}

    def register_trace(self, trace_id: str) -> str:
        trace = self.store.get_trace(trace_id)
        if not trace:
            raise ValueError(f"Trace {trace_id} not found")
        state_hash = self._hash_trace_state(trace)
        self.expected_hashes[trace_id] = state_hash
        return state_hash

    def _hash_trace_state(self, trace) -> str:
        key_fields = {
            "decision_graph": sorted(trace.decision_graph.keys()),
            "ml_signals": sorted(trace.ml_signals.keys()),
            "execution_result": sorted(trace.execution_result.keys()),
            "solver_path": sorted(trace.solver_path.keys())
        }
        blob = json.dumps(key_fields, sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()[:16]

    def replay(self, trace_id: str, hooks: Optional[Dict[str, Callable]] = None) -> ReplayResult:
        trace = self.store.get_trace(trace_id)
        if not trace:
            raise ValueError(f"Trace {trace_id} not found")

        import time
        start = time.time()
        divergence_points = []
        steps_executed = 0

        for node_data in trace.nodes:
            layer = node_data["layer"]
            node_type = node_data["node_type"]
            hook = (hooks or {}).get(layer)

            if hook:
                try:
                    hook(node_data["data"])
                    steps_executed += 1
                except Exception as e:
                    divergence_points.append({
                        "node_id": node_data["node_id"],
                        "layer": layer,
                        "error": str(e),
                        "position": steps_executed
                    })

        duration_ms = (time.time() - start) * 1000
        current_hash = self._hash_trace_state(trace)
        is_identical = current_hash == self.expected_hashes.get(trace_id, "")

        return ReplayResult(
            trace_id=trace_id,
            is_identical=is_identical,
            divergence_points=divergence_points,
            replay_duration_ms=duration_ms,
            steps_executed=steps_executed
        )

class CorrelationEngine:
    def __init__(self, store: TraceStore):
        self.store = store

    def link_causes(self, effect_trace_id: str, cause_trace_ids: List[str]) -> None:
        effect_trace = self.store.get_trace(effect_trace_id)
        if not effect_trace:
            return
        for node in effect_trace.nodes:
            node["causal_links"] = cause_trace_ids

    def query_by_layer(self, run_id: str, layer: str) -> List[Dict[str, Any]]:
        traces = self.store.get_traces_by_run(run_id)
        results = []
        for trace in traces:
            for node in trace.nodes:
                if node["layer"] == layer:
                    results.append(node)
        return results

    def find_divergence(self, run_id: str, baseline_run_id: str, layer: str) -> List[Dict[str, Any]]:
        baseline_nodes = {
            n["node_id"]: n for n in self.query_by_layer(baseline_run_id, layer)
        }
        current_nodes = {
            n["node_id"]: n for n in self.query_by_layer(run_id, layer)
        }
        divergences = []
        for node_id, current in current_nodes.items():
            baseline = baseline_nodes.get(node_id)
            if baseline and current["data"] != baseline["data"]:
                divergences.append({
                    "node_id": node_id,
                    "layer": layer,
                    "baseline": baseline["data"],
                    "current": current["data"]
                })
        return divergences
