"""
SBS Runtime Integration v5.2 — ENFORCED MODE.

Transforms SBS from audit system → runtime enforcement layer.
SBS hooks are inserted into critical execution points:
    INPUT → DRL → CCL → SBS_ENFORCE → F2 → SBS_ENFORCE → EXECUTE → SBS_ENFORCE → DESC

Usage
-----
    from sbs.runtime import SBSRuntimeEnforcer, InvariantViolation, SBS_MODE

    enforcer = SBSRuntimeEnforcer(spec, engine, mode=SBS_MODE.ENFORCED)
    enforcer.enforce("post_quorum", state)
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sbs.boundary_spec import SystemBoundarySpec
    from sbs.global_invariant_engine import GlobalInvariantEngine

__all__ = [
    "SBS_MODE",
    "InvariantViolation",
    "ViolationPolicy",
    "ExecutionStage",
    "SBSRuntimeEnforcer",
]


# ── SBS_MODE (plain class — avoids Flag/auto bug in Python 3.12.1) ─────────────

class _SBS_MODE_TYPE:
    """SBS enforcement mode — controls how invariants are applied."""
    OFF = 0       # SBS disabled; no overhead
    AUDIT = 1     # Async validation; log but do not block
    ENFORCED = 2  # Synchronous enforcement; block on violation

SBS_MODE = _SBS_MODE_TYPE()


class InvariantViolation(Exception):
    """
    Raised when a runtime invariant is violated.
    """

    def __init__(
        self,
        stage: str,
        failed_invariants: list,
        state_snapshot: dict,
        policy: "ViolationPolicy | None" = None,
    ) -> None:
        self.stage = stage
        self.failed_invariants = failed_invariants
        self.state_snapshot = state_snapshot
        self.policy = policy
        msg = (
            f"[{stage}] InvariantViolation — "
            f"{len(failed_invariants)} invariant(s) violated: "
            f"{failed_invariants}"
        )
        super().__init__(msg)


class ViolationPolicy:
    """
    Policy applied when an invariant violation is detected.
    """

    class Level:
        CRITICAL = "CRITICAL"
        WARNING = "WARNING"
        RECOVERABLE = "RECOVERABLE"

    def __init__(
        self,
        level: str = Level.CRITICAL,
        reconcile_fn=None,
    ) -> None:
        self.level = level
        self.reconcile_fn = reconcile_fn

    def apply(self, stage: str, violations: list, state: dict) -> None:
        if self.level == self.Level.CRITICAL:
            raise InvariantViolation(stage, violations, state, policy=self)

        if self.level == self.Level.RECOVERABLE and self.reconcile_fn:
            self.reconcile_fn(stage, state)


class ExecutionStage:
    """Canonical execution stage names for SBS enforcement points."""

    PRE_DRL = "pre_drl"
    POST_DRL = "post_drl"
    PRE_QUORUM = "pre_quorum"
    POST_QUORUM = "post_quorum"
    PRE_COMMIT = "pre_commit"
    POST_COMMIT = "post_commit"
    PRE_EXECUTE = "pre_execute"
    POST_EXECUTE = "post_execute"


class SBSRuntimeEnforcer:
    """
    Runtime SBS enforcement layer.

    Integrates SystemBoundarySpec and GlobalInvariantEngine into the
    critical execution path of ATOMFederationOS.
    """

    STAGES = [
        ExecutionStage.PRE_DRL,
        ExecutionStage.POST_DRL,
        ExecutionStage.PRE_QUORUM,
        ExecutionStage.POST_QUORUM,
        ExecutionStage.PRE_COMMIT,
        ExecutionStage.POST_COMMIT,
    ]

    def __init__(
        self,
        boundary_spec: "SystemBoundarySpec",
        invariant_engine: "GlobalInvariantEngine",
        mode=2,  # SBS_MODE.ENFORCED
        default_policy: ViolationPolicy | None = None,
    ) -> None:
        self.spec = boundary_spec
        self.engine = invariant_engine
        self.mode = mode
        self._audit_log: list[dict] = []

        if default_policy is not None:
            self._default_policy = default_policy
        elif mode == SBS_MODE.ENFORCED:
            self._default_policy = ViolationPolicy(level=ViolationPolicy.Level.CRITICAL)
        else:
            self._default_policy = ViolationPolicy(level=ViolationPolicy.Level.WARNING)

        self._stage_policies: dict = {}

    def set_policy(self, stage: str, policy: ViolationPolicy) -> None:
        self._stage_policies[stage] = policy

    def enforce(self, stage: str, state: dict) -> bool:
        if self.mode == SBS_MODE.OFF:
            return False

        drl_state = state.get("drl", {})
        ccl_state = state.get("ccl", {})
        f2_state = state.get("f2", {})
        desc_state = state.get("desc", {})

        if not any([drl_state, ccl_state, f2_state, desc_state]):
            drl_state = ccl_state = f2_state = desc_state = state

        spec_ok = self.spec.validate(state)
        engine_ok = self.engine.evaluate(drl_state, ccl_state, f2_state, desc_state)
        engine_violations = self.engine.get_violations()

        boundary_violations = list(self.spec.get_violations())
        all_violations = boundary_violations + engine_violations

        audit_entry = {
            "stage": stage,
            "mode": self.mode,
            "spec_ok": spec_ok,
            "engine_ok": engine_ok,
            "violations": all_violations,
            "state_hash": hash(str(sorted(state.items()))) if state else 0,
        }
        self._audit_log.append(audit_entry)

        if not all_violations:
            return True

        stage_policy = self._stage_policies.get(stage, self._default_policy)

        if self.mode == SBS_MODE.AUDIT:
            stage_policy.apply(stage, all_violations, state)
            return False

        stage_policy.apply(stage, all_violations, state)
        return False

    def get_audit_log(self) -> list[dict]:
        return list(self._audit_log)

    def get_last_audit(self) -> dict | None:
        return self._audit_log[-1] if self._audit_log else None

    def clear_audit_log(self) -> None:
        self._audit_log.clear()

    def get_violations_summary(self) -> dict:
        summary: dict = {}
        for entry in self._audit_log:
            stage = entry["stage"]
            if entry["violations"]:
                summary[stage] = summary.get(stage, 0) + len(entry["violations"])
        return summary
