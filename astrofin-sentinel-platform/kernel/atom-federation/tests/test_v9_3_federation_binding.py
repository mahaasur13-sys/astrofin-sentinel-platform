"""
test_v9_3_federation_binding.py — v9.3 Federation Binding Layer Tests

Tests for three phases:
  Phase 1: ProofAwarePolicySync — proof → ACCEPT/QUARANTINE/PARTIAL
  Phase 2: ProofAwareConsensusResolver — proof-weighted candidate ranking
  Phase 3: ProofEnrichedDeltaMessage + GossipProofEngine — proof in gossip

Integration scenario:
  1. Node_A receives delta from Node_B
  2. PolicySync evaluates cross-origin equivalence
  3. Consensus ranks candidates by proof validity
  4. Gossip propagates proof metadata alongside delta
"""

from __future__ import annotations

import sys

sys.path.insert(0, ".")

import time

from federation.delta_gossip.dag_hash_modes import DAGHashMode
from federation.delta_gossip.protocol import DeltaGossipMessage
from federation.proof_aware_consensus import (
    ProofAwareConsensusCandidate,
    ProofAwareConsensusResolver,
)
from federation.proof_aware_policy_sync import (
    ProofAwarePolicySync,
    SyncVerdict,
)
from federation.proof_enriched_gossip import (
    GossipProofEngine,
    ProofEnrichedDeltaMessage,
    ProofMetadata,
    filter_by_proof_trust,
    rank_messages_by_proof,
)
from orchestration.consistency.invariant_contract.cross_origin_proof import (
    ProofOrigin,
)


class TestPhase1ProofAwarePolicySync:
    """Phase 1: proof → policy sync gate."""

    def test_identical_digests_accept(self):
        sync = ProofAwarePolicySync(node_id="node_A")
        d = ["d1", "d2", "d3", "d4"]
        decision = sync.evaluate_remote_theta(d, d, tick=1)
        assert decision.verdict == SyncVerdict.ACCEPT
        assert decision.proof.is_valid()
        assert decision.enforcement_action.name == "LOG_ONLY"
        log.info("✅ test_identical_digests_accept")

    def test_diverged_digests_quarantine(self):
        sync = ProofAwarePolicySync(node_id="node_A")
        d = ["d1", "d2", "d3", "d4"]
        decision = sync.evaluate_remote_theta(d, ["x1", "x2", "x3", "x4"], tick=2)
        assert decision.verdict == SyncVerdict.QUARANTINE
        assert decision.enforcement_action.name == "QUARANTINE"
        assert decision.quarantined_nodes == []
        log.info("✅ test_diverged_digests_quarantine")

    def test_one_side_empty_partial(self):
        sync = ProofAwarePolicySync(node_id="node_A")
        d = ["d1", "d2", "d3", "d4"]
        decision = sync.evaluate_remote_theta([], d, tick=3)
        assert decision.verdict == SyncVerdict.PARTIAL
        log.info("✅ test_one_side_empty_partial")

    def test_quarantine_node_tracking(self):
        sync = ProofAwarePolicySync(node_id="node_A")
        d = ["d1", "d2", "d3", "d4"]
        decision = sync.evaluate_remote_theta(
            d, ["x1", "x2", "x3", "x4"],
            remote_node_id="node_B", tick=4,
        )
        assert decision.verdict == SyncVerdict.QUARANTINE
        assert "node_B" in sync.quarantined_nodes()
        sync.lift_quarantine("node_B")
        assert "node_B" not in sync.quarantined_nodes()
        log.info("✅ test_quarantine_node_tracking")

    def test_batch_evaluation(self):
        sync = ProofAwarePolicySync(node_id="node_A")
        d = ["d1", "d2", "d3", "d4"]
        remote_states = [
            (d, d, "node_B", ProofOrigin.REMOTE),
            (d, ["x1", "x2", "x3", "x4"], "node_C", ProofOrigin.REMOTE),
            (d, d, "node_D", ProofOrigin.SNAPSHOT),
        ]
        decisions = sync.evaluate_batch(remote_states, tick=5)
        assert len(decisions) == 3
        assert decisions[0].verdict == SyncVerdict.ACCEPT
        assert decisions[1].verdict == SyncVerdict.QUARANTINE
        assert decisions[2].verdict == SyncVerdict.ACCEPT
        log.info("✅ test_batch_evaluation")

    def test_decision_log(self):
        sync = ProofAwarePolicySync(node_id="node_A")
        d = ["d1", "d2", "d3", "d4"]
        sync.evaluate_remote_theta(d, d, tick=1)
        sync.evaluate_remote_theta(d, ["x1", "x2", "x3", "x4"], tick=2)
        log = sync.decision_log()
        assert len(log) == 2
        assert log[0].verdict == SyncVerdict.ACCEPT
        assert log[1].verdict == SyncVerdict.QUARANTINE
        log.info("✅ test_decision_log")


class TestPhase2ProofAwareConsensus:
    """Phase 2: proof-weighted consensus ranking."""

    def test_proof_valid_wins_over_invalid(self):
        resolver = ProofAwareConsensusResolver(node_id="node_A")
        c1 = ProofAwareConsensusCandidate(
            candidate_id="node_X", root_hash="hash_A", seq=10,
            stability_score=0.7, drift_score=0.2,
            proof_valid=True, proof_origin=ProofOrigin.REMOTE,
        )
        c2 = ProofAwareConsensusCandidate(
            candidate_id="node_Y", root_hash="hash_B", seq=9,
            stability_score=0.9, drift_score=0.1,
            proof_valid=False, proof_origin=ProofOrigin.SYNTHETIC,
        )
        winner = resolver.rank_candidates([c1, c2])
        assert winner.candidate_id == "node_X"
        log.info("✅ test_proof_valid_wins_over_invalid")

    def test_require_proof_filters_false(self):
        resolver = ProofAwareConsensusResolver(node_id="node_A")
        c1 = ProofAwareConsensusCandidate(
            candidate_id="node_X", root_hash="hash_A", seq=5,
            stability_score=0.5, drift_score=0.3,
            proof_valid=True, proof_origin=ProofOrigin.REMOTE,
        )
        c2 = ProofAwareConsensusCandidate(
            candidate_id="node_Y", root_hash="hash_B", seq=4,
            stability_score=0.9, drift_score=0.1,
            proof_valid=False,
        )
        winner = resolver.rank_candidates([c1, c2], require_proof=True)
        assert winner.candidate_id == "node_X"
        log.info("✅ test_require_proof_filters_false")

    def test_origin_priority_remote_over_replay(self):
        resolver = ProofAwareConsensusResolver(node_id="node_A")
        c_remote = ProofAwareConsensusCandidate(
            candidate_id="remote_peer", root_hash="hash_R", seq=5,
            stability_score=0.6, drift_score=0.3,
            proof_valid=True, proof_origin=ProofOrigin.REMOTE,
        )
        c_replay = ProofAwareConsensusCandidate(
            candidate_id="replay_peer", root_hash="hash_R2", seq=6,
            stability_score=0.6, drift_score=0.3,
            proof_valid=True, proof_origin=ProofOrigin.REPLAY,
        )
        winner = resolver.rank_candidates([c_replay, c_remote])
        assert winner.candidate_id == "remote_peer"
        log.info("✅ test_origin_priority_remote_over_replay")

    def test_no_proof_fallback_to_stability(self):
        resolver = ProofAwareConsensusResolver(node_id="node_A")
        c_no_proof = ProofAwareConsensusCandidate(
            candidate_id="no_proof", root_hash="hash_N", seq=3,
            stability_score=0.8, drift_score=0.1,
            proof_valid=None,
        )
        c_weak = ProofAwareConsensusCandidate(
            candidate_id="weak_proof", root_hash="hash_W", seq=4,
            stability_score=0.6, drift_score=0.2,
            proof_valid=False,
        )
        winner = resolver.rank_candidates([c_no_proof, c_weak])
        assert winner.candidate_id == "no_proof"
        log.info("✅ test_no_proof_fallback_to_stability")

    def test_empty_candidates_returns_none(self):
        resolver = ProofAwareConsensusResolver(node_id="node_A")
        winner = resolver.rank_candidates([])
        assert winner is None
        log.info("✅ test_empty_candidates_returns_none")


class TestPhase3ProofEnrichedGossip:
    """Phase 3: proof metadata in delta gossip."""

    def test_attach_proof_to_message(self):
        GossipProofEngine()
        base_msg = DeltaGossipMessage(
            source_node_id="node_2",
            root_hash="root_abc",
            changed_node_ids=["node_A", "node_B"],
            changed_hashes={"node_A": "ha", "node_B": "hb"},
            seq=42,
            ts_ns=time.time_ns(),
            hash_mode=DAGHashMode.CONSENSUS,
        )
        meta = ProofMetadata(
            proof_hash="fedcba9876543210",
            proof_origin=ProofOrigin.REMOTE,
            proof_valid=True,
            proof_tick=100,
        )
        enriched = ProofEnrichedDeltaMessage.from_base_message(base_msg, meta)
        assert enriched.proof_metadata.proof_hash == "fedcba9876543210"
        assert enriched.proof_metadata.proof_valid is True
        assert enriched.is_proof_valid() is True
        log.info("✅ test_attach_proof_to_message")

    def test_proof_cache_hit(self):
        gpe = GossipProofEngine()
        base_msg = DeltaGossipMessage(
            source_node_id="node_2",
            root_hash="root_abc",
            changed_node_ids=["node_A"],
            changed_hashes={"node_A": "ha"},
            seq=42,
            ts_ns=time.time_ns(),
            hash_mode=DAGHashMode.CONSENSUS,
        )
        meta = ProofMetadata(proof_hash="cached_hash", proof_valid=True)
        enriched = ProofEnrichedDeltaMessage.from_base_message(base_msg, meta)
        gpe.cache_proof_result("cached_hash", True)
        assert gpe.verify_proof_from_message(enriched) is True
        log.info("✅ test_proof_cache_hit")

    def test_proof_cache_miss_returns_none(self):
        gpe = GossipProofEngine()
        base_msg = DeltaGossipMessage(
            source_node_id="node_2",
            root_hash="root_abc",
            changed_node_ids=["node_A"],
            changed_hashes={"node_A": "ha"},
            seq=42,
            ts_ns=time.time_ns(),
            hash_mode=DAGHashMode.CONSENSUS,
        )
        meta = ProofMetadata(proof_hash="unknown_hash", proof_valid=None)
        enriched = ProofEnrichedDeltaMessage.from_base_message(base_msg, meta)
        assert gpe.verify_proof_from_message(enriched) is None
        log.info("✅ test_proof_cache_miss_returns_none")

    def test_filter_by_proof_trust(self):
        base_msg = DeltaGossipMessage(
            source_node_id="node_2",
            root_hash="root_abc",
            changed_node_ids=["node_A"],
            changed_hashes={"node_A": "ha"},
            seq=42,
            ts_ns=time.time_ns(),
            hash_mode=DAGHashMode.CONSENSUS,
        )
        msg_valid = ProofEnrichedDeltaMessage.from_base_message(
            base_msg, ProofMetadata(proof_valid=True))
        msg_invalid = ProofEnrichedDeltaMessage.from_base_message(
            base_msg, ProofMetadata(proof_valid=False))
        msg_unchecked = ProofEnrichedDeltaMessage.from_base_message(
            base_msg, ProofMetadata())

        filtered = filter_by_proof_trust(
            [msg_valid, msg_invalid, msg_unchecked], require_valid_proof=True)
        assert len(filtered) == 2
        assert msg_invalid not in filtered
        assert msg_valid in filtered
        assert msg_unchecked in filtered
        log.info("✅ test_filter_by_proof_trust")

    def test_rank_messages_by_proof(self):
        base_msg = DeltaGossipMessage(
            source_node_id="node_2",
            root_hash="root_abc",
            changed_node_ids=["node_A"],
            changed_hashes={"node_A": "ha"},
            seq=42,
            ts_ns=time.time_ns(),
            hash_mode=DAGHashMode.CONSENSUS,
        )
        msg_invalid = ProofEnrichedDeltaMessage.from_base_message(
            base_msg, ProofMetadata(proof_valid=False))
        msg_valid = ProofEnrichedDeltaMessage.from_base_message(
            base_msg, ProofMetadata(proof_valid=True))
        msg_unchecked = ProofEnrichedDeltaMessage.from_base_message(
            base_msg, ProofMetadata())

        ranked = rank_messages_by_proof([msg_invalid, msg_valid, msg_unchecked])
        assert ranked[0].proof_metadata.proof_valid is True
        assert ranked[-1].proof_metadata.proof_valid is False
        log.info("✅ test_rank_messages_by_proof")


class TestIntegrationFullPipeline:
    """Full v9.3 pipeline: gossip → policy_sync → consensus."""

    def test_full_pipeline(self):
        # Step 1: remote peer sends delta with proof metadata
        remote_digests = ["d1", "d2", "d3", "d4"]
        local_replay_digests = ["d1", "d2", "d3", "d4"]  # identical = trust

        # Build delta message
        delta_msg = DeltaGossipMessage(
            source_node_id="node_B",
            root_hash="root_B_abc123",
            changed_node_ids=["node_1", "node_2"],
            changed_hashes={"node_1": "hash_1", "node_2": "hash_2"},
            seq=100,
            ts_ns=time.time_ns(),
            hash_mode=DAGHashMode.CONSENSUS,
        )

        # Step 2: ProofAwarePolicySync evaluates cross-origin equivalence
        sync = ProofAwarePolicySync(node_id="node_A")
        decision = sync.evaluate_remote_theta(
            remote_digests=remote_digests,
            replay_digests=local_replay_digests,
            remote_origin=ProofOrigin.REMOTE,
            remote_node_id="node_B",
            tick=50,
        )
        assert decision.verdict == SyncVerdict.ACCEPT, (
            f"Expected ACCEPT, got {decision.verdict}: {decision.reason}"
        )

        # Step 3: Attach proof to delta message
        gpe = GossipProofEngine()
        enriched = gpe.attach_proof_to_message(delta_msg, decision.proof, verified=True)
        assert enriched.is_proof_valid() is True

        # Step 4: Consensus candidate ranking
        resolver = ProofAwareConsensusResolver(node_id="node_A")
        candidate = ProofAwareConsensusCandidate(
            candidate_id="node_B",
            root_hash="root_B_abc123",
            seq=100,
            stability_score=0.75,
            drift_score=0.2,
            proof_valid=enriched.is_proof_valid(),
            proof_origin=ProofOrigin.REMOTE,
        )
        winner = resolver.rank_candidates([candidate])
        assert winner is not None
        assert winner.candidate_id == "node_B"
        assert winner.proof_valid is True

        log.info("✅ test_full_pipeline")


# ─────────────────────────────────────────────────────────────────
# Run all tests
# ─────────────────────────────────────────────────────────────────

def run_all():
    test_classes = [
        TestPhase1ProofAwarePolicySync,
        TestPhase2ProofAwareConsensus,
        TestPhase3ProofEnrichedGossip,
        TestIntegrationFullPipeline,
    ]

    total = passed = 0
    for cls in test_classes:
        log.info(f"\n--- {cls.__name__} ---")
        instance = cls()
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                total += 1
                try:
                    getattr(instance, method_name)()
                    passed += 1
                except AssertionError as e:
                    log.info(f"  ❌ {method_name}: {e}")
                except Exception as e:
                    log.info(f"  💥 {method_name}: {e}")

    log.info(f"\n{'='*50}")
    log.info(f"Results: {passed}/{total} passed")
    if passed == total:
        log.info("✅ All v9.3 federation binding tests pass")
    else:
        log.info(f"❌ {total - passed} tests failed")


if __name__ == "__main__":
    run_all()
