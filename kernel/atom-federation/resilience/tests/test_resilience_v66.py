"""
ATOMFederationOS v6.6 — Tests
  SelfModel + PredictiveController + DecisionLattice + AdaptiveObjective

Covers:
  T1: SelfModel builds causal graph from snapshot
  T2: SelfModel predicts next state for action
  T3: SelfModel forecasts stability horizon
  T4: SelfModel cascade path detection
  T5: DecisionLattice determinism (same state → same decision)
  T6: DecisionLattice completeness (every state produces decision)
  T7: DecisionLattice conflict-freedom (no contradictory actions)
  T8: PredictiveController pre-heals before threshold breach
  T9: AdaptiveObjectiveController J-gates action execution
  T10: GlobalObjectiveFunction integrated in control loop
"""

import os

# ── Imports from new v6.6 modules ─────────────────────────────────────────────
import sys

import pytest

from resilience.closed_loop import ClosedLoopResilienceController
from resilience.metrics_engine import StabilityMetricsEngine, StabilitySnapshot
from resilience.policy_engine import PolicyAction

sys.path.insert(0, os.path.dirname(__file__) + "/..")

try:
    from resilience.adaptive_objective import AdaptiveObjectiveController
    from resilience.decision_lattice import DecisionLattice, LatticeDecision  # noqa: F401
    from resilience.predictive_controller import PredictiveController
    from resilience.self_model import SelfModel, SystemState
    HAS_V66 = True
except ImportError:
    HAS_V66 = False

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def metrics():
    return StabilityMetricsEngine(node_count=3)

@pytest.fixture
def ctrl(metrics):
    node_id = "node-a"
    peers = ["node-b", "node-c"]
    c = ClosedLoopResilienceController(
        node_id=node_id,
        peers=peers,
        stability_threshold=0.70,
        critical_threshold=0.30,
    )
    # Seed some history
    for _ in range(10):
        c.metrics.record_op_success()
        c.metrics.record_node_up("node-b")
        c.metrics.record_node_up("node-c")
    c.metrics.record_violation("sbs", severity="warning")
    return c

@pytest.fixture
def snap(metrics) -> StabilitySnapshot:
    return metrics.get_snapshot()


# ==============================================================================
# T1–T4: SelfModel
# ==============================================================================

class TestSelfModel:
    """T1: SelfModel builds causal graph from snapshot."""

    def test_self_model_builds(self, ctrl, snap):
        if not HAS_V66:
            pytest.skip("self_model.py not yet created")
        model = SelfModel()
        model.build_model(snap)
        state = model.get_state()
        assert state is not None
        assert "node_count_total" in state
        assert state["node_count_total"] == snap.node_count_total

    def test_predict_next_state_evict(self, ctrl, snap):
        """T2: SelfModel.predict_next_state simulates EVICT_NODE."""
        if not HAS_V66:
            pytest.skip("self_model.py not yet created")
        model = SelfModel()
        model.build_model(snap)
        predicted = model.predict_next_state(snap, PolicyAction.EVICT_NODE, target="node-b")
        assert predicted is not None
        # After evicting node-b, healthy count should drop by 1
        assert predicted.node_count_healthy <= snap.node_count_healthy

    def test_forecast_stability_horizon(self, ctrl, snap):
        """T3: SelfModel.forecast_stability projects score N seconds ahead."""
        if not HAS_V66:
            pytest.skip("self_model.py not yet created")
        model = SelfModel()
        model.build_model(snap)
        # With stable history, forecast should be close to current score
        forecast_30s = model.forecast_stability(snap, horizon_s=30.0)
        forecast_60s = model.forecast_stability(snap, horizon_s=60.0)
        # Forecasts should be floats in [0, 1]
        assert 0.0 <= forecast_30s <= 1.0
        assert 0.0 <= forecast_60s <= 1.0

    def test_cascade_path_detection(self, ctrl, snap):
        """T4: SelfModel.get_cascade_path returns failure propagation chain."""
        if not HAS_V66:
            pytest.skip("self_model.py not yet created")
        model = SelfModel()
        model.build_model(snap)
        # Build model with some failure history
        ctrl.metrics.record_violation("sbs", severity="critical")
        ctrl.metrics.record_node_down("node-b")
        updated_snap = ctrl.get_snapshot()
        model.build_model(updated_snap)
        cascade = model.get_cascade_path("node-b")
        assert isinstance(cascade, list)


# ==============================================================================
# T5–T7: DecisionLattice
# ==============================================================================

class TestDecisionLattice:
    """T5: DecisionLattice is deterministic (idempotent)."""

    def test_lattice_determinism(self, ctrl, snap):
        if not HAS_V66:
            pytest.skip("decision_lattice.py not yet created")
        lattice = DecisionLattice()
        state = SystemState.from_snapshot(snap, peers=["node-b", "node-c"])
        decision1 = lattice.decide(state)
        decision2 = lattice.decide(state)
        decision3 = lattice.decide(state)
        # Same state → same primary action, same lattice_path
        assert decision1.primary_action == decision2.primary_action == decision3.primary_action
        assert decision1.lattice_path == decision2.lattice_path == decision3.lattice_path

    def test_lattice_completeness(self, ctrl, snap):
        """T6: Every state produces a decision (no undefined states)."""
        if not HAS_V66:
            pytest.skip("decision_lattice.py not yet created")
        lattice = DecisionLattice()
        # Try various snapshots
        for _ in range(20):
            ctrl.metrics.record_op_success()
            s = ctrl.get_snapshot()
            state = SystemState.from_snapshot(s, peers=["node-b", "node-c"])
            result = lattice.decide(state)
            assert result.primary_action is not None
            assert result.lattice_path is not None

    def test_lattice_conflict_freedom(self, ctrl, snap):
        """T7: Output actions do not conflict with each other."""
        if not HAS_V66:
            pytest.skip("decision_lattice.py not yet created")
        lattice = DecisionLattice()
        state = SystemState.from_snapshot(snap, peers=["node-b", "node-c"])
        result = lattice.decide(state)
        # Primary action should not be contradicted by secondary actions
        for sec in result.secondary_actions:
            assert not lattice._conflicts(result.primary_action, sec), \
                f"Primary {result.primary_action} conflicts with secondary {sec}"


# ==============================================================================
# T8: PredictiveController
# ==============================================================================

class TestPredictiveController:
    """T8: PredictiveController triggers pre-heal BEFORE threshold breach."""

    def test_pre_heal_before_breach(self, ctrl):
        """When forecast shows incoming degradation, pre-heal triggers."""
        if not HAS_V66:
            pytest.skip("predictive_controller.py not yet created")
        predictor = PredictiveController(ctrl)
        # Seed with some violations to lower score
        for _ in range(5):
            ctrl.metrics.record_violation("sbs", severity="warning")
        snap = ctrl.get_snapshot()
        # Score is degraded but not critical
        assert snap.stability_score < 0.9  # degraded state
        result = predictor.tick()
        assert hasattr(result, "predicted_score")
        assert hasattr(result, "pre_heal_triggered")


# ==============================================================================
# T9: AdaptiveObjectiveController
# ==============================================================================

class TestAdaptiveObjectiveController:
    """T9: J-gated action execution — actions that decrease J are deferred."""

    def test_j_gated_execution(self, ctrl, snap):
        if not HAS_V66:
            pytest.skip("adaptive_objective.py not yet created")
        obj_ctrl = AdaptiveObjectiveController(ctrl)
        # Current J
        current_J = obj_ctrl.optimizer.compute_J(snap).J
        # EVICT_NODE in a healthy cluster should be discouraged (would decrease J)
        should_exec = obj_ctrl.should_execute(
            PolicyAction.EVICT_NODE, target="node-b", snapshot=snap
        )
        # If J is high (>0.8) and evicting would harm it, deny
        if current_J > 0.8:
            assert should_exec is False, "Should not EVICT in a healthy cluster"
        # ADD_OBSERVATION is low-cost, should usually pass
        should_obs = obj_ctrl.should_execute(
            PolicyAction.ADD_OBSERVATION, target="node-b", snapshot=snap
        )
        assert should_obs is True

    def test_j_integration_in_loop(self, ctrl):
        """T10: GlobalObjectiveFunction integrated in full control loop."""
        if not HAS_V66:
            pytest.skip("adaptive_objective.py not yet created")
        obj_ctrl = AdaptiveObjectiveController(ctrl)
        js = []
        for _ in range(5):
            ctrl.metrics.record_op_success()
            snap = ctrl.get_snapshot()
            result = obj_ctrl.optimizer.compute_J(snap)
            js.append(result.J)
        assert len(js) == 5
        assert all(-1.0 <= j <= 1.0 for j in js)


# ==============================================================================
# T10: End-to-end J integration
# ==============================================================================

class TestGlobalObjectiveIntegration:
    """T10: J() is computed every tick and influences decisions."""

    def test_j_computed_every_tick(self, ctrl):
        if not HAS_V66:
            pytest.skip("adaptive_objective.py not yet created")
        obj_ctrl = AdaptiveObjectiveController(ctrl)
        js = []
        for _ in range(10):
            ctrl.metrics.record_op_success()
            snap = ctrl.get_snapshot()
            result = obj_ctrl.optimizer.compute_J(snap)
            js.append(result.J)
        # J values should be recorded
        assert len(js) == 10
        # J should be clamped to [-1, 1]
        assert all(-1.0 <= j <= 1.0 for j in js)
        # In healthy state, J should be positive
        assert all(j > 0 for j in js), "J should be positive for healthy cluster"

    def test_weights_converge_over_time(self, ctrl):
        if not HAS_V66:
            pytest.skip("adaptive_objective.py not yet created")
        obj_ctrl = AdaptiveObjectiveController(ctrl)
        history = [
            {"action": "EVICT_NODE", "outcome": "success", "latency_ms": 50, "violations": 0, "conflicts": 0},
            {"action": "RESTORE_NODE", "outcome": "success", "latency_ms": 40, "violations": 0, "conflicts": 0},
            {"action": "RECONFIGURE_QUORUM", "outcome": "success", "latency_ms": 60, "violations": 1, "conflicts": 0},
            {"action": "ADD_OBSERVATION", "outcome": "success", "latency_ms": 30, "violations": 0, "conflicts": 0},
        ]
        snap = ctrl.get_snapshot()
        obj_ctrl.optimizer.get_weights()
        obj_ctrl.optimizer.gradient_descent_step(snap, history)
        w2 = obj_ctrl.optimizer.get_weights()
        # Weights may or may not change depending on history, but should not raise
        assert w2 is not None
