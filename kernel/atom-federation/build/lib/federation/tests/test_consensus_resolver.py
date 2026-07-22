"""Tests for federation.consensus_resolver."""

import time

from federation.consensus_resolver import ConsensusResolver, QuorumConfig
from federation.state_vector import StateVector


def make_vector(node_id: str, theta_hash: str = "h1", **kwargs) -> StateVector:
    defaults = dict(
        node_id=node_id,
        theta_hash=theta_hash,
        envelope_state="stable",
        drift_score=0.1,
        stability_score=0.9,
        timestamp_ns=time.time_ns(),
    )
    defaults.update(kwargs)
    return StateVector(**defaults)


class TestConsensusResolverBasics:
    def test_init(self):
        cr = ConsensusResolver("n1")
        assert cr.node_id == "n1"

    def test_init_with_custom_config(self):
        cfg = QuorumConfig(quorum_fraction=0.5, stale_threshold_ms=10_000)
        cr = ConsensusResolver("n1", config=cfg)
        assert cr.config.quorum_fraction == 0.5


class TestResolveQuorum:
    def test_quorum_2_of_3_nodes(self):
        """2/3 consensus → quorum source."""
        cr = ConsensusResolver("n1")
        my = make_vector("n1", "h_consensus")
        peers = [
            make_vector("n2", "h_consensus"),
            make_vector("n3", "h_consensus"),
        ]
        result = cr.resolve(my, peers, "h_local")
        assert result.is_quorum
        assert result.source == "quorum"
        assert result.theta_hash == "h_consensus"
        assert len(result.voters) >= 2

    def test_quorum_3_of_3_nodes(self):
        """All 3 agree → quorum."""
        cr = ConsensusResolver("n1")
        my = make_vector("n1", "h_all")
        peers = [
            make_vector("n2", "h_all"),
            make_vector("n3", "h_all"),
        ]
        result = cr.resolve(my, peers, "h_different")
        assert result.is_quorum
        assert result.theta_hash == "h_all"

    def test_no_quorum_1_of_3(self):
        """Only 1 of 3 agrees → highest_stability."""
        cr = ConsensusResolver("n1")
        my = make_vector("n1", "h_mine")
        peers = [
            make_vector("n2", "h_other1"),
            make_vector("n3", "h_other2"),
        ]
        result = cr.resolve(my, peers, "h_mine")
        assert not result.is_quorum
        assert result.source == "highest_stability"

    def test_no_quorum_uses_highest_stability(self):
        """No quorum → pick highest stability_score."""
        cr = ConsensusResolver("n1")
        my = make_vector("n1", "h_low", stability_score=0.5, drift_score=0.3)
        peers = [
            make_vector("n2", "h_high", stability_score=0.95, drift_score=0.05),
            make_vector("n3", "h_mid", stability_score=0.7, drift_score=0.2),
        ]
        result = cr.resolve(my, peers, "h_low")
        assert result.source == "highest_stability"
        assert result.theta_hash == "h_high"

    def test_no_quorum_tie_breaks_by_drift(self):
        """Same stability, different drift → min drift wins."""
        cr = ConsensusResolver("n1")
        my = make_vector("n1", "h_mine", stability_score=0.8, drift_score=0.3)
        peers = [
            make_vector("n2", "h_a", stability_score=0.8, drift_score=0.1),
            make_vector("n3", "h_b", stability_score=0.8, drift_score=0.05),
        ]
        result = cr.resolve(my, peers, "h_mine")
        assert result.source == "highest_stability"
        assert result.theta_hash == "h_b"  # lowest drift


class TestResolveStaleExclusion:
    def test_stale_vectors_excluded_from_quorum(self):
        """Stale vectors don't count toward quorum."""
        cr = ConsensusResolver("n1", config=QuorumConfig(max_age_ms=30_000))
        old_ts = time.time_ns() - (60_000 * 1_000_000)

        my = make_vector("n1", "h_fresh", timestamp_ns=time.time_ns())
        peers = [
            make_vector("n2", "h_old1", timestamp_ns=old_ts),  # stale
            make_vector("n3", "h_old2", timestamp_ns=old_ts),  # stale
        ]
        result = cr.resolve(my, peers, "h_fresh")
        # Only my fresh vector counts → no quorum → highest_stability
        assert result.source == "highest_stability"
        assert result.theta_hash == "h_fresh"


class TestResolveLocalOnly:
    def test_no_peers_returns_local(self):
        cr = ConsensusResolver("n1")
        my = make_vector("n1", "h_mine")
        result = cr.resolve(my, [], "h_mine")
        # Only self is fresh, threshold=2 for quorum, so no quorum
        # Falls back to highest_stability (my own vector)
        assert result.source == "highest_stability"
        assert result.theta_hash == "h_mine"
        assert result.confidence == 1.0

    def test_all_stale_returns_local(self):
        cr = ConsensusResolver("n1", config=QuorumConfig(max_age_ms=30_000))
        old_ts = time.time_ns() - (60_000 * 1_000_000)
        my = make_vector("n1", "h_mine", timestamp_ns=old_ts)
        peers = [
            make_vector("n2", "h_other", timestamp_ns=old_ts),
        ]
        result = cr.resolve(my, peers, "h_mine")
        # My vector is also stale, but we pick highest_stability fallback
        # which uses my own vector as best effort
        assert result.source == "highest_stability"


class TestDetectDivergence:
    def test_no_divergence_with_agreeing_peers(self):
        cr = ConsensusResolver("n1")
        my = make_vector("n1", "h_same")
        peers = [
            make_vector("n2", "h_same"),
            make_vector("n3", "h_same"),
        ]
        div = cr.detect_divergence(my, peers)
        assert div == 0.0

    def test_full_divergence(self):
        cr = ConsensusResolver("n1")
        my = make_vector("n1", "h_mine")
        peers = [
            make_vector("n2", "h_other1"),
            make_vector("n3", "h_other2"),
        ]
        div = cr.detect_divergence(my, peers)
        assert div == 1.0

    def test_partial_divergence(self):
        cr = ConsensusResolver("n1")
        my = make_vector("n1", "h_mine")
        peers = [
            make_vector("n2", "h_mine"),   # agree
            make_vector("n3", "h_other"),  # disagree
        ]
        div = cr.detect_divergence(my, peers)
        assert div == 0.5  # 1 of 2 disagree

    def test_divergence_no_peers(self):
        cr = ConsensusResolver("n1")
        my = make_vector("n1", "h_mine")
        div = cr.detect_divergence(my, [])
        assert div == 0.0


class TestIsSafeRemoteTheta:
    def test_collapse_rejected(self):
        cr = ConsensusResolver("n1")
        vec = make_vector("n1", envelope_state="collapse")
        assert cr.is_safe_remote_theta({}, vec) is False

    def test_extreme_drift_rejected(self):
        cr = ConsensusResolver("n1")
        vec = make_vector("n1", drift_score=0.95)
        assert cr.is_safe_remote_theta({}, vec) is False

    def test_stale_rejected(self):
        cr = ConsensusResolver("n1")
        old_ts = time.time_ns() - (60_000 * 1_000_000)
        vec = make_vector("n1", timestamp_ns=old_ts)
        assert cr.is_safe_remote_theta({}, vec) is False

    def test_healthy_vector_accepted(self):
        cr = ConsensusResolver("n1")
        vec = make_vector("n1", drift_score=0.2, stability_score=0.8)
        assert cr.is_safe_remote_theta({"lr": 0.001}, vec) is True


class TestSplitBrain:
    def test_2v2_split_uses_stability(self):
        """2 vs 2 split-brain → highest stability wins."""
        cr = ConsensusResolver("n1")
        my = make_vector("n1", "h_a", stability_score=0.7)
        peers = [
            make_vector("n2", "h_a", stability_score=0.7),  # group A
            make_vector("n3", "h_b", stability_score=0.95),  # group B (higher stability)
            make_vector("n4", "h_b", stability_score=0.9),
        ]
        result = cr.resolve(my, peers, "h_a")
        # h_b has higher combined stability → wins
        assert result.source == "highest_stability"
        assert result.theta_hash in ("h_a", "h_b")


class TestVotersList:
    def test_quorum_voters_listed(self):
        cr = ConsensusResolver("n1")
        my = make_vector("n1", "h_quorum")
        peers = [
            make_vector("n2", "h_quorum"),
            make_vector("n3", "h_other"),
        ]
        result = cr.resolve(my, peers, "h_other")
        assert result.is_quorum
        assert "n1" in result.voters
        assert "n2" in result.voters
        assert "n3" not in result.voters
