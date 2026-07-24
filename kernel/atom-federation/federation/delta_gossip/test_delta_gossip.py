"""
Tests for federation.delta_gossip.

Covers:
  - DeltaGossipProtocol push/receive with delta messages
  - DeltaRouter routing decisions (selective vs full fanout)
  - AntiEntropy merkle reconciliation
  - ConvergeConsensus delta-based quorum
  - Integration: fingerprint → delta → gossip → consensus
"""

import time

from federation.delta_gossip import (
    AntiEntropy,
    ConvergeConsensus,
    DeltaGossipMessage,
    DeltaGossipProtocol,
    DeltaRouter,
)
from federation.state_vector import StateVector


def make_vector(node_id: str, theta_hash: str = "h1", **kwargs) -> StateVector:
    defaults = dict(
        node_id=node_id, theta_hash=theta_hash,
        envelope_state="stable", drift_score=0.1,
        stability_score=0.9, timestamp_ns=time.time_ns(),
    )
    defaults.update(kwargs)
    return StateVector(**defaults)


def make_delta(
    source: str, root_hash: str = "r1",
    changed_ids: list[str] | None = None,
    changed_hashes: dict[str, str] | None = None,
    seq: int = 1,
) -> DeltaGossipMessage:
    return DeltaGossipMessage(
        source_node_id=source,
        root_hash=root_hash,
        changed_node_ids=changed_ids or [],
        changed_hashes=changed_hashes or {},
        seq=seq,
        ts_ns=time.time_ns(),
    )


# ─────────────────────────────────────────────────────────────────
# DeltaGossipMessage
# ─────────────────────────────────────────────────────────────────

class TestDeltaGossipMessage:
    def test_delta_size(self):
        d = make_delta("n1", changed_ids=["a", "bb"], changed_hashes={"a": "x", "bb": "yy"})
        assert d.delta_size > 0

    def test_is_empty_true(self):
        d = make_delta("n1", changed_ids=[])
        assert d.is_empty() is True

    def test_is_empty_false(self):
        d = make_delta("n1", changed_ids=["a"])
        assert d.is_empty() is False


# ─────────────────────────────────────────────────────────────────
# DeltaGossipProtocol — basics
# ─────────────────────────────────────────────────────────────────

class TestDeltaGossipProtocolBasics:
    def test_init(self):
        p = DeltaGossipProtocol(node_id="n1")
        assert p.node_id == "n1"
        assert p.peer_ids == []

    def test_register_peer(self):
        p = DeltaGossipProtocol(node_id="n1")
        p.register_peer("n2")
        assert "n2" in p.peer_ids

    def test_unregister_peer(self):
        p = DeltaGossipProtocol(node_id="n1")
        p.register_peer("n2")
        p.unregister_peer("n2")
        assert "n2" not in p.peer_ids


# ─────────────────────────────────────────────────────────────────
# DeltaGossipProtocol — delta flow
# ─────────────────────────────────────────────────────────────────

class TestDeltaGossipFlow:
    def test_build_delta_message(self):
        p = DeltaGossipProtocol(node_id="n1")
        msg = p.build_delta_message(
            root_hash="abc123",
            changed_node_ids=["node_A", "node_B"],
            changed_hashes={"node_A": "ha", "node_B": "hb"},
        )
        assert msg.source_node_id == "n1"
        assert msg.root_hash == "abc123"
        assert set(msg.changed_node_ids) == {"node_A", "node_B"}
        assert msg.seq == 1

    def test_build_delta_message_seq_increments(self):
        p = DeltaGossipProtocol(node_id="n1")
        m1 = p.build_delta_message("r1", [], {})
        m2 = p.build_delta_message("r2", ["a"], {"a": "h"})
        assert m2.seq == m1.seq + 1

    def test_push_to_no_peers_returns_empty(self):
        p = DeltaGossipProtocol(node_id="n1")
        delta = p.build_delta_message("r1", ["a"], {"a": "h"})
        vec = make_vector("n1")
        result = p.push(delta, vec)
        assert result == []

    def test_push_to_registered_peers(self):
        p = DeltaGossipProtocol(node_id="n1")
        p.register_peer("n2")
        p.register_peer("n3")
        delta = p.build_delta_message("r1", ["a"], {"a": "h"})
        vec = make_vector("n1")
        result = p.push(delta, vec)
        assert len(result) == 0  # no full sync needed

    def test_push_skips_in_sync_peer(self):
        """Peer with same root_hash is skipped."""
        p = DeltaGossipProtocol(node_id="n1")
        p.register_peer("n2")
        # Pre-seed peer with same root_hash
        p._peers["n2"].last_root_hash = "r1"

        delta = p.build_delta_message("r1", ["a"], {"a": "h"})
        vec = make_vector("n1")
        recipients = p.push(delta, vec)
        assert "n2" not in recipients

    def test_receive_delta_updates_peer_state(self):
        p = DeltaGossipProtocol(node_id="n1")
        p.register_peer("n2")
        delta = make_delta("n2", root_hash="r2", changed_ids=["x"], changed_hashes={"x": "hx"}, seq=5)
        is_new, rh = p.receive_delta(delta)
        assert is_new is True
        assert rh == "r2"
        assert p._peers["n2"].last_root_hash == "r2"
        assert p._peers["n2"].last_seq == 5

    def test_receive_delta_rejects_stale(self):
        p = DeltaGossipProtocol(node_id="n1")
        p.register_peer("n2")
        p._peers["n2"].last_seq = 10
        delta = make_delta("n2", root_hash="r2", seq=5)
        is_new, _ = p.receive_delta(delta)
        assert is_new is False

    def test_receive_delta_unknown_peer_registers(self):
        p = DeltaGossipProtocol(node_id="n1")
        delta = make_delta("n999", root_hash="rX", seq=1)
        is_new, rh = p.receive_delta(delta)
        assert is_new is True
        assert "n999" in p.peer_ids


# ─────────────────────────────────────────────────────────────────
# DeltaRouter
# ─────────────────────────────────────────────────────────────────

class TestDeltaRouter:
    def test_init(self):
        r = DeltaRouter()
        assert r.summary()["tracked_nodes"] == 0

    def test_register_and_peek(self):
        r = DeltaRouter()
        r.register_node("n1", "rootA", seq=1, changed_ids=["a"])
        seq, rh = r.peer_fingerprint("n1")
        assert seq == 1
        assert rh == "rootA"

    def test_peers_needing_delta_filters_in_sync(self):
        r = DeltaRouter()
        # n1 and n2 have same root
        r.register_node("n1", "rootA", seq=1, changed_ids=[])
        r.register_node("n2", "rootA", seq=1, changed_ids=[])
        # n3 has different root
        r.register_node("n3", "rootB", seq=2, changed_ids=["b"])

        needing = r.peers_needing_delta("rootA")
        assert "n3" in needing
        assert "n1" not in needing
        assert "n2" not in needing

    def test_update_peer_fingerprint(self):
        r = DeltaRouter()
        r.update_peer_fingerprint("n2", "rootX", seq=5, changed_ids=["c"])
        seq, rh = r.peer_fingerprint("n2")
        assert seq == 5
        assert rh == "rootX"


# ─────────────────────────────────────────────────────────────────
# AntiEntropy
# ─────────────────────────────────────────────────────────────────

class TestAntiEntropy:
    def test_build_tree_empty(self):
        ae = AntiEntropy()
        tree = ae.build_tree({})
        assert tree.is_leaf is True
        assert tree.node_ids == []

    def test_build_tree_single_node(self):
        ae = AntiEntropy()
        tree = ae.build_tree({"n1": "hash1"})
        assert tree.is_leaf is True
        assert tree.node_ids == ["n1"]

    def test_build_tree_multiple_nodes(self):
        ae = AntiEntropy()
        tree = ae.build_tree({"n1": "h1", "n2": "h2", "n3": "h3", "n4": "h4"})
        assert tree.is_leaf is False
        assert set(tree.node_ids) == {"n1", "n2", "n3", "n4"}

    def test_merkle_digest_layered(self):
        ae = AntiEntropy()
        digest = ae.merkle_digest({"n1": "h1", "n2": "h2"})
        assert 0 in digest
        assert len(digest[0]) > 0

    def test_reconcile_detects_missing_on_both_sides(self):
        ae = AntiEntropy()
        mine = {"n1": "h", "n2": "h"}
        theirs = {"n2": "h", "n3": "h"}
        missing_mine, missing_theirs, differ = ae.reconcile(mine, theirs)
        assert "n3" in missing_mine
        assert "n1" in missing_theirs
        assert differ == []

    def test_reconcile_detects_content_divergence(self):
        ae = AntiEntropy()
        mine = {"n1": "ha", "n2": "h"}
        theirs = {"n1": "hb", "n2": "h"}
        _, _, differ = ae.reconcile(mine, theirs)
        assert "n1" in differ

    def test_reconcile_returns_empty_when_in_sync(self):
        ae = AntiEntropy()
        state = {"n1": "h", "n2": "h"}
        a, b, c = ae.reconcile(state, state)
        assert a == [] and b == [] and c == []

    def test_prove_membership(self):
        ae = AntiEntropy()
        hashes = {"n1": "ha", "n2": "hb", "n3": "hc"}
        proof = ae.prove_membership("n1", hashes)
        root = ae.build_tree(hashes).digest
        assert ae.verify_proof("n1", "ha", proof, root) is True


# ─────────────────────────────────────────────────────────────────
# ConvergeConsensus
# ─────────────────────────────────────────────────────────────────

class TestConvergeConsensus:
    def test_no_peers_returns_local(self):
        cc = ConvergeConsensus(node_id="n1")
        result = cc.resolve("rootA", my_seq=1, my_changed_ids=["a"], peer_messages=[])
        assert result.source == "no_peers"
        assert result.converged_root_hash == "rootA"

    def test_quorum_on_root_hash(self):
        cc = ConvergeConsensus(node_id="n1")
        peer_msgs = [
            make_delta("n2", root_hash="rootA", seq=2),
            make_delta("n3", root_hash="rootA", seq=3),
        ]
        result = cc.resolve("rootA", my_seq=1, my_changed_ids=["a"], peer_messages=peer_msgs)
        assert result.is_quorum is True
        assert result.converged_root_hash == "rootA"

    def test_no_quorum_falls_back_to_highest_seq(self):
        cc = ConvergeConsensus(node_id="n1")
        from federation.delta_gossip.consensus import DeltaConsensusConfig
        cc.config = DeltaConsensusConfig(quorum_fraction=0.67)
        peer_msgs = [
            make_delta("n2", root_hash="rootA", seq=2),
            make_delta("n3", root_hash="rootB", seq=10),
        ]
        result = cc.resolve("rootA", my_seq=1, my_changed_ids=["a"], peer_messages=peer_msgs)
        assert result.converged_root_hash == "rootB"
        assert result.source == "highest_seq"

    def test_detect_divergence(self):
        cc = ConvergeConsensus(node_id="n1")
        peer_msgs = [
            make_delta("n2", root_hash="rootA"),
            make_delta("n3", root_hash="rootB"),
        ]
        div = cc.detect_divergence("rootA", peer_msgs)
        assert 0.0 < div <= 1.0


# ─────────────────────────────────────────────────────────────────
# Integration: fingerprint → delta → gossip → consensus
# ─────────────────────────────────────────────────────────────────

class TestDeltaGossipIntegration:
    def test_end_to_end_delta_flow(self):
        """
        Simulate: node1 changes 2 nodes → builds delta → pushes to node2
        → node2 receives → updates peer state → consensus resolves.
        """
        # Node1: build delta
        p1 = DeltaGossipProtocol(node_id="n1")
        p1.register_peer("n2")
        delta = p1.build_delta_message(
            root_hash="root_v2",
            changed_node_ids=["node_A", "node_B"],
            changed_hashes={"node_A": "ha", "node_B": "hb"},
        )
        make_vector("n1", theta_hash="root_v2")

        # Node2: receives delta
        p2 = DeltaGossipProtocol(node_id="n2")
        p2.register_peer("n1")
        is_new, rh = p2.receive_delta(delta)
        assert is_new is True
        assert rh == "root_v2"

        # Consensus: both nodes converge
        cc = ConvergeConsensus(node_id="n1")
        peer_msgs = [delta]
        result = cc.resolve("root_v2", my_seq=1, my_changed_ids=["node_A", "node_B"], peer_messages=peer_msgs)
        assert result.is_quorum is True

    def test_delta_replaces_full_state_fanout(self):
        """
        Verify delta carries minimum info — no full StateVector fields.
        """
        p = DeltaGossipProtocol(node_id="n1")
        p.register_peer("n2")
        delta = p.build_delta_message(
            root_hash="root99",
            changed_node_ids=["n1", "n2", "n3"],
            changed_hashes={"n1": "h1", "n2": "h2", "n3": "h3"},
        )
        # Delta should NOT contain envelope_state, drift_score, stability_score
        assert not hasattr(delta, "envelope_state")
        assert not hasattr(delta, "drift_score")
        # Only fingerprint + delta fields
        assert hasattr(delta, "root_hash")
        assert hasattr(delta, "changed_node_ids")
        assert hasattr(delta, "changed_hashes")
        assert hasattr(delta, "seq")

    def test_router_eliminates_unnecessary_push(self):
        """
        Verify DeltaRouter skips peers already in sync.
        """
        router = DeltaRouter()
        router.register_node("n1", "root_same", seq=1, changed_ids=[])
        router.register_node("n2", "root_same", seq=1, changed_ids=[])
        router.register_node("n3", "root_diff", seq=2, changed_ids=["a"])

        needing = router.peers_needing_delta("root_same")
        assert len(needing) == 1
        assert "n3" in needing
        assert "n1" not in needing
        assert "n2" not in needing


# ─────────────────────────────────────────────────────────────────
# AntiEntropy with digests
# ─────────────────────────────────────────────────────────────────

class TestAntiEntropyDigestReconcile:
    def test_reconcile_with_digests_fast_path(self):
        ae = AntiEntropy()
        hashes = {"a": "h", "b": "h2"}
        digest = ae.merkle_digest(hashes)
        result = ae.reconcile_with_digests(
            my_root_digest=digest[max(digest)],
            my_hashes=hashes,
            their_root_digest=digest[max(digest)],
            their_hashes=hashes,
        )
        assert result["in_sync"] is True

    def test_reconcile_with_digests_slow_path(self):
        ae = AntiEntropy()
        mine = {"a": "ha"}
        theirs = {"b": "hb"}
        mine_digest = ae.merkle_digest(mine)
        theirs_digest = ae.merkle_digest(theirs)
        result = ae.reconcile_with_digests(
            my_root_digest=mine_digest[max(mine_digest)],
            my_hashes=mine,
            their_root_digest=theirs_digest[max(theirs_digest)],
            their_hashes=theirs,
        )
        assert result["in_sync"] is False
        assert "a" in result["missing_on_their_side"]
        assert "b" in result["missing_on_my_side"]
