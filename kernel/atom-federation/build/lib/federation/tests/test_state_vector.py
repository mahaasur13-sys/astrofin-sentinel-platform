"""Tests for federation.state_vector."""

import time

from federation.state_vector import StateVector


class TestStateVectorBasics:
    def test_create_vector(self):
        sv = StateVector(
            node_id="n1",
            theta_hash="abc123",
            envelope_state="stable",
            drift_score=0.1,
            stability_score=0.95,
        )
        assert sv.node_id == "n1"
        assert sv.theta_hash == "abc123"
        assert sv.envelope_state == "stable"

    def test_timestamp_auto_populated(self):
        before = time.time_ns()
        sv = StateVector(
            node_id="n1",
            theta_hash="abc123",
            envelope_state="stable",
            drift_score=0.1,
            stability_score=0.95,
        )
        after = time.time_ns()
        assert before <= sv.timestamp_ns <= after

    def test_severity_mapping(self):
        assert (
            StateVector(
                node_id="n", theta_hash="x", envelope_state="stable",
                drift_score=0.0, stability_score=1.0,
            ).severity.value
            == "negligible"
        )
        assert (
            StateVector(
                node_id="n", theta_hash="x", envelope_state="warning",
                drift_score=0.4, stability_score=0.6,
            ).severity.value
            == "medium"
        )
        assert (
            StateVector(
                node_id="n", theta_hash="x", envelope_state="critical",
                drift_score=0.7, stability_score=0.3,
            ).severity.value
            == "high"
        )
        assert (
            StateVector(
                node_id="n", theta_hash="x", envelope_state="collapse",
                drift_score=1.0, stability_score=0.0,
            ).severity.value
            == "critical"
        )


class TestStateVectorAge:
    def test_age_ms_zero_at_creation(self):
        sv = StateVector(
            node_id="n",
            theta_hash="x",
            envelope_state="stable",
            drift_score=0.0,
            stability_score=1.0,
            timestamp_ns=time.time_ns(),
        )
        assert sv.age_ms < 10  # within 10ms

    def test_is_stale_false_when_fresh(self):
        sv = StateVector(
            node_id="n",
            theta_hash="x",
            envelope_state="stable",
            drift_score=0.0,
            stability_score=1.0,
            timestamp_ns=time.time_ns(),
        )
        assert not sv.is_stale(max_age_ms=30_000)

    def test_is_stale_true_when_old(self):
        old_ns = time.time_ns() - (60_000 * 1_000_000)  # 60s ago
        sv = StateVector(
            node_id="n",
            theta_hash="x",
            envelope_state="stable",
            drift_score=0.0,
            stability_score=1.0,
            timestamp_ns=old_ns,
        )
        assert sv.is_stale(max_age_ms=30_000)


class TestStateVectorHashTheta:
    def test_hash_theta_stable(self):
        theta1 = {"lr": 0.001, "gamma": 0.9}
        theta2 = {"gamma": 0.9, "lr": 0.001}  # same, different order
        assert StateVector.hash_theta(theta1) == StateVector.hash_theta(theta2)

    def test_hash_theta_different_for_different_dicts(self):
        t1 = {"lr": 0.001}
        t2 = {"lr": 0.002}
        assert StateVector.hash_theta(t1) != StateVector.hash_theta(t2)

    def test_hash_theta_returns_16_chars(self):
        h = StateVector.hash_theta({"a": 1})
        assert len(h) == 16
        assert h.isalnum()


class TestStateVectorStr:
    def test_str_contains_node_id(self):
        sv = StateVector(
            node_id="node-42",
            theta_hash="h",
            envelope_state="stable",
            drift_score=0.1,
            stability_score=0.9,
        )
        assert "node-42" in str(sv)
        assert "stable" in str(sv)
        assert "0.100" in str(sv)
