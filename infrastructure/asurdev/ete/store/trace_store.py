#!/usr/bin/env python3
"""
ETE — Execution Trace Engine: Store
Stores full DAG of every decision in the system.
"""
import json
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum, auto

class TraceType(Enum):
    DECISION = auto()
    ML_SIGNAL = auto()
    POLICY_CONSTRAINT = auto()
    SOLVER_PATH = auto()
    EXECUTION = auto()
    ROLLBACK = auto()
    GOVERNANCE = auto()
    EBL_CHECK = auto()

@dataclass
class TraceNode:
    node_id: str
    node_type: TraceType
    layer: str
    parent_ids: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp_ns: int = field(default_factory=lambda: time.time_ns())
    causal_links: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.name,
            "layer": self.layer,
            "parent_ids": self.parent_ids,
            "data": self.data,
            "timestamp_ns": self.timestamp_ns,
            "causal_links": self.causal_links,
            "metadata": self.metadata
        }

@dataclass
class ExecutionTrace:
    trace_id: str
    run_id: str
    decision_graph: Dict[str, Any] = field(default_factory=dict)
    ml_signals: Dict[str, Any] = field(default_factory=dict)
    policy_constraints: Dict[str, Any] = field(default_factory=dict)
    solver_path: Dict[str, Any] = field(default_factory=dict)
    execution_result: Dict[str, Any] = field(default_factory=dict)
    risk_score: Dict[str, Any] = field(default_factory=dict)
    rollback_status: Dict[str, Any] = field(default_factory=dict)
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    status: str = "running"

    def add_node(self, node: TraceNode) -> None:
        self.nodes.append(node.to_dict())
        if node.node_type == TraceType.DECISION:
            self.decision_graph[node.node_id] = node.data
        elif node.node_type == TraceType.ML_SIGNAL:
            self.ml_signals[node.node_id] = node.data
        elif node.node_type == TraceType.SOLVER_PATH:
            self.solver_path[node.node_id] = node.data
        elif node.node_type == TraceType.EXECUTION:
            self.execution_result[node.node_id] = node.data
        elif node.node_type == TraceType.ROLLBACK:
            self.rollback_status[node.node_id] = node.data

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "run_id": self.run_id,
            "decision_graph": self.decision_graph,
            "ml_signals": self.ml_signals,
            "policy_constraints": self.policy_constraints,
            "solver_path": self.solver_path,
            "execution_result": self.execution_result,
            "risk_score": self.risk_score,
            "rollback_status": self.rollback_status,
            "nodes": self.nodes,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status
        }

class TraceStore:
    def __init__(self, store_dir: str = "/tmp/ete_traces"):
        self.store_dir = store_dir
        self._traces: Dict[str, ExecutionTrace] = {}
        self._correlation_index: Dict[str, List[str]] = {}

    def create_trace(self, run_id: str) -> ExecutionTrace:
        trace_id = f"tr_{uuid.uuid4().hex[:16]}"
        trace = ExecutionTrace(trace_id=trace_id, run_id=run_id)
        self._traces[trace_id] = trace
        self._correlation_index.setdefault(run_id, []).append(trace_id)
        return trace

    def add_node(self, trace_id: str, node: TraceNode) -> None:
        trace = self._traces.get(trace_id)
        if trace:
            trace.add_node(node)

    def finalize(self, trace_id: str, status: str = "completed") -> None:
        trace = self._traces.get(trace_id)
        if trace:
            trace.completed_at = datetime.now(timezone.utc).isoformat()
            trace.status = status

    def get_trace(self, trace_id: str) -> Optional[ExecutionTrace]:
        return self._traces.get(trace_id)

    def get_traces_by_run(self, run_id: str) -> List[ExecutionTrace]:
        trace_ids = self._correlation_index.get(run_id, [])
        return [self._traces[tid] for tid in trace_ids if tid in self._traces]

    def store(self, path: str) -> None:
        for trace in self._traces.values():
            with open(f"{path}/{trace.trace_id}.json", "w") as f:
                json.dump(trace.to_dict(), f, indent=2)

    def load(self, path: str) -> None:
        import os
        for fn in os.listdir(path):
            if fn.endswith(".json"):
                with open(f"{path}/{fn}") as f:
                    data = json.load(f)
                    trace = ExecutionTrace(**data)
                    self._traces[trace.trace_id] = trace
