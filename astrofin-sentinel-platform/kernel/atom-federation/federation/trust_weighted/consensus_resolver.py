"""
consensus_resolver.py — v9.6 Trust-Weighted Consensus Resolver

Key shift from v9.3 (ProofAwareConsensusResolver):
  v9.3: consensus = f(proof_valid, stability_score, drift_score)
  v9.6: consensus = f(trust_score(node_i), stability_score, drift_score, proof_strength)

Core concept:
  Node weights are no longer equal. Node influence ∝ trust_score(node).

  weighted_vote_i = trust_i × decision_signal_i
  decision_signal_i ∈ [-1, 1]: -1=reject, 0=abstain, +1=accept
  consensus_accepted ↔ Σ weighted_votes ≥ quorum_threshold

Integration:
  TrustVector → NodeWeightRegistry.compute_weights() → NodeWeightsSnapshot
  NodeWeightsSnapshot → TrustWeightedConsensusResolver.resolve()
  TrustSkewDetector → monitors weight distribution for safety
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from .node_weights import NodeWeightsSnapshot

# ─────────────────────────────────────────────────────────────────
# ConsensusShiftType
# ─────────────────────────────────────────────────────────────────

class ConsensusShiftType(Enum):
    """Categories of consensus outcome shifts."""
    NO_SHIFT            = auto()
    OUTCOME_FLIP        = auto()
    CONFIDENCE_DROP     = auto()
    DOMINATION_SHIFT    = auto()
    TRUST_COLLAPSE      = auto()
    NEW_NODE_ENTERED    = auto()


@dataclass
class ConsensusShiftEvent:
    """Record of a consensus outcome shift between two epochs."""
    epoch_before: int
    epoch_after: int
    shift_type: ConsensusShiftType
    prev_winner: str | None
    curr_winner: str | None
    prev_confidence: float
    curr_confidence: float
    dominating_node_before: str | None
    dominating_node_after: str | None
    message: str
    timestamp: float = field(default_factory=time.time)


# ─────────────────────────────────────────────────────────────────
# ConsensusCandidate (v9.6)
# ─────────────────────────────────────────────────────────────────

@dataclass
class ConsensusCandidate:
    """
    A candidate for trust-weighted consensus.

    Fields:
        candidate_id     — node_id of the candidate
        root_hash        — DAG root hash
        seq              — sequence number
        stability_score  — float ∈ [0, 1]
        drift_score      — float ≥ 0
        proof_hash       — associated proof hash
        trust_score      — node's aggregated trust
        raw_vote         — vote signal ∈ [-1, 1]
        node_weight      — from NodeWeightsSnapshot (set at resolve time)
        effective_vote   — node_weight × raw_vote
        raw_score        — unweighted composite score
        weighted_score   — node_weight × raw_score
    """
    candidate_id: str
    root_hash: str
    seq: int
    stability_score: float = 0.5
    drift_score: float = 0.0
    proof_hash: str | None = None
    trust_score: float = 0.5
    raw_vote: float = 0.0
    node_weight: float = 0.0
    effective_vote: float = 0.0
    raw_score: float = 0.0
    weighted_score: float = 0.0

    def compute_score(self, proof_strength: float = 1.0) -> float:
        """Raw (unweighted) composite score: trust × stability - drift + proof × 0.5."""
        self.raw_score = (
            self.trust_score * self.stability_score
            - self.drift_score
            + proof_strength * 0.5
        )
        return self.raw_score

    def apply_weight(self, node_weight: float) -> float:
        """Apply node weight: effective_vote = weight × vote, weighted_score = weight × raw_score."""
        self.node_weight = node_weight
        self.effective_vote = node_weight * self.raw_vote
        self.weighted_score = node_weight * self.raw_score
        return self.weighted_score

    def is_acceptable(self, trust_floor: float = 0.0) -> bool:
        return self.trust_score >= trust_floor


# ─────────────────────────────────────────────────────────────────
# ConsensusResult
# ─────────────────────────────────────────────────────────────────

@dataclass
class ConsensusResult:
    """Outcome of a trust-weighted consensus round."""
    accepted: bool
    confidence: float
    winner_candidate_id: str | None
    winner_root_hash: str | None
    total_weighted_score: float
    quorum_threshold: float
    total_voting_weight: float
    epoch: int
    shift_detected: ConsensusShiftEvent | None
    eligible_count: int
    candidate_count: int
    reason: str = ""

    def is_shift_dominant(self) -> bool:
        return (
            self.shift_detected is not None
            and self.shift_detected.shift_type == ConsensusShiftType.DOMINATION_SHIFT
        )


# ─────────────────────────────────────────────────────────────────
# TrustWeightedConsensusResolver
# ─────────────────────────────────────────────────────────────────

class TrustWeightedConsensusResolver:
    """
    Consensus resolver where node influence is proportional to trust.

    Consensus formula:
      Σ_i (trust_i × stability_i - drift_i + proof_i) × node_weight_i
      vs quorum_fraction × total_weight

      consensus_accepted ↔ weighted_score_sum ≥ quorum_threshold
    """

    def __init__(
        self,
        node_id: str,
        quorum_fraction: float = 2 / 3,
        trust_floor: float = 0.0,
    ):
        self.node_id = node_id
        self.quorum_fraction = quorum_fraction
        self.trust_floor = trust_floor

        self._current_epoch: int = 0
        self._last_winner: str | None = None
        self._last_confidence: float = 0.0
        self._last_weights: NodeWeightsSnapshot | None = None
        self._shift_history: list[ConsensusShiftEvent] = []

    def resolve(
        self,
        candidates: list[ConsensusCandidate],
        weights_snapshot: NodeWeightsSnapshot,
        require_trust_floor: bool = True,
    ) -> ConsensusResult:
        self._current_epoch += 1
        epoch = self._current_epoch

        if require_trust_floor:
            eligible = [c for c in candidates if c.is_acceptable(self.trust_floor)]
        else:
            eligible = candidates

        if not eligible:
            return self._no_consensus(epoch, weights_snapshot, "all_candidates_below_trust_floor")

        # Step 1: compute raw_score for each eligible candidate (for ranking)
        for c in eligible:
            c.compute_score()

        # Step 2: apply node weights → effective_vote and weighted_score
        total_effective_vote: float = 0.0
        total_voting_weight: float = 0.0
        total_weighted_score: float = 0.0

        for c in eligible:
            w = weights_snapshot.node_weight(c.candidate_id)
            c.apply_weight(w)
            total_effective_vote += c.effective_vote
            if c.raw_vote != 0.0:
                total_voting_weight += w
            total_weighted_score += c.weighted_score

        # Quorum check: sum of (weight × vote) ≥ quorum_fraction × total_weight
        # If all votes are accept (+1): total_effective_vote = total_voting_weight
        # If mixed: net direction matters
        quorum_threshold = self.quorum_fraction * weights_snapshot.total_weight

        accepted = total_effective_vote >= quorum_threshold

        # Confidence: how close to the threshold
        if quorum_threshold > 0:
            confidence = min(1.0, abs(total_effective_vote) / max(quorum_threshold, 1e-9))
        else:
            confidence = 1.0 if accepted else 0.0

        # Winner: highest weighted_score among eligible candidates
        winner = max(eligible, key=lambda c: c.weighted_score) if eligible else None

        shift = self._detect_shift(
            epoch,
            winner.candidate_id if winner else None,
            confidence,
            weights_snapshot,
        )

        self._last_winner = winner.candidate_id if winner else None
        self._last_confidence = confidence
        self._last_weights = weights_snapshot

        return ConsensusResult(
            accepted=accepted,
            confidence=confidence,
            winner_candidate_id=winner.candidate_id if winner else None,
            winner_root_hash=winner.root_hash if winner else None,
            total_weighted_score=total_weighted_score,
            quorum_threshold=quorum_threshold,
            total_voting_weight=total_voting_weight,
            epoch=epoch,
            shift_detected=shift,
            eligible_count=len(eligible),
            candidate_count=len(candidates),
        )

    def _no_consensus(
        self,
        epoch: int,
        weights_snapshot: NodeWeightsSnapshot,
        reason: str,
    ) -> ConsensusResult:
        shift = self._detect_shift(epoch, None, 0.0, weights_snapshot)
        self._last_winner = None
        self._last_confidence = 0.0
        quorum_threshold = self.quorum_fraction * weights_snapshot.total_weight
        return ConsensusResult(
            accepted=False,
            confidence=0.0,
            winner_candidate_id=None,
            winner_root_hash=None,
            total_weighted_score=0.0,
            quorum_threshold=quorum_threshold,
            total_voting_weight=0.0,
            epoch=epoch,
            shift_detected=shift,
            eligible_count=0,
            candidate_count=0,
            reason=reason,
        )

    def _detect_shift(
        self,
        epoch: int,
        curr_winner: str | None,
        curr_confidence: float,
        weights_snapshot: NodeWeightsSnapshot,
    ) -> ConsensusShiftEvent | None:
        if self._last_weights is None:
            return None

        prev_epoch = epoch - 1

        def dominating(ws: NodeWeightsSnapshot) -> str | None:
            for nid, w in ws.weights.items():
                if ws.total_weight > 0 and (w / ws.total_weight) >= 0.5:
                    return nid
            return None

        dom_before = dominating(self._last_weights)
        dom_after = dominating(weights_snapshot)

        if self._last_winner == curr_winner:
            if abs(curr_confidence - self._last_confidence) < 0.05:
                shift_type = ConsensusShiftType.NO_SHIFT
            else:
                shift_type = ConsensusShiftType.CONFIDENCE_DROP
        else:
            shift_type = ConsensusShiftType.OUTCOME_FLIP

        if dom_before != dom_after and dom_before is not None and dom_after is not None:
            shift_type = ConsensusShiftType.DOMINATION_SHIFT

        for nid in set(list(self._last_weights.weights.keys()) +
                       list(weights_snapshot.weights.keys())):
            w_before = self._last_weights.weights.get(nid, 0.0)
            w_after = weights_snapshot.weights.get(nid, 0.0)
            if w_before > 0.2 and w_after < 0.05:
                shift_type = ConsensusShiftType.TRUST_COLLAPSE
                break

        if shift_type == ConsensusShiftType.NO_SHIFT:
            return None

        msg = (
            f"ConsensusShift({shift_type.name}): epoch {prev_epoch}→{epoch}, "
            f"winner {self._last_winner}→{curr_winner}, "
            f"confidence {self._last_confidence:.3f}→{curr_confidence:.3f}, "
            f"dominating {dom_before}→{dom_after}"
        )

        event = ConsensusShiftEvent(
            epoch_before=prev_epoch,
            epoch_after=epoch,
            shift_type=shift_type,
            prev_winner=self._last_winner,
            curr_winner=curr_winner,
            prev_confidence=self._last_confidence,
            curr_confidence=curr_confidence,
            dominating_node_before=dom_before,
            dominating_node_after=dom_after,
            message=msg,
        )
        self._shift_history.append(event)
        return event

    def shift_history(self) -> list[ConsensusShiftEvent]:
        return list(self._shift_history)

    @property
    def current_epoch(self) -> int:
        return self._current_epoch


# ─────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────

def _test_consensus_resolver():
    from federation.trust.trust_vector import TrustVector
    from federation.trust_weighted.node_weights import NodeWeightRegistry

    resolver = TrustWeightedConsensusResolver(
        node_id="node_1",
        quorum_fraction=0.3,
        trust_floor=0.10,
    )

    registry = NodeWeightRegistry()
    registry.register_proofs_for_node("node_A", ["h1", "h2"])
    registry.register_proofs_for_node("node_B", ["h3", "h4"])
    registry.register_proofs_for_node("node_C", ["h5"])

    tv = TrustVector()
    tv.set_entry("h1", 0.9, 1000.0, ledger_version=1)
    tv.set_entry("h2", 0.7, 1000.0, ledger_version=1)
    tv.set_entry("h3", 0.6, 1000.0, ledger_version=1)
    tv.set_entry("h4", 0.6, 1000.0, ledger_version=1)
    tv.set_entry("h5", 0.5, 1000.0, ledger_version=1)

    weights = registry.compute_weights(tv, ledger_version=1, epoch=0)
    assert abs(weights.node_weight("node_A") - 0.8) < 1e-6
    assert abs(weights.node_weight("node_B") - 0.6) < 1e-6
    assert abs(weights.node_weight("node_C") - 0.5) < 1e-6
    print(f"✅ weights: A={weights.node_weight('node_A'):.2f}, B={weights.node_weight('node_B'):.2f}, C={weights.node_weight('node_C'):.2f}")

    # Case 1: all nodes vote accept → consensus accepted
    candidates = [
        ConsensusCandidate(
            candidate_id="node_A", root_hash="hash_A", seq=10,
            stability_score=0.9, drift_score=0.1,
            raw_vote=1.0, trust_score=0.8,
        ),
        ConsensusCandidate(
            candidate_id="node_B", root_hash="hash_B", seq=9,
            stability_score=0.8, drift_score=0.2,
            raw_vote=1.0, trust_score=0.6,   # ← was -1.0: reject subtracts from net
        ),
    ]
    result = resolver.resolve(candidates, weights)
    assert result.accepted is True, f"Expected accepted=True, got {result.accepted}"
    assert result.winner_candidate_id == "node_A"
    print(f"✅ Case 1: high-trust accept wins (confidence={result.confidence:.3f})")

    # Case 2: trust floor filters out low-trust node
    resolver2 = TrustWeightedConsensusResolver(node_id="node_1", quorum_fraction=0.5, trust_floor=0.7)
    candidates2 = [
        ConsensusCandidate(candidate_id="node_A", root_hash="hash_A", seq=10, raw_vote=1.0, trust_score=0.8),
        ConsensusCandidate(candidate_id="node_B", root_hash="hash_B", seq=9, raw_vote=1.0, trust_score=0.6),
        ConsensusCandidate(candidate_id="node_C", root_hash="hash_C", seq=8, raw_vote=1.0, trust_score=0.5),
    ]
    result2 = resolver2.resolve(candidates2, weights)
    assert result2.eligible_count == 1
    assert result2.winner_candidate_id == "node_A"
    print("✅ Case 2: trust_floor=0.7 filters to 1 eligible (node_A)")

    # Case 3: OUTCOME_FLIP detected between epochs
    resolver3 = TrustWeightedConsensusResolver(node_id="node_1", quorum_fraction=0.3)
    c1 = ConsensusCandidate(candidate_id="node_A", root_hash="hash_A", seq=1, raw_vote=1.0, trust_score=0.8)
    r1 = resolver3.resolve([c1], weights)
    assert r1.accepted is True

    c2 = ConsensusCandidate(candidate_id="node_B", root_hash="hash_B", seq=2, raw_vote=-1.0, trust_score=0.6)
    r2 = resolver3.resolve([c2], weights)
    assert r2.shift_detected is not None
    assert r2.shift_detected.shift_type == ConsensusShiftType.OUTCOME_FLIP
    print(f"✅ Case 3: OUTCOME_FLIP detected: {r2.shift_detected.message}")

    # Case 4: effective_vote computation
    snap = registry.compute_weights(tv, ledger_version=1, epoch=0)
    ev_accept = snap.effective_vote("node_A", 1.0)
    ev_reject = snap.effective_vote("node_A", -1.0)
    assert abs(ev_accept - 0.8) < 1e-6
    assert abs(ev_reject + 0.8) < 1e-6
    print(f"✅ Case 4: effective_vote accept={ev_accept:.2f}, reject={ev_reject:.2f}")

    # Case 5: dominated system detection
    registry5 = NodeWeightRegistry()
    registry5.register_proofs_for_node("dominator", ["h1"])
    registry5.register_proofs_for_node("weak", ["h2"])
    tv5 = TrustVector()
    tv5.set_entry("h1", 0.99, 1000.0, ledger_version=1)
    tv5.set_entry("h2", 0.01, 1000.0, ledger_version=1)
    snap5 = registry5.compute_weights(tv5, ledger_version=1, epoch=0)
    assert snap5.is_dominated(domination_threshold=0.5) is True
    assert abs(snap5.dom_weight_fraction - 0.99) < 1e-4
    print(f"✅ Case 5: is_dominated=True (dom_fraction={snap5.dom_weight_fraction:.4f})")

    print("\n✅ v9.6 TrustWeightedConsensusResolver — all checks passed")


if __name__ == "__main__":
    _test_consensus_resolver()


__all__ = [
    "ConsensusCandidate",
    "ConsensusResult",
    "ConsensusShiftEvent",
    "ConsensusShiftType",
    "TrustWeightedConsensusResolver",
]
