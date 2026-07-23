"""
test_stress_envelope.py — chaos layer tests
All tests for StabilityEnvelope, EnvelopeState, MetricBound, EnvelopeBounds.
"""
import math

import pytest

from orchestration.chaos.stress_envelope import (
    EnvelopeBounds,
    EnvelopeState,
    MetricBound,
    StabilityEnvelope,
)


class TestMetricBound:
    """MetricBound: immutable bound checker."""

    def test_within_bounds_returns_false(self):
        b = MetricBound(lower=0.6, upper=1.0)
        assert not b.is_violated(0.8)

    def test_at_lower_boundary_not_violated(self):
        b = MetricBound(lower=0.6, upper=1.0)
        assert not b.is_violated(0.6)

    def test_at_upper_boundary_not_violated(self):
        b = MetricBound(lower=0.6, upper=1.0)
        assert not b.is_violated(1.0)

    def test_below_lower_is_violated(self):
        b = MetricBound(lower=0.6, upper=1.0)
        assert b.is_violated(0.5)

    def test_above_upper_is_violated(self):
        b = MetricBound(lower=0.6, upper=1.0)
        assert b.is_violated(1.1)

    def test_violation_magnitude_below(self):
        b = MetricBound(lower=0.6, upper=1.0)
        assert b.violation_magnitude(0.4) == pytest.approx(0.2)

    def test_violation_magnitude_above(self):
        b = MetricBound(lower=0.6, upper=1.0)
        assert b.violation_magnitude(1.2) == pytest.approx(0.2)

    def test_violation_magnitude_within_is_zero(self):
        b = MetricBound(lower=0.6, upper=1.0)
        assert b.violation_magnitude(0.8) == 0.0


class TestEnvelopeBounds:
    """EnvelopeBounds: default bound set."""

    def test_default_plan_stability_index_bound(self):
        b = EnvelopeBounds()
        assert b.plan_stability_index.lower == 0.6
        assert b.plan_stability_index.upper == 1.0

    def test_default_coherence_drop_rate_bound(self):
        b = EnvelopeBounds()
        assert b.coherence_drop_rate.lower == 0.0
        assert b.coherence_drop_rate.upper == 0.15

    def test_default_replanning_frequency_bound(self):
        b = EnvelopeBounds()
        assert b.replanning_frequency.lower == 0.0
        assert b.replanning_frequency.upper == 0.4

    def test_default_oscillation_index_bound(self):
        b = EnvelopeBounds()
        assert b.oscillation_index.lower == 0.0
        assert b.oscillation_index.upper == 0.3

    def test_default_dag_structural_drift_bound(self):
        b = EnvelopeBounds()
        assert b.dag_structural_drift.lower == 0.0
        assert b.dag_structural_drift.upper == 0.3

    def test_from_dict_custom_bounds(self):
        data = {
            "plan_stability_index": (0.5, 0.95),
            "coherence_drop_rate": (0.0, 0.20),
        }
        b = EnvelopeBounds.from_dict(data)
        assert b.plan_stability_index.lower == 0.5
        assert b.plan_stability_index.upper == 0.95
        assert b.coherence_drop_rate.upper == 0.20


class TestStabilityEnvelope:
    """StabilityEnvelope: core envelope logic."""

    def test_is_within_all_metrics_inside_bounds(self):
        env = StabilityEnvelope()
        metrics = {
            "plan_stability_index": 0.85,
            "coherence_drop_rate": 0.05,
            "replanning_frequency": 0.1,
            "oscillation_index": 0.1,
            "dag_structural_drift": 0.1,
        }
        assert env.is_within(metrics) is True

    def test_is_within_returns_false_on_violation(self):
        env = StabilityEnvelope()
        metrics = {
            "plan_stability_index": 0.50,
            "coherence_drop_rate": 0.05,
            "replanning_frequency": 0.1,
            "oscillation_index": 0.1,
            "dag_structural_drift": 0.1,
        }
        assert env.is_within(metrics) is False

    def test_violations_returns_empty_when_stable(self):
        env = StabilityEnvelope()
        metrics = {"plan_stability_index": 0.8, "coherence_drop_rate": 0.05}
        assert env.violations(metrics) == []

    def test_violations_returns_records_for_out_of_bounds(self):
        env = StabilityEnvelope()
        metrics = {
            "plan_stability_index": 0.50,
            "coherence_drop_rate": 0.05,
            "replanning_frequency": 0.1,
            "oscillation_index": 0.1,
            "dag_structural_drift": 0.1,
        }
        records = env.violations(metrics)
        assert len(records) == 1
        assert records[0].metric == "plan_stability_index"
        assert records[0].severity > 0

    def test_violations_multiple_metrics_violated(self):
        env = StabilityEnvelope()
        metrics = {
            "plan_stability_index": 0.50,
            "coherence_drop_rate": 0.25,
            "replanning_frequency": 0.1,
            "oscillation_index": 0.1,
            "dag_structural_drift": 0.1,
        }
        records = env.violations(metrics)
        assert len(records) == 2
        metrics_violated = {r.metric for r in records}
        assert "plan_stability_index" in metrics_violated
        assert "coherence_drop_rate" in metrics_violated

    def test_violation_score_zero_when_stable(self):
        env = StabilityEnvelope()
        metrics = {
            "plan_stability_index": 0.8,
            "coherence_drop_rate": 0.05,
            "replanning_frequency": 0.1,
            "oscillation_index": 0.1,
            "dag_structural_drift": 0.1,
        }
        assert env.violation_score(metrics) == 0.0

    def test_violation_score_positive_when_violated(self):
        env = StabilityEnvelope()
        metrics = {
            "plan_stability_index": 0.50,
            "coherence_drop_rate": 0.0,
            "replanning_frequency": 0.0,
            "oscillation_index": 0.0,
            "dag_structural_drift": 0.0,
        }
        score = env.violation_score(metrics)
        assert 0.0 < score <= 1.0

    def test_violation_score_capped_at_one(self):
        env = StabilityEnvelope()
        metrics = {
            "plan_stability_index": 0.0,
            "coherence_drop_rate": 0.0,
            "replanning_frequency": 0.0,
            "oscillation_index": 0.0,
            "dag_structural_drift": 0.0,
        }
        score = env.violation_score(metrics)
        assert score == 1.0

    def test_classify_stable(self):
        env = StabilityEnvelope()
        metrics = {
            "plan_stability_index": 0.85,
            "coherence_drop_rate": 0.05,
            "replanning_frequency": 0.1,
            "oscillation_index": 0.1,
            "dag_structural_drift": 0.1,
        }
        assert env.classify(metrics) == EnvelopeState.STABLE

    def test_classify_warning_single_violation(self):
        env = StabilityEnvelope()
        metrics = {
            "plan_stability_index": 0.50,
            "coherence_drop_rate": 0.05,
            "replanning_frequency": 0.1,
            "oscillation_index": 0.1,
            "dag_structural_drift": 0.1,
        }
        assert env.classify(metrics) == EnvelopeState.WARNING

    def test_classify_warning_two_violations(self):
        env = StabilityEnvelope()
        metrics = {
            "plan_stability_index": 0.50,
            "coherence_drop_rate": 0.25,
            "replanning_frequency": 0.1,
            "oscillation_index": 0.1,
            "dag_structural_drift": 0.1,
        }
        assert env.classify(metrics) == EnvelopeState.WARNING

    def test_classify_critical_three_violations(self):
        env = StabilityEnvelope()
        metrics = {
            "plan_stability_index": 0.50,
            "coherence_drop_rate": 0.25,
            "replanning_frequency": 0.6,
            "oscillation_index": 0.1,
            "dag_structural_drift": 0.1,
        }
        assert env.classify(metrics) == EnvelopeState.CRITICAL

    def test_classify_collapse_coherence_drop_rate(self):
        env = StabilityEnvelope()
        metrics = {
            "plan_stability_index": 0.85,
            "coherence_drop_rate": 0.50,
            "replanning_frequency": 0.1,
            "oscillation_index": 0.1,
            "dag_structural_drift": 0.1,
        }
        assert env.classify(metrics) == EnvelopeState.COLLAPSE

    def test_classify_collapse_plan_stability_index(self):
        env = StabilityEnvelope()
        metrics = {
            "plan_stability_index": 0.15,
            "coherence_drop_rate": 0.05,
            "replanning_frequency": 0.1,
            "oscillation_index": 0.1,
            "dag_structural_drift": 0.1,
        }
        assert env.classify(metrics) == EnvelopeState.COLLAPSE

    def test_classify_collapse_oscillation_index(self):
        env = StabilityEnvelope()
        metrics = {
            "plan_stability_index": 0.85,
            "coherence_drop_rate": 0.05,
            "replanning_frequency": 0.1,
            "oscillation_index": 0.90,
            "dag_structural_drift": 0.1,
        }
        assert env.classify(metrics) == EnvelopeState.COLLAPSE

    def test_collapse_takes_priority_over_critical(self):
        env = StabilityEnvelope()
        metrics = {
            "plan_stability_index": 0.15,
            "coherence_drop_rate": 0.50,
            "replanning_frequency": 0.6,
            "oscillation_index": 0.9,
            "dag_structural_drift": 0.5,
        }
        assert env.classify(metrics) == EnvelopeState.COLLAPSE

    def test_classify_ignores_unknown_metrics(self):
        env = StabilityEnvelope()
        metrics = {
            "plan_stability_index": 0.50,
            "coherence_drop_rate": 0.05,
            "replanning_frequency": 0.1,
            "oscillation_index": 0.1,
            "dag_structural_drift": 0.1,
            "unknown_metric": 999.0,
        }
        assert env.classify(metrics) == EnvelopeState.WARNING

    def test_record_violations_updates_history(self):
        env = StabilityEnvelope()
        violated = {
            "plan_stability_index": 0.50,
            "coherence_drop_rate": 0.05,
            "replanning_frequency": 0.1,
            "oscillation_index": 0.1,
            "dag_structural_drift": 0.1,
        }
        stable = {
            "plan_stability_index": 0.85,
            "coherence_drop_rate": 0.05,
            "replanning_frequency": 0.1,
            "oscillation_index": 0.1,
            "dag_structural_drift": 0.1,
        }
        env.record_violations(violated)
        env.record_violations(stable)
        assert len(env._violation_history) == 2

    def test_recent_violation_trend_returns_nan_when_empty(self):
        env = StabilityEnvelope()
        assert math.isnan(env.recent_violation_trend())

    def test_recent_violation_trend_computes_avg(self):
        env = StabilityEnvelope()
        violated = {
            "plan_stability_index": 0.50,
            "coherence_drop_rate": 0.05,
            "replanning_frequency": 0.1,
            "oscillation_index": 0.1,
            "dag_structural_drift": 0.1,
        }
        stable = {
            "plan_stability_index": 0.85,
            "coherence_drop_rate": 0.05,
            "replanning_frequency": 0.1,
            "oscillation_index": 0.1,
            "dag_structural_drift": 0.1,
        }
        env.record_violations(violated)
        env.record_violations(stable)
        trend = env.recent_violation_trend(window=2)
        assert 0.0 <= trend <= 1.0

    def test_explain_returns_full_diagnostic(self):
        env = StabilityEnvelope()
        metrics = {
            "plan_stability_index": 0.50,
            "coherence_drop_rate": 0.05,
            "replanning_frequency": 0.1,
            "oscillation_index": 0.1,
            "dag_structural_drift": 0.1,
        }
        explanation = env.explain(metrics)
        assert explanation["state"] == EnvelopeState.WARNING.value
        assert explanation["violation_count"] == 1
        assert explanation["is_within"] is False
        assert len(explanation["violations"]) == 1
        assert explanation["violations"][0]["metric"] == "plan_stability_index"


class TestStabilityEnvelopeViolationScoreFromEpisodes:
    """StabilityEnvelope.violation_score_from_episodes integration."""

    def test_returns_zero_for_empty_episodes(self):
        env = StabilityEnvelope()
        score = env.violation_score_from_episodes([], tick=10)
        assert score == 0.0

    def test_oscillating_episode_increases_oscillation_index(self):
        from orchestration.planning_observability.drift_profiler import DriftEpisode, DriftType
        env = StabilityEnvelope()
        episodes = [
            DriftEpisode(
                drift_type=DriftType.OSCILLATING_PLAN,
                start_tick=10, end_tick=10,
                severity=0.15, description="oscillation",
                evidence={},
            )
        ]
        score = env.violation_score_from_episodes(episodes, tick=10)
        assert score > 0.0

    def test_unstable_goal_episode_decreases_plan_stability(self):
        from orchestration.planning_observability.drift_profiler import DriftEpisode, DriftType
        env = StabilityEnvelope()
        episodes = [
            DriftEpisode(
                drift_type=DriftType.UNSTABLE_GOAL,
                start_tick=10, end_tick=10,
                severity=0.3, description="goal drift",
                evidence={},
            )
        ]
        score = env.violation_score_from_episodes(episodes, tick=10)
        assert score > 0.0

    def test_structural_dag_drift_episode(self):
        from orchestration.planning_observability.drift_profiler import DriftEpisode, DriftType
        env = StabilityEnvelope()
        episodes = [
            DriftEpisode(
                drift_type=DriftType.STRUCTURAL_DAG_DRIFT,
                start_tick=10, end_tick=10,
                severity=0.5, description="dag drift",
                evidence={},
            )
        ]
        score = env.violation_score_from_episodes(episodes, tick=10)
        assert score > 0.0

    def test_coherence_collapse_triggers_collapse(self):
        from orchestration.planning_observability.drift_profiler import DriftEpisode, DriftType
        env = StabilityEnvelope()
        episodes = [
            DriftEpisode(
                drift_type=DriftType.COHERENCE_COLLAPSE,
                start_tick=10, end_tick=10,
                severity=0.25, description="coherence collapse",
                evidence={},
            )
        ]
        score = env.violation_score_from_episodes(episodes, tick=10)
        assert score == 1.0

    def test_multiple_episodes_combined(self):
        from orchestration.planning_observability.drift_profiler import DriftEpisode, DriftType
        env = StabilityEnvelope()
        episodes = [
            DriftEpisode(
                drift_type=DriftType.OSCILLATING_PLAN,
                start_tick=10, end_tick=10,
                severity=0.15, description="osc",
                evidence={},
            ),
            DriftEpisode(
                drift_type=DriftType.UNSTABLE_GOAL,
                start_tick=11, end_tick=11,
                severity=0.3, description="goal",
                evidence={},
            ),
        ]
        score = env.violation_score_from_episodes(episodes, tick=11)
        assert score > 0.0
