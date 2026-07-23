# ruff: noqa: F821
"""
proof_aware_consensus.py — v9.3 Phase 2: Proof-Weighted Consensus Resolution

Key shift from Phase 1:
  Phase 1: proof → policy sync gate (ACCEPT/QUARANTINE/PARTIAL)
  Phase 2: proof validity → consensus candidate ranking

Before (v9.2 and before):
    Candidate ranking by:
      - stability_score (only)
      - drift_score (secondary)

After (v9.3):
    Candidate ranking by:
      1. proof_valid: boolean (null means no proof available)
      2. stability_score: float
      3. drift_score: float (lower is better)
      4. proof_origin: ProofOrigin priority (REMOTE > SNAPSHOT > REPLAY > SYNTHETIC)

Ranking formula:
    score = (
        10.0 if proof_valid else -10.0
    ) + (
        stability_score
    ) + (
        -drift_score        # lower drift is better
    ) + (
        origin_bonus        # REMOTE=+0.5, SNAPSHOT=+0.3, REPLAY=+0.1, SYNTHETIC=+0.0
    )

Integration points:
    - ConvergeQuorumResult (delta_gossip/consensus.py) — proof_hash presence
    - DeltaGossipMessage — proof_hash field (added in Phase 3)
    - SemanticProofEngine — proof validation
    - ProofOrigin priority matrix
"""

from __future__ import annotations

from dataclasses import dataclass, field

from federation.delta_gossip.consensus import ConvergeQuorumResult
from federation.delta_gossip.dag_hash_modes import DAGHashMode
from orchestration.consistency.invariant_contract.cross_origin_proof import (

import logging
log = logging.getLogger(__name__)

    ProofOrigin,
    SemanticProofEngine,
)

# ─────────────────────────────────────────────────────────────────
# ProofAwareConsensusCandidate
# ─────────────────────────────────────────────────────────────────

@dataclass
class ProofAwareConsensusCandidate:
    """
    Consensus candidate enriched with proof metadata.

    Fields:
        candidate_id     — node_id of the candidate
        root_hash        — DAG root hash of this candidate
        seq              — sequence number
        stability_score  — from StateVector
        drift_score      — from StateVector
        proof_valid      — whether a valid SemanticProof exists for this candidate
        proof_origin     — ProofOrigin of the candidate's proof (if any)
        proof_hash       — proof hash (if any)
        changed_node_ids — changed node IDs from delta message
        raw_score        — computed ranking score
    """
    candidate_id: str
    root_hash: str
    seq: int
    stability_score: float = 0.5
    drift_score: float = 0.0
    proof_valid: bool | None = None   # None = no proof data
    proof_origin: ProofOrigin | None = None
    proof_hash: str | None = None
    changed_node_ids: list[str] = field(default_factory=list)
    raw_score: float = 0.0

    def compute_score(
        self,
        proof_ledger: ProofLedger | None = None,
        now: float | None = None,
    ) -> float:
        """
        Compute composite ranking score.

        Higher is better.
        When proof_ledger + now are provided: uses continuous trust_score ∈ [0, 1]
          score = 10.0 * trust_score
        Otherwise: falls back to legacy boolean proof_valid signal
          score = (10.0 if proof_valid else -10.0) + stability_score - drift_score + origin_bonus
        """
        if proof_ledger is not None and self.proof_hash and now is not None:
            trust = proof_ledger.trust_score(self.proof_hash, now)
            # Apply origin_bonus on top of trust signal
            origin_bonus = {
                ProofOrigin.REMOTE:    0.5,
                ProofOrigin.SNAPSHOT: 0.3,
                ProofOrigin.REPLAY:   0.1,
                ProofOrigin.SYNTHETIC: 0.0,
                None: 0.0,
            }.get(self.proof_origin, 0.0)
            self.raw_score = 10.0 * trust + self.stability_score - self.drift_score + origin_bonus
            return self.raw_score

        base = 10.0 if self.proof_valid is True else (-10.0 if self.proof_valid is False else 0.0)
        origin_bonus = {
            ProofOrigin.REMOTE:    0.5,
            ProofOrigin.SNAPSHOT: 0.3,
            ProofOrigin.REPLAY:   0.1,
            ProofOrigin.SYNTHETIC: 0.0,
            None: 0.0,
        }.get(self.proof_origin, 0.0)
        self.raw_score = base + self.stability_score - self.drift_score + origin_bonus
        return self.raw_score


# ─────────────────────────────────────────────────────────────────
# ProofAwareConsensusResolver
# ─────────────────────────────────────────────────────────────────

class ProofAwareConsensusResolver:
    """
    Consensus resolver with proof-aware candidate ranking.

    Replaces simple stability_score ranking with multi-signal ranking:
      proof_valid → stability_score → drift_score → origin_priority

    Usage:
        resolver = ProofAwareConsensusResolver(node_id="node_1")
        candidates = [
            ProofAwareConsensusCandidate(candidate_id="node_2", proof_valid=True, ...),
            ProofAwareConsensusCandidate(candidate_id="node_3", proof_valid=False, ...),
        ]
        winner = resolver.rank_candidates(candidates)
    """

    def __init__(self, node_id: str):
        self.node_id = node_id
        self._engine = SemanticProofEngine()

    def rank_candidates(
        self,
        candidates: list[ProofAwareConsensusCandidate],
        require_proof: bool = False,
    ) -> ProofAwareConsensusCandidate | None:
        """
        Rank candidates and return the winner.

        Args:
            candidates: list of proof-aware candidates
            require_proof: if True, reject candidates with proof_valid=False

        Returns:
            Highest-ranked candidate, or None if all disqualified
        """
        if not candidates:
            return None

        # Compute scores
        for c in candidates:
            c.compute_score()

        # Filter if require_proof
        if require_proof:
            candidates = [c for c in candidates if c.proof_valid is not False]

        if not candidates:
            return None

        # Sort by score descending
        ranked = sorted(candidates, key=lambda c: c.raw_score, reverse=True)
        return ranked[0]

    def resolve_with_quorum(
        self,
        quorum_result: ConvergeQuorumResult,
        candidates: list[ProofAwareConsensusCandidate],
        require_proof: bool = False,
    ) -> tuple[ProofAwareConsensusCandidate | None, ConvergeQuorumResult]:
        """
        Combine ConvergeQuorumResult with proof-aware ranking.

        If quorum reached via root_hash agreement AND a candidate matches
        that root_hash with proof_valid=True → high confidence.
        If quorum reached but no matching candidate with valid proof →
        fall back to proof-aware ranking among all candidates.

        Returns:
            (winning_candidate, quorum_result)
        """
        if not candidates:
            return None, quorum_result

        # Try to match quorum root_hash with proof-valid candidate
        matching = [
            c for c in candidates
            if c.root_hash == quorum_result.converged_root_hash
        ]

        if matching and quorum_result.is_quorum:
            for c in matching:
                c.compute_score()
            proof_valid_candidates = [c for c in matching if c.proof_valid is True]
            if proof_valid_candidates:
                # Quorum + proof = highest confidence
                best = sorted(proof_valid_candidates, key=lambda x: x.raw_score, reverse=True)[0]
                return best, quorum_result

        # Fall back to full ranking
        return self.rank_candidates(candidates, require_proof=require_proof), quorum_result

    def validate_proof_candidate(
        self,
        candidate: ProofAwareConsensusCandidate,
        trusted_digests: list[str],
        mode: DAGHashMode = DAGHashMode.CONSENSUS,
    ) -> bool:
        """
        Validate that a candidate's root_hash is consistent with trusted digests.

        Used for post-consensus validation before applying state.
        """
        if not candidate.proof_valid:
            return False

        from orchestration.consistency.invariant_contract.cross_mode_validator import SemanticTree

        if not candidate.proof_hash:
            return False

        # Verify the candidate's proof by re-running equivalence
        try:
            tree_a = SemanticTree.from_digest_list(trusted_digests, mode)
            tree_b = SemanticTree.from_digest_list(
                [candidate.root_hash] + (candidate.changed_node_ids[:3] or []),
                mode,
            )
            proof = self._engine.prove_equivalence(tree_a, tree_b)
            return proof.is_valid()
        except Exception:
            return False


# ─────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────

def _test_v9_3_phase2():
    """Sanity test for v9.3 Phase 2."""
    resolver = ProofAwareConsensusResolver(node_id="node_1")

    # Case 1: proof_valid=True wins over proof_valid=False
    c1 = ProofAwareConsensusCandidate(
        candidate_id="node_2", root_hash="hash_A", seq=10,
        stability_score=0.7, drift_score=0.2,
        proof_valid=True, proof_origin=ProofOrigin.REMOTE,
    )
    c2 = ProofAwareConsensusCandidate(
        candidate_id="node_3", root_hash="hash_B", seq=9,
        stability_score=0.9, drift_score=0.1,
        proof_valid=False, proof_origin=ProofOrigin.SYNTHETIC,
    )
    # c1: 10 + 0.7 - 0.2 + 0.5 = 11.0
    # c2: -10 + 0.9 - 0.1 + 0.0 = -9.2
    winner = resolver.rank_candidates([c1, c2])
    assert winner is not None and winner.candidate_id == "node_2", (
        f"Expected node_2 (proof_valid=True), got {winner.candidate_id if winner else None}"
    )
    log.info(f"✅ Case 1: proof_valid=True wins (score={winner.raw_score:.2f})")

    # Case 2: require_proof filters out invalid
    c3 = ProofAwareConsensusCandidate(
        candidate_id="node_4", root_hash="hash_C", seq=8,
        stability_score=0.95, drift_score=0.05,
        proof_valid=True, proof_origin=ProofOrigin.REMOTE,
    )
    c4 = ProofAwareConsensusCandidate(
        candidate_id="node_5", root_hash="hash_D", seq=7,
        stability_score=0.8, drift_score=0.1,
        proof_valid=False,
    )
    winner2 = resolver.rank_candidates([c3, c4], require_proof=True)
    assert winner2.candidate_id == "node_4"
    log.info("✅ Case 2: require_proof filters proof_valid=False")

    # Case 3: origin priority — REMOTE > REPLAY > SYNTHETIC
    c_remote = ProofAwareConsensusCandidate(
        candidate_id="remote_node", root_hash="hash_R", seq=5,
        stability_score=0.6, drift_score=0.3,
        proof_valid=True, proof_origin=ProofOrigin.REMOTE,
    )
    c_replay = ProofAwareConsensusCandidate(
        candidate_id="replay_node", root_hash="hash_R2", seq=6,
        stability_score=0.6, drift_score=0.3,
        proof_valid=True, proof_origin=ProofOrigin.REPLAY,
    )
    # Both same stability/drift; REMOTE gets +0.5 vs +0.1 → wins
    winner3 = resolver.rank_candidates([c_replay, c_remote])  # order reversed
    assert winner3.candidate_id == "remote_node"
    log.info("✅ Case 3: origin priority — REMOTE > REPLAY")

    # Case 4: no proof data — rank by stability + drift only
    c_no_proof = ProofAwareConsensusCandidate(
        candidate_id="no_proof_node", root_hash="hash_N", seq=3,
        stability_score=0.8, drift_score=0.1,
        proof_valid=None,
    )
    c_weak_proof = ProofAwareConsensusCandidate(
        candidate_id="weak_proof_node", root_hash="hash_W", seq=4,
        stability_score=0.6, drift_score=0.2,
        proof_valid=False,
    )
    winner4 = resolver.rank_candidates([c_no_proof, c_weak_proof])
    assert winner4.candidate_id == "no_proof_node"  # higher stability, lower drift
    log.info("✅ Case 4: no proof data — fallback to stability + drift")

    log.info("\n✅ v9.3 Phase 2: ProofAwareConsensusResolver — all checks passed")


if __name__ == "__main__":
    _test_v9_3_phase2()


__all__ = [
    "ProofAwareConsensusCandidate",
    "ProofAwareConsensusResolver",
]
