"""
test_cross_origin_proof.py — v9.2 Cross-Origin Equivalence Proof Layer Tests
"""
from __future__ import annotations

import sys

sys.path.insert(0, ".")

from federation.delta_gossip.dag_hash_modes import DAGHashMode
from orchestration.consistency.invariant_contract.cross_mode_validator import SemanticTree
from orchestration.consistency.invariant_contract.cross_origin_proof import (
    ProjectionStep,
    ProofOrigin,
    SemanticProofEngine,
    get_cross_origin_equivalence_invariant,
)


class TestSemanticProofEngine:
    """SemanticProofEngine: prove_equivalence and prove_from_digests."""

    def test_identical_digests_equivalent(self):
        d = ["d1", "d2", "d3", "d4"]
        engine = SemanticProofEngine()
        proof = engine.prove_from_digests(d, d)
        assert proof.is_valid(), "identical digests must be equivalent"
        assert proof.equivalence_result.is_equivalent
        assert proof.proof_hash not in ("", "empty")
        assert len(proof.projection_steps) >= 2  # at least CONSENSUS projections

    def test_different_digests_not_equivalent(self):
        d = ["d1", "d2", "d3", "d4"]
        engine = SemanticProofEngine()
        proof = engine.prove_from_digests(d, ["x1", "x2", "x3", "x4"])
        assert not proof.is_valid()
        assert not proof.equivalence_result.is_equivalent
        assert proof.equivalence_result.divergence_reason is not None
        assert "CONSENSUS hash mismatch" in proof.equivalence_result.divergence_reason

    def test_empty_digests_returns_empty_proof(self):
        engine = SemanticProofEngine()
        p = engine.prove_from_digests([], [])
        assert p.equivalence_result.is_equivalent  # empty = trivially ok
        assert p.proof_hash == "empty"

    def test_proof_log_records(self):
        engine = SemanticProofEngine()
        d = ["a", "b", "c"]
        engine.prove_from_digests(d, d)
        engine.prove_from_digests(d, ["x", "y", "z"])
        log = engine.proof_log()
        assert len(log) == 2
        assert log[0].equivalence_result.is_equivalent
        assert not log[1].equivalence_result.is_equivalent

    def test_proof_id_unique(self):
        engine = SemanticProofEngine()
        d = ["a", "b"]
        p1 = engine.prove_from_digests(d, d)
        p2 = engine.prove_from_digests(d, d)
        assert p1.proof_id != p2.proof_id

    def test_proof_to_dict(self):
        engine = SemanticProofEngine()
        d = ["a", "b", "c"]
        proof = engine.prove_from_digests(d, d)
        dct = proof.to_dict()
        assert "proof_id" in dct
        assert "source_a_origin" in dct
        assert "projection_steps" in dct
        assert "equivalence" in dct
        assert "proof_hash" in dct

    def test_cross_check_causal_projection(self):
        """Both trees project to same CONSENSUS, then to CAUSAL — must match."""
        d = ["d1", "d2", "d3", "d4"]
        engine = SemanticProofEngine()
        proof = engine.prove_from_digests(d, d)
        assert proof.is_valid()
        causal_steps = [s for s in proof.projection_steps if s.to_mode == DAGHashMode.CAUSAL]
        assert len(causal_steps) == 2, "both sides should have CAUSAL projection steps"
        assert causal_steps[0].projection_digest == causal_steps[1].projection_digest

    def test_proof_ticks_stored(self):
        engine = SemanticProofEngine()
        d = ["a", "b"]
        # build trees manually to pass ticks
        tree_a = SemanticTree.from_digest_list(d, DAGHashMode.CONSENSUS)
        tree_b = SemanticTree.from_digest_list(d, DAGHashMode.CONSENSUS)
        p = engine.prove_equivalence(tree_a, tree_b, tick_a=10, tick_b=20)
        assert p.ticks == (10, 20)

    def test_proof_metadata_passed(self):
        engine = SemanticProofEngine()
        d = ["a", "b"]
        tree_a = SemanticTree.from_digest_list(d, DAGHashMode.CONSENSUS)
        tree_b = SemanticTree.from_digest_list(d, DAGHashMode.CONSENSUS)
        meta = {"source": "test", "run": 1}
        p = engine.prove_equivalence(tree_a, tree_b, metadata=meta)
        assert p.metadata == meta


class TestProjectionStep:
    """ProjectionStep dataclass and field ordering."""

    def test_step_fields(self):
        step = ProjectionStep(
            from_mode=DAGHashMode.CONSENSUS,
            to_mode=DAGHashMode.CAUSAL,
            intermediate_tree_hash="abc",
            projection_digest="def",
        )
        assert step.from_mode == DAGHashMode.CONSENSUS
        assert step.to_mode == DAGHashMode.CAUSAL
        assert step.intermediate_tree_hash == "abc"
        assert step.projection_digest == "def"
        assert step.step_id.startswith("proj_")


class TestCrossOriginInvariant:
    """CROSS_ORIGIN_EQUIVALENCE invariant."""

    def test_invariant_passes_with_valid_proof(self):
        engine = SemanticProofEngine()
        d = ["a", "b", "c"]
        proof = engine.prove_from_digests(d, d)
        inv = get_cross_origin_equivalence_invariant()
        result = inv.evaluate({"proof": proof})
        assert result.satisfied
        assert result.severity.name == "CRITICAL"
        assert result.enforcement_action.name == "QUARANTINE"

    def test_invariant_fails_with_invalid_proof(self):
        engine = SemanticProofEngine()
        d = ["a", "b", "c"]
        proof = engine.prove_from_digests(d, ["x", "y", "z"])
        inv = get_cross_origin_equivalence_invariant()
        result = inv.evaluate({"proof": proof})
        assert not result.satisfied
        assert result.severity.name == "CRITICAL"
        assert result.enforcement_action.name == "QUARANTINE"

    def test_invariant_passes_with_empty_digests(self):
        inv = get_cross_origin_equivalence_invariant()
        result = inv.evaluate({})
        assert result.satisfied  # no data = not a violation

    def test_invariant_fails_with_one_side_empty(self):
        inv = get_cross_origin_equivalence_invariant()
        result = inv.evaluate({"remote_digests": ["a", "b"]})
        assert not result.satisfied

    def test_invariant_builds_proof_from_digests(self):
        """Invariant should build its own proof when proof not provided."""
        inv = get_cross_origin_equivalence_invariant()
        d = ["a", "b", "c"]
        result = inv.evaluate({"remote_digests": d, "replay_digests": d})
        assert result.satisfied
        result2 = inv.evaluate({"remote_digests": d, "replay_digests": ["x", "y", "z"]})
        assert not result2.satisfied

    def test_invariant_tags(self):
        inv = get_cross_origin_equivalence_invariant()
        assert "cross_origin" in inv.tags
        assert "v9.2" in inv.tags
        assert "critical" in inv.tags
        assert "proof" in inv.tags


class TestProofOrigin:
    """ProofOrigin enum values."""

    def test_all_origins_present(self):
        assert ProofOrigin.REMOTE is not None
        assert ProofOrigin.REPLAY is not None
        assert ProofOrigin.SNAPSHOT is not None
        assert ProofOrigin.SYNTHETIC is not None

    def test_origin_in_proof(self):
        engine = SemanticProofEngine()
        d = ["a", "b"]
        proof = engine.prove_from_digests(d, d, origin_a=ProofOrigin.REMOTE, origin_b=ProofOrigin.REPLAY)
        assert proof.source_a[1] == ProofOrigin.REMOTE
        assert proof.source_b[1] == ProofOrigin.REPLAY
