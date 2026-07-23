#!/usr/bin/env python3
"""
L9 EBL — Execution Boundary Gate
All infra actions MUST pass through this gate.
"""
import time
import uuid
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from l9_ebl.capabilities.registry import (
    ExecutionContext, Capability, CapabilityDenied, enforce, enforce_any
)

class ActionResult(Enum):
    ALLOW = auto()
    DENY = auto()
    REDIRECT = auto()
    ESCALATE = auto()

@dataclass
class GateDecision:
    action: ActionResult
    trace_id: str
    reason: str
    enforced_at: str = field(default_factory=lambda: time.time_ns())
    redirect_target: Optional[str] = None
    escalated_to: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action.name,
            "trace_id": self.trace_id,
            "reason": self.reason,
            "enforced_at_ns": self.enforced_at,
            "redirect_target": self.redirect_target,
            "escalated_to": self.escalated_to
        }

class ExecutionGate:
    def __init__(self, capability_registry, policy_compiler, constraint_graph):
        self.cr = capability_registry
        self.pc = policy_compiler
        self.cg = constraint_graph
        self.audit_log: List[GateDecision] = []
        self.deny_count: Dict[str, int] = {}
        self.escalation_threshold = 3

    def check(self, ctx: ExecutionContext, action: str, params: Dict[str, Any]) -> GateDecision:
        trace_id = ctx.trace_id
        rule = self.cg.get_guard(action)

        if not rule:
            decision = GateDecision(
                action=ActionResult.DENY,
                trace_id=trace_id,
                reason=f"No guard rule for action={action}"
            )
            self._log_decision(decision)
            return decision

        violations = rule.validate(params)
        if violations:
            decision = GateDecision(
                action=ActionResult.DENY,
                trace_id=trace_id,
                reason=f"Constraint violations: {violations}"
            )
            self._log_decision(decision)
            return decision

        if self.deny_count.get(action, 0) >= self.escalation_threshold:
            decision = GateDecision(
                action=ActionResult.ESCALATE,
                trace_id=trace_id,
                reason=f"Escalation threshold reached for {action}",
                escalated_to="governance_kernel"
            )
            self._log_decision(decision)
            return decision

        decision = GateDecision(
            action=ActionResult.ALLOW,
            trace_id=trace_id,
            reason="All guards passed"
        )
        self._log_decision(decision)
        return decision

    def _log_decision(self, decision: GateDecision) -> None:
        self.audit_log.append(decision)
        if decision.action == ActionResult.DENY:
            reason = decision.reason.split(":")[0].strip()
            self.deny_count[reason] = self.deny_count.get(reason, 0) + 1

    def audit_summary(self) -> Dict[str, Any]:
        return {
            "total_checks": len(self.audit_log),
            "deny_count": self.deny_count,
            "escalations": sum(1 for d in self.audit_log if d.action == ActionResult.ESCALATE)
        }
