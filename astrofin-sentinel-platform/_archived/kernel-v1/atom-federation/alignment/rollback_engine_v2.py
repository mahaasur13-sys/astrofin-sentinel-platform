"""
rollback_engine_v2.py — v10.0 Reality Alignment Layer

RollbackEngine v2: Branching causal rollback.

Key architectural invariant (preserved):
  Events are NEVER deleted. Rollback introduces a new causal branch
  that supersedes the drifted plan, preserving full audit trail.

Rollback types:
  partial   — invalidate specific nodes, re-execute only failed subgraph
  full      — checkpoint restore + re-plan from last stable state
  shadow    — run drifted plan in shadow mode alongside corrected plan
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from alignment.drift_detector import (
    CompositeDriftReport,
    DriftSeverity,
)
from alignment.plan_reality_comparator import PlanRealityBinding
from core.deterministic import DeterministicUUIDFactory


class RollbackType(Enum):
    NONE = "none"
    SHADOW = "shadow"
    PARTIAL = "partial"
    FULL = "full"


@dataclass
class RollbackScope:
    rollback_id: str
    plan_id: str
    trace_id: str
    rollback_type: RollbackType
    invalidate_nodes: list[str]
    rederive_edges: list[tuple[str, str]]
    checkpoint_before: bool
    checkpoint_id: str = ""
    branch_id: str = ""
    parent_trace_id: str = ""

    @property
    def is_noop(self) -> bool:
        return self.rollback_type == RollbackType.NONE

    @property
    def is_full(self) -> bool:
        return self.rollback_type == RollbackType.FULL


@dataclass
class RollbackPlan:
    rollback_scope: RollbackScope
    recovery_steps: list[str]
    estimated_retry_cost_ms: float
    can_self_heal: bool
    rollback_confidence: float


@dataclass
class RollbackResult:
    rollback_id: str
    rollback_type: RollbackType
    applied: bool
    new_trace_id: str
    new_branch_id: str
    previous_trace_id: str
    recovery_duration_ms: float
    drift_score_before: float
    drift_score_after: float | None
    is_stable: bool
    messages: list[str]


class RollbackDecider:
    def decide(
        self,
        binding: PlanRealityBinding,
        report: CompositeDriftReport,
    ) -> RollbackScope:
        rollback_id = DeterministicUUIDFactory.make_id('rollback', binding.plan_id, salt='')
        severity = report.severity

        if severity == DriftSeverity.OK:
            return self._noop_scope(rollback_id, binding, report)
        if severity == DriftSeverity.DEGRADED:
            return self._shadow_scope(rollback_id, binding, report)
        if severity == DriftSeverity.CRITICAL:
            if report.layer3.is_diverged:
                return self._full_scope(rollback_id, binding, report)
            return self._partial_scope(rollback_id, binding, report)
        return self._full_scope(rollback_id, binding, report)

    def _noop_scope(self, rid: str, b: PlanRealityBinding, r: CompositeDriftReport) -> RollbackScope:
        return RollbackScope(rollback_id=rid, plan_id=b.plan_id, trace_id=b.trace_id,
                             rollback_type=RollbackType.NONE, invalidate_nodes=[],
                             rederive_edges=[], checkpoint_before=False)

    def _shadow_scope(self, rid: str, b: PlanRealityBinding, r: CompositeDriftReport) -> RollbackScope:
        return RollbackScope(rollback_id=rid, plan_id=b.plan_id, trace_id=b.trace_id,
                             rollback_type=RollbackType.SHADOW, invalidate_nodes=[],
                             rederive_edges=[], checkpoint_before=True)

    def _partial_scope(self, rid: str, b: PlanRealityBinding, r: CompositeDriftReport) -> RollbackScope:
        invalidate = list(dict.fromkeys(
            r.rollback_target_nodes + b.causal_violations()
        ))
        return RollbackScope(rollback_id=rid, plan_id=b.plan_id, trace_id=b.trace_id,
                             rollback_type=RollbackType.PARTIAL, invalidate_nodes=invalidate[:10],
                             rederive_edges=[], checkpoint_before=True)

    def _full_scope(
        self,
        rollback_id: str,
        binding: PlanRealityBinding,
        report: CompositeDriftReport,
    ) -> RollbackScope:
        # Full: invalidate all nodes + new causal branch
        all_nodes = [m.planned.node_id for m in binding.node_mappings]
        branch_id = DeterministicUUIDFactory.make_id('rollback_branch', binding.plan_id, salt='')
        return RollbackScope(rollback_id=rollback_id, plan_id=binding.plan_id, trace_id=binding.trace_id,
                             rollback_type=RollbackType.FULL, invalidate_nodes=all_nodes,
                             rederive_edges=[], checkpoint_before=True,
                             checkpoint_id="", branch_id=branch_id, parent_trace_id=binding.trace_id)


class RollbackPlanner:
    def plan(self, scope: RollbackScope, binding: PlanRealityBinding) -> RollbackPlan:
        if scope.is_noop:
            return RollbackPlan(scope, ["No rollback — drift is OK"], 0.0, True, 1.0)
        if scope.rollback_type == RollbackType.SHADOW:
            return RollbackPlan(scope, [
                "1. Mark current plan as SHADOW (observe-only)",
                "2. Spawn corrected plan in shadow mode",
                "3. Compare outcomes: if shadow.drift < original → promote",
                "4. Otherwise: keep original plan",
            ], 50.0, True, 0.70)
        if scope.rollback_type == RollbackType.PARTIAL:
            n = len(scope.invalidate_nodes)
            return RollbackPlan(scope, [
                f"1. Invalidate {n} drifted nodes",
                "2. Re-derive dependency edges for subgraph",
                "3. Re-execute frontier only (not full DAG)",
                "4. Record new trace + re-run drift detection",
            ], n * 100.0, True, 0.80)
        # FULL
        n = len(scope.invalidate_nodes)
        return RollbackPlan(scope, [
            f"1. Create checkpoint (branch={scope.branch_id})",
            f"2. Invalidate all {n} nodes",
            "3. Semantic re-plan from last stable epoch",
            "4. Execute new plan + emit COMPENSATION events",
            "5. Verify: new drift_score < 0.20 → commit branch",
        ], n * 150.0, False, 0.60)


class RollbackExecutor:
    def __init__(self):
        self._history: list[RollbackResult] = []

    def apply(self, plan: RollbackPlan, binding: PlanRealityBinding,
              drift_before: float) -> RollbackResult:
        if plan.rollback_scope.is_noop:
            return RollbackResult(
                rollback_id=plan.rollback_scope.rollback_id,
                rollback_type=plan.rollback_scope.rollback_type,
                applied=False, new_trace_id="", new_branch_id="",
                previous_trace_id=binding.trace_id,
                recovery_duration_ms=0.0, drift_score_before=drift_before,
                drift_score_after=None, is_stable=True,
                messages=["No rollback — drift is OK"],
            )
        branch_id = plan.rollback_scope.branch_id or DeterministicUUIDFactory.make_id('rb_branch', binding.plan_id, salt='')
        new_trace_id = DeterministicUUIDFactory.make_id('trace', binding.plan_id, salt='')[:12]
        result = RollbackResult(
            rollback_id=plan.rollback_scope.rollback_id,
            rollback_type=plan.rollback_scope.rollback_type,
            applied=True, new_trace_id=new_trace_id, new_branch_id=branch_id,
            previous_trace_id=binding.trace_id,
            recovery_duration_ms=plan.estimated_retry_cost_ms,
            drift_score_before=drift_before, drift_score_after=None,
            is_stable=False,
            messages=[f"Rollback {plan.rollback_scope.rollback_type.value} applied"],
        )
        self._history.append(result)
        return result

    def history(self) -> list[RollbackResult]:
        return list(self._history)
