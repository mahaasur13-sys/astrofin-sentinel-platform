"""test_observability.py — planning_observability layer tests.
All 30 tests for trace logger, evaluation metrics, and drift profiler.
"""
from orchestration.planning_observability import (
    DriftProfiler,
    DriftType,
    EvaluationMetrics,
    EvaluationMetricsCollector,
    PlanTraceLogger,
    TraceEventType,
)


class TestPlanTraceLogger:
    """PlanTraceLogger: event recording and query."""

    def test_log_node_added_increments_count(self):
        logger = PlanTraceLogger()
        logger.log_node_added(1, "p1", "n1", "do_x", 0.9, True)
        assert logger.total_nodes == 1

    def test_log_node_completed_records_event(self):
        logger = PlanTraceLogger()
        logger.log_node_completed(1, "p1", "n1", 0.85)
        events = logger.recent_events()
        assert len(events) == 1
        assert events[0].event_type == TraceEventType.NODE_COMPLETED

    def test_log_plan_created_increments_plan_count(self):
        logger = PlanTraceLogger()
        logger.log_plan_created(1, "p1", ["n1", "n2"])
        assert logger.total_plans == 1

    def test_log_eval_score_records_score_point(self):
        logger = PlanTraceLogger()
        logger.log_eval_score(1, "p1", 0.8, 0.7, 0.6, 0.5, 0.65)
        trajectory = logger.score_trajectory("p1")
        assert len(trajectory) == 1
        assert trajectory[0].overall == 0.65

    def test_score_trajectory_filters_by_plan(self):
        logger = PlanTraceLogger()
        logger.log_eval_score(1, "p1", 0.8, 0.7, 0.6, 0.5, 0.65)
        logger.log_eval_score(2, "p2", 0.8, 0.7, 0.6, 0.5, 0.65)
        assert len(logger.score_trajectory("p1")) == 1
        assert len(logger.score_trajectory("p2")) == 1

    def test_log_cycle_detected_and_broken(self):
        logger = PlanTraceLogger()
        logger.log_cycle_detected(1, "p1", ["n1", "n2", "n3"])
        logger.log_cycle_broken(2, "p1", ["n1", "n2", "n3"], "edge_removal")
        cycles = logger.cycle_summary()
        assert len(cycles) == 1
        assert cycles[0].broken_via == "edge_removal"

    def test_log_replan_triggered_records(self):
        logger = PlanTraceLogger()
        logger.log_replan_triggered(1, "p1", "coherence_drop", 0.75, 0.80, 3)
        replans = logger.replan_summary()
        assert len(replans) == 1
        assert replans[0].trigger_reason == "coherence_drop"
        assert logger.total_replans == 1

    def test_trace_completeness_full(self):
        logger = PlanTraceLogger()
        logger.log_plan_created(1, "p1", ["n1"])
        logger.log_eval_score(2, "p1", 0.8, 0.7, 0.6, 0.5, 0.65)
        assert logger.trace_completeness() == 1.0

    def test_trace_completeness_partial(self):
        logger = PlanTraceLogger()
        logger.log_plan_created(1, "p1", ["n1"])
        logger.log_plan_created(2, "p2", ["n2"])
        logger.log_eval_score(3, "p1", 0.8, 0.7, 0.6, 0.5, 0.65)
        assert logger.trace_completeness() == 0.5

    def test_to_dict_returns_stats(self):
        logger = PlanTraceLogger()
        logger.log_node_added(1, "p1", "n1", "do_x", 0.9, True)
        logger.log_plan_created(1, "p1", ["n1"])
        d = logger.to_dict()
        assert d["total_nodes"] == 1
        assert d["total_plans"] == 1


class TestEvaluationMetricsCollector:
    """EvaluationMetricsCollector: metrics computation."""

    def test_plan_stability_index_stable(self):
        scores = [0.800, 0.801, 0.800, 0.799, 0.800]
        psi = EvaluationMetricsCollector.plan_stability_index(scores)
        assert 0.60 < psi < 1.0

    def test_plan_stability_index_chaotic(self):
        scores = [0.10, 0.95, 0.10, 0.95, 0.10]
        psi = EvaluationMetricsCollector.plan_stability_index(scores)
        assert 0.40 < psi < 0.70

    def test_plan_stability_index_single_point(self):
        psi = EvaluationMetricsCollector.plan_stability_index([0.80])
        assert psi == 1.0

    def test_replanning_frequency(self):
        freq = EvaluationMetricsCollector.replanning_frequency(5, 10)
        assert freq == 0.5

    def test_replanning_frequency_zero_plans(self):
        freq = EvaluationMetricsCollector.replanning_frequency(0, 0)
        assert freq == 0.0

    def test_coherence_drop_rate(self):
        traj = [0.80, 0.74, 0.68, 0.66, 0.60]
        rate = EvaluationMetricsCollector.coherence_drop_rate(traj, 0.05)
        assert rate > 0

    def test_coherence_recovery_rate(self):
        traj = [0.60, 0.64, 0.68, 0.72, 0.76]
        rate = EvaluationMetricsCollector.coherence_recovery_rate(traj, 0.03)
        assert rate > 0

    def test_dag_complexity(self):
        comp = EvaluationMetricsCollector.dag_complexity(20, 4)
        assert comp == 5.0

    def test_dag_growth_rate_expanding(self):
        counts = [5, 7, 10, 14, 19]
        rate = EvaluationMetricsCollector.dag_growth_rate(counts)
        assert rate > 0

    def test_planning_health_score_composite(self):
        metrics = EvaluationMetrics(
            tick=10,
            plan_stability_index=0.95,
            evaluation_entropy=0.5,
            coherence_entropy=0.5,
            replanning_frequency=0.2,
            replanning_burst_ratio=0.1,
            coherence_drop_rate=0.05,
            coherence_recovery_rate=0.1,
            dag_complexity=5.0,
            dag_branching_factor=1.5,
            dag_depth=4,
            dag_growth_rate=0.5,
            score_trend=0.01,
        )
        health = EvaluationMetricsCollector.planning_health_score(metrics)
        assert 0.0 <= health <= 1.0
        assert health > 0.8


class TestDriftProfiler:
    """DriftProfiler: degradation detection."""

    def test_oscillation_detected_oscillating(self):
        profiler = DriftProfiler(
            oscillation_window=10,
            coherence_drop_threshold=0.105,
        )
        coherence = [0.75, 0.90, 0.75, 0.90, 0.75, 0.75]
        profile = profiler.detect_oscillation(coherence, 5, 10, "p1")
        assert profile.is_oscillating
        assert profile.oscillation_frequency == 1.0
        assert abs(profile.avg_coherence_delta) == 0.0

    def test_oscillation_not_detected_stable(self):
        profiler = DriftProfiler()
        coherence = [0.80, 0.81, 0.82, 0.83, 0.84]
        profile = profiler.detect_oscillation(coherence, 2, 10, "p1")
        assert not profile.is_oscillating

    def test_oscillation_insufficient_data(self):
        profiler = DriftProfiler()
        profile = profiler.detect_oscillation([0.80], 1, 10, "p1")
        assert not profile.is_oscillating

    def test_goal_drift_detected(self):
        profiler = DriftProfiler(coherence_drop_threshold=0.03)
        coherence_at_replans = [0.90, 0.80, 0.70, 0.60, 0.50]
        profile = profiler.detect_goal_drift(coherence_at_replans, 20, "p1", goal_drift_threshold=0.03)
        assert profile.is_drift_detected
        assert profile.drift_magnitude > 0

    def test_goal_drift_not_detected_stable(self):
        profiler = DriftProfiler()
        coherence_at_replans = [0.80, 0.81, 0.80, 0.81, 0.80]
        profile = profiler.detect_goal_drift(coherence_at_replans, 20, "p1")
        assert not profile.is_drift_detected

    def test_weight_instability_detected(self):
        profiler = DriftProfiler()
        adjustments = [0.01, 0.02, 0.05, 0.10, 0.20, 0.35]
        profile = profiler.detect_weight_instability(adjustments)
        assert profile.is_weight_instability_detected
        assert profile.weight_adjustment_variance > 0

    def test_weight_instability_not_detected(self):
        profiler = DriftProfiler()
        adjustments = [0.05, 0.05, 0.05, 0.05, 0.05]
        profile = profiler.detect_weight_instability(adjustments)
        assert not profile.is_weight_instability_detected

    def test_dag_drift_detected_on_node_change(self):
        profiler = DriftProfiler(dag_snapshot_interval=1)
        profiler.record_dag_snapshot(
            [{"node_id": "n1"}, {"node_id": "n2"}], 5
        )
        profiler.record_dag_snapshot(
            [{"node_id": "n1"}, {"node_id": "n2"}], 10
        )
        current = [
            {"node_id": "n1"}, {"node_id": "n3"}, {"node_id": "n4"},
            {"node_id": "n5"}, {"node_id": "n6"}, {"node_id": "n7"},
        ]
        profile = profiler.detect_dag_drift(current)
        assert profile.is_drift_detected
        assert profile.structural_similarity < 0.60

    def test_dag_drift_not_detected_similar(self):
        profiler = DriftProfiler(
            dag_snapshot_interval=1,
            structural_similarity_threshold=0.50,
        )
        profiler.record_dag_snapshot(
            [{"node_id": "n1"}, {"node_id": "n2"}], 5
        )
        profiler.record_dag_snapshot(
            [{"node_id": "n1"}, {"node_id": "n2"}], 10
        )
        current = [{"node_id": "n1"}, {"node_id": "n2"}, {"node_id": "n3"}]
        profile = profiler.detect_dag_drift(current)
        assert not profile.is_drift_detected

    def test_full_scan_returns_episodes(self):
        profiler = DriftProfiler(
            oscillation_window=10,
            drift_window=20,
            weight_window=30,
            dag_snapshot_interval=1,
            coherence_drop_threshold=0.12,
        )
        profiler.goal_drift_threshold = 0.095
        coherence = [0.70, 0.90, 0.70, 0.90, 0.70, 0.90]
        coherence_at_replans = [0.90, 0.80, 0.70, 0.60, 0.50, 0.40]
        weight_adjustments = [0.01, 0.02, 0.05, 0.10, 0.20, 0.35]
        current_nodes = [{"node_id": f"n{i}"} for i in range(1, 8)]

        profiler.record_dag_snapshot(
            [{"node_id": "n1"}, {"node_id": "n3"}], 5
        )
        profiler.record_dag_snapshot(
            [{"node_id": "n1"}, {"node_id": "n3"}], 10
        )

        episodes = profiler.scan(
            tick=20,
            plan_id="p1",
            coherence_trajectory=coherence,
            replan_count=6,
            coherence_at_replans=coherence_at_replans,
            weight_adjustments=weight_adjustments,
            current_nodes=current_nodes,
        )

        drift_types = {e.drift_type for e in episodes}
        assert DriftType.OSCILLATING_PLAN in drift_types
        assert DriftType.UNSTABLE_GOAL in drift_types
        assert DriftType.UNSTABLE_WEIGHTS in drift_types
        assert DriftType.STRUCTURAL_DAG_DRIFT in drift_types

    def test_full_scan_empty_when_healthy(self):
        profiler = DriftProfiler()
        coherence = [0.80, 0.81, 0.82, 0.83]
        coherence_at_replans = [0.80, 0.81, 0.80, 0.81]
        weight_adjustments = [0.05, 0.05, 0.05, 0.05]
        current_nodes = [{"node_id": "n1"}, {"node_id": "n2"}]

        episodes = profiler.scan(
            tick=10,
            plan_id="p1",
            coherence_trajectory=coherence,
            replan_count=1,
            coherence_at_replans=coherence_at_replans,
            weight_adjustments=weight_adjustments,
            current_nodes=current_nodes,
        )
        assert len(episodes) == 0
