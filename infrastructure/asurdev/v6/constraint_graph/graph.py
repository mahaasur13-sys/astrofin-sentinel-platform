#!/usr/bin/env python3
"""
Constraint Graph — G = (V, E)
Cluster represented as directed constraint graph:
  V: compute nodes, jobs, queues, resource pools
  E: capacity, affinity, anti-affinity, temporal, SLA constraints
"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ConstraintType(Enum):
    CAPACITY      = "capacity"       # GPU(node) >= sum(jobs assigned)
    AFFINITY      = "affinity"       # job ∈ allowed_node_set
    ANTI_AFFINITY = "anti_affinity"  # jobA ≠ node if conflict
    TEMPORAL      = "temporal"       # job_start >= t + migration_delay
    SLA           = "sla"            # P(latency > threshold) < 0.05
    MEMORY        = "memory"         # sum(memory) <= node.memory_capacity
    NETWORK       = "network"        # bandwidth constraints


@dataclass
class Constraint:
    ctype: ConstraintType
    source: str           # node_id or job_id
    target: Optional[str] = None
    params: dict = field(default_factory=dict)
    violated: bool = False

    @property
    def id(self) -> str:
        t = self.target or ""
        return f"{self.ctype.value}:{self.source}:{t}"


@dataclass
class NodeV:
    """Vertex in constraint graph."""
    vid: str              # node_id or job_id
    vtype: str           # "compute_node" | "job" | "queue" | "resource_pool"
    capacity: dict = field(default_factory=dict)    # gpu, cpu, memory
    load: dict = field(default_factory=dict)       # current load
    metadata: dict = field(default_factory=dict)


@dataclass
class ConstraintGraph:
    """
    Directed constraint graph G = (V, E).
    V: compute nodes, jobs, queues, resource pools
    E: typed constraints between vertices
    """
    vertices: dict[str, NodeV] = field(default_factory=dict)
    edges: list[Constraint] = field(default_factory=list)

    def add_node(self, node: NodeV):
        self.vertices[node.vid] = node

    def add_edge(self, constraint: Constraint):
        self.edges.append(constraint)

    def add_capacity_constraint(self, node_id: str, resource: str, limit: float):
        """GPU/CPU/memory capacity: sum(assigned) <= limit."""
        self.add_edge(Constraint(
            ctype=ConstraintType.CAPACITY,
            source=node_id,
            params={"resource": resource, "limit": limit}
        ))

    def add_affinity_constraint(self, job_id: str, allowed_nodes: list[str]):
        """Job can only run on specific nodes."""
        for node_id in allowed_nodes:
            self.add_edge(Constraint(
                ctype=ConstraintType.AFFINITY,
                source=job_id,
                target=node_id,
                params={"allowed": allowed_nodes}
            ))

    def add_anti_affinity_constraint(self, job_id: str, forbidden_node: str, reason: str = ""):
        """Job cannot run on specific node."""
        self.add_edge(Constraint(
            ctype=ConstraintType.ANTI_AFFINITY,
            source=job_id,
            target=forbidden_node,
            params={"reason": reason}
        ))

    def add_temporal_constraint(self, job_id: str, earliest_start: float, migration_delay: float = 0.0):
        """Job start time >= earliest_start + migration_delay."""
        self.add_edge(Constraint(
            ctype=ConstraintType.TEMPORAL,
            source=job_id,
            params={"earliest_start": earliest_start, "migration_delay": migration_delay}
        ))

    def add_sla_constraint(self, job_id: str, max_latency: float, target_p: float = 0.05):
        """P(latency > max_latency) < target_p."""
        self.add_edge(Constraint(
            ctype=ConstraintType.SLA,
            source=job_id,
            params={"max_latency": max_latency, "target_p": target_p}
        ))

    def get_node_constraints(self, node_id: str) -> list[Constraint]:
        """All constraints involving a specific node."""
        return [
            c for c in self.edges
            if c.source == node_id or c.target == node_id
        ]

    def validate_placement(self, job_id: str, node_id: str) -> tuple[bool, list[str]]:
        """
        Check if job can be placed on node.
        Returns (valid, list_of_violation_reasons).
        """
        violations = []
        job = self.vertices.get(job_id)
        node = self.vertices.get(node_id)

        if not job or not node:
            return False, ["job or node not found"]

        # 1. Capacity constraint
        for resource, limit in node.capacity.items():
            assigned = self._sum_assigned(job_id, node_id, resource)
            if assigned + (job.load.get(resource, 0)) > limit:
                violations.append(f"capacity:{resource}")

        # 2. Affinity constraint
        affinity_edges = [c for c in self.edges if c.ctype == ConstraintType.AFFINITY and c.source == job_id]
        if affinity_edges and node_id not in [c.target for c in affinity_edges]:
            violations.append("affinity:not_allowed")

        # 3. Anti-affinity constraint
        anti_edges = [c for c in self.edges if c.ctype == ConstraintType.ANTI_AFFINITY and c.source == job_id and c.target == node_id]
        if anti_edges:
            violations.append("anti_affinity:forbidden")

        # 4. Memory constraint
        mem_limit = node.capacity.get("memory", float("inf"))
        if node.load.get("memory", 0) + job.load.get("memory", 0) > mem_limit:
            violations.append("memory:overload")

        return len(violations) == 0, violations

    def _sum_assigned(self, job_id: str, node_id: str, resource: str) -> float:
        """Sum of resource usage by all jobs on node (excluding job_id)."""
        return 0.0  # Simplified — real implementation reads active job state
