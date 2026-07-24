"""Reality Consensus Fusion (RCF) layer — v11.1.

This layer observes the outputs of:
  * OTL (trusted sensor fusion)
  * GSL (soundness score)
  * GCPL/BCIL/ADLR (model convergence, Byzantine safety, liveness recovery)
  * branch.py / BranchStore (branch entropy)

RCF only observes and produces decisions; it never mutates events or bypasses quorum logic.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from enum import Enum
from statistics import variance


class StabilityLevel(str, Enum):
    STABLE = "STABLE"
    UNSTABLE = "UNSTABLE"
    CRITICAL = "CRITICAL"


@dataclass
class Action:
    name: str
    reason: str
    tags: Sequence[str] = field(default_factory=tuple)


@dataclass
class ConsensusReport:
    consensus_score: float
    stability: StabilityLevel
    drift_vector: dict
    chosen_branch: str
    trust_distribution: dict[str, float]
    actions: list[Action]
    metrics: dict[str, float]


class RCF:
    """Reality Consensus Fusion observer + decision layer."""

    def __init__(
        self,
        weight_otl: float = 0.25,
        weight_gsl: float = 0.20,
        weight_gcpl: float = 0.20,
        weight_bcil: float = 0.20,
        weight_entropy: float = 0.15,
    ) -> None:
        total = weight_otl + weight_gsl + weight_gcpl + weight_bcil + weight_entropy
        if abs(total - 1.0) > 1e-6:
            raise ValueError("RCF weights must sum to 1")
        self.w_otl = weight_otl
        self.w_gsl = weight_gsl
        self.w_gcpl = weight_gcpl
        self.w_bcil = weight_bcil
        self.w_entropy = weight_entropy

    def evaluate(
        self,
        model_state: dict,
        observed_state: dict,
        sensor_bundle: dict,
        branch_state: dict,
    ) -> ConsensusReport:
        """Compute reality consensus and pick actions."""
        otl_fusion = observed_state.get("fusion_score", 0.0)
        gsl_score = observed_state.get("soundness_score", model_state.get("gsl_score", 0.0))
        gcpl_C = model_state.get("gcpl_C", 0.0)
        bcil_safety = model_state.get("bcil_safety", 0.0)
        branch_entropy = branch_state.get("entropy", 0.0)
        branch_id = branch_state.get("current_branch", "primary")
        branch_state.get("status", "nominal")

        drift_vector = {
            "model_vs_observed": otl_fusion - gcpl_C,
            "soundness_gap": gsl_score - otl_fusion,
            "branch_entropy": branch_entropy,
        }

        raw_score = (
            self.w_otl * otl_fusion
            + self.w_gsl * gsl_score
            + self.w_gcpl * gcpl_C
            + self.w_bcil * bcil_safety
            - self.w_entropy * branch_entropy
        )
        consensus_score = self._clamp(raw_score)
        stability = self._classify(consensus_score)

        trust_distribution = sensor_bundle.get("trust", {})
        trust_variance = self._safe_variance(trust_distribution.values())

        sensor_agreement = self._sensor_agreement(sensor_bundle)
        cross_layer_divergence = abs(otl_fusion - gcpl_C) + abs(gsl_score - otl_fusion)

        actions: list[Action] = []
        if stability == StabilityLevel.CRITICAL:
            actions.append(Action("ROLLBACK_SHADOW", "RCF detected critical drift", ("rollback", "shadow")))
            actions.append(Action("ADLR_FORCE_SELECT", "Liveness recovery trigger", ("liveness",)))
            actions.append(Action("BCIL_SOFT_VETO", "Request Byzantine soft veto", ("byzantine",)))
            actions.append(Action("ISOLATE_BRANCH", "High entropy branch isolation", ("branch",)))
        elif stability == StabilityLevel.UNSTABLE:
            actions.append(Action("REWEIGHT_SENSORS", "Boost trust decay", ("sensors",)))
            actions.append(Action("GSL_RECONCILE", "Soundness reconciliation", ("soundness",)))
            actions.append(Action("ADLR_INCREASE_PRESSURE", "Increase trust decay pressure", ("liveness",)))
        else:  # STABLE
            actions.append(Action("ALLOW_GCPL_MERGE", "GCPL merge allowed", ("merge",)))
            actions.append(Action("ALLOW_BRANCH_CONVERGENCE", "Branch entropy contained", ("branch",)))
            actions.append(Action("RESET_OSCILLATION", "Clear oscillation counters", ("observability",)))

        metrics = {
            "reality_consensus_score": consensus_score,
            "sensor_agreement_index": sensor_agreement,
            "branch_entropy": branch_entropy,
            "cross_layer_divergence": cross_layer_divergence,
            "trust_weight_variance": trust_variance,
        }

        return ConsensusReport(
            consensus_score=consensus_score,
            stability=stability,
            drift_vector=drift_vector,
            chosen_branch=branch_id if stability != StabilityLevel.CRITICAL else branch_id + "-isolated",
            trust_distribution=trust_distribution,
            actions=actions,
            metrics=metrics,
        )

    def _classify(self, score: float) -> StabilityLevel:
        if score >= 0.70:
            return StabilityLevel.STABLE
        if score >= 0.40:
            return StabilityLevel.UNSTABLE
        return StabilityLevel.CRITICAL

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, value))

    @staticmethod
    def _sensor_agreement(sensor_bundle: dict) -> float:
        values = sensor_bundle.get("fusion_quality", [])
        if not values:
            return 0.0
        avg = sum(values) / len(values)
        if len(values) == 1:
            return avg
        return max(0.0, min(1.0, avg * (len(values) / (len(values) + 1))))

    @staticmethod
    def _safe_variance(values: Iterable[float]) -> float:
        values = [v for v in values if v is not None]
        if len(values) < 2:
            return 0.0
        try:
            return variance(values)
        except Exception:
            return 0.0
