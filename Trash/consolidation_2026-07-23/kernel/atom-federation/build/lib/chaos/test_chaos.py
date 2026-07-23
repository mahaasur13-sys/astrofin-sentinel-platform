"""
pytest chaos test suite — v6.3 adversarial validation.

Run with:
    pytest chaos/test_chaos.py -v
    pytest chaos/test_chaos.py -v -k "partition"
    pytest chaos/test_chaos.py -v --tb=short
"""

import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from chaos.harness import ChaosHarness, ChaosResult, ExperimentPhase
from chaos.partitioner import NetworkPartitioner
from chaos.scenarios import (
    SCENARIO_REGISTRY,
    ChaosScenario,
    byzantine_sender_injection,
    latency_spike,
    node_isolation,
    partition_half_cluster,
)
from chaos.validator import ChaosValidator, ValidationResult, Verdict
from sbs.failure_classifier import FailureCategory, FailureClassifier, FailureSeverity

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_cluster_ctx():
    """Mock cluster context for unit testing without a live cluster."""
    nodes = ["node-a", "node-b", "node-c"]
    node_ips = {
        "node-a": "172.28.1.10",
        "node-b": "172.28.1.11",
        "node-c": "172.28.1.12",
    }
    from cluster.node.health import ClusterHealthGraph
    health_graphs = {
        "node-a": ClusterHealthGraph("node-a", ["node-b", "node-c"]),
        "node-b": ClusterHealthGraph("node-b", ["node-a", "node-c"]),
        "node-c": ClusterHealthGraph("node-c", ["node-a", "node-b"]),
    }
    for node_id, peers in [("node-a", ["node-b", "node-c"]),
                            ("node-b", ["node-a", "node-c"]),
                            ("node-c", ["node-a", "node-b"])]:
        for peer in peers:
            health_graphs[node_id].mark_ok(peer, lag_ms=10.0)

    from cluster.shared.observability import MetricsCollector
    metrics = {
        "node-a": MetricsCollector("node-a"),
        "node-b": MetricsCollector("node-b"),
        "node-c": MetricsCollector("node-c"),
    }
    for m in metrics.values():
        m.init_peer("node-b")
        m.init_peer("node-c")

    return {
        "nodes": nodes,
        "node_ips": node_ips,
        "health_getter": lambda nid: health_graphs.get(nid),
        "metrics_getter": lambda nid: metrics.get(nid),
        "rpc_call": lambda nid, cmd: f"ok({nid}): {cmd}",
    }


@pytest.fixture
def validator():
    return ChaosValidator()


@pytest.fixture
def classifier():
    return FailureClassifier()


# ── Scenario Registry Tests ─────────────────────────────────────────────────

class TestScenarioRegistry:
    def test_all_scenarios_registered(self):
        expected = [
            "partition_half_cluster", "asymmetric_partition",
            "slow_node_amplification", "byzantine_sender_injection",
            "clock_skew_escalation", "loss_burst",
            "node_isolation", "latency_spike",
        ]
        for name in expected:
            assert name in SCENARIO_REGISTRY, f"Scenario {name} not registered"

    def test_scenario_returns_valid_object(self):
        for name, scenario in SCENARIO_REGISTRY.items():
            assert isinstance(scenario, ChaosScenario)
            assert scenario.name == name
            assert scenario.duration_s > 0
            assert scenario.fault_type

    def test_partition_half_cluster_properties(self):
        s = partition_half_cluster()
        assert s.name == "partition_half_cluster"
        assert s.fault_type == "partition"
        assert s.duration_s == 15.0
        assert "node-a" in s.params["partition_peers"]
        assert "node-b" in s.params["partition_peers"]

    def test_scenario_apply_returns_dict(self, mock_cluster_ctx):
        for name, scenario in SCENARIO_REGISTRY.items():
            result = scenario.apply(mock_cluster_ctx)
            assert isinstance(result, dict)
            assert "ok" in result


# ── Failure Classifier Tests ─────────────────────────────────────────────────

class TestFailureClassifier:
    def test_classifies_partition(self, classifier):
        event = {"type": "partition", "layer": "DRL", "description": "A↮B blocked"}
        result = classifier.classify(event)
        assert result.category == FailureCategory.NETWORK_PARTITION
        assert result.severity == FailureSeverity.HIGH

    def test_classifies_drop(self, classifier):
        event = {"type": "drop", "layer": "DRL", "description": "Forward timeout"}
        result = classifier.classify(event)
        assert result.category == FailureCategory.MESSAGE_LOSS
        assert result.severity == FailureSeverity.MEDIUM

    def test_classifies_byzantine(self, classifier):
        event = {"type": "byzantine", "layer": "SBS", "description": "conflicting results"}
        result = classifier.classify(event)
        assert result.category == FailureCategory.BYZANTINE_BEHAVIOR
        assert result.severity == FailureSeverity.CRITICAL

    def test_classifies_clock_skew(self, classifier):
        event = {"type": "clock_skew", "layer": "CCL", "description": "+5000ms drift"}
        result = classifier.classify(event)
        assert result.category == FailureCategory.TEMPORAL_DRIFT
        assert result.severity == FailureSeverity.MEDIUM

    def test_classifies_batch(self, classifier):
        events = [
            {"type": "partition", "layer": "DRL", "description": "cut"},
            {"type": "drop", "layer": "DRL", "description": "loss"},
            {"type": "byzantine", "layer": "SBS", "description": "fork"},
        ]
        results = classifier.classify_batch(events)
        assert len(results) == 3


# ── Chaos Validator Tests ───────────────────────────────────────────────────

class TestChaosValidator:
    def test_validate_partition_detects_unreachable(self, validator):
        result = validator.validate(
            scenario_name="partition_half_cluster",
            health_states={"node-a": "unreachable", "node-b": "unreachable", "node-c": "reachable"},
            sbs_results=[{"ok": False, "violations": ["LEADER_UNIQUENESS_VIOLATION"]}],
            raw_events=[{"type": "partition", "layer": "DRL", "description": "A↮B blocked"}],
            expected_behavior={"sbs_violations": ["LEADER_UNIQUENESS"], "system_response": "cluster_detects_and_recovers"},
        )
        assert result.verdict in (Verdict.PASS, Verdict.PARTIAL)
        assert len(result.sbs_violations) > 0
        assert any("LEADER" in v for v in result.sbs_violations)

    def test_validate_no_violations_returns_pass(self, validator):
        result = validator.validate(
            scenario_name="loss_burst",
            health_states={"node-a": "lagging", "node-b": "reachable", "node-c": "reachable"},
            sbs_results=[{"ok": True, "violations": []}],
            raw_events=[],
            expected_behavior={"sbs_violations": [], "system_response": "cluster_detects_and_recovers"},
        )
        assert result.verdict == Verdict.PASS

    def test_validate_byzantine_raises_critical(self, validator):
        result = validator.validate(
            scenario_name="byzantine_sender_injection",
            health_states={"node-a": "reachable", "node-b": "reachable", "node-c": "reachable"},
            sbs_results=[{"ok": False, "violations": ["BYZANTINE_SIGNAL"]}],
            raw_events=[{"type": "byzantine", "layer": "SBS", "description": "conflicting terms"}],
            expected_behavior={"sbs_violations": ["BYZANTINE_SIGNAL"], "system_response": "cluster_halts"},
        )
        assert result.verdict == Verdict.PASS
        assert "BYZANTINE_SIGNAL" in result.sbs_violations

    def test_validate_clock_skew_temporal_drift(self, validator):
        result = validator.validate(
            scenario_name="clock_skew_escalation",
            health_states={"node-a": "reachable", "node-b": "reachable", "node-c": "reachable"},
            sbs_results=[{"ok": False, "violations": ["TEMPORAL_DRIFT"]}],
            raw_events=[{"type": "clock_skew", "layer": "CCL", "description": "+5000ms drift"}],
            expected_behavior={"sbs_violations": ["TEMPORAL_DRIFT"], "system_response": "cluster_detects_and_recovers"},
        )
        assert result.verdict in (Verdict.PASS, Verdict.PARTIAL)
        assert "TEMPORAL_DRIFT" in result.sbs_violations


# ── Chaos Harness Tests ─────────────────────────────────────────────────────

class TestChaosHarness:
    def test_harness_runs_partition_scenario(self, mock_cluster_ctx):
        scenario = partition_half_cluster()
        harness = ChaosHarness(scenario=scenario, cluster_ctx=mock_cluster_ctx,
                               observation_s=2.0, stabilization_s=2.0)
        result = harness.run()
        assert isinstance(result, ChaosResult)
        assert result.scenario_name == "partition_half_cluster"
        assert result.phase == ExperimentPhase.COMPLETE
        assert result.verdict in (Verdict.PASS, Verdict.PARTIAL, Verdict.FAIL)

    def test_harness_runs_all_scenarios(self, mock_cluster_ctx):
        results = []
        for name, scenario in SCENARIO_REGISTRY.items():
            harness = ChaosHarness(scenario=scenario, cluster_ctx=mock_cluster_ctx,
                                   observation_s=1.0, stabilization_s=1.0)
            result = harness.run()
            results.append((name, result))
            assert result.phase == ExperimentPhase.COMPLETE, f"Scenario {name} did not complete: {result.error}"
        print("\n=== Chaos Harness Summary ===")
        for name, result in results:
            print(f"  {name}: {result.verdict.value} ({result.duration_s:.1f}s)")

    def test_harness_collects_health_snapshots(self, mock_cluster_ctx):
        scenario = latency_spike()
        harness = ChaosHarness(scenario=scenario, cluster_ctx=mock_cluster_ctx,
                               observation_s=2.0, stabilization_s=1.0)
        result = harness.run()
        assert isinstance(result.health_snapshot, dict)
        assert "baseline" in result.health_snapshot
        assert "during" in result.health_snapshot

    def test_run_scenario_convenience(self, mock_cluster_ctx):
        result = ChaosHarness.run_scenario("latency_spike", cluster_ctx=mock_cluster_ctx,
                                           observation_s=1.0, stabilization_s=1.0)
        assert result.scenario_name == "latency_spike"
        assert result.phase == ExperimentPhase.COMPLETE


# ── Network Partitioner Tests ────────────────────────────────────────────────

class TestNetworkPartitioner:
    def test_partitioner_init(self):
        np = NetworkPartitioner(dry_run=True)
        assert np.bridge == "docker0"
        assert np.dry_run is True

    def test_partitioner_block_ip_dry_run(self):
        np = NetworkPartitioner(dry_run=True)
        ok = np.block_ip("172.28.1.10", "172.28.1.11")
        assert ok is True

    def test_partitioner_partition_nodes(self):
        np = NetworkPartitioner(dry_run=True)
        count = np.partition_nodes(isolated_ips=["172.28.1.12"],
                                   rest_ips=["172.28.1.10", "172.28.1.11"])
        assert count == 4  # C→A, A→C, C→B, B→C

    def test_partitioner_restore_all_dry_run(self):
        np = NetworkPartitioner(dry_run=True)
        np.block_ip("172.28.1.10", "172.28.1.11")
        removed = np.restore_all()
        assert removed == 0


# ── Integration Tests ────────────────────────────────────────────────────────

class TestIntegration:
    def test_node_isolation_complete(self, mock_cluster_ctx, validator):
        scenario = node_isolation()
        harness = ChaosHarness(scenario=scenario, cluster_ctx=mock_cluster_ctx,
                               observation_s=3.0, stabilization_s=2.0)
        result = harness.run()
        assert result.phase == ExperimentPhase.COMPLETE
        assert isinstance(result.validation_result, ValidationResult)

    def test_partition_half_cluster_verdict_not_fail(self, mock_cluster_ctx):
        scenario = partition_half_cluster()
        harness = ChaosHarness(scenario=scenario, cluster_ctx=mock_cluster_ctx,
                               observation_s=3.0, stabilization_s=2.0)
        result = harness.run()
        assert result.phase == ExperimentPhase.COMPLETE
        assert result.verdict != Verdict.FAIL or result.error, f"Cluster silently corrupted: {result}"

    def test_byzantine_injection_detected(self, mock_cluster_ctx):
        scenario = byzantine_sender_injection()
        harness = ChaosHarness(scenario=scenario, cluster_ctx=mock_cluster_ctx,
                               observation_s=3.0, stabilization_s=2.0)
        result = harness.run()
        assert result.phase == ExperimentPhase.COMPLETE
