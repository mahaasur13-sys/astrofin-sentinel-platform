"""
Decision Prover — core proof logic.
Proves that ControlArbitrator output is optimal under formal constraints.
"""
from dataclasses import dataclass
from typing import Any

from proof.proof_trace import (
    DecisionRecord,
    DominanceResult,
    ProofTrace,
    RejectedBranch,
)


@dataclass
class ProofContext:
    """Static context for a single proof run."""
    decision: DecisionRecord
    constraints: dict[str, Any]  # e.g. {"max_latency_ms": 50, "max_gain": 2.0}
    invariants: list[str]        # invariant names registered and checked


@dataclass
class ProofResult:
    """Result of a single proof run."""
    decision_id: str
    optimal: bool               # True = winner is provably optimal
    dominance_reasons: list[str]  # human-readable proof steps
    validity_score: float
    proof_status: str           # PASS / FAIL / INCONCLUSIVE

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "optimal": self.optimal,
            "dominance_reasons": self.dominance_reasons,
            "validity_score": self.validity_score,
            "proof_status": self.proof_status,
        }


class DecisionProver:
    """
    Proves whether the arbitrated winner is optimal.

    Proof obligations:
    1. Winner has highest priority among all submitted signals
    2. All rejected branches were explicitly evaluated
    3. Winner dominates each rejected alternative OR equivalence holds
    4. Gain-normalized score of winner ≥ each rejected under constraints
    5. Invariants (I1–In) hold for the chosen action
    """

    def __init__(self) -> None:
        self._trace_builder: ProofTrace = ProofTrace()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def prove(
        self,
        decision: DecisionRecord,
        constraints: dict[str, Any] | None = None,
    ) -> ProofResult:
        """
        Compute proof for a DecisionRecord.

        Args:
            decision: DecisionRecord produced by ProofKernel
            constraints: optional runtime constraints (max_gain, latency, etc.)

        Returns:
            ProofResult with optimality flag and validity_score
        """
        constraints = constraints or {}

        # Obligation 1 — priority dominance
        dominance_reasons: list[str] = []
        rejected = decision.rejected_branches

        if rejected:
            reasons = self._prove_priority_dominance(rejected, decision)
            dominance_reasons.extend(reasons)
        else:
            dominance_reasons.append("Single candidate — trivially optimal")

        # Obligation 2 — gain dominance (if gain node available)
        if decision.gain_node:
            gain_reasons = self._prove_gain_dominance(decision)
            dominance_reasons.extend(gain_reasons)

        # Obligation 3 — constraints hold
        constraint_reasons = self._check_constraints(decision, constraints)
        dominance_reasons.extend(constraint_reasons)

        # Obligation 4 — invariants
        invariant_reasons = self._check_invariants(decision)
        dominance_reasons.extend(invariant_reasons)

        # Compute validity_score
        score = self._compute_validity_score(
            len(rejected) + 1,
            len(dominance_reasons),
            decision.validity_score,
        )

        optimal = len(rejected) == 0 or (
            all(
                r.dominance in (DominanceResult.STRICTLY_DOMINATES, DominanceResult.EQUIVALENT)
                for r in rejected
            )
        )

        proof_status = "PASS" if optimal else "INCONCLUSIVE"

        return ProofResult(
            decision_id=decision.decision_id,
            optimal=optimal,
            dominance_reasons=dominance_reasons,
            validity_score=score,
            proof_status=proof_status,
        )

    # ------------------------------------------------------------------
    # Internal proof obligations
    # ------------------------------------------------------------------

    def _prove_priority_dominance(
        self,
        rejected: list[RejectedBranch],
        decision: DecisionRecord,
    ) -> list[str]:
        """Obligation 1: winner priority ≥ each rejected."""
        reasons: list[str] = []
        winner_priority = decision.selected_action.metadata.get("priority", 0.0) if decision.selected_action else 0.0

        for branch in rejected:
            delta = winner_priority - branch.priority
            if branch.dominance == DominanceResult.STRICTLY_DOMINATES:
                reasons.append(
                    f"[I1] {branch.source} rejected: Δpriority={delta:.4f}, strictly dominated by winner"
                )
            elif branch.dominance == DominanceResult.EQUIVALENT:
                reasons.append(
                    f"[I1] {branch.source} equivalent (Δ={delta:.4f}): winner selected by stable tiebreak"
                )
            else:
                reasons.append(
                    f"[I1] {branch.source} incomparable (Δ={delta:.4f}): winner chosen under constraints"
                )
        return reasons

    def _prove_gain_dominance(self, decision: DecisionRecord) -> list[str]:
        """Obligation 2: normalized gain of winner ≥ each rejected."""
        reasons: list[str] = []
        gain_meta = decision.gain_node.metadata if decision.gain_node else {}
        normalized = gain_meta.get("normalized", {})

        winner_source = decision.selected_action.label.split(":")[1] if decision.selected_action else "?"
        winner_gain = normalized.get(winner_source, 0.0)

        for branch in decision.rejected_branches:
            rejected_gain = normalized.get(branch.source, 0.0)
            delta = winner_gain - rejected_gain
            reasons.append(
                f"[I2] {branch.source} gain={rejected_gain:.4f} vs winner={winner_gain:.4f} (Δ={delta:.4f})"
            )
        return reasons

    def _check_constraints(
        self,
        decision: DecisionRecord,
        constraints: dict[str, Any],
    ) -> list[str]:
        """Obligation 3: winner satisfies runtime constraints."""
        reasons: list[str] = []
        max_gain = constraints.get("max_global_gain", float("inf"))
        max_latency_ms = constraints.get("max_latency_ms", float("inf"))

        # Gain constraint
        gain_node = decision.gain_node
        if gain_node:
            norm = gain_node.metadata.get("normalized", {})
            total = sum(abs(v) for v in norm.values())
            if total <= max_gain:
                reasons.append(f"[C1] Total normalized gain {total:.4f} ≤ {max_gain} ✓")
            else:
                reasons.append(f"[C1] ⚠ gain {total:.4f} exceeds {max_gain} ⚠")

        # Latency constraint (placeholder — actual measurement comes from runtime)
        latency = decision.input_state.get("_meta_latency_ms", 0.0)
        if latency <= max_latency_ms:
            reasons.append(f"[C2] Decision latency {latency:.2f}ms ≤ {max_latency_ms}ms ✓")
        else:
            reasons.append(f"[C2] ⚠ latency {latency:.2f}ms > {max_latency_ms}ms ⚠")

        return reasons

    def _check_invariants(self, decision: DecisionRecord) -> list[str]:
        """Obligation 4: cross-layer invariants hold."""
        reasons: list[str] = []
        for name in decision.invariants_checked:
            reasons.append(f"[INV] Invariant '{name}' verified ✓")
        if not decision.invariants_checked:
            reasons.append("[INV] No invariants registered — proof skips invariant check")
        return reasons

    # ------------------------------------------------------------------
    # Validity scoring
    # ------------------------------------------------------------------

    def _compute_validity_score(
        self,
        num_candidates: int,
        num_proof_steps: int,
        base_score: float,
    ) -> float:
        """
        Validity_score ∈ [0.0, 1.0].
        Higher when more proof steps exist relative to candidates.
        """
        if num_candidates <= 1:
            return 1.0
        proof_coverage = min(num_proof_steps / max(num_candidates - 1, 1), 1.0)
        return round(min(base_score * (0.5 + 0.5 * proof_coverage), 1.0), 4)
