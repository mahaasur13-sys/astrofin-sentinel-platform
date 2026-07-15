#!/usr/bin/env python3
"""
GovernanceGate — L8/L9 Mandatory Execution Barrier

Decision states: APPROVED | REJECTED | ESCALATED
Pre-execution: validates constraints + risk scores
Mid-execution: kill switch (interrupt on threshold breach)
Post-execution: audit trail generation
"""
from __future__ import annotations
import uuid
from enum import Enum

class Decision(Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"

class GovernanceGate:
    """
    L8 + L9 mandatory gate. NO execution without approval.
    Every DAG passes through here before hitting the scheduler.
    """

    def __init__(self):
        self._decision_log = []

    def pre_check(self, dag: dict, context: dict) -> tuple[Decision, str]:
        dag_id = dag["dag_id"]
        risk_score = context.get("risk_score", 0.0)
        max_risk = dag.get("metadata", {}).get("constraints", {}).get("max_risk", 1.0)
        if risk_score > max_risk:
            decision = Decision.REJECTED
            reason = f"risk_score {risk_score} > max_risk {max_risk}"
        elif risk_score > 0.5:
            decision = Decision.ESCALATED
            reason = f"risk_score {risk_score} requires human review"
        else:
            decision = Decision.APPROVED
            reason = "all constraints satisfied"
        entry = {"dag_id": dag_id, "decision": decision.value, "reason": reason, "ts": str(uuid.uuid4())}
        self._decision_log.append(entry)
        return decision, reason

    def mid_check(self, dag_id: str, context: dict) -> bool:
        risk = context.get("risk_score", 0.0)
        if risk > 0.9:
            return False  # KILL
        return True  # CONTINUE

    def post_check(self, dag_id: str, outcome: dict) -> dict:
        return {
            "dag_id": dag_id, "outcome": outcome.get("status", "unknown"),
            "nodes_executed": outcome.get("nodes_executed", 0),
            "audit_id": str(uuid.uuid4())[:12],
        }

if __name__ == "__main__":
    gate = GovernanceGate()
    d, r = gate.pre_check({"dag_id": "test", "metadata": {"constraints": {"max_risk": 0.25}}}, {"risk_score": 0.1})
    print(f"Decision: {d.value}, Reason: {r}")
