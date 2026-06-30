"""
Tests for Swarm Layer v7.3 — worker_projection_engine, causal_merge_protocol,
swarm_divergence_field, distributed_tensor_alignment.
"""

from swarm.causal_merge_protocol import CausalMergeProtocol, SwarmDAG
from swarm.distributed_tensor_alignment import (
    DistributedTensorAlignment,
    WorkerSTensor,
)
from swarm.swarm_divergence_field import (
    FieldSeverity,
    SwarmDivergenceFieldEngine,
)
from swarm.worker_projection_engine import (
    WorkerProjectionEngine,
)


class TestWorkerProjectionEngine:
    def test_project_single_worker(self):
        engine = WorkerProjectionEngine(["state", "delta", "rate", "depth", "time"])
        raw = {"cpu": 0.8, "mem": 0.6, "disk": 0.5}
        proj = engine.project_worker_state("w1", 1, 1000, raw)
        assert proj.worker_id == "w1"
        assert proj.sequence_number == 1
        assert len(proj.axes) == 5
        assert proj.axes["state"].magnitude > 0

    def test_identical_workers_same_projection(self):
        engine = WorkerProjectionEngine(["state", "delta", "rate", "depth", "time"])
        raw1 = {"cpu": 0.8, "mem": 0.6}
        raw2 = {"cpu": 0.8, "mem": 0.6}
        p1 = engine.project_worker_state("w1", 1, 1000, raw1)
        p2 = engine.project_worker_state("w2", 1, 1000, raw2)
        d = engine.pairwise_swarm_distance(p1, p2)
        assert d["state"] < 1e-6

    def test_different_workers_divergent(self):
        engine = WorkerProjectionEngine(["state", "delta", "rate", "depth", "time"])
        raw1 = {"cpu": 0.8, "mem": 0.6}
        raw2 = {"cpu": 0.1, "mem": 0.9}
        p1 = engine.project_worker_state("w1", 1, 1000, raw1)
        p2 = engine.project_worker_state("w2", 1, 1000, raw2)
        d = engine.pairwise_swarm_distance(p1, p2)
        assert d["state"] > 0.1

    def test_pairwise_axis_distance_inf_on_missing_axis(self):
        engine = WorkerProjectionEngine(["state", "delta", "rate", "depth", "time"])
        raw = {"cpu": 0.8}
        proj = engine.project_worker_state("w1", 1, 1000, raw)
        d = engine.pairwise_axis_distance(proj, proj, "nonexistent_axis")
        assert d == float("inf")


class TestCausalMergeProtocol:
    def test_merge_identical_dags(self):
        proto = CausalMergeProtocol()
        dag1 = {"B": ["A"]}   # A→B (A is cause of B)
        dag2 = {"B": ["A"]}   # A→B
        result = proto.merge_worker_dags({"w1": dag1, "w2": dag2})
        assert ("A", "B") in result.edges

    def test_merge_missing_edge(self):
        proto = CausalMergeProtocol()
        dag1 = {"B": ["A"]}   # A→B
        dag2 = {"B": []}      # no edge
        result = proto.merge_worker_dags({"w1": dag1, "w2": dag2})
        assert ("A", "B") in result.edges

    def test_merge_reversed_edge_conflict(self):
        proto = CausalMergeProtocol()
        dag1 = {"A": ["B"]}   # B→A (reversed: A is cause of B, worker sees B→A)
        dag2 = {"B": ["A"]}   # A→B (correct: A is cause of B)
        result = proto.merge_worker_dags({"w1": dag1, "w2": dag2})
        assert len(result.conflicts_resolved) >= 1
        # Should keep majority direction or resolved edge
        assert len(result.edges) >= 1

    def test_swarm_causal_depth(self):
        proto = CausalMergeProtocol()
        dag = {"C": ["B"], "B": ["A"], "A": []}
        swarm_dag = SwarmDAG(nodes=["A", "B", "C"], edges=[("A", "B"), ("B", "C")], conflicts_resolved=[], edge_origin_count={})
        depths = proto.compute_swarm_causal_depth(swarm_dag)
        assert depths["A"] == 0
        assert depths["B"] == 1
        assert depths["C"] == 2


class TestSwarmDivergenceFieldEngine:
    def test_identical_projections_identical_field(self):
        engine = SwarmDivergenceFieldEngine(["state", "delta", "rate", "depth", "time"])
        proj_engine = WorkerProjectionEngine(["state", "delta", "rate", "depth", "time"])
        raw = {"cpu": 0.8}
        p1 = proj_engine.project_worker_state("w1", 1, 1000, raw)
        p2 = proj_engine.project_worker_state("w2", 1, 1000, raw)
        field = engine.build_field([p1, p2])
        assert field.global_coherence > 0.99
        assert field.field_severity == FieldSeverity.IDENTICAL

    def test_different_projections_divergent_field(self):
        engine = SwarmDivergenceFieldEngine(["state", "delta", "rate", "depth", "time"])
        proj_engine = WorkerProjectionEngine(["state", "delta", "rate", "depth", "time"])
        p1 = proj_engine.project_worker_state("w1", 1, 1000, {"cpu": 0.8})
        p2 = proj_engine.project_worker_state("w2", 1, 1000, {"cpu": 0.1})
        field = engine.build_field([p1, p2])
        # Coherence is cosine-based: same direction vectors give 1.0.
        # The key divergence signal is the delta_magnitude on "state" axis.
        state_flux = next(f for f in field.divergence_fluxes if f.axis == "state")
        assert state_flux.delta_magnitude > 0.1  # magnitudes differ
        assert state_flux.severity != FieldSeverity.IDENTICAL

    def test_most_divergent_axis_detected(self):
        engine = SwarmDivergenceFieldEngine(["state", "delta"])
        proj_engine = WorkerProjectionEngine(["state", "delta"])
        p1 = proj_engine.project_worker_state("w1", 1, 1000, {"x": 0.0, "y": 0.0})
        p2 = proj_engine.project_worker_state("w2", 1, 1000, {"x": 1.0, "y": 0.0})
        field = engine.build_field([p1, p2])
        assert field.most_divergent_axis in ("state", "delta")


class TestDistributedTensorAlignment:
    def test_align_identical_tensors(self):
        engine = DistributedTensorAlignment(["state", "delta", "rate", "depth", "time"])
        tensors = [
            WorkerSTensor("w1", 1, 1000, {"state": 0.5, "delta": 0.3, "rate": 0.2, "depth": 0.1, "time": 0.05}, 0.93, "MINOR"),
            WorkerSTensor("w2", 1, 1000, {"state": 0.5, "delta": 0.3, "rate": 0.2, "depth": 0.1, "time": 0.05}, 0.93, "MINOR"),
        ]
        result = engine.align(tensors)
        assert result.global_coherence > 0.99
        assert result.partition_count == 2

    def test_align_different_tensors_divergence(self):
        engine = DistributedTensorAlignment(["state", "delta"])
        tensors = [
            WorkerSTensor("w1", 1, 1000, {"state": 0.9, "delta": 0.9}, 0.9, "MINOR"),
            WorkerSTensor("w2", 1, 1000, {"state": 0.1, "delta": 0.1}, 0.1, "CRITICAL"),
        ]
        result = engine.align(tensors)
        assert result.global_coherence < 1.0
        assert result.partition_count == 2
        assert result.coherence_matrix[0][1] < 1.0

    def test_reconcile_swarm_S(self):
        engine = DistributedTensorAlignment(["state", "delta"])
        tensors = [
            WorkerSTensor("w1", 1, 1000, {"state": 0.8, "delta": 0.4}, 0.6, "MINOR"),
            WorkerSTensor("w2", 1, 1000, {"state": 0.2, "delta": 0.6}, 0.4, "MODERATE"),
        ]
        result = engine.align(tensors)
        reconciled = engine.reconcile_swarm_S(result)
        assert "state" in reconciled
        assert "delta" in reconciled
        assert all(isinstance(v, float) for v in reconciled.values())


class TestIntegrationSwarmLayer:
    def test_full_swarm_pipeline(self):
        # 1. Project 3 workers with different states
        proj_engine = WorkerProjectionEngine(["state", "delta", "rate", "depth", "time"])
        p1 = proj_engine.project_worker_state("w1", 1, 1000, {"cpu": 0.9, "mem": 0.7})
        p2 = proj_engine.project_worker_state("w2", 1, 1000, {"cpu": 0.8, "mem": 0.6})
        p3 = proj_engine.project_worker_state("w3", 1, 1000, {"cpu": 0.1, "mem": 0.9})

        # 2. Build divergence field
        field_engine = SwarmDivergenceFieldEngine(["state", "delta", "rate", "depth", "time"])
        field = field_engine.build_field([p1, p2, p3])
        assert field.global_coherence > 0.0
        assert len(field.divergence_fluxes) > 0

        # 3. Merge causal DAGs
        merge_proto = CausalMergeProtocol()
        worker_dags = {
            "w1": {"cpu": ["mem"], "mem": []},
            "w2": {"cpu": ["mem"], "mem": []},
            "w3": {"cpu": ["mem"], "mem": []},
        }
        swarm_dag = merge_proto.merge_worker_dags(worker_dags)
        assert len(swarm_dag.nodes) >= 2

        # 4. Align S tensors
        engine = DistributedTensorAlignment(["state", "delta", "rate", "depth", "time"])
        tensors = [
            WorkerSTensor("w1", 1, 1000, {"state": p1.axes["state"].magnitude, "delta": p1.axes["delta"].magnitude, "rate": p1.axes["rate"].magnitude, "depth": p1.axes["depth"].magnitude, "time": p1.axes["time"].magnitude}, p1.axes["state"].magnitude, "MINOR"),
            WorkerSTensor("w2", 1, 1000, {"state": p2.axes["state"].magnitude, "delta": p2.axes["delta"].magnitude, "rate": p2.axes["rate"].magnitude, "depth": p2.axes["depth"].magnitude, "time": p2.axes["time"].magnitude}, p2.axes["state"].magnitude, "MINOR"),
            WorkerSTensor("w3", 1, 1000, {"state": p3.axes["state"].magnitude, "delta": p3.axes["delta"].magnitude, "rate": p3.axes["rate"].magnitude, "depth": p3.axes["depth"].magnitude, "time": p3.axes["time"].magnitude}, p3.axes["state"].magnitude, "MODERATE"),
        ]
        result = engine.align(tensors)
        assert result.partition_count == 3
        assert len(result.coherence_matrix) == 3
