#!/usr/bin/env python3
"""
Admission Controller — K8s-style validating webhook.
All decisions from v6+v7 MUST pass through here.
POST /admit → SafetyKernel → admit / reject / degrade.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import hashlib


class AdmissionController:
    """
    K8s-style admission controller.
    All decisions flow: decision → constraint → policy_verifier → safety_kernel → admit/reject/degrade.
    """

    def __init__(
        self,
        safety_kernel,        # SafetyKernel instance
        constraint_compiler,   # ConstraintCompiler instance
        policy_verifier,       # PolicyVerifier instance
    ):
        self.safety_kernel = safety_kernel
        self.constraint_compiler = constraint_compiler
        self.policy_verifier = policy_verifier
        self._request_log: list[dict] = []

    def admit(self, request: dict) -> dict:
        """
        Primary admission endpoint.
        Request:
            {
                "decision": {...},
                "context": {...}
            }
        Response:
            {
                "status": "ADMITTED | REJECTED | DEGRADED",
                "reason": "...",
                "risk_score": 0.XX,
                "incident_id": "..." (if rejected)
            }
        """
        decision = request.get("decision", {})
        context = self._build_context(request.get("context", {}))

        # Step 1: compile constraints if needed
        compiled = self.constraint_compiler.validate(decision, context)
        if compiled.get("violations"):
            return self._reject(
                decision,
                "constraint_compilation_failed",
                violations=compiled["violations"],
            )

        # Step 2: policy verification
        policy_ok, reason = self.policy_verifier.verify(decision)
        if not policy_ok:
            return self._reject(decision, reason, violations=["policy_verification_failed"])

        # Step 3: safety kernel gate
        result = self.safety_kernel.admit(decision, context)

        # Log
        self._log_request(request, result)

        return {
            "status": result.status.value,
            "reason": result.reason,
            "risk_score": result.risk_score,
            "violations": result.violations,
            "approved_by": result.approved_by,
        }

    def _build_context(self, raw_context: dict) -> "DecisionContext":
        """Build DecisionContext from raw request."""
        from v8.safety_kernel.engine import DecisionContext
        return DecisionContext(
            cluster_state=raw_context.get("cluster_state", {}),
            ml_predictions=raw_context.get("ml_predictions", {}),
            policy_hash=raw_context.get("policy_hash", ""),
            optimizer_output=raw_context.get("optimizer_output", {}),
            v7_ensemble_votes=raw_context.get("v7_ensemble_votes", {}),
            risk_score=raw_context.get("risk_score", 0.0),
        )

    def _reject(self, decision: dict, reason: str, violations: list[str]) -> dict:
        incident_id = hashlib.sha256(f"{reason}{decision}".encode()).hexdigest()[:12]
        return {
            "status": "REJECTED",
            "reason": reason,
            "risk_score": 1.0,
            "violations": violations,
            "incident_id": incident_id,
        }

    def _log_request(self, request: dict, result) -> None:
        self._request_log.append({
            "decision": request.get("decision", {}).get("id", "unknown"),
            "status": result.status.value,
            "risk_score": result.risk_score,
        })

    def get_rejection_rate(self) -> float:
        if not self._request_log:
            return 0.0
        rejected = sum(1 for r in self._request_log if r["status"] == "REJECTED")
        return rejected / len(self._request_log)
