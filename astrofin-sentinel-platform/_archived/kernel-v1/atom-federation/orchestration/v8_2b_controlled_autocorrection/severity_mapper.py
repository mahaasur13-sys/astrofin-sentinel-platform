"""Severity → MutationClass mapping and threshold configuration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SeverityLevel(Enum):
    """Discrete severity bands that map to mutation classes."""

    NEGLIGIBLE = "negligible"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MutationClass(Enum):
    """
    Supported mutation classes ordered by invasiveness.

    RETUNE      — incremental parameter adjustment within ε-bounds
    REWEIGHT    — reshape action distribution weights (PPO/GAIL)
    REPLAN      — replace entire planning horizon trajectory
    RESET       — full parameter reinitialization from reference model
    """

    RETUNE = "retune"
    REWEIGHT = "reweight"
    REPLAN = "replan"
    RESET = "reset"


@dataclass(frozen=True)
class SeverityThresholds:
    """
    Configurable thresholds for severity level assignment.

    All thresholds are inclusive lower bounds.
    """

    negligible_max: float = 0.05
    low_max: float = 0.20
    medium_max: float = 0.45
    high_max: float = 0.75
    # > high_max → CRITICAL


class SeverityActionMapper:
    """
    Maps a continuous drift_score ∈ [0, 1] to (SeverityLevel, MutationClass)
    and resolves the preferred mutation class based on policy mode.
    """

    def __init__(self, thresholds: SeverityThresholds | None = None):
        self._t = thresholds or SeverityThresholds()

    def classify(self, drift_score: float) -> SeverityLevel:
        """Discretise a continuous drift score to a severity band."""
        if drift_score <= self._t.negligible_max:
            return SeverityLevel.NEGLIGIBLE
        elif drift_score <= self._t.low_max:
            return SeverityLevel.LOW
        elif drift_score <= self._t.medium_max:
            return SeverityLevel.MEDIUM
        elif drift_score <= self._t.high_max:
            return SeverityLevel.HIGH
        else:
            return SeverityLevel.CRITICAL

    def mutation_class_for(self, severity: SeverityLevel) -> MutationClass:
        """
        Default severity → mutation class mapping.

        Escalation ladder:
          NEGLIGIBLE → RETUNE (no action technically, but log for density)
          LOW        → RETUNE
          MEDIUM     → REWEIGHT
          HIGH       → REPLAN
          CRITICAL   → RESET
        """
        return {
            SeverityLevel.NEGLIGIBLE: MutationClass.RETUNE,
            SeverityLevel.LOW: MutationClass.RETUNE,
            SeverityLevel.MEDIUM: MutationClass.REWEIGHT,
            SeverityLevel.HIGH: MutationClass.REPLAN,
            SeverityLevel.CRITICAL: MutationClass.RESET,
        }[severity]

    def resolve(self, drift_score: float) -> tuple[SeverityLevel, MutationClass]:
        """Convenience: classify + map in one call."""
        sev = self.classify(drift_score)
        return sev, self.mutation_class_for(sev)

    # ── Vectorised helpers ──────────────────────────────────────────────────

    def classify_batch(self, drift_scores: list[float]) -> list[SeverityLevel]:
        return [self.classify(ds) for ds in drift_scores]

    def resolve_batch(
        self, drift_scores: list[float]
    ) -> list[tuple[SeverityLevel, MutationClass]]:
        return [self.resolve(ds) for ds in drift_scores]
