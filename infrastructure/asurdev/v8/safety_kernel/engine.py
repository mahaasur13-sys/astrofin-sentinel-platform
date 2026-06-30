#!/usr/bin/env python3
"""
Safety Kernel — final admission gate for all decisions.
v8: admit / reject / downgrade decisions from v6+v7.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class DecisionStatus(Enum):
    ADMITTED = "ADMITTED"
    REJECTED = "REJECTED"
    DEGRADED = "DEGRADED"
    ROLLBACK_L1 = "ROLLBACK_L1"
    ROLLBACK_L2 = "ROLLBACK_L2"
    ROLLBACK_L3 = "ROLLBACK_L3"


# Immutable HARD constraints — cannot be overridden
IMMUTABLE_CONSTRAINTS = {
    "no_deadlock",
    "no_resource_overcommit",
    "no_node_starvation",
    "max_p99_latency",
    "failure_rate_ceiling",
    "no_orphaned_jobs",
    "min_replication_factor",
}


@dataclass
class DecisionContext:
    """Environment snapshot at decision time."""
    cluster_state: dict
    ml_predictions: dict
    policy_hash: str
    optimizer_output: dict
    v7_ensemble_votes: dict
    risk_score: float


@dataclass
class AdmissionResult:
    status: DecisionStatus
    reason: Optional[str] = None
    risk_score: float = 0.0
    violations: list[str] = field(default_factory=list)
    approved_by: Optional[str] = None


class SafetyKernel:
    """
    Final admission gate — runs BEFORE every decision executes.
    
    Pipeline:
        1. constraint_engine.validate(decision)
        2. policy_verifier.check(decision)
        3. risk_score(decision, context) > RISK_LIMIT
        4. admit / reject / downgrade
    """

    def __init__(
        self,
        risk_limit: float = 0.8,
        constraint_engine=None,   # injected
        policy_verifier=None,      # injected
        rollback_engine=None,       # injected
        incident_manager=None,     # injected
    ):
        self.risk_limit = risk_limit
        self.constraint_engine = constraint_engine
        self.policy_verifier = policy_verifier
        self.rollback_engine = rollback_engine
        self.incident_manager = incident_manager
        self._admission_log: list[AdmissionResult] = []

    def admit(self, decision: dict, context: DecisionContext) -> AdmissionResult:
        """
        Primary admission function.
        Returns: AdmissionResult with status + violations.
        """
        # STEP 1: constraint validation
        violations = self.constraint_engine.validate(decision, context)
        if violations:
            incident = self.incident_manager.create(
                trigger_type="constraint_violation",
                severity=self._severity_from_violations(violations),
                details={"decision": decision, "violations": violations},
            )
            return AdmissionResult(
                status=DecisionStatus.REJECTED,
                reason="constraint_violation",
                risk_score=1.0,
                violations=violations,
            )

        # STEP 2: policy verification (static + regret bound)
        policy_ok, policy_reason = self.policy_verifier.verify(decision)
        if not policy_ok:
            return AdmissionResult(
                status=DecisionStatus.REJECTED,
                reason=policy_reason,
                risk_score=0.95,
                violations=["policy_verification_failed"],
            )

        # STEP 3: risk scoring
        risk = self._compute_risk_score(decision, context)
        if risk > self.risk_limit:
            # Try degrade instead of hard reject
            degraded = self._try_degrade(decision, context, risk)
            if degraded:
                return degraded
            incident = self.incident_manager.create(
                trigger_type="risk_threshold_exceeded",
                severity=0.8,
                details={"decision": decision, "risk_score": risk},
            )
            return AdmissionResult(
                status=DecisionStatus.REJECTED,
                reason="risk_above_limit",
                risk_score=risk,
                violations=["risk_threshold_exceeded"],
            )

        # STEP 4: admission
        result = AdmissionResult(
            status=DecisionStatus.ADMITTED,
            risk_score=risk,
            approved_by="safety_kernel",
        )
        self._admission_log.append(result)
        return result

    def _compute_risk_score(self, decision: dict, context: DecisionContext) -> float:
        """Compute composite risk score [0, 1]."""
        scores = []

        # ML prediction risk
        if context.ml_predictions.get("failure_prob") is not None:
            scores.append(context.ml_predictions["failure_prob"])

        # v7 ensemble disagreement risk
        votes = list(context.v7_ensemble_votes.values())
        if len(votes) >= 2:
            disagreement = 1 - sum(votes) / len(votes) / max(votes) if max(votes) > 0 else 1
            scores.append(disagreement)

        # Resource contention risk
        scores.append(context.cluster_state.get("contention_score", 0))

        return min(scores) if scores else 0.0

    def _try_degrade(
        self, decision: dict, context: DecisionContext, risk: float
    ) -> Optional[AdmissionResult]:
        """Attempt degraded admission instead of hard reject."""
        # Downgrade GPU job → CPU-only
        if decision.get("requires_gpu") and not decision.get("gpu_compatible"):
            decision["requires_gpu"] = False
            decision["degraded"] = True
            return AdmissionResult(
                status=DecisionStatus.DEGRADED,
                reason="gpu_job_degraded_to_cpu",
                risk_score=risk * 0.5,
                approved_by="safety_kernel.degrade",
            )
        return None

    def _severity_from_violations(self, violations: list[str]) -> float:
        """Map violations to severity score."""
        critical = {"no_deadlock", "no_resource_overcommit", "failure_rate_ceiling"}
        if any(v in critical for v in violations):
            return 1.0
        return 0.5

    def get_admission_rate(self) -> float:
        """Return fraction of admitted decisions."""
        if not self._admission_log:
            return 0.0
        admitted = sum(1 for r in self._admission_log if r.status == DecisionStatus.ADMITTED)
        return admitted / len(self._admission_log)
