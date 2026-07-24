"""
Tests for v9.10 — Semantic Consistency Lock Layer.
"""
import time

import pytest

from federation.semantic.v910 import (
    DriftDetector,
    DriftKind,
    EventStore,
    EventType,
    HashMode,
    SemanticBinder,
)


class TestEventBasics:
    def test_event_creation(self):
        EventStore.reset()
        ev = EventStore.emit(EventType.GOSSIP, "h1")
        assert ev.entity_hash == "h1"
        assert ev.type == EventType.GOSSIP
        assert ev.hash_mode == HashMode.CAUSAL

    def test_event_sink_id_unique(self):
        EventStore.reset()
        ev1 = EventStore.emit(EventType.GOSSIP, "h1")
        ev2 = EventStore.emit(EventType.CONSENSUS, "h2")
        assert ev1.event_id != ev2.event_id

    def test_content_hash(self):
        EventStore.reset()
        ev = EventStore.emit(EventType.GOSSIP, "h1", metadata=["k=v"])
        ch = ev.content_hash()
        assert len(ch) == 64

    def test_consensus_hash_requires_ref(self):
        EventStore.reset()
        ev = EventStore.emit(EventType.CONSENSUS, "h1", consensus_ref="")
        with pytest.raises(ValueError):
            ev.consensus_hash()

    def test_consensus_hash_ok(self):
        EventStore.reset()
        ev = EventStore.emit(EventType.CONSENSUS, "h1", consensus_ref="c-ref-1")
        h = ev.consensus_hash()
        assert len(h) == 64

    def test_verify_integrity(self):
        EventStore.reset()
        ev = EventStore.emit(EventType.GOSSIP, "h1")
        assert ev.verify_integrity() is True


class TestEventStore:
    def test_reset(self):
        EventStore.reset()
        EventStore.emit(EventType.GOSSIP, "h1")
        assert EventStore.size() == 1
        EventStore.reset()
        assert EventStore.size() == 0

    def test_emit_multiple_same_entity(self):
        """Multiple events can reference the same entity_hash across layers."""
        EventStore.reset()
        EventStore.emit(EventType.GOSSIP, "shared-root", metadata=["from=n1"])
        EventStore.emit(EventType.CONSENSUS, "shared-root", metadata=["voters=n1,n2"])
        EventStore.emit(EventType.PROOF, "shared-root", metadata=["proof=abc"])
        assert EventStore.size() == 3
        events = EventStore.query_entity("shared-root")
        assert len(events) == 3

    def test_resolve_returns_projection(self):
        EventStore.reset()
        EventStore.emit(EventType.GOSSIP, "x")
        EventStore.emit(EventType.CONSENSUS, "x")
        proj = EventStore.resolve("x")
        assert proj is not None
        assert proj.entity_hash == "x"
        assert len(proj.gossip_events) == 1
        assert len(proj.consensus_events) == 1

    def test_resolve_unknown_returns_none(self):
        EventStore.reset()
        assert EventStore.resolve("nonexistent") is None

    def test_consensus_is_canonical(self):
        EventStore.reset()
        EventStore.emit(EventType.GOSSIP, "same-root")
        time.sleep(1e-6)
        EventStore.emit(EventType.CONSENSUS, "same-root")
        proj = EventStore.resolve("same-root")
        assert proj is not None
        assert proj.canonical is not None
        assert proj.canonical.type == EventType.CONSENSUS


class TestSemanticProjection:
    def test_has_consensus_true(self):
        EventStore.reset()
        EventStore.emit(EventType.CONSENSUS, "c-root")
        proj = EventStore.resolve("c-root")
        assert proj is not None
        assert proj.has_consensus() is True

    def test_has_consensus_false(self):
        EventStore.reset()
        EventStore.emit(EventType.GOSSIP, "g-root")
        proj = EventStore.resolve("g-root")
        assert proj is not None
        assert proj.has_consensus() is False

    def test_event_ids(self):
        EventStore.reset()
        EventStore.emit(EventType.GOSSIP, "r")
        EventStore.emit(EventType.CONSENSUS, "r")
        EventStore.emit(EventType.PROOF, "r")
        proj = EventStore.resolve("r")
        assert proj is not None
        assert len(proj.event_ids()) == 3


class TestDriftDetector:
    def test_no_drift_clean_system(self):
        EventStore.reset()
        EventStore.emit(EventType.GOSSIP, "root1")
        EventStore.emit(EventType.CONSENSUS, "root1")
        detector = DriftDetector()
        reports = detector.scan_all()
        assert len(reports) == 0

    def test_detects_proof_consensus_mismatch(self):
        EventStore.reset()
        # PROOF with consensus_ref pointing to a different entity_hash
        consensus_ev = EventStore.emit(EventType.CONSENSUS, "agreed-root")
        # PROOF was computed for a different root but references this consensus
        EventStore.emit(
            EventType.PROOF,
            "drifted-root",  # different from consensus entity_hash
            consensus_ref=consensus_ev.event_id,
        )
        detector = DriftDetector()
        reports = detector.scan_all()
        assert any(r.kind == DriftKind.PROOF_CONSENSUS for r in reports)

    def test_identity_collision_scenario(self):
        EventStore.reset()
        # Test the projection reconstruction when multiple entities
        # reference the same event_id (collision scenario).
        ev1 = EventStore.emit(EventType.GOSSIP, "entity-A")
        # Make entity-B point to the same event_id as entity-A
        EventStore._by_entity.setdefault("entity-B", []).append(ev1.event_id)

        proj_a = EventStore.resolve("entity-A")
        proj_b = EventStore.resolve("entity-B")

        # Both projections should see the same event_id
        assert ev1.event_id in proj_a.event_ids()
        assert ev1.event_id in proj_b.event_ids()
        # The collision is that one physical event_id is shared across 2 entities
        assert len(proj_a.event_ids()) == 1
        assert len(proj_b.event_ids()) == 1
        # Verify the same event_id was emitted once but indexed twice
        assert EventStore.size() == 1
        assert len(EventStore.query_entity("entity-A")) == 1
        assert len(EventStore.query_entity("entity-B")) == 1
        # The two query_entity results are the SAME event
        assert EventStore.query_entity("entity-A")[0].event_id == EventStore.query_entity("entity-B")[0].event_id

    def test_scan_all_empty_store(self):
        EventStore.reset()
        detector = DriftDetector()
        reports = detector.scan_all()
        assert reports == []


class TestSemanticBinder:
    def test_bind_gossip(self):
        EventStore.reset()
        ev = SemanticBinder.bind_gossip("delta-h1", seq=5, peers=["n2", "n3"])
        assert ev.type == EventType.GOSSIP
        assert ev.entity_hash == "delta-h1"
        assert "seq=5" in ev.metadata

    def test_bind_consensus(self):
        EventStore.reset()
        ev = SemanticBinder.bind_consensus("root-v3", voters=["n1", "n2"], outcome="decided")
        assert ev.type == EventType.CONSENSUS
        assert ev.entity_hash == "root-v3"
        assert ev.hash_mode == HashMode.CONSENSUS

    def test_bind_proof(self):
        EventStore.reset()
        ev = SemanticBinder.bind_proof("entity-root", "proof-hash-xyz")
        assert ev.type == EventType.PROOF
        assert ev.entity_hash == "entity-root"

    def test_bind_trust(self):
        EventStore.reset()
        ev = SemanticBinder.bind_trust("trust-root", "snapshot-v1")
        assert ev.type == EventType.TRUST
        assert ev.trust_context == "snapshot-v1"

    def test_bind_replay(self):
        EventStore.reset()
        ev = SemanticBinder.bind_replay("replay-root", "trace-abc")
        assert ev.type == EventType.REPLAY
        assert ev.entity_hash == "replay-root"

    def test_full_integration(self):
        """Canonical cycle: gossip delta -> consensus decision -> proof -> bind all."""
        EventStore.reset()
        SemanticBinder.bind_gossip("delta-root", seq=1, peers=["n2"])
        consensus_ev = SemanticBinder.bind_consensus("delta-root", voters=["n1", "n2"], outcome="agree")
        SemanticBinder.bind_proof("delta-root", "zkp-xyz", consensus_ref=consensus_ev.event_id)

        assert EventStore.size() == 3
        proj = EventStore.resolve("delta-root")
        assert proj is not None
        assert len(proj.event_ids()) == 3
        assert proj.has_consensus() is True
        assert proj.canonical.type == EventType.CONSENSUS

        detector = DriftDetector()
        reports = detector.scan_all()
        assert len(reports) == 0
