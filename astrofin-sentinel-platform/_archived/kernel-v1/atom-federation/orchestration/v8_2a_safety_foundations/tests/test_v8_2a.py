"""
Tests for v8.2a Safety Foundations
Module: orchestration.v8_2a_safety_foundations
"""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from orchestration.v8_2a_safety_foundations import (
    GovernorDecision,
    GovernorSignal,
    GovernorThresholds,
    InvariantChecker,
    InvariantViolation,
    MutationLedger,
    NormInvariant,
    RollbackEngine,
    SpectralInvariant,
    StabilityGovernor,
    TriggerSource,
)

# ── InvariantChecker ──────────────────────────────────────────────────────

class TestNormInvariant:
    def test_within_bound_passes(self):
        inv = NormInvariant("test_drift", epsilon=0.5, p=2)
        old = np.array([0.0, 0.0])
        new = np.array([0.2, 0.3])
        assert inv.check(old, new) is True

    def test_exceeds_bound_fails(self):
        inv = NormInvariant("test_drift", epsilon=0.3, p=2)
        old = np.array([0.0, 0.0])
        new = np.array([0.2, 0.4])
        assert inv.check(old, new) is False

    def test_validate_raises(self):
        inv = NormInvariant("test_drift", epsilon=0.1, p=2)
        old = np.zeros(5)
        new = np.ones(5) * 0.3
        with pytest.raises(InvariantViolation) as exc_info:
            inv.validate(old, new)
        assert exc_info.value.invariant_name == "test_drift"
        assert "norm" in str(exc_info.value).lower()

    def test_validate_ok_no_raise(self):
        inv = NormInvariant("test_drift", epsilon=1.0, p=2)
        old = np.zeros(3)
        new = np.array([0.5, 0.4, 0.3])
        inv.validate(old, new)  # should not raise


class TestSpectralInvariant:
    def test_within_bound_passes(self):
        inv = SpectralInvariant("gain_bound", lambda_max=0.9)
        K_old = np.eye(2) * 0.5
        K_new = np.eye(2) * 0.8
        inv.validate(K_old, K_new)  # no raise

    def test_exceeds_bound_raises(self):
        inv = SpectralInvariant("gain_bound", lambda_max=0.9)
        K_old = np.eye(2) * 0.5
        K_new = np.eye(2) * 1.2  # spectral radius = 1.2 > 0.9
        with pytest.raises(InvariantViolation) as exc_info:
            inv.validate(K_old, K_new)
        assert "spectral radius" in str(exc_info.value).lower()


class TestInvariantChecker:
    def test_register_and_validate_ok(self):
        checker = InvariantChecker()
        checker.register(NormInvariant("p_drift", epsilon=0.2, p=2))
        theta_old = np.zeros(4)
        theta_new = np.array([0.1, 0.05, 0.08, 0.05])
        checker.validate(theta_old, theta_new)  # no raise

    def test_fail_fast_on_first_violation(self):
        checker = InvariantChecker()
        checker.register(NormInvariant("a", epsilon=1.0, p=2))
        checker.register(NormInvariant("b", epsilon=0.01, p=2))
        checker.register(SpectralInvariant("c", lambda_max=0.9))
        old = np.zeros(4)
        new = np.ones(4) * 0.5
        # NormInvariant("a") passes (norm=1.0 <= 1.0), NormInvariant("b") fails
        with pytest.raises(InvariantViolation) as exc_info:
            checker.validate(old, new)
        assert exc_info.value.invariant_name == "b"

    def test_validate_bulk_collects_all_violations(self):
        checker = InvariantChecker()
        checker.register(NormInvariant("drift", epsilon=0.2, p=2))
        pairs = [
            (np.zeros(3), np.array([0.1, 0.05, 0.05])),  # pass
            (np.zeros(3), np.array([0.5, 0.4, 0.3])),    # fail
            (np.zeros(3), np.array([0.1, 0.2, 0.05])),    # fail
        ]
        violations = checker.validate_bulk(pairs)
        assert len(violations) == 2
        assert violations[0].details["pair_index"] == 1
        assert violations[1].details["pair_index"] == 2


# ── StabilityGovernor ──────────────────────────────────────────────────────

class TestStabilityGovernor:
    def make_signal(
        self,
        health=0.8,
        psi=0.85,
        coherence_drop=0.1,
        drift_severity=0.2,
        oscillation=False,
        mutation_density=0.1,
        recent_mutation_density=0.1,
    ) -> GovernorSignal:
        return GovernorSignal(
            health_score=health,
            plan_stability_index=psi,
            coherence_drop_rate=coherence_drop,
            drift_severity=drift_severity,
            oscillation_detected=oscillation,
            recent_mutation_density=recent_mutation_density,
        )

    def test_oscillation_hard_blocks(self):
        gov = StabilityGovernor()
        sig = self.make_signal(health=0.9, oscillation=True)
        assert gov.evaluate(sig) == GovernorDecision.BLOCK

    def test_low_health_blocks(self):
        gov = StabilityGovernor()
        sig = self.make_signal(health=0.2)
        assert gov.evaluate(sig) == GovernorDecision.BLOCK

    def test_high_drift_severity_blocks(self):
        gov = StabilityGovernor()
        sig = self.make_signal(drift_severity=0.9)
        assert gov.evaluate(sig) == GovernorDecision.BLOCK

    def test_high_mutation_density_blocks(self):
        gov = StabilityGovernor(GovernorThresholds(mutation_density_max=0.5))
        sig = self.make_signal(recent_mutation_density=0.6)
        assert gov.evaluate(sig) == GovernorDecision.BLOCK

    def test_warning_zone_defers(self):
        gov = StabilityGovernor(GovernorThresholds(health_warn=0.6, health_block=0.3))
        sig = self.make_signal(health=0.45)
        assert gov.evaluate(sig) == GovernorDecision.DEFER

    def test_psi_and_health_critical_escalates(self):
        gov = StabilityGovernor()
        # After reordering, ESCALATE check runs before DEFER.
        # PSI=0.05 < 0.1 and health=0.49 < 0.5 → ESCALATE (step 5, before DEFER step 6)
        sig = GovernorSignal(health_score=0.49, plan_stability_index=0.05,
                             coherence_drop_rate=0.1, drift_severity=0.2,
                             oscillation_detected=False, recent_mutation_density=0.1)
        assert gov.evaluate(sig) == GovernorDecision.ESCALATE

    def test_healthy_signal_allows(self):
        gov = StabilityGovernor()
        sig = self.make_signal(health=0.8, psi=0.85, drift_severity=0.1)
        assert gov.evaluate(sig) == GovernorDecision.ALLOW

    def test_filter_allowed(self):
        gov = StabilityGovernor()
        signals = [
            self.make_signal(health=0.8),   # ALLOW
            self.make_signal(health=0.2),   # BLOCK
            self.make_signal(health=0.45),  # DEFER
        ]
        allowed = gov.filter_allowed(signals)
        assert len(allowed) == 1

    def test_explain_shows_reasons(self):
        gov = StabilityGovernor()
        sig = self.make_signal(health=0.2, drift_severity=0.9)
        explanation = gov.explain(sig)
        assert "BLOCK" in explanation
        assert "health" in explanation or "drift" in explanation


# ── MutationLedger ───────────────────────────────────────────────────────

class TestMutationLedger:
    def test_record_creates_entry(self):
        ledger = MutationLedger()
        entry = ledger.record(
            theta_old=np.array([1.0, 2.0]),
            theta_new=np.array([1.2, 2.1]),
            trigger_source=TriggerSource.DRIFT_RETUNE,
            trigger_metadata={"drift_episode_id": "ep_001", "severity_score": 0.62},
            governor_decision="ALLOW",
            invariants_passed=["param_drift"],
        )
        assert entry.mutation_id is not None
        assert entry.trigger_source == "drift_retune"
        np.testing.assert_allclose(entry.diff, [0.2, 0.1], atol=1e-9)
        assert entry.diff_norm_l2 > 0

    def test_record_multiple_order_preserved(self):
        ledger = MutationLedger()
        e1 = ledger.record(np.zeros(2), np.array([0.1, 0.1]), TriggerSource.SCHEDULED)
        e2 = ledger.record(np.ones(2), np.array([1.1, 1.2]), TriggerSource.DRIFT_REPLAN)
        assert ledger.count() == 2
        assert ledger.last() == e2
        assert ledger.all()[0] == e1

    def test_by_trigger_filters(self):
        ledger = MutationLedger()
        ledger.record(np.zeros(2), np.ones(2), TriggerSource.DRIFT_RETUNE)
        ledger.record(np.zeros(2), np.ones(2), TriggerSource.DRIFT_RETUNE)
        ledger.record(np.zeros(2), np.ones(2), TriggerSource.DRIFT_REPLAN)
        assert len(ledger.by_trigger(TriggerSource.DRIFT_RETUNE)) == 2
        assert len(ledger.by_trigger(TriggerSource.DRIFT_REPLAN)) == 1

    def test_rolling_density_zero_entries(self):
        ledger = MutationLedger()
        assert ledger.rolling_density(window=10) == 0.0

    def test_rolling_density(self):
        ledger = MutationLedger()
        for _ in range(5):
            ledger.record(np.zeros(2), np.ones(2), TriggerSource.SCHEDULED)
        density = ledger.rolling_density(window=10)
        assert density == 1.0  # all 5 entries within last 10

    def test_diff_stats(self):
        ledger = MutationLedger()
        for _ in range(3):
            ledger.record(np.zeros(3), np.ones(3) * 0.5, TriggerSource.SCHEDULED)
        stats = ledger.diff_stats()
        assert stats["total_mutations"] == 3
        assert stats["max_l2"] > 0

    def test_flush_and_reload(self):
        ledger = MutationLedger()
        ledger.record(np.zeros(3), np.array([0.1, 0.2, 0.3]), TriggerSource.MANUAL_OVERRIDE)
        ledger.record(np.ones(3), np.array([1.1, 1.2, 1.3]), TriggerSource.DRIFT_RETUNE)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "ledger.jsonl"
            ledger.flush(path)
            assert path.exists()

            loaded = MutationLedger.load(path)
            assert loaded.count() == 2
            assert loaded.all()[0].trigger_source == "manual_override"
            assert loaded.all()[1].trigger_source == "drift_retune"

    def test_get_by_id(self):
        ledger = MutationLedger()
        entry = ledger.record(np.zeros(2), np.ones(2), TriggerSource.SCHEDULED)
        found = ledger.get(entry.mutation_id)
        assert found == entry
        assert ledger.get("nonexistent-id") is None


# ── RollbackEngine ────────────────────────────────────────────────────────

class TestRollbackEngine:
    def test_checkpoint_stores_state(self):
        engine = RollbackEngine()
        theta = np.array([1.0, 2.0, 3.0])
        cp = engine.checkpoint(theta, metadata={"health_score": 0.85})
        assert cp.checkpoint_id is not None
        assert cp.theta == [1.0, 2.0, 3.0]
        assert cp.metadata["health_score"] == 0.85

    def test_restore_returns_exact_state(self):
        engine = RollbackEngine()
        theta = np.array([1.5, -0.7, 3.2])
        cp = engine.checkpoint(theta)
        restored = engine.restore(cp.checkpoint_id)
        np.testing.assert_array_equal(restored, theta)

    def test_restore_unknown_raises_keyerror(self):
        engine = RollbackEngine()
        with pytest.raises(KeyError):
            engine.restore("nonexistent-id")

    def test_revert_last_mutation(self):
        ledger = MutationLedger()
        theta_old = np.array([1.0, 2.0])
        theta_new = np.array([1.3, 2.2])
        entry = ledger.record(theta_old, theta_new, TriggerSource.DRIFT_RETUNE)

        engine = RollbackEngine()
        success, theta_reverted = engine.revert(entry.mutation_id, ledger)
        assert success is True
        np.testing.assert_array_equal(theta_reverted, theta_old)

    def test_revert_unknown_mutation_returns_false(self):
        engine = RollbackEngine()
        ledger = MutationLedger()
        success, theta = engine.revert("no-such-id", ledger)
        assert success is False
        assert theta is None

    def test_latest_checkpoint(self):
        engine = RollbackEngine()
        engine.checkpoint(np.array([1.0]))
        cp2 = engine.checkpoint(np.array([2.0]))
        assert engine.latest().checkpoint_id == cp2.checkpoint_id

    def test_flush_and_reload(self):
        engine = RollbackEngine()
        engine.checkpoint(np.array([1.0, 2.0]), metadata={"v": 1})
        engine.checkpoint(np.array([3.0, 4.0]), metadata={"v": 2})

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "checkpoints.json"
            engine.flush(path)
            assert path.exists()

            loaded = RollbackEngine.load(path)
            assert len(loaded) == 2
            latest = loaded.latest()
            assert latest.theta == [3.0, 4.0]

    def test_checkpoints_are_immutable(self):
        """Multiple checkpoints with same theta are distinct."""
        engine = RollbackEngine()
        theta = np.array([1.0, 2.0])
        cp1 = engine.checkpoint(theta, metadata={"n": 1})
        cp2 = engine.checkpoint(theta, metadata={"n": 2})
        assert cp1.checkpoint_id != cp2.checkpoint_id
        assert cp1.metadata["n"] == 1
        assert cp2.metadata["n"] == 2


# ── Integration: full pipeline ────────────────────────────────────────────

class TestFullPipeline:
    def test_full_safe_mutation_pipeline(self):
        """
        Simulate a full safe mutation pipeline:
        1. snapshot → 2. governor check → 3. invariant check → 4. ledger record
        """
        # 1. Initial state
        theta_old = np.array([0.5, -0.3, 0.1, 0.7])
        theta_new = np.array([0.55, -0.28, 0.12, 0.72])  # small delta

        # 2. Stability governor check
        gov = StabilityGovernor()
        signal = GovernorSignal(
            health_score=0.78,
            plan_stability_index=0.82,
            coherence_drop_rate=0.12,
            drift_severity=0.35,
            oscillation_detected=False,
            recent_mutation_density=0.2,
        )
        decision = gov.evaluate(signal)
        assert decision == GovernorDecision.ALLOW

        # 3. Invariant check
        checker = InvariantChecker()
        checker.register(NormInvariant("param_drift", epsilon=0.15, p=2))
        checker.validate(theta_old, theta_new)  # should not raise

        # 4. Ledger record
        ledger = MutationLedger()
        entry = ledger.record(
            theta_old,
            theta_new,
            trigger_source=TriggerSource.DRIFT_RETUNE,
            trigger_metadata={"drift_episode_id": "ep_test", "severity_score": 0.35},
            governor_decision=decision.value,
            invariants_passed=["param_drift"],
        )
        assert entry.mutation_id is not None

        # 5. Rollback test
        engine = RollbackEngine()
        restored = engine.restore(engine.checkpoint(theta_old).checkpoint_id)
        np.testing.assert_array_equal(restored, theta_old)

    def test_blocked_mutation_not_recorded(self):
        """
        When governor blocks, no mutation should be recorded.
        Simulates a blocked drift episode.
        """
        np.zeros(4)
        np.ones(4) * 0.5

        gov = StabilityGovernor()
        signal = GovernorSignal(
            health_score=0.25,           # < health_block=0.30 → BLOCK
            plan_stability_index=0.4,
            coherence_drop_rate=0.5,
            drift_severity=0.3,
            oscillation_detected=False,
            recent_mutation_density=0.1,
        )
        decision = gov.evaluate(signal)
        assert decision == GovernorDecision.BLOCK

        # No ledger entry should be created for blocked mutations
        # (caller is responsible for this invariant)
        MutationLedger()
        # In real code: skip ledger.record() when decision != ALLOW
        assert decision != GovernorDecision.ALLOW
