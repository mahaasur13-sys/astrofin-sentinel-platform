"""
test_incremental_causal_verifier.py
===================================
Tests for IncrementalCausalVerifier — O(1) causal equivalence.
"""
from consistency_v2.incremental_causal_verifier import (

import logging
log = logging.getLogger(__name__)

    CausalFingerprint,
    IncrementalCausalVerifier,
)


def test_causal_fingerprint_add_and_identical():
    """Fingerprint changes on add, is_identical works on same content."""
    fp1 = CausalFingerprint()
    fp2 = CausalFingerprint()
    fp1.add_event("e1", causal_parents=[])
    fp2.add_event("e1", causal_parents=[])
    identical, reason = fp1.is_identical(fp2)
    assert identical is True
    assert reason == "causally_equivalent"


def test_causal_fingerprint_different_events():
    """Different events produce different fingerprints."""
    fp1 = CausalFingerprint()
    fp2 = CausalFingerprint()
    fp1.add_event("e1", causal_parents=[])
    fp2.add_event("e2", causal_parents=[])
    identical, reason = fp1.is_identical(fp2)
    assert identical is False
    assert "mismatch" in reason


def test_incremental_causal_verifier_equivalence():
    """Verifier correctly detects equivalence."""
    v = IncrementalCausalVerifier()
    v.add_exec_event("e1", causal_parents=[])
    v.add_replay_event("e1", causal_parents=[])
    identical, reason, fps = v.check_equivalence()
    assert identical is True
    assert fps["exec"]["event_count"] == 1
    assert fps["replay"]["event_count"] == 1


def test_incremental_causal_verifier_divergence():
    """Verifier correctly detects divergence."""
    v = IncrementalCausalVerifier()
    v.add_exec_event("e1", causal_parents=[])
    v.add_replay_event("e2", causal_parents=[])
    identical, reason, fps = v.check_equivalence()
    assert identical is False


def test_incremental_causal_verifier_sync_from_events():
    """sync_from_events rebuilds fingerprints from event lists."""
    v = IncrementalCausalVerifier()

    class MockEvent:
        def __init__(self, eid, parents=None):
            self.event_id = eid
            self.payload = {"causal_parents": parents or []}

    exec_events = [MockEvent("e1"), MockEvent("e2", parents=["e1"])]
    replay_events = [MockEvent("e1"), MockEvent("e2", parents=["e1"])]
    v.sync_from_events(exec_events, replay_events)
    identical, reason, _ = v.check_equivalence()
    assert identical is True


def test_incremental_causal_verifier_fingerprint_dict():
    """CausalFingerprint.to_dict() serializes correctly."""
    fp = CausalFingerprint()
    fp.add_event("e1", causal_parents=["p1"])
    d = fp.to_dict()
    assert "rolling_hash" in d
    assert d["event_count"] == 1
    assert d["rolling_hash"] != 0


if __name__ == "__main__":
    test_causal_fingerprint_add_and_identical()
    test_causal_fingerprint_different_events()
    test_incremental_causal_verifier_equivalence()
    test_incremental_causal_verifier_divergence()
    test_incremental_causal_verifier_sync_from_events()
    test_incremental_causal_verifier_fingerprint_dict()
    log.info("All IncrementalCausalVerifier tests passed.")
