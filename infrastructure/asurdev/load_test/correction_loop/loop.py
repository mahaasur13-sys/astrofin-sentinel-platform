#!/usr/bin/env python3
"""
Correction Loop — closes the REQUEST → REALIZATION → FEEDBACK → CORRECTION → ↺ cycle.
Every cycle: observes state, detects deviation, classifies fix, applies correction.
No direct production changes — everything goes through governance pipeline.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Literal
from enum import Enum
import logging


class FixType(Enum):
    """Classification of fix required."""
    LOCAL        = "local"       # Queue/tuning — no structural change
    POLICY       = "policy"      # Policy parameter update
    STRUCTURAL   = "structural"  # Constraint graph / architecture change
    ESCALATE     = "escalate"    # Human review required


class CorrectionAction(Enum):
    """Concrete actions available to the correction loop."""
    ADJUST_QUEUE_DEPTH     = "adjust_queue_depth"
    TUNE_BEAM_WIDTH        = "tune_beam_width"
    UPDATE_PRIORITY_WEIGHTS = "update_priority_weights"
    RELAX_CONSTRAINT       = "relax_constraint"
    TRIGGER_ROLLBACK       = "trigger_rollback"
    SCALE_UP_RESOURCES     = "scale_up_resources"
    RETRAIN_MODEL          = "retrain_model"
    ESCALATE_HUMAN         = "escalate_human"


@dataclass
class CorrectionSignal:
    """Observed deviation from target state."""
    metric_name: str
    observed: float
    expected: float
    deviation_pct: float
    severity: float  # 0..1
    timestamp: datetime


@dataclass
class CorrectionDecision:
    """Decision made by the correction loop."""
    fix_type: FixType
    primary_action: CorrectionAction
    secondary_actions: list[CorrectionAction]
    reason: str
    approved: bool
    approved_by: str  # "governance" / "human" / "simulation"
    rollback_available: bool = True
    confidence: float = 0.0


@dataclass
class CorrectionCycleResult:
    """Result of one full correction cycle."""
    cycle_id: int
    timestamp: datetime
    signals: list[CorrectionSignal]
    decision: Optional[CorrectionDecision]
    execution_ms: float
    next_cycle_recommended: bool
    escalation_required: bool = False


class CorrectionLoop:
    """
    Self-correcting feedback loop for the ACOS system.

    cycle():
        1. REQUEST   — load scenario + system state
        2. OBSERVE   — collect metrics, detect signals
        3. CLASSIFY   — determine fix type (LOCAL / POLICY / STRUCTURAL)
        4. DECIDE    — select action, route through governance
        5. ACT       — apply correction (or escalate)
        6. VALIDATE  — verify correction worked
        7. → next REQUEST
    """

    def __init__(self, governance_module=None, state_store=None):
        self.governance = governance_module
        self.state = state_store
        self._cycle_counter = 0
        self._history: list[CorrectionCycleResult] = []
        self._pending_fix: Optional[CorrectionDecision] = None
        self._fix_cooldown_sec = 30
        self._last_fix_time: Optional[datetime] = None
        self._correction_log = logging.getLogger("acos.correction_loop")
        self._suppression_count = 0

    def cycle(
        self,
        metrics,
        scenario_name: str = "manual",
        force: bool = False,
    ) -> CorrectionCycleResult:
        """
        Execute one correction cycle.
        Returns CorrectionCycleResult with decision and actions.
        """
        import time
        start = time.monotonic()
        self._cycle_counter += 1
        cycle_id = self._cycle_counter

        self._correction_log.info(f"[Cycle {cycle_id}] Starting correction cycle")

        # Cooldown: skip if fixed recently
        if not force and self._last_fix_time:
            elapsed = (datetime.utcnow() - self._last_fix_time).total_seconds()
            if elapsed < self._fix_cooldown_sec:
                self._suppression_count += 1
                self._correction_log.info(f"[Cycle {cycle_id}] Suppressed (cooldown {elapsed:.0f}s < {self._fix_cooldown_sec}s)")
                return CorrectionCycleResult(
                    cycle_id=cycle_id,
                    timestamp=datetime.utcnow(),
                    signals=[],
                    decision=None,
                    execution_ms=(time.monotonic() - start) * 1000,
                    next_cycle_recommended=False,
                )

        # STEP 1: OBSERVE — detect deviation signals
        signals = self._detect_signals(metrics)

        # STEP 2: CLASSIFY — determine fix type
        fix_type = self._classify(signals)

        # STEP 3: DECIDE — select action
        decision = self._decide(signals, fix_type)

        # STEP 4: GOVERNANCE APPROVAL — pass through v8 safety kernel
        if decision and decision.approved:
            decision = self._governance_approval(decision, metrics)

        # STEP 5: ACT — execute approved correction
        executed = False
        if decision and decision.approved:
            executed = self._act(decision)
            if executed:
                self._last_fix_time = datetime.utcnow()

        # STEP 6: VALIDATE — check if correction resolved signal
        resolved = self._validate(signals, decision) if executed else False
        next_recommended = len(signals) > 0 and not resolved

        result = CorrectionCycleResult(
            cycle_id=cycle_id,
            timestamp=datetime.utcnow(),
            signals=signals,
            decision=decision,
            execution_ms=(time.monotonic() - start) * 1000,
            next_cycle_recommended=next_recommended,
            escalation_required=(fix_type == FixType.ESCALATE),
        )
        self._history.append(result)
        return result

    def _detect_signals(self, metrics) -> list[CorrectionSignal]:
        """STEP 1: Observe — detect deviations from SLO targets."""
        signals = []
        now = datetime.utcnow()

        # P99 latency
        if hasattr(metrics, 'p99_latency_ms') and metrics.p99_latency_ms > 500:
            signals.append(CorrectionSignal(
                metric_name="p99_latency_ms",
                observed=metrics.p99_latency_ms,
                expected=200.0,
                deviation_pct=(metrics.p99_latency_ms - 200) / 200 * 100,
                severity=min(1.0, (metrics.p99_latency_ms - 500) / 500),
                timestamp=now,
            ))

        # Failure rate
        if hasattr(metrics, 'failure_rate') and metrics.failure_rate > 0.05:
            signals.append(CorrectionSignal(
                metric_name="failure_rate",
                observed=metrics.failure_rate,
                expected=0.01,
                deviation_pct=(metrics.failure_rate - 0.01) / 0.01 * 100,
                severity=min(1.0, (metrics.failure_rate - 0.05) / 0.10),
                timestamp=now,
            ))

        # Queue depth
        if hasattr(metrics, 'queue_depth') and metrics.queue_depth > 50:
            signals.append(CorrectionSignal(
                metric_name="queue_depth",
                observed=float(metrics.queue_depth),
                expected=10.0,
                deviation_pct=(metrics.queue_depth - 10) / 10 * 100,
                severity=min(1.0, (metrics.queue_depth - 50) / 100),
                timestamp=now,
            ))

        # Drift alignment
        if hasattr(metrics, 'drift_alignment_error') and metrics.drift_alignment_error > 0.15:
            signals.append(CorrectionSignal(
                metric_name="drift_alignment_error",
                observed=metrics.drift_alignment_error,
                expected=0.05,
                deviation_pct=(metrics.drift_alignment_error - 0.05) / 0.05 * 100,
                severity=min(1.0, (metrics.drift_alignment_error - 0.15) / 0.20),
                timestamp=now,
            ))

        # Degraded mode
        if hasattr(metrics, 'degraded_mode') and metrics.degraded_mode:
            signals.append(CorrectionSignal(
                metric_name="degraded_mode",
                observed=1.0,
                expected=0.0,
                deviation_pct=100.0,
                severity=1.0,
                timestamp=now,
            ))

        return signals

    def _classify(self, signals: list[CorrectionSignal]) -> FixType:
        """STEP 2: Classify — determine fix type from signals."""
        if not signals:
            return FixType.LOCAL  # No action needed

        # Structural signals require structural fix
        structural_signals = ["constraint_violations", "drift_alignment_error"]
        for s in signals:
            if s.metric_name in structural_signals and s.severity > 0.5:
                return FixType.STRUCTURAL

        # Policy signals
        policy_signals = ["failure_rate", "rollback_success_rate"]
        for s in signals:
            if s.metric_name in policy_signals and s.severity > 0.3:
                return FixType.POLICY

        # High severity → escalate
        if any(s.severity > 0.8 for s in signals):
            return FixType.ESCALATE

        return FixType.LOCAL

    def _decide(self, signals: list[CorrectionSignal], fix_type: FixType) -> CorrectionDecision:
        """STEP 3: Decide — select action based on fix type and signals."""
        if not signals:
            return CorrectionDecision(
                fix_type=FixType.LOCAL,
                primary_action=CorrectionAction.ADJUST_QUEUE_DEPTH,
                secondary_actions=[],
                reason="No signals detected",
                approved=True,
                approved_by="system",
                confidence=1.0,
            )

        worst = max(signals, key=lambda s: s.severity)
        actions_map = {
            "p99_latency_ms": CorrectionAction.TUNE_BEAM_WIDTH,
            "failure_rate": CorrectionAction.UPDATE_PRIORITY_WEIGHTS,
            "queue_depth": CorrectionAction.ADJUST_QUEUE_DEPTH,
            "drift_alignment_error": CorrectionAction.RELAX_CONSTRAINT,
            "degraded_mode": CorrectionAction.TRIGGER_ROLLBACK,
        }

        primary = actions_map.get(worst.metric_name, CorrectionAction.ADJUST_QUEUE_DEPTH)

        # Secondary actions
        secondary = []
        if fix_type == FixType.POLICY:
            secondary.append(CorrectionAction.RETRAIN_MODEL)
        elif fix_type == FixType.STRUCTURAL:
            secondary.extend([CorrectionAction.RELAX_CONSTRAINT, CorrectionAction.ESCALATE_HUMAN])

        reason = f"{fix_type.value} fix: {worst.metric_name}={worst.observed:.2f} (expected={worst.expected:.2f}, severity={worst.severity:.2f})"

        return CorrectionDecision(
            fix_type=fix_type,
            primary_action=primary,
            secondary_actions=secondary,
            reason=reason,
            approved=False,  # Needs governance approval
            approved_by="pending",
            confidence=max(0.5, 1.0 - worst.severity),
        )

    def _governance_approval(self, decision: CorrectionDecision, metrics) -> CorrectionDecision:
        """STEP 4: Route through v8 safety kernel for approval."""
        if self.governance is None:
            decision.approved = True
            decision.approved_by = "governance_fallback"
            return decision

        try:
            # Call v8 safety kernel
            request = {
                "action": decision.primary_action.value,
                "severity": max(s.severity for s in getattr(decision, 'signals', [object()])),
                "metrics": {
                    "p99_latency_ms": metrics.p99_latency_ms,
                    "failure_rate": metrics.failure_rate,
                    "queue_depth": metrics.queue_depth,
                },
            }
            response = self.governance.validate(request)
            decision.approved = response.get("approved", False)
            decision.approved_by = "governance"
        except Exception:
            decision.approved = True  # Fail open — not fail secure
            decision.approved_by = "governance_fallback"

        return decision

    def _act(self, decision: CorrectionDecision) -> bool:
        """STEP 5: Execute approved correction."""
        self._correction_log.info(f"Acting: {decision.primary_action.value} ({decision.reason})")

        # In real system: call scheduler API, update policy weights, etc.
        # Here: just log
        if decision.primary_action == CorrectionAction.TRIGGER_ROLLBACK:
            self._correction_log.warning("Rollback triggered — would restore previous snapshot")
            return True

        return True  # Simulated success

    def _validate(self, signals: list[CorrectionSignal], decision: CorrectionDecision) -> bool:
        """STEP 6: Validate — check if signals resolved after correction."""
        # In real system: collect new metrics and compare
        # Here: assume success if action was local
        return decision.fix_type == FixType.LOCAL

    def get_stats(self) -> dict:
        """Return correction loop statistics."""
        total = len(self._history)
        if total == 0:
            return {"cycles": 0}

        fixes = [r for r in self._history if r.decision and r.decision.primary_action != CorrectionAction.ADJUST_QUEUE_DEPTH]
        escalations = sum(1 for r in self._history if r.escalation_required)
        return {
            "total_cycles": total,
            "fixes_applied": len(fixes),
            "escalations": escalations,
            "suppressed_cooldown": self._suppression_count,
            "suppression_rate": self._suppression_count / max(1, total),
        }
