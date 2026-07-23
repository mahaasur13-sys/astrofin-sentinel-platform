from chaos.stress_envelope import (
    StabilityEnvelope,
    StabilityState,
)


class TestStabilityEnvelope:
    """StabilityEnvelope: health classification."""

    def test_stable_case(self):
        env = StabilityEnvelope()
        metrics = {
            "plan_stability_index": 0.9,
            "coherence_drop_rate": 0.05,
            "replanning_frequency": 0.2,
            "oscillation_index": 0.1,
        }
        report = env.evaluate(metrics)
        assert report.state == StabilityState.STABLE
        assert report.violation_score == 0.0

    def test_warning_case(self):
        env = StabilityEnvelope()
        metrics = {
            "plan_stability_index": 0.55,  # slightly below min 0.6
        }
        report = env.evaluate(metrics)
        assert report.state in (StabilityState.WARNING, StabilityState.CRITICAL)

    def test_collapse_case(self):
        env = StabilityEnvelope()
        metrics = {
            "plan_stability_index": 0.2,
            "coherence_drop_rate": 0.5,
            "oscillation_index": 0.9,
        }
        report = env.evaluate(metrics)
        assert report.state == StabilityState.COLLAPSE
        assert report.violation_score > 0.5

    def test_critical_case(self):
        env = StabilityEnvelope()
        metrics = {
            "plan_stability_index": 0.4,
            "replanning_frequency": 0.5,
        }
        report = env.evaluate(metrics)
        assert report.state in (StabilityState.CRITICAL, StabilityState.COLLAPSE)

    def test_violation_score_normalized(self):
        env = StabilityEnvelope()
        metrics = {
            "plan_stability_index": 0.5,  # 0.1 below min
            "coherence_drop_rate": 0.2,   # 0.05 above max
        }
        score = env.violation_score(metrics)
        assert score > 0
        assert score < 1.0

    def test_unknown_metrics_ignored(self):
        env = StabilityEnvelope()
        metrics = {
            "plan_stability_index": 0.9,
            "unknown_metric": 999.0,
        }
        report = env.evaluate(metrics)
        assert report.state == StabilityState.STABLE
        assert "unknown_metric" not in report.violated_metrics

    def test_violated_metrics_reported(self):
        env = StabilityEnvelope()
        metrics = {
            "plan_stability_index": 0.3,
            "coherence_drop_rate": 0.4,
        }
        report = env.evaluate(metrics)
        assert "plan_stability_index" in report.violated_metrics
        assert "coherence_drop_rate" in report.violated_metrics

    def test_boundary_exact_min_is_stable(self):
        env = StabilityEnvelope()
        metrics = {
            "plan_stability_index": 0.6,  # exactly at min
            "coherence_drop_rate": 0.0,
            "replanning_frequency": 0.0,
            "oscillation_index": 0.0,
        }
        report = env.evaluate(metrics)
        assert report.state == StabilityState.STABLE

    def test_boundary_exact_max_is_stable(self):
        env = StabilityEnvelope()
        metrics = {
            "plan_stability_index": 1.0,  # exactly at max
            "coherence_drop_rate": 0.15,
            "replanning_frequency": 0.4,
            "oscillation_index": 0.3,
        }
        report = env.evaluate(metrics)
        assert report.state == StabilityState.STABLE
