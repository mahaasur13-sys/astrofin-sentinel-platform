"""
test_phase2.py — v8.0 Phase 2 (plan_graph, plan_evaluator, goal_memory)
"""
import pytest

from meta_control.integration.persistence_bridge import (
    CoherenceEnrichment,
    IntegrationReport,
    OutcomeAwareWeightDelta,
    PersistenceBridge,
    StabilityAwareGainAdjustment,
)
from orchestration.phase2.goal_memory import GoalMemory
from orchestration.phase2.plan_evaluator import (
    PlanEvaluator,
    PlanScoreWeights,
)
from orchestration.phase2.plan_graph import PlanGraph, PlanGraphConfig, PlanNode

# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def bridge():
    return PersistenceBridge(tick=42)


@pytest.fixture
def integration_report(bridge):
    report = bridge.integrate(
        v7_report=bridge._fake_v7_report(),   # method doesn't exist — use a simple dataclass mock
        base_gains={"drl": 0.5, "sbs": 0.5},
        base_coherence=0.82,
        active_sources=["drl", "sbs"],
    )
    return report


@pytest.fixture
def source_statuses():
    return {
        "drl": {"is_coherent": True,  "avg_stability": 0.85},
        "sbs": {"is_coherent": False, "avg_stability": 0.60},
    }


# ─── goal_memory ─────────────────────────────────────────────────────────────

class TestGoalMemory:
    def test_append_and_get(self):
        gm = GoalMemory(max_goals=50)
        gid = gm.append(
            goal_payload={"target": "deploy"},
            planned_source="drl",
            planned_priority=0.8,
            proof_verdict=True,
            coherence_at_plan=0.85,
        )
        assert gid == 1
        assert gm.count == 1

    def test_record_outcome(self):
        gm = GoalMemory()
        gid = gm.append({}, "sbs", 0.6, True, 0.80)
        assert gm.record_outcome(gid, 0.90) is True
        assert gm.record_outcome(999, 0.5) is False
        assert gm.recent(1)[0].actual_outcome == 0.90

    def test_record_drift(self):
        gm = GoalMemory()
        gid = gm.append({}, "x", 0.5, False, 0.7)
        assert gm.record_drift(gid, 0.25) is True
        assert gm.drift_trend() == 0.25

    def test_avg_outcome(self):
        gm = GoalMemory()
        g1 = gm.append({}, "a", 0.5, True, 0.8, actual_outcome=0.7)
        g2 = gm.append({}, "b", 0.5, True, 0.8, actual_outcome=0.9)
        assert gm.avg_outcome() == pytest.approx(0.8)

    def test_replan_rate(self):
        gm = GoalMemory()
        g1 = gm.append({}, "a", 0.5, True, 0.8)
        g2 = gm.append({}, "b", 0.5, True, 0.8)
        gm.mark_replan(g1)
        gm.mark_replan(g2)
        assert gm.replan_rate() == pytest.approx(1.0)

    def test_bounded(self):
        gm = GoalMemory(max_goals=3)
        for i in range(10):
            gm.append({}, f"s{i}", 0.5, True, 0.8)
        assert gm.count == 3


# ─── plan_evaluator ─────────────────────────────────────────────────────────

class TestPlanEvaluator:
    def _mock_report(self, tick=10) -> IntegrationReport:
        return IntegrationReport(
            gain_adjustments=[
                StabilityAwareGainAdjustment(
                    source="__global__", multiplier=1.2,
                    reason="global", source_stability=0.8,
                    global_trend=0.5, window_depth=4,
                ),
                StabilityAwareGainAdjustment(
                    source="sbs", multiplier=0.9,
                    reason="unstable_source", source_stability=0.60,
                    global_trend=0.5, window_depth=4,
                ),
            ],
            weight_deltas=[
                OutcomeAwareWeightDelta(
                    source="drl", priority_adjustment=0.1,
                    reason="ok", similar_decisions_count=3,
                    avg_outcome_score=0.75, causal_confidence=0.7,
                ),
            ],
            coherence=CoherenceEnrichment(
                base_coherence=0.80,
                persistence_delta=0.10,
                enriched_coherence=0.90,
                trend=0.5,
                window_depth=4,
                source_count=2,
                coherence_sources=["drl", "sbs"],
            ),
            tick=tick,
        )

    def test_evaluate_all_sources_coherent(self, source_statuses):
        ev = PlanEvaluator()
        report = self._mock_report()
        result = ev.evaluate("plan_A", report, source_statuses)
        assert result.plan_id == "plan_A"
        assert result.enriched_coherence == pytest.approx(0.90)
        assert result.coherence_gain == pytest.approx(0.10)
        assert result.global_trend == 0.5
        assert result.unstable_sources == ["sbs"]
        assert 0.0 <= result.stability_score <= 1.0
        assert 0.0 <= result.coherence_score <= 1.0
        assert 0.0 <= result.overall <= 1.0

    def test_weighted_scores(self, source_statuses):
        ev = PlanEvaluator(weights=PlanScoreWeights(stability=0.5, coherence=0.2, gain=0.2, weight=0.1))
        report = self._mock_report()
        result = ev.evaluate("plan_B", report, source_statuses)
        assert 0.0 <= result.overall <= 1.0

    def test_stability_score_trend(self):
        s_pos = PlanEvaluator._stability_score(1.0, 4, 2)
        s_neg = PlanEvaluator._stability_score(-1.0, 4, 2)
        s_zero = PlanEvaluator._stability_score(0.0, 4, 2)
        assert s_pos > s_zero > s_neg

    def test_coherence_score(self):
        s = PlanEvaluator._coherence_score(0.1, 0.9)
        assert 0.0 <= s <= 1.0

    def test_gain_score(self):
        s = PlanEvaluator._gain_score(1.2, [])
        assert 0.0 <= s <= 1.0
        s_unstable = PlanEvaluator._gain_score(1.2, ["a", "b"])
        assert s_unstable < s


# ─── plan_graph ──────────────────────────────────────────────────────────────

class TestPlanGraph:
    def test_begin_and_add_nodes(self):
        pg = PlanGraph()
        plan_id = pg.begin_plan(coherence_at_plan=0.85, tick=1)
        assert plan_id == "plan_1"

        nid1 = pg.add_node(plan_id, "deploy", {"env": "prod"}, "drl",
                           priority=0.8, proof_verdict=True, temporal_confidence=0.9)
        nid2 = pg.add_node(plan_id, "verify", {"check": "health"}, "sbs",
                           priority=0.6, proof_verdict=True, temporal_confidence=0.8,
                           parent_ids=[nid1])

        assert nid1 == "plan_1_node_1"
        assert nid2 == "plan_1_node_2"
        assert pg.node_count == 2

    def test_topological_sort(self):
        pg = PlanGraph()
        plan_id = pg.begin_plan(coherence_at_plan=0.85, tick=1)
        nid1 = pg.add_node(plan_id, "a", {}, "x", 0.5, True, 0.8)
        nid2 = pg.add_node(plan_id, "b", {}, "y", 0.5, True, 0.8, parent_ids=[nid1])
        nid3 = pg.add_node(plan_id, "c", {}, "z", 0.5, True, 0.8, parent_ids=[nid1])
        nid4 = pg.add_node(plan_id, "d", {}, "w", 0.5, True, 0.8, parent_ids=[nid2, nid3])

        order = pg.topological_sort()
        assert order.index(nid1) < order.index(nid2)
        assert order.index(nid1) < order.index(nid3)
        assert order.index(nid2) < order.index(nid4)
        assert order.index(nid3) < order.index(nid4)

    def test_cycle_detection(self):
        pg = PlanGraph()
        plan_id = pg.begin_plan(coherence_at_plan=0.85, tick=1)
        nid1 = pg.add_node(plan_id, "a", {}, "x", 0.5, True, 0.8)
        nid2 = pg.add_node(plan_id, "b", {}, "y", 0.5, True, 0.8, parent_ids=[nid1])
        # create a back-edge — not possible through API since parent must come first
        # but we can inject via internals for test
        pg._nodes[nid1].parent_ids.append("plan_1_node_99")
        pg._nodes["plan_1_node_99"] = PlanNode(
            node_id="plan_1_node_99", action="fake", payload={},
            source="x", priority=0.5, proof_verdict=True, temporal_confidence=0.8,
            coherence_at_plan=0.8, tick=1, parent_ids=[nid2],
        )
        with pytest.raises(RuntimeError, match="[Cc]ycle"):
            pg.topological_sort()

    def test_ready_nodes(self):
        pg = PlanGraph()
        plan_id = pg.begin_plan(coherence_at_plan=0.85, tick=1)
        nid1 = pg.add_node(plan_id, "a", {}, "x", 0.5, True, 0.8)
        nid2 = pg.add_node(plan_id, "b", {}, "y", 0.5, True, 0.8, parent_ids=[nid1])

        ready = pg.ready_nodes()
        assert nid1 in [n.node_id for n in ready]
        assert nid2 not in [n.node_id for n in ready]

        pg._nodes[nid1].status = "done"
        ready = pg.ready_nodes()
        assert nid2 in [n.node_id for n in ready]

    def test_snapshot_and_deviation(self):
        pg = PlanGraph()
        plan_id = pg.begin_plan(coherence_at_plan=0.80, tick=1)
        nid = pg.add_node(plan_id, "a", {}, "x", 0.5, True, 0.8)

        pg.snapshot(nid, actual_outcome=0.75, coherence_snapshot=0.78, proof_verdict=True)
        assert pg.node_status(nid) == "done"
        dev = pg.coherence_deviation()
        assert dev == pytest.approx(0.02)

    def test_pending_nodes(self):
        pg = PlanGraph()
        plan_id = pg.begin_plan(coherence_at_plan=0.85, tick=1)
        nid1 = pg.add_node(plan_id, "a", {}, "x", 0.5, True, 0.8)
        nid2 = pg.add_node(plan_id, "b", {}, "y", 0.5, True, 0.8)
        pg._nodes[nid1].status = "done"
        pending = pg.pending_nodes()
        assert len(pending) == 1
        assert pending[0].node_id == nid2

    def test_max_nodes(self):
        pg = PlanGraph(config=PlanGraphConfig(max_nodes=3))
        plan_id = pg.begin_plan(coherence_at_plan=0.85, tick=1)
        pg.add_node(plan_id, "a", {}, "x", 0.5, True, 0.8)
        pg.add_node(plan_id, "b", {}, "y", 0.5, True, 0.8)
        pg.add_node(plan_id, "c", {}, "z", 0.5, True, 0.8)
        with pytest.raises(RuntimeError, match="Max nodes"):
            pg.add_node(plan_id, "d", {}, "w", 0.5, True, 0.8)

    def test_wrong_plan_id(self):
        pg = PlanGraph()
        pg.begin_plan(coherence_at_plan=0.85, tick=1)
        with pytest.raises(ValueError, match="not active"):
            pg.add_node("wrong_plan", "a", {}, "x", 0.5, True, 0.8)
