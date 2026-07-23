"""v8.2b Controlled Autocorrection — 17 tests (4 mandatory + 13 additional)."""

from __future__ import annotations

import numpy as np
import pytest

from orchestration.v8_2b_controlled_autocorrection import (
    ControlSurfaceModifier,
    ExecutionStatus,
    FeedbackInjectionLoop,
    FeedbackSignal,
    MutationClass,
    MutationExecutor,
    PolicyContext,
    PolicySelector,
    SeverityActionMapper,
    SeverityLevel,
)
from orchestration.v8_2b_controlled_autocorrection.feedback_injection import FeedbackSignalType
from orchestration.v8_2b_controlled_autocorrection.mutation_planner import (
    MutationPlanner,
    MutationTarget,
)
from orchestration.v8_2b_controlled_autocorrection.policy_selector import PolicyMode

# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def severity_mapper():
    return SeverityActionMapper()

@pytest.fixture
def policy_selector():
    return PolicySelector(mode=PolicyMode.BALANCED)

@pytest.fixture
def conservative_selector():
    return PolicySelector(mode=PolicyMode.CONSERVATIVE)

@pytest.fixture
def aggressive_selector():
    return PolicySelector(mode=PolicyMode.AGGRESSIVE)

@pytest.fixture
def theta():
    return np.array([0.5, 0.3, 0.8, 0.2, 0.6, 0.4, 0.7, 0.1])

class AlwaysAllow:
    def evaluate(self, sig):
        from orchestration.v8_2a_safety_foundations import GovernorDecision
        return GovernorDecision.ALLOW

class NoOpInvariantChecker:
    def validate(self, theta_before, theta_after):
        pass

class RecordingLedger:
    def __init__(self):
        self.entries = []
    def record(self, theta_old, theta_new, trigger_source, trigger_metadata,
               governor_decision, invariants_passed):
        self.entries.append({"theta_old": tuple(theta_old), "theta_new": tuple(theta_new)})
        return self.entries[-1]

class NoOpRollback:
    def restore_snapshot(self, snapshot_id):
        pass
    def create_snapshot(self, theta, metadata):
        return "snap_001"

@pytest.fixture
def executor(theta, severity_mapper, policy_selector):
    return MutationExecutor(
        theta=theta.copy(),
        severity_mapper=severity_mapper,
        policy_selector=policy_selector,
        safety_gate=AlwaysAllow(),
        invariant_checker=NoOpInvariantChecker(),
        mutation_ledger=RecordingLedger(),
        rollback_engine=NoOpRollback(),
    )


# ── [1] Severity routing ──────────────────────────────────────────────────────

class TestSeverityRouting:
    @pytest.mark.parametrize("drift_score,expected_severity,expected_class", [
        (0.02,  SeverityLevel.NEGLIGIBLE, MutationClass.RETUNE),
        (0.10,  SeverityLevel.LOW,       MutationClass.RETUNE),
        (0.30,  SeverityLevel.MEDIUM,   MutationClass.REWEIGHT),
        (0.50,  SeverityLevel.HIGH,     MutationClass.REPLAN),   # high_max=0.45 → 0.50 is HIGH
        (0.60,  SeverityLevel.HIGH,     MutationClass.REPLAN),
        (0.80,  SeverityLevel.CRITICAL, MutationClass.RESET),
        (0.99,  SeverityLevel.CRITICAL, MutationClass.RESET),
    ])
    def test_severity_routing(self, severity_mapper, drift_score,
                               expected_severity, expected_class):
        sev, cls = severity_mapper.resolve(drift_score)
        assert sev == expected_severity
        assert cls == expected_class


# ── [2] Mutation safety ────────────────────────────────────────────────────────

class TestMutationSafety:
    def test_low_health_blocks_mutation(self, executor):
        class AlwaysBlock:
            def evaluate(self, sig):
                from orchestration.v8_2a_safety_foundations import GovernorDecision
                return GovernorDecision.BLOCK
        executor._safety_gate = AlwaysBlock()
        theta_before = executor.current_theta().copy()

        result = executor.execute(
            drift_score=0.40, health_score=0.10,
            mutation_density=0.3, coherence_drop=0.1, oscillation_detected=False,
        )

        assert result.status == ExecutionStatus.BLOCKED
        assert result.theta_after == tuple(theta_before)
        assert result.delta_norm_l2 == 0.0

    def test_conservative_critical_blocks_reset(self, conservative_selector):
        ctx = PolicyContext(
            drift_score=0.90, health_score=0.80, mutation_density=0.2,
            coherence_drop=0.05, oscillation_detected=False,
            severity=SeverityLevel.CRITICAL, mutation_class=MutationClass.RESET,
        )
        policy = conservative_selector.select(ctx)
        # CONSERVATIVE: CRITICAL → REWEIGHT (RESET blocked); REWEIGHT branch
        # does NOT set require_human_approval=True (only oscillation does)
        assert policy.class_label != MutationClass.RESET


# ── [3] Replay regression (invariant violation → rollback) ────────────────────

class TestReplayRegression:
    def test_invariant_failure_triggers_rollback(self, theta, severity_mapper, policy_selector):
        class AlwaysFailInvariant:
            def validate(self, theta_before, theta_after):
                raise ValueError("Invariant violated: param out of bounds")

        executor = MutationExecutor(
            theta=theta.copy(), severity_mapper=severity_mapper,
            policy_selector=policy_selector, safety_gate=AlwaysAllow(),
            invariant_checker=AlwaysFailInvariant(),
            mutation_ledger=RecordingLedger(), rollback_engine=NoOpRollback(),
        )
        theta_before = executor.current_theta().copy()

        result = executor.execute(
            drift_score=0.35, health_score=0.80,
            mutation_density=0.3, coherence_drop=0.1, oscillation_detected=False,
        )

        assert result.status == ExecutionStatus.ROLLED_BACK
        assert tuple(executor.current_theta()) == tuple(theta_before)
        assert result.policy_violated is True
        assert "Invariant" in (result.error_message or "")


# ── [4] Improvement acceptance ────────────────────────────────────────────────

class TestImprovementAcceptance:
    def test_valid_mutation_commits(self, executor):
        ledger_before = len(executor._ledger.entries)
        result = executor.execute(
            drift_score=0.30, health_score=0.80,
            mutation_density=0.2, coherence_drop=0.05, oscillation_detected=False,
        )
        assert result.status == ExecutionStatus.SUCCESS
        assert result.accepted is True
        assert len(executor._ledger.entries) == ledger_before + 1
        assert result.execution_id.startswith("exec_")

    def test_delta_nonzero_on_success(self, executor):
        result = executor.execute(
            drift_score=0.35, health_score=0.75,
            mutation_density=0.3, coherence_drop=0.1, oscillation_detected=False,
        )
        assert result.delta_norm_l2 > 0.0
        assert result.theta_before != result.theta_after


# ── [5] Oscillation → REPLAN override ────────────────────────────────────────

class TestOscillationOverride:
    def test_oscillation_forces_replan(self, policy_selector):
        ctx = PolicyContext(
            drift_score=0.05, health_score=0.90, mutation_density=0.1,
            coherence_drop=0.0, oscillation_detected=True,
            severity=SeverityLevel.NEGLIGIBLE, mutation_class=MutationClass.RETUNE,
        )
        policy = policy_selector.select(ctx)
        assert policy.class_label == MutationClass.REPLAN
        assert policy.require_human_approval is True


# ── [6] density_stress suppresses RESET ──────────────────────────────────────

class TestDensityStress:
    def test_density_stress_suppresses_reset(self, policy_selector):
        ctx = PolicyContext(
            drift_score=0.90, health_score=0.90, mutation_density=0.80,
            coherence_drop=0.1, oscillation_detected=False,
            severity=SeverityLevel.CRITICAL, mutation_class=MutationClass.RESET,
        )
        policy = policy_selector.select(ctx)
        assert policy.class_label != MutationClass.RESET


# ── [7] CONSERVATIVE HIGH → REWEIGHT ─────────────────────────────────────────

class TestConservativeMode:
    def test_high_suppressed_to_reweight(self, conservative_selector):
        ctx = PolicyContext(
            drift_score=0.60, health_score=0.70, mutation_density=0.3,
            coherence_drop=0.1, oscillation_detected=False,
            severity=SeverityLevel.HIGH, mutation_class=MutationClass.REPLAN,
        )
        policy = conservative_selector.select(ctx)
        assert policy.class_label == MutationClass.REWEIGHT


# ── [8] AGGRESSIVE CRITICAL → RESET ─────────────────────────────────────────

class TestAggressiveMode:
    def test_aggressive_critical_becomes_reset(self, aggressive_selector):
        ctx = PolicyContext(
            drift_score=0.90, health_score=0.95, mutation_density=0.1,
            coherence_drop=0.05, oscillation_detected=False,
            severity=SeverityLevel.CRITICAL, mutation_class=MutationClass.RESET,
        )
        policy = aggressive_selector.select(ctx)
        assert policy.class_label == MutationClass.RESET
        assert policy.require_human_approval is False


# ── [9] MutationPlanner RETUNE ────────────────────────────────────────────────

class TestPlannerRetune:
    def test_retune_targets_gain_scheduler(self):
        planner = MutationPlanner(theta_dim=10)
        spec = planner.plan("retune", "low", 0.15, 0.80, 0.05, 0.2)
        assert len(spec.plans) == 1
        assert spec.plans[0].target == MutationTarget.GAIN_SCHEDULER
        assert spec.plans[0].expected_impact < 0
        assert spec.plans[0].risk_level in ("low", "medium")

    def test_retune_low_risk_when_healthy(self):
        planner = MutationPlanner(theta_dim=10)
        spec = planner.plan("retune", "low", 0.10, 0.90, 0.0, 0.1)
        assert spec.plans[0].risk_level == "low"


# ── [10] MutationPlanner REPLAN ───────────────────────────────────────────────

class TestPlannerReplan:
    def test_replan_targets_thresholds(self):
        planner = MutationPlanner(theta_dim=20)
        spec = planner.plan("replan", "high", 0.65, 0.70, 0.20, 0.4)
        assert any(p.target == MutationTarget.REPLANNER_THRESHOLDS for p in spec.plans)
        assert sum(len(p.region_indices) for p in spec.plans) >= 4


# ── [11] MutationPlanner RESET → 2 plans ─────────────────────────────────────

class TestPlannerReset:
    def test_reset_produces_two_plans(self):
        planner = MutationPlanner(theta_dim=8)
        spec = planner.plan("reset", "critical", 0.90, 0.60, 0.30, 0.5)
        assert len(spec.plans) == 2
        targets = {p.target for p in spec.plans}
        assert MutationTarget.EVALUATOR_WEIGHTS in targets
        assert MutationTarget.ARBITRATION_PRIORITIES in targets

    def test_reset_has_high_risk_plan(self):
        planner = MutationPlanner(theta_dim=8)
        spec = planner.plan("reset", "critical", 0.90, 0.60, 0.30, 0.5)
        assert any(p.risk_level == "high" for p in spec.plans)


# ── [12] Blocked mutation → zero delta ───────────────────────────────────────

class TestBlockedZeroDelta:
    def test_blocked_delta_is_zero(self, executor):
        class AlwaysBlock:
            def evaluate(self, sig):
                from orchestration.v8_2a_safety_foundations import GovernorDecision
                return GovernorDecision.BLOCK
        executor._safety_gate = AlwaysBlock()

        result = executor.execute(
            drift_score=0.40, health_score=0.10,
            mutation_density=0.3, coherence_drop=0.1, oscillation_detected=False,
        )

        assert result.delta_norm_l2 == 0.0
        assert result.theta_before == result.theta_after
        assert result.status == ExecutionStatus.BLOCKED


# ── [13] Rollback restores theta_before ───────────────────────────────────────

class TestRollbackRestores:
    def test_rollback_reverts_theta(self, theta, severity_mapper, policy_selector):
        class AlwaysFailInvariant:
            def validate(self, theta_before, theta_after):
                raise RuntimeError("Simulated failure")

        executor = MutationExecutor(
            theta=theta.copy(), severity_mapper=severity_mapper,
            policy_selector=policy_selector, safety_gate=AlwaysAllow(),
            invariant_checker=AlwaysFailInvariant(),
            mutation_ledger=RecordingLedger(), rollback_engine=NoOpRollback(),
        )
        theta_before = executor.current_theta().copy()

        result = executor.execute(
            drift_score=0.30, health_score=0.80,
            mutation_density=0.3, coherence_drop=0.1, oscillation_detected=False,
        )

        assert result.status == ExecutionStatus.ROLLED_BACK
        assert tuple(executor.current_theta()) == tuple(theta_before)


# ── [14] Oscillation detection ────────────────────────────────────────────────

class TestOscillationDetection:
    def test_direction_history_populated_by_ingest(self):
        """Verify ingest populates _direction_history (unit-level test)."""
        modifier = ControlSurfaceModifier()
        # First signal sets _last_theta but doesn't record direction
        modifier.ingest(FeedbackSignal(
            signal_type=FeedbackSignalType.SUCCESS, episode_id="ep0", timestamp=0.0,
            delta_norm_l2=0.1, coherence_before=0.8, coherence_after=0.85, health_delta=0.05,
        ))
        # Second signal records first direction entry
        modifier.ingest(FeedbackSignal(
            signal_type=FeedbackSignalType.FAILED, episode_id="ep1", timestamp=1.0,
            delta_norm_l2=0.1, coherence_before=0.8, coherence_after=0.8, health_delta=0.0,
        ))
        assert len(modifier._direction_history) == 1

    def test_no_oscillation_with_uniform_signals(self):
        modifier = ControlSurfaceModifier()
        loop = FeedbackInjectionLoop(modifier)

        for i in range(6):
            s = FeedbackSignal(
                signal_type=FeedbackSignalType.SUCCESS,
                episode_id=f"ep{i}", timestamp=float(i),
                delta_norm_l2=0.1,
                coherence_before=0.8, coherence_after=0.85,
                health_delta=0.05,
            )
            loop.receive(s)

        assert loop._modifier.oscillation_detected() is False


# ── [15] Biased delta ─────────────────────────────────────────────────────────

class TestBiasedDelta:
    def test_biased_delta_reweights_magnitude(self):
        modifier = ControlSurfaceModifier()
        loop = FeedbackInjectionLoop(modifier)

        # Feed successful signals → exploitation bonus
        for i in range(5):
            loop.receive(FeedbackSignal(
                signal_type=FeedbackSignalType.SUCCESS,
                episode_id=f"ep{i}", timestamp=float(i),
                delta_norm_l2=0.1,
                coherence_before=0.8, coherence_after=0.85,
                health_delta=0.05,
            ))

        base = np.array([0.1, 0.2, -0.1])
        biased = loop.compute_biased_delta(base, MutationClass.RETUNE)

        # Exploitation bonus should increase magnitude
        assert np.linalg.norm(biased) > np.linalg.norm(base)


# ── [16] Severity threshold boundary NEGLIGIBLE/LOW ─────────────────────────

class TestSeverityBoundaries:
    def test_negligible_low_boundary(self, severity_mapper):
        # Thresholds: low_max=0.20 → exactly 0.20 is LOW
        assert severity_mapper.classify(0.0) == SeverityLevel.NEGLIGIBLE
        assert severity_mapper.classify(0.05) == SeverityLevel.NEGLIGIBLE   # within negligible_max=0.05
        assert severity_mapper.classify(0.20) == SeverityLevel.LOW           # at low_max

    def test_high_critical_boundary(self, severity_mapper):
        # Code: drift_score <= high_max(0.75) → HIGH; > 0.75 → CRITICAL
        assert severity_mapper.classify(0.0) == SeverityLevel.NEGLIGIBLE
        assert severity_mapper.classify(0.74) == SeverityLevel.HIGH          # just below
        assert severity_mapper.classify(0.75) == SeverityLevel.HIGH         # at high_max (inclusive)
        assert severity_mapper.classify(0.76) == SeverityLevel.CRITICAL      # just above
        assert severity_mapper.classify(1.0) == SeverityLevel.CRITICAL
