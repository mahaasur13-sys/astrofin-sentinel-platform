#!/usr/bin/env python3
"""
Constraint Engine — validates feasibility before optimization.
Hard constraints: MUST be satisfied.
Soft constraints: penalty in objective.
"""

from dataclasses import dataclass
from enum import Enum, auto


class ViolationType(Enum):
    GPU_MEM_EXCEEDED = auto()
    CPU_MEM_EXCEEDED = auto()
    PARTITION_OFFLINE = auto()
    NODE_DRAINED = auto()
    NETWORK_PARTITION = auto()
    ANTI_AFFINITY = auto()
    RESERVATION_CONFLICT = auto()
    MAX_JOB_PER_USER = auto()


@dataclass
class ConstraintViolation:
    type: ViolationType
    node_id: str
    job_id: str
    message: str
    severity: str = "hard"  # "hard" or "soft"


@dataclass
class PlacementContext:
    node_id: str
    job_id: str
    requested_gpu_mem_gb: float
    requested_cpu_mem_gb: float
    partition: str
    required_nodes: tuple[str, ...]  # anti-affinity group
    reservation_id: str | None = None


class ConstraintEngine:
    def __init__(self, config: dict | None = None):
        self.config = config or {}
        # Node capacities (from cluster state)
        self._node_gpu_mem: dict[str, float] = {}
        self._node_cpu_mem: dict[str, float] = {}
        self._node_gpus_total: dict[str, int] = {}
        self._node_state: dict[str, str] = {}  # up / drained / down
        self._node_partitions: dict[str, list[str]] = {}
        # Current allocation snapshot
        self._allocated_gpu_mem: dict[str, float] = {}
        self._allocated_cpu_mem: dict[str, float] = {}
        # Partition config
        self._partition_nodes: dict[str, list[str]] = {}
        # Limits
        self._max_jobs_per_user: int = self.config.get("max_jobs_per_user", 200)
        self._max_gpu_per_partition: dict[str, int] = {}

    def load_cluster_state(self, state: dict) -> None:
        """Load cluster topology from state dict."""
        nodes = state.get("nodes", {})
        for node_id, node_info in nodes.items():
            self._node_gpu_mem[node_id] = node_info.get("gpu_mem_gb", 8.0)
            self._node_cpu_mem[node_id] = node_info.get("cpu_mem_gb", 32.0)
            self._node_gpus_total[node_id] = node_info.get("gpus", 1)
            self._node_state[node_id] = node_info.get("state", "up")
            self._node_partitions[node_id] = node_info.get("partitions", ["default"])
        for part in state.get("partitions", {}).values():
            self._partition_nodes[part["name"]] = part.get("nodes", [])
        # Reset allocations
        self._allocated_gpu_mem = dict.fromkeys(nodes, 0.0)
        self._allocated_cpu_mem = dict.fromkeys(nodes, 0.0)

    def set_allocations(self, allocations: list[dict]) -> None:
        """Set current allocations from job list. Call before validate()."""
        self._allocated_gpu_mem = dict.fromkeys(self._node_gpu_mem, 0.0)
        self._allocated_cpu_mem = dict.fromkeys(self._node_cpu_mem, 0.0)
        for job in allocations:
            nid = job["node_id"]
            self._allocated_gpu_mem[nid] = self._allocated_gpu_mem.get(
                nid, 0
            ) + job.get("gpu_mem_gb", 0)
            self._allocated_cpu_mem[nid] = self._allocated_cpu_mem.get(
                nid, 0
            ) + job.get("cpu_mem_gb", 0)

    def validate(self, placement: PlacementContext) -> list[ConstraintViolation]:
        """
        Validate a single placement (node_id + job_id).
        Returns list of violations (empty = valid).
        """
        violations = []
        nid = placement.node_id
        # --- HARD CONSTRAINTS ---
        # 1. Node state
        if self._node_state.get(nid, "up") != "up":
            violations.append(
                ConstraintViolation(
                    ViolationType.NODE_DRAINED,
                    nid,
                    placement.job_id,
                    f"Node {nid} is {self._node_state[nid]}, not up",
                )
            )
        # 2. Partition match
        if placement.partition not in self._node_partitions.get(nid, []):
            violations.append(
                ConstraintViolation(
                    ViolationType.PARTITION_OFFLINE,
                    nid,
                    placement.job_id,
                    f"Node {nid} not in partition {placement.partition}",
                )
            )
        # 3. GPU memory capacity
        avail_gpu = self._node_gpu_mem.get(nid, 0) - self._allocated_gpu_mem.get(nid, 0)
        if placement.requested_gpu_mem_gb > avail_gpu - 0.001:
            violations.append(
                ConstraintViolation(
                    ViolationType.GPU_MEM_EXCEEDED,
                    nid,
                    placement.job_id,
                    f"GPU mem {placement.requested_gpu_mem_gb}GB > available {avail_gpu:.1f}GB",
                )
            )
        # 4. CPU memory capacity
        avail_cpu = self._node_cpu_mem.get(nid, 0) - self._allocated_cpu_mem.get(nid, 0)
        if placement.requested_cpu_mem_gb > avail_cpu - 0.001:
            violations.append(
                ConstraintViolation(
                    ViolationType.CPU_MEM_EXCEEDED,
                    nid,
                    placement.job_id,
                    f"CPU mem {placement.requested_cpu_mem_gb}GB > available {avail_cpu:.1f}GB",
                )
            )
        # 5. Network partition (check if node isolated)
        if self._is_node_partitioned(nid):
            violations.append(
                ConstraintViolation(
                    ViolationType.NETWORK_PARTITION,
                    nid,
                    placement.job_id,
                    f"Node {nid} is network-partitioned",
                )
            )
        return violations

    def validate_batch(
        self, placements: list[PlacementContext]
    ) -> dict[str, list[ConstraintViolation]]:
        """Validate all placements, return {job_id: violations}."""
        results = {}
        for p in placements:
            v = self.validate(p)
            if v:
                results[p.job_id] = v
        return results

    def get_feasible_nodes(
        self, job: dict, forbidden_nodes: set[str] | None = None
    ) -> list[str]:
        """Return list of nodes that can satisfy this job (hard constraints only)."""
        forbidden = forbidden_nodes or set()
        feasible = []
        for nid in self._node_gpu_mem:
            if nid in forbidden:
                continue
            ctx = PlacementContext(
                node_id=nid,
                job_id=job.get("id", "?"),
                requested_gpu_mem_gb=job.get("gpu_mem_gb", 8.0),
                requested_cpu_mem_gb=job.get("cpu_mem_gb", 0),
                partition=job.get("partition", "default"),
                required_nodes=job.get("anti_affinity_nodes", ()),
                reservation_id=job.get("reservation_id"),
            )
            if not self.validate(ctx):
                feasible.append(nid)
        return feasible

    def _is_node_partitioned(self, node_id: str) -> bool:
        """Check if node has lost connectivity to mesh."""
        # Simple: check if node has wireguard peers in up state
        # Placeholder: real impl would query network state
        return False

    def is_feasible(self, placements: list[PlacementContext]) -> bool:
        """True if ALL placements satisfy hard constraints."""
        return all(not self.validate(p) for p in placements)
