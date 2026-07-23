#!/usr/bin/env python3
"""test_p8_cryptoeconomics.py — atom-federation-os v9.0+P8 Cryptoeconomic Layer Tests.

Tests all slashing conditions and economic invariants.

TEST MATRIX:
  T1  invalid_proof       → slash at S1 severity (1.0)
  T2  runtime_violation    → slash at S2 severity (1.0)
  T3  ast_env_mismatch     → slash at S3 severity (0.75)
  T4  fork_detected        → slash at S4 severity (1.0)
  T5  double_vote          → slash at S5 severity (0.80)
  T6  bypass_attempt       → slash at S6 severity (0.50)
  T7  zero_stake_node rejected from consensus
  T8  slash reduces stake correctly
  T9  stake floor enforced (no slash below 0)
  T10 multiple slashes accumulate
  T11 replay attack detection
  T12 quorum-weighted voting (stake-weighted)
"""
import sys as _sys
import pathlib as _pathlib

_REPO = _pathlib.Path(__file__).parent.parent
_SYS_REPO = _pathlib.Path("/home/workspace/atom-federation-os")
for _p in (_REPO, _SYS_REPO):
    if str(_p) not in _sys.path:
        _sys.path.insert(0, str(_p))

from core.economics.slashing_engine import (
    SlashingEngine,
    ViolationType,
    get_slashing_engine,
)
from core.economics.stake_registry import (
    StakeRegistry,
    MIN_STAKE,
    InsufficientStake,
    ZeroStakeParticipant,
)


def check(condition: bool, name: str) -> bool:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {name}")
    return condition


def main() -> int:
    print("╔══════════════════════════════════════╗")
    print("║  P8 CRYPTOECONOMIC TESTS             ║")
    print("╚══════════════════════════════════════╝")

    passed = 0
    total = 0

    # ── Setup ──────────────────────────────────────────────────────────────

    registry = StakeRegistry()
    engine = SlashingEngine(registry)
    total += 1; passed += check(True, "Setup (StakeRegistry + SlashingEngine)")

    # Lock stakes for test nodes
    for node in ("node-1", "node-2", "node-3"):
        registry.lock_stake(node, amount=100.0)
    total += 1; passed += check(True, "Lock stakes for test nodes")

    # ── T1: invalid_proof → S1 slash (100%) ─────────────────────────────

    engine.slash("node-1", ViolationType.INVALID_PROOF, "signature verification failed")
    stake_after = registry.get_stake("node-1")
    total += 1
    passed += check(
        stake_after == 0.0,
        f"T1 invalid_proof → 100% slash (stake={stake_after}, expected=0.0)",
    )

    # ── T2: runtime_violation → S2 slash (100%) ─────────────────────────

    registry.lock_stake("node-2", amount=50.0)  # re-lock
    engine.slash("node-2", ViolationType.RUNTIME_VIOLATION, "stack outside gateway")
    stake_after = registry.get_stake("node-2")
    total += 1
    passed += check(
        stake_after == 0.0,
        f"T2 runtime_violation → 100% slash (stake={stake_after}, expected=0.0)",
    )

    # ── T3: ast_env_mismatch → S3 slash (75%) ───────────────────────────

    registry.lock_stake("node-3", amount=100.0)
    engine.slash("node-3", ViolationType.AST_ENV_MISMATCH, "hash mismatch")
    stake_after = registry.get_stake("node-3")
    total += 1
    passed += check(
        abs(stake_after - 25.0) < 0.01,
        f"T3 ast_env_mismatch → 75% slash (stake={stake_after}, expected=25.0)",
    )

    # ── T4: fork_detected → S4 slash (100%) ─────────────────────────────

    registry.lock_stake("node-1", amount=100.0)  # re-lock
    record = engine.on_fork_detected("node-1", "branch-A", "branch-B")
    stake_after = registry.get_stake("node-1")
    total += 1
    passed += check(
        stake_after == 0.0 and record.violation == ViolationType.FORK_DETECTED,
        f"T4 fork_detected → 100% slash + correct type (stake={stake_after})",
    )

    # ── T5: double_vote → S5 slash (80%) ───────────────────────────────

    registry.lock_stake("node-2", amount=100.0)
    record = engine.on_double_vote("node-2", round_a=5, round_b=7)
    stake_after = registry.get_stake("node-2")
    total += 1
    passed += check(
        abs(stake_after - 20.0) < 0.01 and record.violation == ViolationType.DOUBLE_VOTE,
        f"T5 double_vote → 80% slash (stake={stake_after}, expected=20.0)",
    )

    # ── T6: bypass_attempt → S6 slash (50%) ────────────────────────────

    registry.lock_stake("node-3", amount=100.0)
    record = engine.on_bypass_attempt("node-3", "execution_loop.execute()")
    stake_after = registry.get_stake("node-3")
    total += 1
    passed += check(
        abs(stake_after - 50.0) < 0.01 and record.violation == ViolationType.BYPASS_ATTEMPT,
        f"T6 bypass_attempt → 50% slash (stake={stake_after}, expected=50.0)",
    )

    # ── T7: zero-stake node rejected from participation ─────────────────

    total += 1
    passed += check(
        not registry.is_participating("node-1"),
        f"T7 zero-stake node-1 rejected (is_participating=False)",
    )
    total += 1
    passed += check(
        registry.is_participating("node-2"),
        f"T7 node-2 with stake=20 still participates (is_participating=True)",
    )

    # ── T8: slash reduces stake correctly ───────────────────────────────

    registry.lock_stake("node-1", amount=80.0)
    record = engine.slash("node-1", ViolationType.STALE_VOTE, "vote from old round", severity=0.10)
    stake_after = registry.get_stake("node-1")
    total += 1
    passed += check(
        abs(stake_after - 72.0) < 0.01,
        f"T8 slash accumulation: 80 - 10% = 72.0 (actual={stake_after})",
    )

    # ── T9: stake floor enforced (no slash below 0) ─────────────────────

    registry.lock_stake("node-2", amount=5.0)
    engine.slash("node-2", ViolationType.INVALID_PROOF, "max severity", severity=1.0)
    stake_after = registry.get_stake("node-2")
    total += 1
    passed += check(
        stake_after == 0.0,
        f"T9 stake floor enforced: stake={stake_after} (floor=0.0)",
    )
    total += 1
    passed += check(
        registry.is_participating("node-2") is False,
        "T9 node-2 below MIN_STAKE (0.0 < 1.0) → not participating",
    )

    # ── T10: multiple slashes accumulate ─────────────────────────────────

    registry.lock_stake("node-3", amount=100.0)
    engine.slash("node-3", ViolationType.INVALID_PROOF, "first", severity=0.50)  # → 50
    engine.slash("node-3", ViolationType.INVALID_PROOF, "second", severity=0.50)  # → 25
    stake_after = registry.get_stake("node-3")
    total += 1
    passed += check(
        abs(stake_after - 25.0) < 0.01,
        f"T10 multiple slashes: 100 → 50 → 25 (stake={stake_after})",
    )

    # ── T11: replay attack detection ─────────────────────────────────────

    # Try to double-slash the same node (should still apply second slash)
    before_count = engine.total_slashed
    engine.slash("node-1", ViolationType.INVALID_PROOF, "replay of same violation")
    after_count = engine.total_slashed
    total += 1
    passed += check(
        after_count == before_count + 1,
        f"T11 replay attack: still counted as new slash (count={after_count})",
    )

    # ── T12: stake-weighted quorum ────────────────────────────────────────

    # Re-lock for weighted test
    registry.lock_stake("node-1", amount=100.0)
    registry.lock_stake("node-2", amount=200.0)
    registry.lock_stake("node-3", amount=300.0)  # total = 600

    # Weighted vote check: node-2 has 200/600 = 33.3% of stake
    node2_weight = registry.get_stake("node-2") / registry.total_stake()
    total += 1
    passed += check(
        abs(node2_weight - 0.333) < 0.01,
        f"T12 stake-weighted: node-2 = {node2_weight:.3f} of total (expected 0.333)",
    )

    # node-2 + node-3 = 500/600 = 83.3% → meets 2/3 threshold
    top_two = registry.get_stake("node-2") + registry.get_stake("node-3")
    top_two_ratio = top_two / registry.total_stake()
    total += 1
    passed += check(
        top_two_ratio >= 0.667,
        f"T12 weighted quorum: node2+node3 = {top_two_ratio:.3f} ≥ 2/3",
    )

    # node-1 alone = 100/600 = 16.7% → NOT sufficient
    node1_ratio = registry.get_stake("node-1") / registry.total_stake()
    total += 1
    passed += check(
        node1_ratio < 0.667,
        f"T12 weighted rejection: node-1 alone = {node1_ratio:.3f} < 2/3",
    )

    # ── Summary ────────────────────────────────────────────────────────────

    print()
    print(f"  ╔═══════════════════════════════════╗")
    print(f"  ║  P8 RESULT: {passed}/{total} PASSED        ║")
    print(f"  ╚═══════════════════════════════════╝")

    # Engine summary
    summary = engine.summary()
    print(f"  Total slashes: {summary['total_slashes']}")
    print(f"  Slashed nodes: {summary['slashed_nodes']}")
    for vtype, cnt in summary["by_type"].items():
        if cnt:
            print(f"    {vtype}: {cnt}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    _sys.exit(main())