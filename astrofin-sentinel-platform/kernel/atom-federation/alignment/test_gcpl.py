import time

"""test_gcpl.py — v10.3 GCPL tests."""

from alignment.gcpl import (
    ConvergenceFunction,
    GCPLCheckResult,
    GlobalConsistencyChecker,
    GlobalInvariant,
    TerminationProver,
    causal_edit_distance,
)


class MockBranch:
    def __init__(self, bid, events):
        self.branch_id = bid
        self.events = events


# ── Metric space ──────────────────────────────────────────────
def test_edit_distance_identical():
    # Identical event sequences → d = 0
    ids = ["e1", "e2", "e3"]
    a = [type("E", (), {"event_id": i})() for i in ids]
    b = [type("E", (), {"event_id": i})() for i in ids]
    d = causal_edit_distance(a, b)
    assert d == 0.0, f"Identical → 0, got {d}"
    print("  identical: d=0.0 ✅")


def test_edit_distance_disjoint():
    # No common events → d = 1.0
    a = [type("E", (), {"event_id": i})() for i in ["x1", "x2"]]
    b = [type("E", (), {"event_id": i})() for i in ["y1", "y2"]]
    d = causal_edit_distance(a, b)
    assert d == 1.0, f"Disjoint → 1.0, got {d}"
    print("  disjoint: d=1.0 ✅")


def test_edit_distance_partial():
    # Partial LCS
    a = [type("E", (), {"event_id": i})() for i in ["e1", "e2", "e3"]]
    b = [type("E", (), {"event_id": i})() for i in ["e1", "x", "e2", "e3"]]
    d = causal_edit_distance(a, b)
    assert 0.0 < d < 1.0, f"Partial overlap: 0<d<1, got {d}"
    print(f"  partial overlap: d={d:.3f} ✅")


# ── Convergence function ─────────────────────────────────────
def test_mean_pairwise_convergence():
    b1 = MockBranch("b1", [])
    b2 = MockBranch("b2", [])
    b3 = MockBranch("b3", [])
    # All empty → 0 distance → C = 1.0 (perfect convergence)
    c = ConvergenceFunction.mean_pairwise_distance([b1, b2, b3])
    assert c == 0.0, f"All empty → C=0, got {c}"
    print("  mean_pairwise: C=0.0 (identical empty) ✅")


def test_convergence_rate_decreasing():
    # C decreasing over time → negative rate
    history = [0.8, 0.6, 0.4, 0.3, 0.2]
    rate = ConvergenceFunction.convergence_rate(history)
    assert rate < 0, f"Decreasing C → negative rate, got {rate}"
    print(f"  convergence_rate decreasing: {rate:.3f} < 0 ✅")


def test_convergence_rate_increasing():
    # C increasing → positive rate (ALERT)
    history = [0.2, 0.3, 0.4, 0.6, 0.8]
    rate = ConvergenceFunction.convergence_rate(history)
    assert rate > 0, f"Increasing C → positive rate, got {rate}"
    print(f"  convergence_rate increasing: {rate:.3f} > 0 (ALERT) ✅")


# ── GlobalConsistencyChecker ─────────────────────────────────
def test_checker_nominal():
    ck = GlobalConsistencyChecker()
    branches = [MockBranch("b1", []), MockBranch("b2", [])]
    snap = ck.check(
        branches=branches,
        active_branches=branches,
        oscillation_count=0,
        terminal_branch_ids=[],
        last_convergence_ts=time.time(),
        post_audit_pass=5,
        post_audit_total=5,
    )
    assert snap.status == GCPLCheckResult.OK, f"Nominal → OK, got {snap.status}"
    print(f"  nominal 2 branches: {snap.status.value} ✅")


def test_checker_entropy_violation():
    ck = GlobalConsistencyChecker()
    # 33 active branches → violates BRANCH_ENTROPY_BOUNDED
    branches = [MockBranch(f"b{i}", []) for i in range(33)]
    snap = ck.check(
        branches=branches,
        active_branches=branches,
        oscillation_count=0,
        terminal_branch_ids=[],
        last_convergence_ts=time.time(),
        post_audit_pass=5,
        post_audit_total=5,
    )
    assert GlobalInvariant.BRANCH_ENTROPY_BOUNDED in snap.invariant_violations
    assert snap.status == GCPLCheckResult.NON_CONVERGENT
    print("  33 branches → NON_CONVERGENT (BRANCH_ENTROPY) ✅")


def test_checker_irreconcilable_ratio():
    ck = GlobalConsistencyChecker()
    # 4 terminal + 1 active = 5 total → 4/5 = 0.80 > 0.10
    branches = [MockBranch("b0", [])] + [MockBranch(f"t{i}", []) for i in range(4)]
    active = [branches[0]]
    terminal = [f"t{i}" for i in range(4)]
    snap = ck.check(
        branches=branches,
        active_branches=active,
        oscillation_count=0,
        terminal_branch_ids=terminal,
        last_convergence_ts=time.time(),
        post_audit_pass=5,
        post_audit_total=5,
    )
    assert GlobalInvariant.IRRECONCILABLE_RATIO_BOUNDED in snap.invariant_violations
    print("  irreconcilable_ratio=0.80 → NON_CONVERGENT ✅")


# ── TerminationProver ──────────────────────────────────────────
def test_termination_converged():
    prover = TerminationProver()
    res = prover.prove(
        convergence_history=[0.009, 0.005, 0.002, 0.001, 0.0005],
        branch_count_history=[3, 2, 1, 1, 1],
        oscillation_count=0,
    )
    assert res.converged is True
    assert res.deadlocked is False
    print("  C→0: CONVERGED ✅")


def test_termination_terminal_leaves():
    prover = TerminationProver()
    res = prover.prove(
        convergence_history=[0.3, 0.3, 0.3, 0.3],
        branch_count_history=[3, 3, 3, 3],
        oscillation_count=0,
    )
    assert res.terminal_leaves is True
    assert res.deadlocked is False
    print("  |B| stable + no osc: TERMINAL_LEAVES ✅")


def test_termination_deadlock():
    prover = TerminationProver()
    res = prover.prove(
        convergence_history=[0.5, 0.6, 0.7, 0.8, 0.9],
        branch_count_history=[2, 3, 4, 5, 6],
        oscillation_count=3,
    )
    assert res.deadlocked is True
    print("  oscillating + |B| growing: DEADLOCKED ✅")


def run_tests():
    print("\n=== v10.3 GCPL Tests ===")
    tests = [
        ("Metric space", [
            test_edit_distance_identical,
            test_edit_distance_disjoint,
            test_edit_distance_partial,
        ]),
        ("Convergence function", [
            test_mean_pairwise_convergence,
            test_convergence_rate_decreasing,
            test_convergence_rate_increasing,
        ]),
        ("GlobalConsistencyChecker", [
            test_checker_nominal,
            test_checker_entropy_violation,
            test_checker_irreconcilable_ratio,
        ]),
        ("TerminationProver", [
            test_termination_converged,
            test_termination_terminal_leaves,
            test_termination_deadlock,
        ]),
    ]
    total = passed = 0
    for group, fns in tests:
        print(f"\n[ {group} ]")
        for fn in fns:
            total += 1
            try:
                fn()
                passed += 1
            except Exception as e:
                print(f"  ❌ {fn.__name__}: {e}")
    print(f"\n{'='*50}")
    print(f"  RESULT: {passed}/{total} passed")
    return passed == total


if __name__ == "__main__":
    ok = run_tests()
    exit(0 if ok else 1)
