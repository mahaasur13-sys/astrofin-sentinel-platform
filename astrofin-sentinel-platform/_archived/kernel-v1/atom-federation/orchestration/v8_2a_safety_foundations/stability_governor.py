"""
stability_governor.py — hard gate before mutation

v8.2a foundation #2
Blocks mutation if system health or drift severity is too high.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class GovernorDecision(Enum):
    """Governor gate decision."""
    ALLOW = "ALLOW"           # all checks passed → proceed
    BLOCK = "BLOCK"           # stability threshold not met → blocked
    DEFER = "DEFER"           # health above block threshold but below full-allow → wait
    ESCALATE = "ESCALATE"     # health critically low → escalate to human review


@dataclass
class GovernorThresholds:
    """Tunable thresholds for the stability governor."""
    health_block: float = 0.30   # block if health < this
    health_warn: float = 0.55     # defer if health between warn and block
    drift_severity_block: float = 0.85  # block if drift severity > this
    mutation_density_window: int = 10   # count mutations in last N slots
    mutation_density_max: float = 0.6   # block if rate > this


@dataclass
class GovernorSignal:
    """Decision input bundle from v8.1 observability layer."""
    health_score: float           # composite health from v8.1 (0..1)
    plan_stability_index: float  # PSI from v8.1
    coherence_drop_rate: float    # coherence_drop_rate from v8.1
    drift_severity: float         # severity_score from drift classifier (0..1)
    oscillation_detected: bool    # from v8.1 oscillation detector
    recent_mutation_density: float = 0.0  # mutations per slot, rolling window


class StabilityGovernor:
    """
    Hard gate evaluated before every mutation.

    Combines:
      - system health score (v8.1)
      - drift severity (v8.1)
      - recent mutation density (mutation rate limiter)
      - oscillation flag (blocks immediately if True)

    Returns GovernorDecision that callers MUST respect.
    """

    def __init__(self, thresholds: GovernorThresholds | None = None):
        self.thresholds = thresholds or GovernorThresholds()

    def evaluate(self, signal: GovernorSignal) -> GovernorDecision:
        """
        Synchronous single-signal evaluation.

        Returns:
            GovernorDecision — must be respected by caller
        """
        # 1. Immediate block: oscillation detected
        if signal.oscillation_detected:
            return GovernorDecision.BLOCK

        # 2. Block: health critically low
        if signal.health_score < self.thresholds.health_block:
            return GovernorDecision.BLOCK

        # 3. Block: drift severity exceeds threshold
        if signal.drift_severity > self.thresholds.drift_severity_block:
            return GovernorDecision.BLOCK

        # 4. Block: mutation density too high (rate limiter)
        if signal.recent_mutation_density >= self.thresholds.mutation_density_max:
            return GovernorDecision.BLOCK

        # 5. Escalate: PSI near zero and health marginal — check before DEFER zone
        if signal.plan_stability_index < 0.1 and signal.health_score < 0.5:
            return GovernorDecision.ESCALATE

        # 6. Defer: health in warning zone
        if signal.health_score < self.thresholds.health_warn:
            return GovernorDecision.DEFER

        return GovernorDecision.ALLOW

    def evaluate_batch(
        self,
        signals: list[GovernorSignal],
    ) -> list[tuple[GovernorSignal, GovernorDecision]]:
        """Evaluate multiple signals; returns (signal, decision) pairs."""
        return [(s, self.evaluate(s)) for s in signals]

    def filter_allowed(
        self,
        signals: list[GovernorSignal],
    ) -> list[GovernorSignal]:
        """Return only signals that pass (ALLOW)."""
        return [s for s in signals if self.evaluate(s) == GovernorDecision.ALLOW]

    def explain(self, signal: GovernorSignal) -> str:
        """Human-readable explanation of the decision."""
        decision = self.evaluate(signal)
        reasons = []

        if signal.oscillation_detected:
            reasons.append("oscillation_detected=TRUE → hard block")
        if signal.health_score < self.thresholds.health_block:
            reasons.append(f"health={signal.health_score:.3f} < block={self.thresholds.health_block}")
        if signal.drift_severity > self.thresholds.drift_severity_block:
            reasons.append(f"drift_severity={signal.drift_severity:.3f} > block={self.thresholds.drift_severity_block}")
        if signal.recent_mutation_density >= self.thresholds.mutation_density_max:
            reasons.append(f"mutation_density={signal.recent_mutation_density:.3f} >= max={self.thresholds.mutation_density_max}")
        if decision == GovernorDecision.DEFER:
            reasons.append(f"health={signal.health_score:.3f} in warning zone")
        if decision == GovernorDecision.ESCALATE:
            reasons.append(f"PSI={signal.plan_stability_index:.3f}+health={signal.health_score:.3f} → escalate")

        return f"[{decision.value}] {'; '.join(reasons) if reasons else 'all checks passed'}"
