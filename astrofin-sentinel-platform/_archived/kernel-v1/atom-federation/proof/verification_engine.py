"""
Verification Engine — cross-layer proof checks.
Drives the invariant registry and decision prover over full decision records.
"""
from dataclasses import dataclass, field
from typing import Any

from proof.decision_prover import DecisionProver, ProofResult
from proof.invariant_registry import InvariantRegistry
from proof.proof_trace import DecisionRecord


@dataclass
class LayerCheck:
    """Result of a single layer verification."""
    layer: str
    passed: bool
    details: str
    proof_steps: list[str] = field(default_factory=list)


@dataclass
class VerificationReport:
    """Full verification report for a decision."""
    decision_id: str
    timestamp: float
    invariant_results: dict[str, bool]
    layer_checks: list[LayerCheck]
    proof_result: ProofResult
    overall_passed: bool
    failed_invariants: list[str]
    failed_layers: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "timestamp": self.timestamp,
            "invariant_results": self.invariant_results,
            "layer_checks": [
                {
                    "layer": lc.layer,
                    "passed": lc.passed,
                    "details": lc.details,
                    "proof_steps": lc.proof_steps,
                }
                for lc in self.layer_checks
            ],
            "proof_result": self.proof_result.to_dict(),
            "overall_passed": self.overall_passed,
            "failed_invariants": self.failed_invariants,
            "failed_layers": self.failed_layers,
        }


class VerificationEngine:
    """
    Cross-layer verification driver.

    Runs invariant checks and proof obligations across all registered
    control layers (DRL / SBS / Coherence / Actuator) for each decision.
    """

    def __init__(self) -> None:
        self._registry = InvariantRegistry()
        self._prover = DecisionProver()
        self._layers = ["drl", "sbs", "coherence", "actuator"]

    # ─── Public API ───────────────────────────────────────────────────────

    def verify(self, record: DecisionRecord) -> VerificationReport:
        """
        Run full verification on a DecisionRecord.

        Steps:
        1. Check all registered invariants (I1–In)
        2. Run per-layer checks
        3. Run decision prover
        4. Compile VerificationReport
        """
        # 1. Invariant checks
        invariant_results = self._registry.check(record)

        # 2. Per-layer checks
        layer_checks = self._run_layer_checks(record)

        # 3. Decision proof
        proof_result = self._prover.prove(record)

        # 4. Compile report
        failed_invariants = [k for k, v in invariant_results.items() if not v]
        failed_layers = [lc.layer for lc in layer_checks if not lc.passed]

        overall_passed = (
            all(invariant_results.values())
            and all(lc.passed for lc in layer_checks)
            and proof_result.optimal
        )

        return VerificationReport(
            decision_id=record.decision_id,
            timestamp=record.timestamp,
            invariant_results=invariant_results,
            layer_checks=layer_checks,
            proof_result=proof_result,
            overall_passed=overall_passed,
            failed_invariants=failed_invariants,
            failed_layers=failed_layers,
        )

    def verify_batch(self, records: list[DecisionRecord]) -> list[VerificationReport]:
        """Verify a batch of decision records."""
        return [self.verify(r) for r in records]

    @property
    def registry(self) -> InvariantRegistry:
        """Direct access to invariant registry."""
        return self._registry

    # ─── Internal ────────────────────────────────────────────────────────

    def _run_layer_checks(self, record: DecisionRecord) -> list[LayerCheck]:
        checks: list[LayerCheck] = []

        # DRL layer: winner priority within [0, 1]
        drl_check = self._check_drl_layer(record)
        checks.append(drl_check)

        # SBS layer: coherence consistency
        sbs_check = self._check_sbs_layer(record)
        checks.append(sbs_check)

        # Coherence layer: temporal smoothness
        coherence_check = self._check_coherence_layer(record)
        checks.append(coherence_check)

        # Actuator layer: gain normalization applied
        actuator_check = self._check_actuator_layer(record)
        checks.append(actuator_check)

        return checks

    def _check_drl_layer(self, record: DecisionRecord) -> LayerCheck:
        winner_priority = (
            record.selected_action.metadata.get("priority", 0.0)
            if record.selected_action else 0.0
        )
        passed = 0.0 <= winner_priority <= 1.0
        return LayerCheck(
            layer="drl",
            passed=passed,
            details=f"DRL priority={winner_priority:.4f} ∈ [0,1] {'✓' if passed else '✗'}",
            proof_steps=[
                f"Priority {winner_priority:.4f} checked: 0.0 ≤ p ≤ 1.0",
            ],
        )

    def _check_sbs_layer(self, record: DecisionRecord) -> LayerCheck:
        if record.arbitration_node is None:
            return LayerCheck(layer="sbs", passed=True, details="No SBS node — SKIP")
        winner = record.arbitration_node.metadata.get("winner", "")
        all_sources = [
            c.metadata.get("source", "?")
            for c in record.arbitration_node.children
        ]
        passed = winner in all_sources
        return LayerCheck(
            layer="sbs",
            passed=passed,
            details=f"SBS winner='{winner}' in {all_sources} {'✓' if passed else '✗'}",
            proof_steps=[
                f"Winner '{winner}' verified in submitted sources",
            ],
        )

    def _check_coherence_layer(self, record: DecisionRecord) -> LayerCheck:
        if record.conflict_node is None:
            return LayerCheck(layer="coherence", passed=True, details="No conflict node — SKIP")
        conflict_meta = record.conflict_node.metadata
        winner = conflict_meta.get("winner", "")
        candidates = conflict_meta.get("candidates", [])
        passed = winner in candidates
        return LayerCheck(
            layer="coherence",
            passed=passed,
            details=f"Coherence winner='{winner}' in {candidates} {'✓' if passed else '✗'}",
            proof_steps=[
                f"Coherence winner '{winner}' exists in candidate set",
            ],
        )

    def _check_actuator_layer(self, record: DecisionRecord) -> LayerCheck:
        if record.gain_node is None:
            return LayerCheck(layer="actuator", passed=False, details="No gain node — FAIL")
        norm = record.gain_node.metadata.get("normalized", {})
        max_gain = record.input_state.get("_meta_max_global_gain", 2.0)
        total = sum(abs(v) for v in norm.values())
        passed = total <= max_gain
        return LayerCheck(
            layer="actuator",
            passed=passed,
            details=f"Total gain={total:.4f} ≤ max={max_gain} {'✓' if passed else '✗'}",
            proof_steps=[
                f"Gain normalization verified: total={total:.4f}",
            ],
        )
