"""Unit tests for ATOM Operator — reconciler logic (no K8s required)."""

import sys
import time
from unittest.mock import MagicMock, patch

from atom_operator.reconciler import Reconciler

# conftest.py already added 'kubernetes/' to sys.path — import operator directly
from atom_operator.state import ClusterState, NodeState


def make_state(phase="Running", replicas=3, ready=3,
                sbs_threshold=0.05, coherence_drift_max=0.1,
                sbs_violation_rate=0.0, coherence_drift=0.0):
    live = ClusterState(
        name="test-cluster",
        namespace="default",
        replicas=replicas,
        sbs_threshold=sbs_threshold,
        coherence_drift_max=coherence_drift_max,
        phase=phase,
        ready_replicas=ready,
        current_version="7.0.0",
        nodes=[
            NodeState(node_id=str(i), status="Running",
                      sbs_violation_rate=sbs_violation_rate,
                      coherence_drift=coherence_drift)
            for i in range(replicas)
        ],
        conditions=[],
    )
    return live


def make_mock_k8s(metrics=None, sts_ready=None):
    k8s = MagicMock()
    if metrics is None:
        metrics = {}

    def mock_patch_status(name, ns, status):
        return {"status": status}

    k8s.patch_status = mock_patch_status

    mock_sts = MagicMock()
    mock_sts.status.ready_replicas = sts_ready if sts_ready is not None else 3
    k8s.read_statefulset.return_value = mock_sts

    return k8s


class TestReconcilerSBSReaction:
    """Step 5 — Phase 5: SBS violation → heal reaction."""

    def test_sbs_above_threshold_triggers_heal(self):
        k8s = make_mock_k8s()
        rec = Reconciler(k8s)

        cluster = make_state(
            sbs_threshold=0.05, sbs_violation_rate=0.08,
            phase="Running", replicas=3, ready=3
        ).to_k8s_status()

        with patch.object(rec, "_query_prometheus", return_value={
            "sbs_violation_rate": 0.08,
            "coherence_drift": 0.0,
            "ready_replicas": 3,
        }):
            result = rec.reconcile({
                "metadata": {"name": "test-cluster", "namespace": "default"},
                "spec": {"replicas": 3},
                "status": cluster,
            })

        assert result.sbs_violation_rate > result.sbs_threshold
        assert result.phase == "Healing"

    def test_sbs_below_threshold_no_heal(self):
        k8s = make_mock_k8s()
        rec = Reconciler(k8s)

        with patch.object(rec, "_query_prometheus", return_value={
            "sbs_violation_rate": 0.01,
            "coherence_drift": 0.0,
            "ready_replicas": 3,
        }):
            result = rec.reconcile({
                "metadata": {"name": "test-cluster", "namespace": "default"},
                "spec": {"replicas": 3},
                "status": make_state(sbs_threshold=0.05, sbs_violation_rate=0.01).to_k8s_status(),
            })

        assert result.phase == "Running"
        assert result.sbs_violation_rate < result.sbs_threshold


class TestReconcilerDriftThrottle:
    """Step 5 — Phase 7: coherence drift → throttle annotation."""

    def test_drift_above_max_patches_throttle(self):
        k8s = make_mock_k8s()
        rec = Reconciler(k8s)

        cluster = make_state(
            coherence_drift_max=0.1, coherence_drift=0.95,
            phase="Running", replicas=3, ready=3
        )

        with patch.object(rec, "_query_prometheus", return_value={
            "sbs_violation_rate": 0.0,
            "coherence_drift": 0.95,
            "ready_replicas": 3,
        }):
            result = rec.reconcile({
                "metadata": {"name": "test-cluster", "namespace": "default"},
                "spec": {"replicas": 3},
                "status": cluster.to_k8s_status(),
            })

        assert result.phase == "Degraded"
        k8s.patch_cluster.assert_called()


class TestReconcilerQuorum:
    """Step 5 — Phase 5: quorum breach → Failed phase."""

    def test_quorum_breach_sets_failed_phase(self):
        k8s = make_mock_k8s(sts_ready=1)
        rec = Reconciler(k8s)

        cluster = make_state(replicas=3, ready=1, phase="Running")

        with patch.object(rec, "_query_prometheus", return_value={
            "sbs_violation_rate": 0.0,
            "coherence_drift": 0.0,
            "ready_replicas": 1,
        }):
            result = rec.reconcile({
                "metadata": {"name": "test-cluster", "namespace": "default"},
                "spec": {"replicas": 3},
                "status": cluster.to_k8s_status(),
            })

        assert result.phase == "Failed"

    def test_quorum_ok_runnning_phase(self):
        k8s = make_mock_k8s(sts_ready=3)
        rec = Reconciler(k8s)

        cluster = make_state(replicas=3, ready=3, phase="Running")

        with patch.object(rec, "_query_prometheus", return_value={
            "sbs_violation_rate": 0.0,
            "coherence_drift": 0.0,
            "ready_replicas": 3,
        }):
            result = rec.reconcile({
                "metadata": {"name": "test-cluster", "namespace": "default"},
                "spec": {"replicas": 3},
                "status": cluster.to_k8s_status(),
            })

        assert result.phase == "Running"


class TestReconcilerScale:
    """Step 5 — Phase 5: scale-up on health_ratio < 0.99."""

    def test_health_ratio_low_triggers_scale_up(self):
        k8s = make_mock_k8s(sts_ready=2)
        rec = Reconciler(k8s)

        cluster = make_state(replicas=3, ready=2, phase="Running")

        with patch.object(rec, "_query_prometheus", return_value={
            "sbs_violation_rate": 0.0,
            "coherence_drift": 0.0,
            "ready_replicas": 2,
        }):
            rec.reconcile({
                "metadata": {"name": "test-cluster", "namespace": "default"},
                "spec": {"replicas": 3},
                "status": cluster.to_k8s_status(),
            })

        k8s.patch_statefulset.assert_called()
        call_args = k8s.patch_statefulset.call_args
        assert call_args[0][0] == "atom-node-test-cluster"
        assert call_args[1]["namespace"] == "default"

    def test_health_ratio_ok_no_scale(self):
        k8s = make_mock_k8s(sts_ready=3)
        rec = Reconciler(k8s)

        cluster = make_state(replicas=3, ready=3, phase="Running")

        with patch.object(rec, "_query_prometheus", return_value={
            "sbs_violation_rate": 0.0,
            "coherence_drift": 0.0,
            "ready_replicas": 3,
        }):
            rec.reconcile({
                "metadata": {"name": "test-cluster", "namespace": "default"},
                "spec": {"replicas": 3},
                "status": cluster.to_k8s_status(),
            })

        for call in k8s.method_calls:
            assert "scale" not in str(call).lower() or "scale_cooldown" in str(call)


class TestReconcilerBootstrap:
    """Step 5 — Phase 3: Pending → bootstrap creates StatefulSet."""

    def test_pending_cluster_triggers_bootstrap(self):
        k8s = make_mock_k8s()
        rec = Reconciler(k8s)

        cluster = make_state(phase="Pending", replicas=3, ready=0)

        with patch.object(rec, "_query_prometheus", return_value=None):
            result = rec.reconcile({
                "metadata": {"name": "test-cluster", "namespace": "default"},
                "spec": {"replicas": 3, "image": "atom:test"},
                "status": cluster.to_k8s_status(),
            })

        k8s.create_statefulset.assert_called()
        k8s.create_service.assert_called()
        assert result.phase == "Running"


class TestReconcilerCooldowns:
    """Heal/scale cooldowns prevent restart storms."""

    def test_heal_respects_cooldown(self):
        k8s = make_mock_k8s()
        rec = Reconciler(k8s)
        rec._heal_cooldown["test-cluster"] = time.time()

        with patch.object(rec, "_query_prometheus", return_value={
            "sbs_violation_rate": 0.1,
            "coherence_drift": 0.0,
            "ready_replicas": 3,
        }):
            result = rec.reconcile({
                "metadata": {"name": "test-cluster", "namespace": "default"},
                "spec": {"replicas": 3},
                "status": make_state(sbs_threshold=0.05, sbs_violation_rate=0.1).to_k8s_status(),
            })

        assert result.phase != "Healing"

    def test_heal_after_cooldown_expired(self):
        k8s = make_mock_k8s()
        rec = Reconciler(k8s)
        rec._heal_cooldown["test-cluster"] = time.time() - rec._heal_cooldown_seconds - 1

        with patch.object(rec, "_query_prometheus", return_value={
            "sbs_violation_rate": 0.1,
            "coherence_drift": 0.0,
            "ready_replicas": 3,
        }):
            result = rec.reconcile({
                "metadata": {"name": "test-cluster", "namespace": "default"},
                "spec": {"replicas": 3},
                "status": make_state(sbs_threshold=0.05, sbs_violation_rate=0.1).to_k8s_status(),
            })

        assert result.phase == "Healing"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
