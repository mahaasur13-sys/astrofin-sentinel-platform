"""
DriftPolicyAdaptor — v7.8
Actuates policy changes in response to detected drift.
Converts ProofDriftDetector output → actionable policy modifications.
"""
from __future__ import annotations

from dataclasses import dataclass

from proof.proof_drift_detector import DriftType
from proof.temporal_verifier import TemporalVerificationReport


@dataclass
class PolicyChange:
    policy_name: str
    parameter: str
    old_value: float
    new_value: float
    reason: str


# Default thresholds per drift type severity
DRIFT_THRESHOLDS = {
    DriftType.SOURCE_SWITCH: 0.15,
    DriftType.REASONING_COLLAPSE: 0.25,
    DriftType.CAUSAL_BREAK: 0.35,
    DriftType.PROOF_REGRESSION: 0.5,
}

# How much to adjust the policy parameter per unit of drift severity
ADJUSTMENT_RATES = {
    DriftType.SOURCE_SWITCH: 0.05,
    DriftType.REASONING_COLLAPSE: 0.10,
    DriftType.CAUSAL_BREAK: 0.15,
    DriftType.PROOF_REGRESSION: 0.20,
}


class DriftPolicyAdaptor:
    """
    Converts temporal verification reports into policy parameter adjustments.
    Acts as the actuator for the drift detection pipeline.

    Example:
        adaptor = DriftPolicyAdaptor()
        report = verifier.verify(chain, graph)
        changes = adaptor.compute_policy_changes(report)
        # changes → list[PolicyChange] to apply to control layer
    """

    def __init__(self):
        self._active_policies: dict[str, dict[str, float]] = {}
        self._drift_history: list[DriftType] = []

    def register_policy(self, name: str, params: dict[str, float]):
        """Register a policy with its current parameter values."""
        self._active_policies[name] = dict(params)

    def compute_policy_changes(
        self,
        report: TemporalVerificationReport,
    ) -> list[PolicyChange]:
        changes: list[PolicyChange] = []

        for drift in report.drift_events:
            self._drift_history.append(drift.drift_type)
            severity = self._compute_severity(drift.drift_type, report)
            policy, param, old_val = self._select_policy_param(drift.drift_type)
            if policy is None:
                continue

            rate = ADJUSTMENT_RATES.get(drift.drift_type, 0.1)
            adjustment = rate * severity
            new_val = old_val - adjustment if drift.drift_type in (
                DriftType.REASONING_COLLAPSE, DriftType.PROOF_REGRESSION
            ) else old_val + adjustment

            # Clamp to [0, 1]
            new_val = max(0.0, min(1.0, new_val))

            self._active_policies[policy][param] = new_val

            changes.append(PolicyChange(
                policy_name=policy,
                parameter=param,
                old_value=old_val,
                new_value=new_val,
                reason=str(drift.drift_type),
            ))

        return changes

    def _compute_severity(
        self, drift_type: DriftType, report: TemporalVerificationReport
    ) -> float:
        """Map drift type + report context → severity [0, 1]."""
        base = DRIFT_THRESHOLDS.get(drift_type, 0.2)
        # Amplify if the overall stability is very low
        if report.overall_stability < 0.4:
            base *= 1.5
        elif report.overall_stability < 0.6:
            base *= 1.2
        return min(1.0, base)

    def _select_policy_param(
        self, drift_type: DriftType
    ) -> tuple[Optional[str], Optional[str], Optional[float]]:
        """
        Map drift type → (policy_name, parameter, current_value).
        Returns (None, ...) if no policy is registered for this drift type.
        """
        mapping = {
            DriftType.SOURCE_SWITCH: ("arbitration", "switch_threshold"),
            DriftType.REASONING_COLLAPSE: ("arbitration", "coherence_weight"),
            DriftType.CAUSAL_BREAK: ("proof", "causal_depth_min"),
            DriftType.PROOF_REGRESSION: ("proof", "validity_threshold"),
        }
        key = mapping.get(drift_type)
        if key is None:
            return None, None, None
        policy_name, param = key
        if policy_name not in self._active_policies:
            return None, None, None
        current = self._active_policies[policy_name].get(param, 0.5)
        return policy_name, param, current

    def get_policy(self, name: str) -> dict[str, float]:
        return dict(self._active_policies.get(name, {}))

    def drift_frequency(self, drift_type: DriftType, window: int = 10) -> float:
        """Return fraction of last `window` drift events matching drift_type."""
        recent = self._drift_history[-window:]
        if not recent:
            return 0.0
        return recent.count(drift_type) / len(recent)
