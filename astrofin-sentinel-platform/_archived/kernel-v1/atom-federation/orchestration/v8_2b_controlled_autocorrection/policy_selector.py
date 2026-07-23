"""Policy synthesis: context + mutation policy + selector."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .severity_mapper import MutationClass, SeverityLevel


class PolicyMode(Enum):
    """Operating mode for the policy selector."""

    CONSERVATIVE = "conservative"  # prefer RETUNE / REWEIGHT only
    BALANCED = "balanced"         # allow REPLAN for HIGH
    AGGRESSIVE = "aggressive"     # allow RESET up to CRITICAL


@dataclass
class PolicyContext:
    """
    Immutable snapshot of system state at the moment of mutation decision.

    All numeric fields are raw values; consumers decide normalisation.
    """

    drift_score: float
    health_score: float
    mutation_density: float
    coherence_drop: float
    oscillation_detected: bool
    severity: SeverityLevel
    mutation_class: MutationClass
    recent_outcome: str | None = None  # "success" | "degraded" | "failed"

    # ── Computed properties ────────────────────────────────────────────────

    @property
    def is_safe_to_mutate(self) -> bool:
        """Rough readiness gate based on health."""
        return self.health_score >= 0.5 and not self.oscillation_detected

    @property
    def density_stress(self) -> bool:
        """True when recent mutation density is elevated."""
        return self.mutation_density >= 0.6


@dataclass
class MutationPolicy:
    """
    Describes what a mutation operation should do and what constraints apply.
    """

    class_label: MutationClass
    severity: SeverityLevel
    mode: PolicyMode

    # ── Constraint fields ────────────────────────────────────────────────────

    max_retune_epsilon: float = 0.15
    reweight_clip_ratio: float = 0.20
    replan_horizon_fraction: float = 0.5
    reset_ref_weight: float = 0.3  # blend weight toward reference model (0=full reset, 1=identity)

    # ── Policy flags ─────────────────────────────────────────────────────────

    allow_degradation: bool = False
    require_human_approval: bool = False
    rollback_on_violation: bool = True

    def describe(self) -> str:
        return (
            f"[{self.mode.value}][{self.severity.value}] {self.class_label.value}\n"
            f"  retune_eps={self.max_retune_epsilon}  "
            f"reweight_clip={self.reweight_clip_ratio}  "
            f"replan_horizon={self.replan_horizon_fraction}  "
            f"reset_ref_weight={self.reset_ref_weight}\n"
            f"  allow_degradation={self.allow_degradation}  "
            f"require_human={self.require_human_approval}  "
            f"rollback_on_violation={self.rollback_on_violation}"
        )


class PolicySelector:
    """
    Selects the appropriate MutationPolicy given a PolicyContext and mode.

    This is a pure, stateless selector — no side effects.
    """

    def __init__(self, mode: PolicyMode = PolicyMode.BALANCED):
        self._mode = mode

    def select(self, ctx: PolicyContext) -> MutationPolicy:
        """
        Core policy selection logic.

        Policy escalation ladder:
          CONSERVATIVE:
            NEGLIGIBLE / LOW       → RETUNE
            MEDIUM                 → REWEIGHT
            HIGH / CRITICAL        → REWEIGHT  (NO reset — escalate only via human)
          BALANCED:
            NEGLIGIBLE / LOW       → RETUNE
            MEDIUM                 → REWEIGHT
            HIGH                   → REPLAN
            CRITICAL              → REPLAN  (RESET requires explicit mode=AGGRESSIVE)
          AGGRESSIVE:
            NEGLIGIBLE / LOW       → RETUNE
            MEDIUM                 → REWEIGHT
            HIGH                   → REPLAN
            CRITICAL              → RESET
        """
        if ctx.oscillation_detected:
            # Oscillation is always REPLAN, regardless of severity
            return MutationPolicy(
                class_label=MutationClass.REPLAN,
                severity=ctx.severity,
                mode=self._mode,
                allow_degradation=False,
                require_human_approval=True,
            )

        if ctx.density_stress and self._mode != PolicyMode.AGGRESSIVE:
            # Suppress RESET in density-stress scenarios unless AGGRESSIVE
            effective_class = MutationClass.REWEIGHT
        else:
            effective_class = self._effective_class(ctx.severity)

        return self._build_policy(ctx, effective_class)

    def _effective_class(
        self, severity: SeverityLevel
    ) -> MutationClass:
        if self._mode == PolicyMode.CONSERVATIVE:
            override = {
                SeverityLevel.HIGH: MutationClass.REWEIGHT,
                SeverityLevel.CRITICAL: MutationClass.REWEIGHT,
            }
        elif self._mode == PolicyMode.BALANCED:
            override = {
                SeverityLevel.CRITICAL: MutationClass.REPLAN,
            }
        else:  # AGGRESSIVE
            override = {}

        return override.get(severity, {
            SeverityLevel.NEGLIGIBLE: MutationClass.RETUNE,
            SeverityLevel.LOW: MutationClass.RETUNE,
            SeverityLevel.MEDIUM: MutationClass.REWEIGHT,
            SeverityLevel.HIGH: MutationClass.REPLAN,
            SeverityLevel.CRITICAL: MutationClass.RESET,
        }[severity])

    def _build_policy(
        self, ctx: PolicyContext, class_label: MutationClass
    ) -> MutationPolicy:
        if class_label == MutationClass.RETUNE:
            max_eps = {PolicyMode.CONSERVATIVE: 0.10, PolicyMode.BALANCED: 0.15, PolicyMode.AGGRESSIVE: 0.20}[self._mode]
            return MutationPolicy(
                class_label=class_label,
                severity=ctx.severity,
                mode=self._mode,
                max_retune_epsilon=max_eps,
            )

        elif class_label == MutationClass.REWEIGHT:
            clip = {PolicyMode.CONSERVATIVE: 0.10, PolicyMode.BALANCED: 0.20, PolicyMode.AGGRESSIVE: 0.30}[self._mode]
            return MutationPolicy(
                class_label=class_label,
                severity=ctx.severity,
                mode=self._mode,
                reweight_clip_ratio=clip,
            )

        elif class_label == MutationClass.REPLAN:
            return MutationPolicy(
                class_label=class_label,
                severity=ctx.severity,
                mode=self._mode,
                replan_horizon_fraction=0.5,
                rollback_on_violation=True,
            )

        else:  # RESET
            return MutationPolicy(
                class_label=class_label,
                severity=ctx.severity,
                mode=self._mode,
                reset_ref_weight=0.3,
                allow_degradation=True,
                require_human_approval=(self._mode != PolicyMode.AGGRESSIVE),
                rollback_on_violation=False,
            )
