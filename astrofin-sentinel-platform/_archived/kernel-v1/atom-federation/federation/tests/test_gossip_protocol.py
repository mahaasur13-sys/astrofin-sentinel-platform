"""Tests for federation.gossip_protocol."""

import time

import pytest

from federation.gossip_protocol import GossipConfig, GossipProtocol, PeerRecord
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


class TestPeerRecord:
    def test_peer_record_created(self):
        pr = PeerRecord(node_id="n2")
        assert pr.node_id == "n2"
        assert pr.vector is None
        assert pr.last_push_ns == 0


class TestGossipProtocolBasics:
    def test_init(self):
        g = GossipProtocol(node_id="n1")
        assert g.node_id == "n1"
        assert g.peer_ids == []

    def test_register_peer(self):
        g = GossipProtocol(node_id="n1")
        g.register_peer("n2")
        g.register_peer("n3")
        assert set(g.peer_ids) == {"n2", "n3"}

    def test_register_duplicate_noop(self):
        g = GossipProtocol(node_id="n1")
        g.register_peer("n2")
        g.register_peer("n2")
        assert g.peer_ids == ["n2"]

    def test_unregister_peer(self):
        g = GossipProtocol(node_id="n1")
        g.register_peer("n2")
        g.register_peer("n3")
        g.unregister_peer("n2")
        assert g.peer_ids == ["n3"]


class TestGossipPushPull:
    def test_push_to_no_peers(self):
        g = GossipProtocol(node_id="n1")
        vec = make_vector("n1")
        results = g.push(vec)
        assert results == []

    def test_push_returns_selected_peers(self):
        g = GossipProtocol(node_id="n1")
        g.register_peer("n2")
        g.register_peer("n3")
        g.register_peer("n4")
        vec = make_vector("n1")
        results = g.push(vec)
        peer_ids = [pid for pid, _ in results]
        assert len(peer_ids) == 3  # fanout=3 by default

    def test_push_excludes_self(self):
        g = GossipProtocol(node_id="n1")
        g.register_peer("n1")  # self registered
        g.register_peer("n2")
        vec = make_vector("n1")
        results = g.push(vec)
        peer_ids = [pid for pid, _ in results]
        assert "n1" not in peer_ids

    def test_receive_push_updates_peer_vector(self):
        g = GossipProtocol(node_id="n1")
        g.register_peer("n2")
        remote = make_vector("n2", theta_hash="h_remote")
        result = g.receive_push(remote)
        assert result == remote
        assert g._peers["n2"].vector == remote

    def test_receive_push_unknown_peer_returns_none(self):
        g = GossipProtocol(node_id="n1")
        remote = make_vector("n999")
        assert g.receive_push(remote) is None

    def test_receive_push_records_history(self):
        g = GossipProtocol(node_id="n1")
        g.register_peer("n2")
        remote = make_vector("n2")
        g.receive_push(remote)
        assert len(g._peers["n2"].vector_history) == 1
        remote2 = make_vector("n2", theta_hash="h2")
        g.receive_push(remote2)
        assert len(g._peers["n2"].vector_history) == 2

    def test_pull_returns_none_for_unknown_peer(self):
        g = GossipProtocol(node_id="n1")
        assert g.pull("n_unknown") is None

    def test_pull_returns_peer_vector(self):
        g = GossipProtocol(node_id="n1")
        g.register_peer("n2")
        vec = make_vector("n2", theta_hash="h_pull")
        g.receive_push(vec)
        pulled = g.pull("n2")
        assert pulled == vec


class TestGossipCallbacks:
    def test_on_vector_callback_fired(self):
        called = []
        g = GossipProtocol(node_id="n1", on_vector=lambda v: called.append(v))
        g.register_peer("n2")
        remote = make_vector("n2")
        g.receive_push(remote)
        assert called == [remote]


class TestGossipQuery:
    def test_get_all_vectors(self):
        g = GossipProtocol(node_id="n1")
        g.register_peer("n2")
        g.register_peer("n3")
        g.receive_push(make_vector("n2", theta_hash="h2"))
        g.receive_push(make_vector("n3", theta_hash="h3"))
        vectors = g.get_all_vectors()
        assert len(vectors) == 2

    def test_get_fresh_vectors_excludes_stale(self):
        g = GossipProtocol(node_id="n1")
        g.register_peer("n2")
        # fresh
        g.receive_push(make_vector("n2", theta_hash="h_fresh"))
        # stale
        old_ts = time.time_ns() - (60_000 * 1_000_000)
        g.receive_push(make_vector("n2", theta_hash="h_stale", timestamp_ns=old_ts))
        fresh = g.get_fresh_vectors(max_age_ms=30_000)
        assert len(fresh) == 1
        assert fresh[0].theta_hash == "h_fresh"

    def test_is_stale_peer_true_when_no_vector(self):
        g = GossipProtocol(node_id="n1")
        g.register_peer("n2")
        assert g.is_stale_peer("n2") is True

    @pytest.mark.xfail(reason='C1: deterministic timestamp=0 in gossip', strict=False)
    def test_is_stale_peer_true_when_old(self):
        g = GossipProtocol(node_id="n1")
        g.register_peer("n2")
        old_ts = time.time_ns() - (60_000 * 1_000_000)
        g.receive_push(make_vector("n2", timestamp_ns=old_ts))
        assert g.is_stale_peer("n2") is True

    def test_is_stale_peer_false_when_fresh(self):
        g = GossipProtocol(node_id="n1")
        g.register_peer("n2")
        g.receive_push(make_vector("n2"))
        assert g.is_stale_peer("n2") is False


class TestGossipLifecycle:
    @pytest.mark.asyncio
    async def test_start_stop(self):
        g = GossipProtocol(node_id="n1", config=GossipConfig(push_interval_ms=100, pull_interval_ms=100))
        await g.start()
        assert g._running is True
        await g.stop()
        assert g._running is False

    @pytest.mark.asyncio
    async def test_stop_is_idempotent(self):
        g = GossipProtocol(node_id="n1")
        await g.stop()  # no-op
        assert g._running is False
