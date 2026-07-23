"""
plan_reality_comparator.py — v10.0 Reality Alignment Layer

Binds a PlannedDAG (from SemanticPlanner) to an ExecutionTrace (from Executor)
producing a causally-aligned comparison record.

This is the bridge: planner output ↔ execution reality.

Invariant:
  Every execution must be paired with its originating plan.
  Pairing is the basis for drift detection.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from alignment.drift_detector import (
    CompositeDriftReport,
    DriftEngine,
    ExecutionTrace,
    PlannedDAG,
    PlannedNode,
)
from core.deterministic import DeterministicClock, DeterministicUUIDFactory


@dataclass
class NodeMapping:
    """Maps a single planned node to its executed counterpart."""
    planned: PlannedNode
    executed_node_id: str | None   # None = missing (not executed)
    matched: bool                    # True if executed_id is found
    output_hash: str = ""
    error: str = ""
    start_ts_ns: int = 0
    end_ts_ns: int = 0

    @property
    def duration_ms(self) -> float:
        if not self.start_ts_ns or not self.end_ts_ns:
            return 0.0
        return (self.end_ts_ns - self.start_ts_ns) / 1e6

    @property
    def is_missing(self) -> bool:
        return not self.matched


@dataclass
class CausalBinding:
    """
    Causal binding between a planned dependency and its execution.
    Tracks whether the dependency was satisfied before the dependent ran.
    """
    plan_dep: str                    # planned dependency node_id
    dependent_node_id: str          # node that depended on plan_dep
    actual_satisfied_before: bool    # did the dep actually complete first?
    actual_order: int                # execution order of plan_dep (-1 if missing)
    dependent_order: int            # execution order of dependent (-1 if missing)
    causal_respected: bool           # plan_dep executed before dependent
    causal_gap_ms: float             # time gap between dep finish and dependent start

    @property
    def is_causal_violation(self) -> bool:
        """Dependency ran AFTER dependent = causal violation."""
        if self.actual_order < 0 or self.dependent_order < 0:
            return True  # missing dep = violation
        return not self.causal_respected


@dataclass
class PlanRealityBinding:
    """
    Immutable binding record: PlannedDAG ↔ ExecutionTrace.

    Produced once per execution cycle.
    Consumed by DriftEngine for drift analysis.
    """
    binding_id: str                 # UUID
    plan_id: str
    trace_id: str
    dag_hash: str
    created_at_ns: int

    # Node-level mappings
    node_mappings: list[NodeMapping]
    # Causal dependency bindings
    causal_bindings: list[CausalBinding]

    # Plan-level stats
    planned_node_count: int
    executed_node_count: int
    missing_node_count: int
    extra_node_count: int            # executed but not planned

    # Execution quality
    execution_duration_ms: float
    planner_confidence: float

    # Derived flags
    has_causal_violations: bool
    has_missing_nodes: bool
    is_fully_bound: bool            # True iff no missing + no extras

    @property
    def coverage_ratio(self) -> float:
        """Fraction of planned nodes that were executed."""
        if self.planned_node_count == 0:
            return 1.0
        return 1.0 - (self.missing_node_count / self.planned_node_count)

    def causal_violations(self) -> list[CausalBinding]:
        return [b for b in self.causal_bindings if b.is_causal_violation]

    def summary(self) -> str:
        flags = []
        if self.has_causal_violations:
            violations = len(self.causal_violations())
            flags.append(f"causal_violations={violations}")
        if self.has_missing_nodes:
            flags.append(f"missing={self.missing_node_count}")
        if self.extra_node_count > 0:
            flags.append(f"extra={self.extra_node_count}")
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        return (
            f"PlanRealityBinding({self.plan_id[:8]}↔{self.trace_id[:8]})"
            f" coverage={self.coverage_ratio:.2f}"
            f" causal_ok={not self.has_causal_violations}"
            f"{flag_str}"
        )


class PlanRealityComparator:
    """
    Binds SemanticPlanner output (PlannedDAG) to Executor output (ExecutionTrace).

    Algorithm:
      1. Hash-match: same output_hash → direct node binding
      2. Name-match: step_name match → fuzzy binding
      3. Structural match: dependency alignment → confirm binding
      4. Causal ordering: check all planned deps were satisfied

    Produces:
      PlanRealityBinding — immutable record for DriftEngine
    """

    def __init__(self, drift_engine: DriftEngine | None = None):
        self._engine = drift_engine or DriftEngine()

    def bind(
        self,
        planned: PlannedDAG,
        trace: ExecutionTrace,
    ) -> PlanRealityBinding:
        """
        Full binding: plan ↔ execution trace.
        Returns immutable PlanRealityBinding.
        """
        binding_id = DeterministicUUIDFactory.make_id('binding', planned.plan_id, salt='')

        # Step 1: Build execution lookup by node_id and output_hash
        exec_by_id: dict[str, Any] = {}
        exec_by_hash: dict[str, Any] = {}
        for n in trace.nodes:
            exec_by_id[n.node_id] = n
            if n.output_hash:
                exec_by_hash[n.output_hash] = n

        planned_ids = {n.node_id for n in planned.nodes}
        executed_ids = {n.node_id for n in trace.nodes}

        # Step 2: Node mappings
        node_mappings: list[NodeMapping] = []
        for pnode in planned.nodes:
            executed = exec_by_id.get(pnode.node_id)

            if executed:
                mapping = NodeMapping(
                    planned=pnode,
                    executed_node_id=executed.node_id,
                    matched=True,
                    output_hash=executed.output_hash,
                    error=executed.error if not executed.success else "",
                    start_ts_ns=executed.start_ts_ns,
                    end_ts_ns=executed.end_ts_ns,
                )
            else:
                # Fuzzy match by step_name
                fuzzy = self._fuzzy_match(pnode, exec_by_id, exec_by_hash)
                mapping = NodeMapping(
                    planned=pnode,
                    executed_node_id=fuzzy,
                    matched=False,
                )
            node_mappings.append(mapping)

        # Step 3: Causal bindings — check planned deps
        causal_bindings: list[CausalBinding] = []
        exec_order_map = {n.node_id: i for i, n in enumerate(trace.nodes)}
        exec_ts_map = {n.node_id: n.start_ts_ns for n in trace.nodes}

        for pnode in planned.nodes:
            dependent_exec = exec_by_id.get(pnode.node_id)
            if not dependent_exec:
                continue

            dependent_order = exec_order_map.get(pnode.node_id, -1)
            dependent_start = exec_ts_map.get(pnode.node_id, 0)

            for dep_id in pnode.planned_deps:
                dep_exec = exec_by_id.get(dep_id)
                if not dep_exec:
                    causal_bindings.append(CausalBinding(
                        plan_dep=dep_id,
                        dependent_node_id=pnode.node_id,
                        actual_satisfied_before=False,
                        actual_order=-1,
                        dependent_order=dependent_order,
                        causal_respected=False,
                        causal_gap_ms=0.0,
                    ))
                    continue

                dep_order = exec_order_map.get(dep_id, -1)
                dep_end = dep_exec.end_ts_ns if hasattr(dep_exec, 'end_ts_ns') else 0

                causal_respected = dep_order >= 0 and dep_order < dependent_order
                gap_ms = (dependent_start - dep_end) / 1e6 if dep_end else 0.0

                causal_bindings.append(CausalBinding(
                    plan_dep=dep_id,
                    dependent_node_id=pnode.node_id,
                    actual_satisfied_before=causal_respected,
                    actual_order=dep_order,
                    dependent_order=dependent_order,
                    causal_respected=causal_respected,
                    causal_gap_ms=gap_ms,
                ))

        # Step 4: Compute flags
        missing = [m for m in node_mappings if m.is_missing]
        extra_ids = executed_ids - planned_ids
        violations = [b for b in causal_bindings if b.is_causal_violation]

        duration_ms = trace.total_duration_ms

        binding = PlanRealityBinding(
            binding_id=binding_id,
            plan_id=planned.plan_id,
            trace_id=trace.trace_id,
            dag_hash=trace.dag_hash,
            created_at_ns=DeterministicClock.get_tick_ns(),
            node_mappings=node_mappings,
            causal_bindings=causal_bindings,
            planned_node_count=len(planned.nodes),
            executed_node_count=len(trace.nodes),
            missing_node_count=len(missing),
            extra_node_count=len(extra_ids),
            execution_duration_ms=duration_ms,
            planner_confidence=planned.confidence,
            has_causal_violations=len(violations) > 0,
            has_missing_nodes=len(missing) > 0,
            is_fully_bound=(len(missing) == 0 and len(extra_ids) == 0),
        )

        return binding

    def _fuzzy_match(
        self,
        pnode: PlannedNode,
        by_id: dict[str, Any],
        by_hash: dict[str, Any],
    ) -> str | None:
        """
        Attempt fuzzy match: by step_name or by partial tool match.
        Returns matched node_id or None.
        """
        # Try by output_hash if we have one
        pnode_hash = self._hash_node(pnode)
        if pnode_hash in by_hash:
            return by_hash[pnode_hash]

        # Try name similarity
        for exec_id, enode in by_id.items():
            if hasattr(enode, 'step_name') and enode.step_name == pnode.step_name:
                return exec_id
            if hasattr(enode, 'tool') and enode.tool == pnode.tool:
                return exec_id

        return None

    def _hash_node(self, node: PlannedNode) -> str:
        data = f"{node.node_id}:{node.step_name}:{node.tool}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def compare_and_report(
        self,
        planned: PlannedDAG,
        trace: ExecutionTrace,
    ) -> tuple[PlanRealityBinding, CompositeDriftReport]:
        """
        Full compare pipeline: bind → analyze → report.
        Returns (binding, drift_report) tuple.
        """
        binding = self.bind(planned, trace)
        report = self._engine.analyze(trace, planned)
        return binding, report
