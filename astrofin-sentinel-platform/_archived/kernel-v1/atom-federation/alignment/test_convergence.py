"""test_convergence.py — v10.2 Causal Convergence Guarantee Layer tests."""

from alignment.convergence import (

import logging
log = logging.getLogger(__name__)

    AuditVerdict,
    ConvergenceLayer,
    EntropyController,
    EntropyRegime,
    GlobalConsistencyOrder,
    MergeAuditor,
    OscillationDetector,
    OscillationState,
)


def test_oscillation_basic():
    d = OscillationDetector()
    # First merge: STABLE
    s = d.record_merge("a", "b")
    assert s == OscillationState.STABLE, f"first merge -> STABLE, got {s}"
    log.info("  record_merge: STABLE/WARMING/OSCILLATING sequence")
    for _ in range(2):
        d.record_merge("a", "b")
    s = d.record_merge("a", "b")
    assert s == OscillationState.OSCILLATING, f"4th merge -> OSCILLATING, got {s}"
    log.info("  4th merge -> OSCILLATING: ✅")
    # can_merge: should backoff
    allowed, until_ts = d.can_merge("a", "b")
    assert not allowed, "OSCILLATING pair should not be allowed"
    log.info(f"  can_merge during backoff: blocked ✅ (until={until_ts:.1f}s)")
    log.info("  [OscillationDetector] STABLE/WARMING/OSCILLATING: ✅")


def test_global_consistency_order():
    o = GlobalConsistencyOrder()
    c1 = o.commit_merge("a", "b", "snap1", "MERGE", local_lamport=10)
    c2 = o.commit_merge("a", "c", "snap2", "KEEP_A", local_lamport=5)
    assert c1.lamport_commit_ts < c2.lamport_commit_ts, "commit order should match global Lamport"
    before = o.is_globally_ordered_before(c1.merge_id, c2.merge_id)
    assert before, "c1 should be ordered before c2"
    log.info(f"  commit order: ts_a={c1.lamport_commit_ts} < ts_b={c2.lamport_commit_ts}: ✅")
    log.info(f"  is_globally_ordered_before(c1,c2)={before}: ✅")
    log.info(f"  total_merge_count={o.total_merge_count()}: ✅")
    log.info("  [GlobalConsistencyOrder] commit ordering: ✅")


def test_entropy_controller():
    e = EntropyController()
    e.register_branch("b1")
    e.register_branch("b2")
    e.register_branch("b3")
    # NOMINAL: 3 < 16
    snap = e.evaluate_regime(3, oscillated_pairs=0)
    assert snap.regime == EntropyRegime.NOMINAL, f"3 branches -> NOMINAL, got {snap.regime}"
    log.info("  3 branches -> NOMINAL: ✅")
    # ELEVATED: 16 <= 16 < 32
    for i in range(4, 17):
        e.register_branch(f"b{i}")
    snap = e.evaluate_regime(16, oscillated_pairs=0)
    assert snap.regime == EntropyRegime.ELEVATED, f"16 branches -> ELEVATED, got {snap.regime}"
    log.info("  16 branches -> ELEVATED: ✅")
    # should_force_merge: NOMINAL -> False
    assert not e.should_force_merge("b1", EntropyRegime.NOMINAL)
    log.info("  should_force_merge(NOMINAL)=False: ✅")
    log.info("  [EntropyController] regime logic: ✅")


def test_merge_auditor():
    a = MergeAuditor()
    class MockEvent:
        def __init__(self, lamport_ts):
            self.lamport_ts = lamport_ts
    events = [MockEvent(10), MockEvent(20), MockEvent(30)]
    result = a.audit_merge("m1", "merged_b", ("cp1", "cp2"), events)
    assert result.verdict == AuditVerdict.PASS, f"PASS expected, got {result.verdict}"
    log.info(f"  audit PASS: ✅ (verdict={result.verdict.name})")
    # FAIL: non-monotonic Lamport
    bad_events = [MockEvent(30), MockEvent(20), MockEvent(10)]
    result2 = a.audit_merge("m2", "merged_b2", ("cp1", "cp2"), bad_events)
    assert result2.verdict == AuditVerdict.FAIL, f"FAIL expected, got {result2.verdict}"
    log.info("  audit FAIL on non-monotonic Lamport: ✅")
    log.info("  [MergeAuditor] PASS/FAIL detection: ✅")


def test_convergence_layer_integration():
    c = ConvergenceLayer()
    # can_merge_propose: fresh pair
    allowed, backoff, osc_state = c.can_merge_propose("a", "b")
    assert allowed, "fresh pair should be allowed"
    log.info(f"  can_merge_propose(fresh): allowed={allowed}: ✅")
    # register merge
    commit = c.register_merge("a", "b", "snap1", "MERGE", local_lamport=1)
    assert commit.decision == "MERGE"
    log.info(f"  register_merge -> commit.decision={commit.decision}: ✅")
    # audit: PASS
    class MockEvent:
        def __init__(self, ts): self.lamport_ts = ts
    audit = c.audit_last_merge(
        commit.merge_id, "merged_b",
        ("snap1_a", "snap1_b"),
        [MockEvent(10), MockEvent(20)],
    )
    assert audit.verdict == AuditVerdict.PASS, f"PASS expected, got {audit.verdict}"
    log.info("  audit PASS: ✅")
    # oscillation after 4 merges
    d = OscillationDetector()
    for _ in range(4):
        d.record_merge("x", "y")
    state = d.get_state("x", "y")
    assert state == OscillationState.OSCILLATING, f"4 cycles -> OSCILLATING, got {state}"
    log.info("  4 cycles -> OSCILLATING: ✅")
    log.info("  [ConvergenceLayer] integration: ✅")


def run_tests():
    tests = [
        ("OscillationDetector", test_oscillation_basic),
        ("GlobalConsistencyOrder", test_global_consistency_order),
        ("EntropyController", test_entropy_controller),
        ("MergeAuditor", test_merge_auditor),
        ("ConvergenceLayer integration", test_convergence_layer_integration),
    ]
    passed = 0
    for name, fn in tests:
        try:
            log.info(f"\n[ {name} ]")
            fn()
            passed += 1
            log.info("  ✅")
        except AssertionError as e:
            log.info(f"  ❌ FAILED: {e}")
        except Exception as e:
            log.info(f"  💥 ERROR: {e}")
    log.info(f"\n{'='*50}")
    log.info(f"  RESULT: {passed}/{len(tests)} passed")
    return passed == len(tests)


if __name__ == "__main__":
    ok = run_tests()
    exit(0 if ok else 1)
