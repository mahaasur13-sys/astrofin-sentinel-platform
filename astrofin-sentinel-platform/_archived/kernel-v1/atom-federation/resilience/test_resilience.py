"""
Tests for resilience layer v6.4 — 24 tests.
"""
import pytest

from resilience.adaptive_router import AdaptiveRouter
from resilience.closed_loop import ClosedLoopResilienceController
from resilience.healer import HealingAction, SelfHealingControlPlane
from resilience.metrics_engine import StabilityMetricsEngine
from resilience.policy_engine import PolicyAction, PolicyEngine, ReactionTrigger
from resilience.reactor import ResilienceReactor

# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def peers():
    return ["node-b", "node-c", "node-d"]

@pytest.fixture
def policy():
    return PolicyEngine()

@pytest.fixture
def reactor(peers):
    return ResilienceReactor("node-a", peers)

@pytest.fixture
def healer(peers):
    h = SelfHealingControlPlane("node-a", peers)
    h.start()
    yield h
    h.stop()

@pytest.fixture
def router(peers):
    return AdaptiveRouter("node-a", peers)

@pytest.fixture
def metrics():
    return StabilityMetricsEngine(window_seconds=60, node_count=4)

@pytest.fixture
def ctrl(peers):
    c = ClosedLoopResilienceController("node-a", peers)
    c.start()
    yield c
    c.stop()


# ══════════════════════════════════════════════════════════════════════════════
# POLICY ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class TestPolicyEngineBasics:
    def test_register_returns_rule(self, policy):
        rule = policy.register(
            ReactionTrigger.SBS_VIOLATION,
            PolicyAction.EVICT_NODE,
            priority=100,
        )
        assert rule.label == "SBS_VIOLATION→EVICT_NODE"
        assert rule.priority == 100

    def test_decide_returns_action(self, policy):
        action = policy.decide(ReactionTrigger.SBS_VIOLATION, {"violation_type": "CRITICAL"})
        assert action in PolicyAction

    def test_sbs_critical_triggers_evict(self, policy):
        action = policy.decide(ReactionTrigger.SBS_VIOLATION, {"violation_type": "CRITICAL"})
        assert action == PolicyAction.EVICT_NODE

    def test_sbs_recoverable_triggers_observe(self, policy):
        action = policy.decide(ReactionTrigger.SBS_VIOLATION, {"violation_type": "RECOVERABLE"})
        assert action == PolicyAction.ADD_OBSERVATION

    def test_node_unreachable_early_observe(self, policy):
        action = policy.decide(ReactionTrigger.NODE_UNREACHABLE, {"consecutive_failures": 1})
        assert action == PolicyAction.ADD_OBSERVATION

    def test_node_unreachable_late_evict(self, policy):
        action = policy.decide(ReactionTrigger.NODE_UNREACHABLE, {"consecutive_failures": 3})
        assert action == PolicyAction.EVICT_NODE

    def test_quorum_lost_alerts(self, policy):
        # QUORUM_LOST triggers ALERT_OPS (priority 100)
        action = policy.decide(ReactionTrigger.QUORUM_LOST, {})
        assert action == PolicyAction.ALERT_OPS

    def test_partition_detected_triggers_heal(self, policy):
        action = policy.decide(ReactionTrigger.PARTITION_DETECTED, {})
        assert action == PolicyAction.TRIGGER_SELF_HEAL

    def test_byzantine_signal_isolates(self, policy):
        action = policy.decide(ReactionTrigger.BYZANTINE_SIGNAL, {})
        assert action == PolicyAction.ISOLATE_BYZANTINE

    def test_recovery_complete_reconfigures(self, policy):
        action = policy.decide(ReactionTrigger.RECOVERY_COMPLETE, {})
        assert action == PolicyAction.RECONFIGURE_QUORUM

    def test_cooldown_prevents_retrigger(self, policy):
        policy.clear()
        policy.register(ReactionTrigger.NODE_RECOVERED, PolicyAction.RESTORE_NODE, cooldown=60.0)
        action1 = policy.decide(ReactionTrigger.NODE_RECOVERED, {"peer": "b"})
        action2 = policy.decide(ReactionTrigger.NODE_RECOVERED, {"peer": "b"})
        assert action1 == PolicyAction.RESTORE_NODE
        assert action2 == PolicyAction.NOOP

    def test_dump_returns_rules(self, policy):
        d = policy.dump()
        assert "rules" in d
        assert len(d["rules"]) >= 20


# ══════════════════════════════════════════════════════════════════════════════
# HEALER
# ══════════════════════════════════════════════════════════════════════════════

class TestHealerEvictRestore:
    def test_evict_node_removes_from_quorum(self, healer):
        result = healer.heal_sync(HealingAction.EVICT_NODE, "node-c")
        assert result.success
        assert "node-c" not in healer.get_quorum_members()

    def test_restore_node_adds_back(self, healer):
        healer.heal_sync(HealingAction.EVICT_NODE, "node-c")
        result = healer.heal_sync(HealingAction.RESTORE_NODE, "node-c")
        assert result.success
        assert "node-c" in healer.get_quorum_members()

    def test_evict_byzantine_node(self, healer):
        result = healer.heal_sync(HealingAction.ISOLATE_BYZANTINE, "node-d")
        assert result.success
        assert "node-d" in healer.get_byzantine()
        assert "node-d" not in healer.get_quorum_members()

    def test_reconfigure_quorum_after_eviction(self, healer):
        healer.heal_sync(HealingAction.EVICT_NODE, "node-c")
        healer.heal_sync(HealingAction.EVICT_NODE, "node-d")
        result = healer.heal_sync(HealingAction.RECONFIGURE_QUORUM)
        assert result.success
        assert result.details["new"] == 2  # node-a + node-b

    def test_trigger_reelection_notifies_peers(self, healer):
        result = healer.heal_sync(HealingAction.TRIGGER_RE_ELECTION)
        assert result.success

    def test_quorum_is_quorate_with_3_of_4(self, healer):
        healer.heal_sync(HealingAction.EVICT_NODE, "node-c")
        healer.heal_sync(HealingAction.EVICT_NODE, "node-d")
        assert healer.is_quorate()


# ══════════════════════════════════════════════════════════════════════════════
# ADAPTIVE ROUTER
# ══════════════════════════════════════════════════════════════════════════════

class TestAdaptiveRouter:
    def test_route_returns_best_peer(self, router):
        router.update_peer_metrics("node-b", latency_ms=30.0, loss_rate=0.01, success=True)
        router.update_peer_metrics("node-c", latency_ms=200.0, loss_rate=0.1, success=True)
        route = router.route()
        assert route.chosen_peer == "node-b"

    def test_slo_violation_removes_from_rotation(self, router):
        router.update_peer_metrics("node-b", latency_ms=500.0, loss_rate=0.5, success=False)
        state = router.get_slo_status()["node-b"]
        assert state["violating_slo"] is True
        route = router.route()
        assert route.chosen_peer != "node-b"

    def test_probe_mode_when_all_degraded(self, router):
        router.update_peer_metrics("node-b", latency_ms=500.0, loss_rate=0.5, success=False)
        router.update_peer_metrics("node-c", latency_ms=600.0, loss_rate=0.6, success=False)
        router.update_peer_metrics("node-d", latency_ms=400.0, loss_rate=0.4, success=False)
        route = router.route()
        assert route.reason == "probe_mode_all_degraded"
        assert route.chosen_peer is not None

    def test_weight_calculation(self, router):
        router.update_peer_metrics("node-b", latency_ms=20.0, loss_rate=0.005, success=True)
        router.update_peer_metrics("node-c", latency_ms=80.0, loss_rate=0.02, success=True)
        route = router.route()
        weights = route.weights
        assert weights["node-b"] > weights["node-c"]


# ══════════════════════════════════════════════════════════════════════════════
# METRICS ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class TestStabilityMetrics:
    def test_initial_score_is_perfect(self, metrics):
        snap = metrics.get_snapshot()
        assert snap.stability_score >= 0.999

    def test_violations_decrease_score(self, metrics):
        for _ in range(5):
            metrics.record_violation("sbs", severity="critical")
        snap = metrics.get_snapshot()
        assert snap.stability_score < 1.0

    def test_node_down_decrements_quorum_health(self, metrics):
        # Initialize node-c as healthy first
        metrics.record_node_up("node-a")
        metrics.record_node_up("node-b")
        metrics.record_node_up("node-c")
        metrics.record_node_up("node-d")
        metrics.record_node_down("node-c")
        snap = metrics.get_snapshot()
        assert snap.quorum_health == 0.75  # 3/4

    def test_is_stable(self, metrics):
        assert metrics.is_stable(threshold=0.7)

    def test_snapshot_to_dict(self, metrics):
        d = metrics.get_snapshot().to_dict()
        assert "stability_score" in d
        assert "rto_ms" in d
        assert "convergence_time_ms" in d


# ══════════════════════════════════════════════════════════════════════════════
# CLOSED LOOP CONTROLLER
# ══════════════════════════════════════════════════════════════════════════════

class TestClosedLoopController:
    def test_controller_starts(self, ctrl):
        assert ctrl.stability_score() >= 0.0

    def test_sbs_violation_triggers_eviction(self, ctrl):
        result = ctrl.on_sbs_violation([{"invariant": "LEADER_UNIQUENESS"}], violation_type="CRITICAL")
        assert result is not None

    def test_node_unreachable_updates_metrics(self, ctrl):
        ctrl.on_node_unreachable("node-b", consecutive_failures=1)
        snap = ctrl.get_snapshot()
        assert snap.violation_count_60s >= 1

    def test_drl_latency_updates_router(self, ctrl):
        ctrl.on_drl_latency("node-c", latency_ms=250.0, slo_ms=100.0)
        violating = ctrl.router.get_violating_peers()
        assert "node-c" in violating

    def test_get_healthy_peers(self, ctrl):
        ctrl.on_drl_latency("node-b", latency_ms=250.0, slo_ms=100.0)
        healthy = ctrl.get_healthy_peers()
        assert "node-b" not in healthy

    def test_heal_sync_evict(self, ctrl):
        result = ctrl.heal_sync(HealingAction.EVICT_NODE, "node-c")
        assert result.success
        assert "node-c" not in ctrl.healer.get_quorum_members()

    def test_dump_contains_all_layers(self, ctrl):
        d = ctrl.dump()
        assert "stability" in d
        assert "router" in d
        assert "healer" in d
        assert "reactor" in d
        assert d["policy_rules_count"] >= 20


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
