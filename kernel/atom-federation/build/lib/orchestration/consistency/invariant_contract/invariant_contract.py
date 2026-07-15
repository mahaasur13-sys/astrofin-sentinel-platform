"""
invariant_contract.py — v8.4b System Invariant Contract Kernel

Core classes:
  InvariantDefinition   — what an invariant IS
  InvariantRegistry     — versioned registration system
  InvariantEvaluator     — state → violations
  InvariantEnforcer     — violations → enforcement actions
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

# ─────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────

class InvariantSeverity(Enum):
    """Severity levels for invariant violations."""
    CRITICAL = auto()   # blocks mutation / triggers immediate rollback
    HIGH     = auto()   # logged and escalated; may block depending on policy
    MEDIUM   = auto()   # logged; corrective action scheduled
    LOW      = auto()   # logged; informational


class EnforcementAction(Enum):
    """What the enforcer does when a violation is detected."""
    BLOCK_MUTATION   = auto()   # abort the pending operation
    ROLLBACK         = auto()   # revert to last safe state
    ESCALATE         = auto()  # alert + increase risk score
    LOG_ONLY         = auto()  # record, no immediate action
    CORRECT          = auto()  # auto-correct within allowed bounds
    QUARANTINE       = auto()  # isolate problematic component


# ─────────────────────────────────────────────────────────────────
# Violation
# ─────────────────────────────────────────────────────────────────

@dataclass
class InvariantViolation:
    """
    Record of a single invariant violation event.
    """
    invariant_id: str
    invariant_name: str
    severity: InvariantSeverity
    message: str
    details: dict[str, Any]
    detected_at: float = field(default_factory=time.time)
    tick: int | None = None
    plan_id: str | None = None

    def __post_init__(self):
        if isinstance(self.severity, str):
            self.severity = InvariantSeverity[self.severity]


# ─────────────────────────────────────────────────────────────────
# InvariantDefinition
# ─────────────────────────────────────────────────────────────────

@dataclass
class InvariantDefinition:
    """
    A declarative system invariant.

    An invariant is a predicate on system state that must hold
    at all times. It is defined by:
      - a name and description
      - a check function: state → bool (True = satisfied)
      - a severity and enforcement policy
      - an optional violation_cost (risk weight)

    Example:
        inv = InvariantDefinition(
            name="NO_OSCILLATION_OVER_THRESHOLD",
            description="Coherence score must not oscillate beyond threshold",
            severity=InvariantSeverity.CRITICAL,
            enforcement_action=EnforcementAction.BLOCK_MUTATION,
            check_fn=lambda state: state["is_oscillating"] is False,
            violation_cost=1.0,
        )
    """
    name: str
    description: str
    severity: InvariantSeverity
    enforcement_action: EnforcementAction
    check_fn: Callable[[dict[str, Any]], bool]
    violation_cost: float = 1.0
    enabled: bool = True
    tags: list[str] = field(default_factory=list)

    # metadata
    id: str = ""  # FIX-6: deterministic, set in __post_init__
    version: str = "1.0"
    created_at: float = field(default_factory=time.time)
    last_triggered_at: float | None = None
    trigger_count: int = 0

    def __post_init__(self):
        # FIX-6: Deterministic ID — same name+version → same ID
        if not self.id:
            import hashlib
            raw = f"{self.name}|{self.version}".encode()
            self.id = hashlib.sha256(raw).hexdigest()[:8]

    def evaluate(self, state: dict[str, Any]) -> InvariantResult:
        """
        Run check_fn against state and return an InvariantResult.

        Catches exceptions from check_fn and treats them as violations.
        """
        if not self.enabled:
            return InvariantResult(
                invariant_id=self.id,
                invariant_name=self.name,
                satisfied=True,
                severity=self.severity,
                enforcement_action=self.enforcement_action,
                violation_cost=0.0,
                message="Invariant is disabled",
            )

        try:
            satisfied = bool(self.check_fn(state))
        except Exception as exc:
            satisfied = False
            exc_details = {"exception": str(exc), "type": type(exc).__name__}
        else:
            exc_details = {}

        if satisfied:
            return InvariantResult(
                invariant_id=self.id,
                invariant_name=self.name,
                satisfied=True,
                severity=self.severity,
                enforcement_action=self.enforcement_action,
                violation_cost=0.0,
                message="Invariant satisfied",
            )

        # violation
        details = {"state_summary": _summarize_state(state)}
        details.update(exc_details)

        violation = InvariantViolation(
            invariant_id=self.id,
            invariant_name=self.name,
            severity=self.severity,
            message=f"Invariant violated: {self.name}",
            details=details,
        )

        self.last_triggered_at = time.time()
        self.trigger_count += 1

        return InvariantResult(
            invariant_id=self.id,
            invariant_name=self.name,
            satisfied=False,
            severity=self.severity,
            enforcement_action=self.enforcement_action,
            violation_cost=self.violation_cost,
            message=f"Invariant violated: {self.name}",
            violation=violation,
        )


# ─────────────────────────────────────────────────────────────────
# InvariantResult
# ─────────────────────────────────────────────────────────────────

@dataclass
class InvariantResult:
    """
    Outcome of evaluating a single invariant against a state.
    """
    invariant_id: str
    invariant_name: str
    satisfied: bool
    severity: InvariantSeverity
    enforcement_action: EnforcementAction
    violation_cost: float
    message: str
    violation: InvariantViolation | None = None

    def __post_init__(self):
        for attr in ("severity", "enforcement_action"):
            val = getattr(self, attr)
            if isinstance(val, str):
                setattr(self, attr, type(val)[val] if hasattr(type(val), val) else val)


# ─────────────────────────────────────────────────────────────────
# SystemRiskProfile
# ─────────────────────────────────────────────────────────────────

@dataclass
class SystemRiskProfile:
    """
    Aggregated risk assessment across all invariants.
    """
    tick: int | None
    total_violations: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    risk_score: float                         # 0.0 (safe) – 1.0 (critical)
    enforcement_blocked: bool                 # True if any CRITICAL enforcement was blocked
    violations: list[InvariantViolation]
    most_recent_tick_violated_invariants: list[str] = field(default_factory=list)

    def is_critical(self) -> bool:
        return self.risk_score >= 0.8 or self.critical_count > 0

    def is_healthy(self) -> bool:
        return self.total_violations == 0

    def to_dict(self) -> dict:
        return {
            "tick": self.tick,
            "total_violations": self.total_violations,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "risk_score": round(self.risk_score, 4),
            "enforcement_blocked": self.enforcement_blocked,
            "violation_count_by_invariant": {
                v.invariant_name: v.invariant_id
                for v in self.violations
            },
        }


# ─────────────────────────────────────────────────────────────────
# InvariantRegistry
# ─────────────────────────────────────────────────────────────────

class InvariantRegistry:
    """
    Versioned registry for system invariants.

    Invariants can be registered, enabled/disabled, versioned,
    and queried by tag, severity, or name.
    """

    def __init__(self):
        self._invariants: dict[str, InvariantDefinition] = {}
        self._version_history: dict[str, list[InvariantDefinition]] = {}

    def register(self, invariant: InvariantDefinition, overwrite: bool = False) -> None:
        """Register an invariant. Raises if name conflicts and overwrite=False."""
        if invariant.name in self._invariants and not overwrite:
            raise ValueError(
                f"Invariant '{invariant.name}' already registered. "
                f"Use overwrite=True to replace."
            )
        # archive old version
        if invariant.name in self._invariants:
            self._version_history.setdefault(invariant.name, []).append(
                self._invariants[invariant.name]
            )
        self._invariants[invariant.name] = invariant

    def get(self, name: str) -> InvariantDefinition | None:
        return self._invariants.get(name)

    def list_all(self) -> list[InvariantDefinition]:
        return list(self._invariants.values())

    def list_by_tag(self, tag: str) -> list[InvariantDefinition]:
        return [inv for inv in self._invariants.values() if tag in inv.tags]

    def list_by_severity(
        self, severity: InvariantSeverity
    ) -> list[InvariantDefinition]:
        return [inv for inv in self._invariants.values() if inv.severity == severity]

    def enable(self, name: str) -> bool:
        inv = self._invariants.get(name)
        if inv:
            inv.enabled = True
            return True
        return False

    def disable(self, name: str) -> bool:
        inv = self._invariants.get(name)
        if inv:
            inv.enabled = False
            return True
        return False

    def remove(self, name: str) -> bool:
        return self._invariants.pop(name, None) is not None

    def version(self, name: str) -> int:
        """Return number of historical versions for this invariant."""
        return len(self._version_history.get(name, []))

    def __len__(self) -> int:
        return len(self._invariants)


# ─────────────────────────────────────────────────────────────────
# InvariantEvaluator
# ─────────────────────────────────────────────────────────────────

class InvariantEvaluator:
    """
    Evaluates a registry of invariants against system state.

    Produces a list of results (one per invariant) and a
    SystemRiskProfile aggregating them.

    Usage:
        evaluator = InvariantEvaluator(registry)
        results = evaluator.evaluate(state, tick=10)
        risk    = evaluator.risk_profile(results, tick=10)
    """

    def __init__(self, registry: InvariantRegistry):
        self.registry = registry

    def evaluate(
        self,
        state: dict[str, Any],
        tick: int | None = None,
    ) -> list[InvariantResult]:
        """
        Run all enabled invariants against state.

        Args:
            state: arbitrary dict capturing current system state.
                   Must contain fields expected by each invariant's check_fn.
            tick: optional tick number for record-keeping.

        Returns:
            List of InvariantResult (one per invariant, including disabled).
        """
        results = []
        for inv in self.registry.list_all():
            result = inv.evaluate(state)
            if tick is not None:
                result = _with_tick(result, tick)
            results.append(result)
        return results

    def risk_profile(
        self,
        results: list[InvariantResult],
        tick: int | None = None,
    ) -> SystemRiskProfile:
        """
        Aggregate evaluation results into a SystemRiskProfile.

        risk_score = Σ (severity_weight × violation_cost) / max_possible
        where severity_weight: CRITICAL=1.0, HIGH=0.6, MEDIUM=0.3, LOW=0.1
        """
        SEVERITY_WEIGHT = {
            InvariantSeverity.CRITICAL: 1.0,
            InvariantSeverity.HIGH: 0.6,
            InvariantSeverity.MEDIUM: 0.3,
            InvariantSeverity.LOW: 0.1,
        }

        # Single-pass: extract violations, total_cost, severity counts simultaneously
        violations: list[InvariantViolation] = []
        total_cost = 0.0
        severity_counts = {s: 0 for s in InvariantSeverity}
        most_recent_tick_violated_invariants: list[str] = []

        for r in results:
            if r.violation is not None:
                violations.append(r.violation)
                total_cost += r.violation_cost
                severity_counts[r.violation.severity] += 1
            if not r.satisfied:
                most_recent_tick_violated_invariants.append(r.invariant_name)

        max_possible = sum(
            SEVERITY_WEIGHT[inv.severity] * inv.violation_cost
            for inv in self.registry.list_all()
        ) or 1.0

        risk_score = min(total_cost / max_possible, 1.0)

        blocked = any(
            r.enforcement_action == EnforcementAction.BLOCK_MUTATION
            and not r.satisfied
            for r in results
        )

        return SystemRiskProfile(
            tick=tick,
            total_violations=len(violations),
            critical_count=severity_counts[InvariantSeverity.CRITICAL],
            high_count=severity_counts[InvariantSeverity.HIGH],
            medium_count=severity_counts[InvariantSeverity.MEDIUM],
            low_count=severity_counts[InvariantSeverity.LOW],
            risk_score=risk_score,
            enforcement_blocked=blocked,
            violations=violations,
            most_recent_tick_violated_invariants=most_recent_tick_violated_invariants,
        )

    def evaluate_with_risk(
        self,
        state: dict[str, Any],
        tick: int | None = None,
    ) -> tuple[list[InvariantResult], SystemRiskProfile]:
        """
        Convenience: evaluate + risk_profile in one call.
        """
        results = self.evaluate(state, tick)
        risk = self.risk_profile(results, tick)
        return results, risk


# ─────────────────────────────────────────────────────────────────
# InvariantEnforcer
# ─────────────────────────────────────────────────────────────────

@dataclass
class EnforcementRecord:
    """Record of an enforcement action taken."""
    invariant_name: str
    action: EnforcementAction
    success: bool
    blocked_mutations: int = 0
    rollbacks_performed: int = 0
    details: dict[str, Any] = field(default_factory=dict)


class InvariantEnforcer:
    """
    Enforces invariant violations via configurable policies.

    Wraps InvariantEvaluator and translates violation results
    into enforcement actions (block, rollback, quarantine, etc.).

    Usage:
        enforcer = InvariantEnforcer(evaluator, block_threshold=0.8)
        violations = enforcer.evaluate(state)
        enforcer.enforce(violations)   # applies configured actions
    """

    def __init__(
        self,
        evaluator: InvariantEvaluator,
        block_threshold: float = 0.8,   # risk_score above this → block everything
        rollback_on_critical: bool = True,
    ):
        self.evaluator = evaluator
        self.block_threshold = block_threshold
        self.rollback_on_critical = rollback_on_critical
        self._enforcement_history: list[EnforcementRecord] = []
        self._blocked_count: int = 0
        self._rollback_count: int = 0

    def evaluate(
        self,
        state: dict[str, Any],
        tick: int | None = None,
    ) -> list[InvariantResult]:
        """Short-cut: run evaluator.evaluate()."""
        return self.evaluator.evaluate(state, tick)

    def enforce(
        self,
        violations: list[InvariantViolation],
        risk_score: float,
        dry_run: bool = False,
    ) -> EnforcementRecord | None:
        """
        Take enforcement actions on a batch of violations.

        If risk_score >= block_threshold → BLOCK_MUTATION for all CRITICALs.

        Returns:
            EnforcementRecord summarizing what was done.
            None if no enforcement was needed.

        Args:
            violations: list of active violations
            risk_score: current system risk score
            dry_run: if True, record what would happen without doing it
        """
        if not violations:
            return None

        critical_violations = [
            v for v in violations if v.severity == InvariantSeverity.CRITICAL
        ]

        # Determine action: ROLLBACK > BLOCK > ESCALATE
        # BLOCK_MUTATION if risk high but no critical violations to rollback
        if self.rollback_on_critical and critical_violations:
            action = EnforcementAction.ROLLBACK
        elif risk_score >= self.block_threshold or critical_violations:
            action = EnforcementAction.BLOCK_MUTATION
        else:
            action = EnforcementAction.ESCALATE

        record = EnforcementRecord(
            invariant_name=", ".join(v.invariant_name for v in violations),
            action=action,
            success=True,
            blocked_mutations=0,
            rollbacks_performed=0,
            details={
                "violation_count": len(violations),
                "critical_count": len(critical_violations),
                "risk_score": risk_score,
            },
        )

        if not dry_run:
            if action == EnforcementAction.ROLLBACK:
                self._rollback_count += 1
                self._blocked_count += 1   # rollback implies blocking first
                record.rollbacks_performed = 1
                record.blocked_mutations = 1
            elif action == EnforcementAction.BLOCK_MUTATION:
                self._blocked_count += 1
                record.blocked_mutations = 1

        self._enforcement_history.append(record)
        return record

    def enforce_from_results(
        self,
        results: list[InvariantResult],
        risk_score: float,
        dry_run: bool = False,
    ) -> EnforcementRecord | None:
        """Convenience: extract violations from results and enforce."""
        violations = [r.violation for r in results if r.violation is not None]
        return self.enforce(violations, risk_score, dry_run)

    def blocked_count(self) -> int:
        return self._blocked_count

    def rollback_count(self) -> int:
        return self._rollback_count

    def enforcement_history(self) -> list[EnforcementRecord]:
        return list(self._enforcement_history)

    # ── high-level check ──────────────────────────────────────────

    def check_and_enforce(
        self,
        state: dict[str, Any],
        tick: int | None = None,
        dry_run: bool = False,
    ) -> SystemRiskProfile:
        """
        Evaluate invariants against state, compute risk, enforce.

        Returns the final SystemRiskProfile.
        """
        results, risk = self.evaluator.evaluate_with_risk(state, tick)
        self.enforce_from_results(results, risk.risk_score, dry_run)
        return risk


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────

def _summarize_state(state: dict[str, Any], max_len: int = 200) -> str:
    """One-line summary of state for violation details."""
    try:
        import json
        s = json.dumps(state, default=str)
        return s[:max_len] + ("..." if len(s) > max_len else "")
    except Exception:
        return str(state)[:max_len]


def _with_tick(result: InvariantResult, tick: int) -> InvariantResult:
    """Attach tick to a result and its violation if present."""
    if result.violation:
        result.violation.tick = tick
    return result
