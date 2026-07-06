"""MutationPlanner — generates concrete mutation plans from policy intent."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class MutationTarget(Enum):
    """What part of θ-space or control surface is being modified."""

    GAIN_SCHEDULER = "gain_scheduler"          # learning rate / step size
    EVALUATOR_WEIGHTS = "evaluator_weights"   # reward model weights
    REPLANNER_THRESHOLDS = "replanner_thresholds"  # drift/divergence thresholds
    ARBITRATION_PRIORITIES = "arbitration_priorities"  # priority over rival policies
    MIXTURE_WEIGHTS = "mixture_weights"       # mixture-of-policies blending


@dataclass
class MutationPlan:
    """
    Concrete mutation to be applied to a parameter region.

    Fields
    ------
    target : MutationTarget
        Which control-surface component to mutate.
    region_indices : slice or list[int]
        Which dimensions of θ to modify.
    delta_spec : str
        Human-readable description of the delta (actual numeric values
        are stored in the parent MutationExecutionSpec).
    rationale : str
        Why this specific target+region combination was chosen.
    expected_impact : float
        Estimated effect on drift_score (negative = improvement).
    risk_level : str
        "low" | "medium" | "high" — how likely this is to cause regression.
    """

    target: MutationTarget
    region_indices: list[int]
    delta_spec: str
    rationale: str
    expected_impact: float
    risk_level: str = "medium"


@dataclass
class MutationExecutionSpec:
    """
    Full set of parameters for one mutation execution attempt.

    Produced by MutationPlanner, consumed by MutationExecutor.
    """

    policy_mode: str  # from MutationPolicy.mode
    severity: str     # from MutationClass
    plans: list[MutationPlan]
    theta_dim: int
    total_regions_touched: int = field(init=False)

    def __post_init__(self):
        self.total_regions_touched = sum(
            len(p.region_indices) for p in self.plans
        )

    @property
    def is_single_region(self) -> bool:
        return self.total_regions_touched <= 3

    def as_summary(self) -> dict:
        return {
            "policy_mode": self.policy_mode,
            "severity": self.severity,
            "plan_count": len(self.plans),
            "regions_touched": self.total_regions_touched,
            "is_single_region": self.is_single_region,
            "targets": [p.target.value for p in self.plans],
        }


class MutationPlanner:
    """
    Generates concrete MutationExecutionSpec from policy + state context.

    This is a pure planner — it asks *what* to change and *where*,
    not *how much* (that is the executor's domain).
    """

    def __init__(self, theta_dim: int):
        self._theta_dim = theta_dim

    def plan(
        self,
        mutation_class: str,   # "retune" | "reweight" | "replan" | "reset"
        severity: str,        # "negligible" | "low" | "medium" | "high" | "critical"
        drift_score: float,
        health_score: float,
        coherence_drop: float,
        mutation_density: float,
    ) -> MutationExecutionSpec:
        """
        Build a MutationExecutionSpec given current system state.

        Planning strategy by mutation class:

        RETUNE
          → target = GAIN_SCHEDULER or EVALUATOR_WEIGHTS
          → region = highest-drift dimensions (|θ - θ_ref| large)
          → expected_impact = -0.05 to -0.15

        REWEIGHT
          → target = MIXTURE_WEIGHTS
          → region = top-N by |weight change rate|
          → expected_impact = -0.10 to -0.25

        REPLAN
          → target = REPLANNER_THRESHOLDS
          → region = full horizon (planning window dimensions)
          → expected_impact = -0.15 to -0.40

        RESET
          → target = EVALUATOR_WEIGHTS
          → region = all dimensions
          → expected_impact = -0.30 to -0.60 (but risky)
        """
        if mutation_class == "retune":
            plans = self._plan_retune(drift_score, health_score)
        elif mutation_class == "reweight":
            plans = self._plan_reweight(drift_score, mutation_density)
        elif mutation_class == "replan":
            plans = self._plan_replan(drift_score, coherence_drop)
        else:  # reset
            plans = self._plan_reset(drift_score, severity)

        return MutationExecutionSpec(
            policy_mode=mutation_class,
            severity=severity,
            plans=plans,
            theta_dim=self._theta_dim,
        )

    # ── Per-class planning ──────────────────────────────────────────────────

    def _plan_retune(
        self, drift_score: float, health_score: float
    ) -> list[MutationPlan]:
        """RETUNE → bias gain scheduler on highest-drift dimensions."""
        # Heuristic: top 20% of dimensions by proximity to bounds
        n = max(1, self._theta_dim // 5)
        region = list(range(n))

        risk = "low" if health_score >= 0.6 else "medium"
        impact = -0.05 - 0.10 * (drift_score - 0.1)

        return [
            MutationPlan(
                target=MutationTarget.GAIN_SCHEDULER,
                region_indices=region,
                delta_spec=f"ε-step on dims 0:{n}, direction = sign(θ)",
                rationale=(
                    f"Top-{n} dimensions show highest parametric drift; "
                    "apply bounded step-size correction"
                ),
                expected_impact=impact,
                risk_level=risk,
            )
        ]

    def _plan_reweight(
        self, drift_score: float, mutation_density: float
    ) -> list[MutationPlan]:
        """REWEIGHT → reshape mixture weights for highest-rate dimensions."""
        n = max(2, self._theta_dim // 4)
        region = list(range(n))

        density_factor = 1.0 + 0.2 * (mutation_density - 0.3)
        impact = -0.10 - 0.15 * drift_score * density_factor
        risk = "low" if mutation_density < 0.6 else "medium"

        return [
            MutationPlan(
                target=MutationTarget.MIXTURE_WEIGHTS,
                region_indices=region,
                delta_spec=f"Reweight clip ±{0.2 * density_factor:.2f} on dims 0:{n}",
                rationale=(
                    f"Top-{n} mixture weights show elevated drift rate; "
                    "reshape weight distribution within safety clip"
                ),
                expected_impact=impact,
                risk_level=risk,
            )
        ]

    def _plan_replan(
        self, drift_score: float, coherence_drop: float
    ) -> list[MutationPlan]:
        """REPLAN → replace replanner thresholds on planning horizon."""
        horizon = max(4, self._theta_dim // 2)
        full_region = list(range(horizon))

        impact = -0.15 - 0.25 * drift_score
        risk = "medium" if coherence_drop < 0.2 else "high"

        return [
            MutationPlan(
                target=MutationTarget.REPLANNER_THRESHOLDS,
                region_indices=full_region,
                delta_spec=f"Replace threshold vector on dims 0:{horizon}",
                rationale=(
                    f"Coherence drop={coherence_drop:.2f} signals horizon drift; "
                    "replace full planning window thresholds"
                ),
                expected_impact=impact,
                risk_level=risk,
            )
        ]

    def _plan_reset(
        self, drift_score: float, severity: str
    ) -> list[MutationPlan]:
        """RESET → full reinitialization of evaluator weights."""
        all_dims = list(range(self._theta_dim))
        all_region = MutationPlan(
            target=MutationTarget.EVALUATOR_WEIGHTS,
            region_indices=all_dims,
            delta_spec=f"Bleed all {self._theta_dim} dims toward reference model",
            rationale=(
                f"CRITICAL severity={severity}, drift_score={drift_score:.2f}; "
                "full parameter reinitialization from reference snapshot"
            ),
            expected_impact=-0.30 - 0.30 * drift_score,
            risk_level="high",
        )

        gate_plan = MutationPlan(
            target=MutationTarget.ARBITRATION_PRIORITIES,
            region_indices=[0],
            delta_spec="Raise arbitration priority of stability envelope to MAX",
            rationale="Prevents rival policies from overriding safety during reset",
            expected_impact=-0.05,
            risk_level="low",
        )

        return [all_region, gate_plan]

    # ── Utility ────────────────────────────────────────────────────────────

    def plan_summary(self, spec: MutationExecutionSpec) -> str:
        """Human-readable planning summary."""
        lines = [
            f"[MutationPlanner] {spec.policy_mode.upper()} | severity={spec.severity}",
            f"  Regions touched: {spec.total_regions_touched}/{spec.theta_dim}",
            f"  Plans: {len(spec.plans)}",
        ]
        for i, p in enumerate(spec.plans):
            lines.append(
                f"  [{i+1}] {p.target.value}  "
                f"dims={p.region_indices}  "
                f"impact={p.expected_impact:+.2f}  "
                f"risk={p.risk_level}"
            )
        return "\n".join(lines)
