"""
plan_graph.py — v8.0 Phase 2
Temporal planning DAG with persistence-grounded evaluation.

goal → historical_outcomes → stability_aware_score → plan_DAG → replan_on_drift
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PlanNode:
    node_id: str
    action: str
    payload: dict[str, Any]
    source: str
    priority: float
    proof_verdict: bool
    temporal_confidence: float
    coherence_at_plan: float
    tick: int
    parent_ids: list[str] = field(default_factory=list)
    children_ids: list[str] = field(default_factory=list)
    status: str = "pending"  # pending / executing / done / skipped


@dataclass
class ExecutionSnapshot:
    tick: int
    node_id: str
    action: str
    actual_outcome: float | None
    coherence_snapshot: float
    proof_verdict: bool


@dataclass
class PlanGraphConfig:
    max_nodes: int = 50
    max_snapshots: int = 200
    coherence_threshold: float = 0.70
    require_proof: bool = True


class PlanGraph:
    """
    Temporal planning graph (DAG) with persistence-grounded scoring.

    Each plan generates a DAG of PlanNodes.
    Nodes are scored using IntegrationReport from PersistenceBridge:
      - enriched_coherence (from coherence layer)
      - stability (from stability_ledger)
      - gain quality (from gain scheduler)
      - weight quality (from proof feedback)

    Execution snapshots are recorded and compared against plan-time scores.
    ReplanTrigger threshold checked after each tick.

    Invariant (v8.0):
      planning = f(current_state, persistence_history, stability_ledger, proof_feedback)
    """

    def __init__(
        self,
        config: PlanGraphConfig | None = None,
    ) -> None:
        self.config = config or PlanGraphConfig()
        self._nodes: dict[str, PlanNode] = {}
        self._root_ids: list[str] = []
        self._plan_counter = 0
        self._node_counter = 0
        self._snapshots: deque[ExecutionSnapshot] = deque(maxlen=self.config.max_snapshots)
        self._active_plan_id: str | None = None
        self._plan_time_coherence: float = 0.0

    # ─── plan construction ────────────────────────────────────────────────────

    def begin_plan(
        self,
        coherence_at_plan: float,
        tick: int,
    ) -> str:
        """Start a new plan. Returns plan_id."""
        self._plan_counter += 1
        self._node_counter = 0
        plan_id = f"plan_{self._plan_counter}"
        self._active_plan_id = plan_id
        self._root_ids.clear()
        self._plan_time_coherence = coherence_at_plan
        return plan_id

    def add_node(
        self,
        plan_id: str,
        action: str,
        payload: dict[str, Any],
        source: str,
        priority: float,
        proof_verdict: bool,
        temporal_confidence: float,
        parent_ids: list[str] | None = None,
    ) -> str:
        """Add a node to the active plan. Returns node_id."""
        if plan_id != self._active_plan_id:
            raise ValueError(f"Plan {plan_id} is not active")
        if len(self._nodes) >= self.config.max_nodes:
            raise RuntimeError(f"Max nodes ({self.config.max_nodes}) reached")

        self._node_counter += 1
        node_id = f"{plan_id}_node_{self._node_counter}"
        parents = parent_ids or []

        node = PlanNode(
            node_id=node_id,
            action=action,
            payload=payload,
            source=source,
            priority=priority,
            proof_verdict=proof_verdict,
            temporal_confidence=temporal_confidence,
            coherence_at_plan=self._plan_time_coherence,
            tick=time.time_ns(),
            parent_ids=parents,
            children_ids=[],
        )
        self._nodes[node_id] = node

        for pid in parents:
            if pid in self._nodes:
                self._nodes[pid].children_ids.append(node_id)

        if not parents:
            self._root_ids.append(node_id)

        return node_id

    def finalize_plan(self) -> list[str]:
        """Return ordered node_ids (topologically sorted)."""
        return self.topological_sort()

    # ─── execution ──────────────────────────────────────────────────────────

    def snapshot(
        self,
        node_id: str,
        actual_outcome: float | None,
        coherence_snapshot: float,
        proof_verdict: bool,
    ) -> None:
        """Record execution result for a node."""
        if node_id not in self._nodes:
            return
        tick = self._nodes[node_id].tick
        self._snapshots.append(ExecutionSnapshot(
            tick=tick,
            node_id=node_id,
            action=self._nodes[node_id].action,
            actual_outcome=actual_outcome,
            coherence_snapshot=coherence_snapshot,
            proof_verdict=proof_verdict,
        ))
        self._nodes[node_id].status = "done"

    def node_status(self, node_id: str) -> str:
        return self._nodes.get(node_id, PlanNode(
            node_id="", action="", payload={}, source="",
            priority=0.0, proof_verdict=False, temporal_confidence=0.0,
            coherence_at_plan=0.0, tick=0,
        )).status

    def pending_nodes(self) -> list[PlanNode]:
        return [n for n in self._nodes.values() if n.status == "pending"]

    def coherence_deviation(self) -> float:
        """
        Max deviation between plan-time coherence and snapshot coherence.
        Used by Replanner to detect coherence drift.
        """
        if not self._snapshots:
            return 0.0
        deviations = [
            abs(self._nodes[s.node_id].coherence_at_plan - s.coherence_snapshot)
            for s in self._snapshots
            if s.node_id in self._nodes
        ]
        return max(deviations) if deviations else 0.0

    # ─── DAG utilities ────────────────────────────────────────────────────────

    def topological_sort(self) -> list[str]:
        """Return node_ids in topological order (roots first)."""
        in_degree: dict[str, int] = {nid: len(node.parent_ids) for nid, node in self._nodes.items()}
        queue = deque([nid for nid, d in in_degree.items() if d == 0])
        sorted_ids: list[str] = []

        while queue:
            nid = queue.popleft()
            sorted_ids.append(nid)
            for child in self._nodes[nid].children_ids:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)

        if len(sorted_ids) != len(self._nodes):
            raise RuntimeError("Cycle detected in plan graph")
        return sorted_ids

    def ready_nodes(self) -> list[PlanNode]:
        """Nodes with all parents done or no parents (roots)."""
        done = {nid for nid, n in self._nodes.items() if n.status == "done"}
        ready: list[PlanNode] = []
        for nid, node in self._nodes.items():
            if node.status != "pending":
                continue
            if not node.parent_ids:
                ready.append(node)
            elif all(p in done for p in node.parent_ids):
                ready.append(node)
        return ready

    # ─── introspection ────────────────────────────────────────────────────────

    def node(self, node_id: str) -> PlanNode | None:
        return self._nodes.get(node_id)

    @property
    def plan_time_coherence(self) -> float:
        return self._plan_time_coherence

    @property
    def active_plan_id(self) -> str | None:
        return self._active_plan_id

    @property
    def snapshot_count(self) -> int:
        return len(self._snapshots)

    @property
    def node_count(self) -> int:
        return len(self._nodes)
