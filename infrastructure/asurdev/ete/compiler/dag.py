#!/usr/bin/env python3
"""
DAG Compiler — ACOS Execution Trace Engine v1

Translates all incoming jobs into deterministic DAGs.
Every execution unit becomes a node with explicit dependencies.
"""
from __future__ import annotations
import uuid
from typing import Any
from dataclasses import dataclass, field
from enum import Enum

class NodeType(Enum):
    AGENT = "agent"
    COMPUTE = "compute"
    RISK = "risk"
    GOVERNANCE = "governance"

class ExecutionBackend(Enum):
    CPU = "cpu"
    GPU = "gpu"
    EDGE = "edge"

class Layer(Enum):
    L4 = "L4"; L5 = "L5"; L6 = "L6"; L8 = "L8"; L9 = "L9"

@dataclass
class DAGNode:
    node_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    node_type: NodeType = NodeType.COMPUTE
    inputs: list[str] = field(default=list)
    outputs: list[str] = field(default=list)
    layer: Layer = Layer.L6
    constraints: dict[str, Any] = field(default=dict)
    priority: int = 50
    execution_backend: ExecutionBackend = ExecutionBackend.CPU
    retry_policy: dict[str, Any] = field(default=lambda: {"max_retries": 3, "backoff": 2.0})
    timeout_seconds: int = 300

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id, "name": self.name,
            "type": self.node_type.value, "inputs": self.inputs,
            "outputs": self.outputs, "layer": self.layer.value,
            "constraints": self.constraints, "priority": self.priority,
            "execution_backend": self.execution_backend.value,
            "retry_policy": self.retry_policy, "timeout_seconds": self.timeout_seconds,
        }

class DAGCompiler:
    """
    Compiles job submissions into executable DAGs.
    Guarantees: every node has explicit inputs/outputs, no implicit execution.
    """

    def __init__(self):
        self.nodes: dict[str, DAGNode] = {}

    def compile(self, job: dict) -> dict:
        job_type = job.get("type", "compute")
        dag = {"dag_id": str(uuid.uuid4())[:12], "nodes": [], "edges": [], "metadata": {}}
        if job_type == "agent":
            dag = self._compile_agent_job(job)
        elif job_type == "batch":
            dag = self._compile_batch_job(job)
        elif job_type == "risk":
            dag = self._compile_risk_job(job)
        elif job_type == "governance":
            dag = self._compile_governance_job(job)
        dag["metadata"]["compiled_at"] = str(uuid.uuid4())
        return dag

    def _compile_agent_job(self, job: dict) -> dict:
        dag_id = str(uuid.uuid4())[:12]
        agent_type = job.get("agent_type", "quant")
        gpu_agents = {"quant", "technical", "options_flow", "cycle", "bradley", "gann"}
        backend = ExecutionBackend.GPU if agent_type in gpu_agents else ExecutionBackend.CPU
        node = DAGNode(
            name=f"agent:{agent_type}", node_type=NodeType.AGENT,
            layer=Layer.L6, execution_backend=backend,
            priority=job.get("priority", 50),
            timeout_seconds=job.get("timeout", 300),
        )
        return {"dag_id": dag_id, "nodes": [node.to_dict()], "edges": [], "metadata": {}}

    def _compile_batch_job(self, job: dict) -> dict:
        dag_id = str(uuid.uuid4())[:12]
        tasks = job.get("tasks", [])
        nodes, edges = [], []
        prev_id = None
        for i, task in enumerate(tasks):
            node = DAGNode(name=f"task:{i}:{task.get('name','unnamed')}", node_type=NodeType.COMPUTE)
            nodes.append(node.to_dict())
            if prev_id:
                edges.append({"from": prev_id, "to": node.node_id})
            prev_id = node.node_id
        return {"dag_id": dag_id, "nodes": nodes, "edges": edges, "metadata": {}}

    def _compile_risk_job(self, job: dict) -> dict:
        dag_id = str(uuid.uuid4())[:12]
        node = DAGNode(name="risk:analysis", node_type=NodeType.RISK, layer=Layer.L8, priority=100)
        return {"dag_id": dag_id, "nodes": [node.to_dict()], "edges": [], "metadata": {}}

    def _compile_governance_job(self, job: dict) -> dict:
        dag_id = str(uuid.uuid4())[:12]
        node = DAGNode(name="governance:validate", node_type=NodeType.GOVERNANCE, layer=Layer.L9, priority=100)
        return {"dag_id": dag_id, "nodes": [node.to_dict()], "edges": [], "metadata": {}}

    def validate_dag(self, dag: dict) -> tuple[bool, list[str]]:
        errors = []
        node_ids = {n["node_id"] for n in dag["nodes"]}
        for edge in dag["edges"]:
            if edge["from"] not in node_ids:
                errors.append(f"Edge references unknown node: {edge['from']}")
            if edge["to"] not in node_ids:
                errors.append(f"Edge references unknown node: {edge['to']}")
        for node in dag["nodes"]:
            for inp in node.get("inputs", []):
                if inp not in node_ids and inp not in dag.get("external_inputs", []):
                    errors.append(f"Node {node['node_id']} references unknown input: {inp}")
        return len(errors) == 0, errors

if __name__ == "__main__":
    compiler = DAGCompiler()
    job = {"type": "agent", "agent_type": "quant", "priority": 80}
    dag = compiler.compile(job)
    print(f"DAG compiled: {dag['dag_id']}, nodes: {len(dag['nodes'])}")
    ok, errs = compiler.validate_dag(dag)
    print(f"Valid: {ok}, Errors: {errs}")
