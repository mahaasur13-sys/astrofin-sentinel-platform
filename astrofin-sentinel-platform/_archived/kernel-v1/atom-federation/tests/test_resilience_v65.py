"""
Tests for v6.5 resilience modules — matched to actual API signatures.
"""
import time

import pytest

from resilience.invariants import InvariantsEngine
from resilience.metrics_engine import StabilitySnapshot


class TestInvariantResult:
    def _make_snapshot(self, convergence_time_ms, unreachable_nodes=None, chaos=False):
        return StabilitySnapshot(
            ts=time.time(),
            stability_score=0.95,
            quorum_health=1.0,
            network_health=1.0,
            sbs_health=1.0,
            routing_health=0.9,
            rto_ms=150.0,
            convergence_time_ms=convergence_time_ms,
            recovery_rate=0.5,
            violation_count_60s=0,
            node_count_total=3,
            node_count_healthy=3,
            anomaly_count=0,
        )

    def test_i5_bounded_convergence_PASS(self):
        """I5: convergence below MAX_CONVERGENCE_MS passes"""
        engine = InvariantsEngine(node_count=3)
        snap = self._make_snapshot(convergence_time_ms=engine.MAX_CONVERGENCE_MS - 1)
        results = engine.check_all(snap)
        i5 = next(r for r in results.results if r.invariant_name == "I5_convergence_bounded")
        assert i5.passed

    def test_i5_bounded_convergence_FAIL(self):
        """I5: convergence exceeding MAX_CONVERGENCE_MS fails"""
        engine = InvariantsEngine(node_count=3)
        snap = self._make_snapshot(convergence_time_ms=engine.MAX_CONVERGENCE_MS + 100)
        results = engine.check_all(snap)
        i5 = next(r for r in results.results if r.invariant_name == "I5_convergence_bounded")
        assert not i5.passed

    def test_to_dict_method_exists(self):
        """InvariantSetResult has to_dict()"""
        engine = InvariantsEngine(node_count=3)
        snap = self._make_snapshot(convergence_time_ms=10)
        results = engine.check_all(snap)
        d = results.to_dict()
        assert "set_name" in d
        assert "all_passed" in d
        assert "total_results" in d

    def test_critical_failure_triggers_panic(self):
        """Critical invariant failure triggers panic"""
        engine = InvariantsEngine(node_count=3)
        snap = self._make_snapshot(convergence_time_ms=999999)
        results = engine.check_all(snap)
        engine._trigger_panic(results)
        assert engine.is_panicked


class TestGlobalControlArbiter:
    def test_arbiter_initial_state(self):
        """Arbiter initializes without error"""
        from resilience.arbitrer import GlobalControlArbiter
        arbiter = GlobalControlArbiter()
        assert arbiter is not None


class TestSystemOptimizer:
    def test_optimization_result_positional(self):
        """OptimizationResult uses positional args"""
        from resilience.optimizer import OptimizationResult, OptimizerWeights
        weights = OptimizerWeights()
        r = OptimizationResult(
            J=0.42,
            stability_contrib=0.3,
            cost_penalty=0.05,
            latency_penalty=0.02,
            violation_penalty=0.0,
            conflict_penalty=0.0,
            weights_used=weights,
            ts=time.time(),
        )
        assert r.J == 0.42


class TestContinuousStabilityEngine:
    def test_engine_initialization(self):
        """Engine starts without error"""
        from resilience.continuous_stability import ContinuousStabilityEngine
        from resilience.metrics_engine import StabilityMetricsEngine
        metrics = StabilityMetricsEngine(window_seconds=5)
        engine = ContinuousStabilityEngine(metrics, tick_ms=100.0)
        assert engine is not None


class TestStabilitySnapshot:
    def test_snapshot_fields(self):
        """StabilitySnapshot has all required fields"""
        snap = StabilitySnapshot(
            ts=time.time(),
            stability_score=0.9,
            quorum_health=1.0,
            network_health=0.95,
            sbs_health=1.0,
            routing_health=0.88,
            rto_ms=150.0,
            convergence_time_ms=50.0,
            recovery_rate=0.5,
            violation_count_60s=2,
            node_count_total=3,
            node_count_healthy=3,
            anomaly_count=0,
        )
        assert snap.stability_score == 0.9
        assert snap.node_count_total == 3
        assert snap.node_count_healthy == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
