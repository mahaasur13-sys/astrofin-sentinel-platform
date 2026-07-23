#!/usr/bin/env python3
"""
Determinism Tests (L10) — verify scheduler produces same decision for same input.
Run: pytest tests/unit/test_determinism.py -v
"""
import pytest
from unittest.mock import MagicMock, patch
from scheduler_v3.scorer import score_and_select


class MockNode:
    def __init__(self, hostname, gpu_count=1, gpu_load=20.0,
                 cpu_load=30.0, mem_gb=32, mem_used=10.0,
                 status="HEALTHY"):
        self.hostname = hostname
        self.roles = ["slurm_compute"] if gpu_count > 0 else ["slurm_compute"]
        self.gpu_count = gpu_count
        self.gpu_model = "RTX3060"
        self.cpu_cores = 8
        self.memory_gb = mem_gb
        self.memory_used_gb = mem_used
        self.gpu_load_pct = gpu_load
        self.cpu_load_pct = cpu_load
        self.health_score = 100
        from state_store import NodeStatus
        self.status = NodeStatus(status)


class MockJob:
    def __init__(self, job_type="gpu", memory_gb=8):
        self.id = "test-job-1"
        self.name = "test"
        self.job_type = job_type
        self.memory_gb = memory_gb
        self.priority = 5


class MockStateStore:
    def __init__(self, nodes):
        self._nodes = nodes

    def get_healthy_nodes(self):
        return self._nodes

    def get_recent_failures(self, minutes=60):
        return []  # No failures for determinism test


def test_same_seed_same_node():
    """Test 1: Same job + same node state → same node selected."""
    nodes = [
        MockNode("rtx-node",   gpu_count=1, gpu_load=20.0, cpu_load=30.0, mem_gb=32, mem_used=10.0),
        MockNode("rk3576-node", gpu_count=0, cpu_load=10.0, mem_gb=16, mem_used=4.0),
    ]
    store = MockStateStore(nodes)
    job = MockJob("gpu", memory_gb=8)

    results = []
    for _ in range(5):
        best, scores = score_and_select(job, store)
        results.append(best.hostname if best else None)

    assert all(r == "rtx-node" for r in results), \
        f"Determinism broken: got {results}"


def test_gpu_load_changes_ranking():
    """Test 2: GPU load change → different node selected (when GPU available)."""
    nodes = [
        MockNode("rtx-hot",   gpu_count=1, gpu_load=90.0, cpu_load=30.0, mem_gb=32, mem_used=10.0),
        MockNode("rtx-cool",  gpu_count=1, gpu_load=10.0, cpu_load=30.0, mem_gb=32, mem_used=10.0),
    ]
    store = MockStateStore(nodes)
    job = MockJob("gpu", memory_gb=8)

    best, scores = score_and_select(job, store)
    assert best.hostname == "rtx-cool", \
        f"Expected rtx-cool (lower GPU load), got {best.hostname}"


def test_duplicate_submission_prevented():
    """Test 3: Deduplication — scheduler must not double-submit."""
    from job_engine import JobEngine
    from state_store import JobStatus

    store = MagicMock()
    admission = MagicMock()

    # Simulate: job already scheduled
    store.is_job_already_scheduled.return_value = True

    engine = JobEngine(store, admission)
    ok, msg = engine.schedule_job("job-123", "rtx-node")

    assert ok is False, "Expected duplicate to be prevented"
    assert "duplicate" in msg.lower()


def test_low_priority_throttled():
    """Test 4: Low-priority job rejected under high load."""
    from admission_controller import AdmissionController, AdmitDecision

    store = MagicMock()
    store.get_total_utilization.return_value = {
        "total_gpu_count": 1,
        "avg_gpu_load_pct": 50.0,
        "total_queue_depth": 10,
        "avg_load": 85.0,  # > 70%
    }

    controller = AdmissionController(store)
    result = controller.admit({
        "id": "job-low",
        "job_type": "cpu",
        "priority": 2,  # Low priority
        "memory_gb": 4,
    })

    assert result.decision == AdmitDecision.REJECT, \
        f"Expected REJECT for low-priority under load, got {result.decision}"


def test_failure_penalty_affects_score():
    """Test 5: Node with recent failures gets lower score."""
    nodes = [
        MockNode("stable",    gpu_count=1, gpu_load=20.0),
        MockNode("flaky",    gpu_count=1, gpu_load=10.0),  # Lower load
    ]
    store = MockStateStore(nodes)

    # Inject 3 recent failures on flaky node
    store.get_recent_failures = lambda m: [
        {"node_hostname": "flaky", "failure_type": "GPU_OOM"}
        for _ in range(3)
    ]

    job = MockJob("gpu")
    best, scores = score_and_select(job, store)

    # flaky should NOT win despite lower GPU load (failure penalty = 3*20=60)
    assert best.hostname == "stable", \
        f"Expected stable (failure penalty on flaky), got {best.hostname}"


def test_backpressure_throttles_queue():
    """Test 6: Queue > 40 → new jobs queued, not rejected."""
    from admission_controller import AdmissionController, AdmitDecision

    store = MagicMock()
    store.get_total_utilization.return_value = {
        "total_gpu_count": 1,
        "avg_gpu_load_pct": 30.0,
        "total_queue_depth": 45,  # > 40 threshold
        "avg_load": 50.0,
    }

    controller = AdmissionController(store)
    result = controller.admit({
        "id": "job-queued",
        "job_type": "gpu",
        "priority": 5,
        "memory_gb": 8,
    })

    assert result.decision == AdmitDecision.QUEUED, \
        f"Expected QUEUED under backpressure, got {result.decision}"
    assert result.wait_time is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
