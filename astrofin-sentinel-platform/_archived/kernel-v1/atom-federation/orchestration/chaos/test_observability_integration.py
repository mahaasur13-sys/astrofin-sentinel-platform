"""
test_observability_integration.py — HARDENING-2 MVP tests

Tests for:
  - DriftCorrelation record creation
  - ImpactScorer deterministic scoring
  - ChaosFeedbackController feedback rules
  - ChaosObservabilityBridge full integration
  - Edge cases: zero/missing signals, empty lists
"""

import pytest

from orchestration.chaos.observability_integration import (
    ChaosFeedbackController,
    ChaosObservabilityBridge,
    ControllerConfig,
    DriftType,
    ImpactScorer,
    ImpactWeights,
)

# ─── ImpactScorer tests ────────────────────────────────────────────────────────

class TestImpactScorer:
    """ImpactScorer: deterministic weighted scoring."""

    def test_score_all_zero_returns_zero(self):
        scorer = ImpactScorer()
        assert scorer.score(0.0, 0.0, 0.0, 0.0) == 0.0

    def test_score_all_ones_returns_one(self):
        scorer = ImpactScorer()
        assert scorer.score(1.0, 1.0, 1.0, 1.0) == 1.0

    def test_score_mixed_returns_correct_weighted_sum(self):
        # w_osc=0.25, w_drop=0.25, w_block=0.30, w_recovery=0.20
        # 1.0*0.25 + 0.5*0.25 + 0.0*0.30 + 1.0*0.20 = 0.25+0.125+0+0.20 = 0.575
        scorer = ImpactScorer()
        impact = scorer.score(1.0, 0.5, 0.0, 1.0)
        assert abs(impact - 0.575) < 0.001

    def test_score_clamps_negative_to_zero(self):
        scorer = ImpactScorer()
        assert scorer.score(-0.5, 0.0, 0.0, 0.0) == 0.0

    def test_score_clamps_above_one_to_one(self):
        scorer = ImpactScorer()
        assert scorer.score(2.0, 2.0, 2.0, 2.0) == 1.0

    def test_score_custom_weights(self):
        weights = ImpactWeights(
            w_oscillation=0.4,
            w_coherence_drop=0.3,
            w_governor_block_rate=0.2,
            w_recovery_time=0.1,
        )
        scorer = ImpactScorer(weights=weights)
        impact = scorer.score(0.5, 0.5, 0.5, 0.5)
        assert abs(impact - 0.5) < 0.001

    def test_score_weights_must_sum_to_one(self):
        # sum = 0.5+0.3+0.1+0.0 = 0.9 → should raise
        bad_weights = ImpactWeights(
            w_oscillation=0.5,
            w_coherence_drop=0.3,
            w_governor_block_rate=0.1,
            w_recovery_time=0.0,
        )
        with pytest.raises(ValueError):
            ImpactScorer(weights=bad_weights)

    def test_explain_returns_breakdown(self):
        scorer = ImpactScorer()
        result = scorer.explain(1.0, 0.5, 0.0, 1.0)
        assert "impact=" in result
        assert "oscillation" in result
        assert "coherence_drop" in result


# ─── ChaosFeedbackController tests ────────────────────────────────────────────

class TestChaosFeedbackController:
    """ChaosFeedbackController: intensity tuning from impact."""

    def test_high_impact_reduces_intensity(self):
        controller = ChaosFeedbackController()
        new_int = controller.feedback(0.80, 0.85)
        assert new_int < 0.80  # reduction

    def test_low_impact_increases_intensity(self):
        controller = ChaosFeedbackController()
        new_int = controller.feedback(0.20, 0.10)
        assert new_int > 0.20  # increase

    def test_mid_impact_holds(self):
        controller = ChaosFeedbackController()
        new_int = controller.feedback(0.50, 0.50)
        assert new_int == 0.50  # no change

    def test_feedback_clamped_to_min(self):
        controller = ChaosFeedbackController(
            config=ControllerConfig(min_intensity=0.10)
        )
        # Even with very high impact, shouldn't drop below min
        result = controller.feedback(0.12, 0.95)
        assert result >= 0.10

    def test_feedback_clamped_to_max(self):
        controller = ChaosFeedbackController(
            config=ControllerConfig(max_intensity=0.90)
        )
        result = controller.feedback(0.90, 0.05)
        assert result <= 0.90

    def test_explain_includes_action(self):
        controller = ChaosFeedbackController()
        result = controller.explain(0.50, 0.80)
        assert "REDUCE" in result
        result = controller.explain(0.50, 0.10)
        assert "INCREASE" in result
        result = controller.explain(0.50, 0.50)
        assert "HOLD" in result


# ─── ChaosObservabilityBridge tests ───────────────────────────────────────────

class TestChaosObservabilityBridge:
    """ChaosObservabilityBridge: full integration surface."""

    def test_record_chaos_event_stored(self):
        bridge = ChaosObservabilityBridge()
        event = bridge.record_chaos_event("e1", "kill_agent", 0.7, 10)
        assert event.event_id == "e1"
        assert event.intensity == 0.7
        assert event.tick_injected == 10

    def test_attach_to_drift_returns_correlation(self):
        bridge = ChaosObservabilityBridge()
        bridge.record_chaos_event("e1", "latency_spike", 0.5, 5)
        corr = bridge.attach_to_drift("e1", DriftType.OSCILLATING_PLAN, 3, 0.6)
        assert corr.chaos_event_id == "e1"
        assert corr.drift_type == DriftType.OSCILLATING_PLAN
        assert corr.lag_ticks == 3
        assert corr.severity == 0.6

    def test_correlations_list_grows(self):
        bridge = ChaosObservabilityBridge()
        bridge.record_chaos_event("e1", "latency_spike", 0.5, 5)
        bridge.attach_to_drift("e1", DriftType.OSCILLATING_PLAN, 3, 0.6)
        bridge.attach_to_drift("e1", DriftType.UNSTABLE_GOAL, 5, 0.4)
        assert len(bridge.correlations) == 2

    def test_correlation_summary_stats(self):
        bridge = ChaosObservabilityBridge()
        bridge.record_chaos_event("e1", "latency_spike", 0.5, 5)
        bridge.attach_to_drift("e1", DriftType.OSCILLATING_PLAN, 3, 0.6)
        bridge.attach_to_drift("e1", DriftType.UNSTABLE_GOAL, 5, 0.4)
        summary = bridge.correlation_summary()
        assert summary["total"] == 2
        assert "oscillating_plan" in summary["by_type"]
        assert summary["avg_lag"] == 4.0
        assert summary["avg_severity"] == 0.5

    def test_correlation_summary_empty(self):
        bridge = ChaosObservabilityBridge()
        summary = bridge.correlation_summary()
        assert summary["total"] == 0

    def test_governor_block_rate_computes(self):
        bridge = ChaosObservabilityBridge()
        bridge.record_governor_decision(True)
        bridge.record_governor_decision(True)
        bridge.record_governor_decision(False)
        rate = bridge.governor_block_rate()
        assert rate == pytest.approx(2 / 3, rel=0.01)

    def test_governor_block_rate_empty_returns_zero(self):
        bridge = ChaosObservabilityBridge()
        assert bridge.governor_block_rate() == 0.0

    def test_compute_impact_uses_governor_block_rate(self):
        bridge = ChaosObservabilityBridge()
        bridge.record_governor_decision(True)
        bridge.record_governor_decision(False)
        impact = bridge.compute_impact(oscillation=0.0, coherence_drop=0.0, recovery_time=1.0)
        # Default weights: w_block=0.30, w_recovery=0.20
        # block_rate=0.5 → 0.30*0.5 = 0.15
        # recovery=1.0 → 0.20*1.0 = 0.20
        # total = 0.35
        assert abs(impact - 0.35) < 0.001

    def test_feedback_returns_new_intensity(self):
        bridge = ChaosObservabilityBridge()
        bridge._current_intensity = 0.50
        new_int = bridge.feedback(impact=0.80)
        assert new_int < 0.50  # high impact → reduce

    def test_feedback_increases_on_low_impact(self):
        bridge = ChaosObservabilityBridge()
        bridge._current_intensity = 0.20
        new_int = bridge.feedback(impact=0.10)
        assert new_int > 0.20  # low impact → increase

    def test_current_intensity_updates_after_feedback(self):
        bridge = ChaosObservabilityBridge()
        bridge._current_intensity = 0.50
        bridge.feedback(impact=0.80)
        assert bridge.current_intensity < 0.50

    def test_explain_contains_state(self):
        bridge = ChaosObservabilityBridge()
        bridge._current_intensity = 0.50
        result = bridge.explain(0.65)
        assert "intensity=" in result
        assert "impact=" in result

    def test_correlations_pruned_at_capacity(self):
        bridge = ChaosObservabilityBridge(max_correlations=3)
        for i in range(5):
            bridge.record_chaos_event(f"e{i}", "kill_agent", 0.5, i)
            bridge.attach_to_drift(f"e{i}", DriftType.OSCILLATING_PLAN, 1, 0.5)
        assert len(bridge.correlations) == 3
        # Most recent 3 should be kept (e2, e3, e4)
        ids = {c.chaos_event_id for c in bridge.correlations}
        assert "e2" in ids
        assert "e3" in ids
        assert "e4" in ids
        assert "e0" not in ids
