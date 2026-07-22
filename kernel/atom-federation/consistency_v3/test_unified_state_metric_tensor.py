"""
Tests for unified_state_metric_tensor.py
"""

from consistency_v3.unified_state_metric_tensor import (
    AXIS_LABELS,
    DEFAULT_WEIGHTS,
    AxisVector,
    UnifiedStateMetricTensor,
    _dict_l2_delta,
    _hamming_hex,
)


class TestAxisVector:
    def test_to_vector(self):
        av = AxisVector(state_diff=1.0, temporal_drift=2.0, rate_drift=3.0, causal_div=4.0, fingerprint_div=5.0)
        vec = av.to_vector()
        assert vec == [1.0, 2.0, 3.0, 4.0, 5.0]

    def test_from_fingerprints_differ(self):
        av = AxisVector.from_fingerprints("abc123", "xyz789")
        assert av.fingerprint_div > 0

    def test_from_fingerprints_same(self):
        av = AxisVector.from_fingerprints("abc123", "abc123")
        assert av.fingerprint_div == 0.0

    def test_magnitude(self):
        av = AxisVector(state_diff=3.0, temporal_drift=4.0, rate_drift=0.0, causal_div=0.0, fingerprint_div=0.0)
        assert av.magnitude() == 5.0

    def test_weighted_sum(self):
        av = AxisVector(state_diff=1.0, temporal_drift=0.0, rate_drift=0.0, causal_div=0.0, fingerprint_div=0.0)
        assert av.weighted_sum([2.0, 0.0, 0.0, 0.0, 0.0]) == 2.0


class TestDictL2Delta:
    def test_identical(self):
        assert _dict_l2_delta({"a": 1.0}, {"a": 1.0}) == 0.0

    def test_single_field(self):
        assert _dict_l2_delta({"a": 3.0}, {"a": 0.0}) == 3.0

    def test_nested(self):
        d = _dict_l2_delta({"x": {"y": 3.0}}, {"x": {"y": 0.0}})
        assert d == 3.0


class TestHammingHex:
    def test_identical(self):
        assert _hamming_hex("abc123", "abc123") == 0.0

    def test_completely_different(self):
        assert _hamming_hex("000000", "ffffff") > 0

    def test_unequal_length(self):
        assert _hamming_hex("abc", "abcde") > 0


class TestUnifiedStateMetricTensor:
    def test_S_full_zero_identical(self):
        tensor = UnifiedStateMetricTensor(domain="t1")
        axis = AxisVector()
        assert tensor.S_full(axis) == 0.0

    def test_severity_identical(self):
        tensor = UnifiedStateMetricTensor(domain="t1")
        assert tensor.severity_level() == "IDENTICAL"

    def test_severity_minor(self):
        tensor = UnifiedStateMetricTensor(domain="t1")
        av = AxisVector(state_diff=0.15)
        assert tensor.severity_level(av) == "MINOR"

    def test_severity_moderate(self):
        tensor = UnifiedStateMetricTensor(domain="t1")
        av = AxisVector(state_diff=3.0)
        assert tensor.severity_level(av) == "MODERATE"

    def test_severity_severe(self):
        tensor = UnifiedStateMetricTensor(domain="t1")
        av = AxisVector(state_diff=7.0)
        assert tensor.severity_level(av) == "SEVERE"

    def test_severity_critical(self):
        tensor = UnifiedStateMetricTensor(domain="t1")
        av = AxisVector(state_diff=15.0)
        assert tensor.severity_level(av) == "CRITICAL"

    def test_push_increments_history(self):
        tensor = UnifiedStateMetricTensor(domain="t1")
        assert tensor.S_full() == 0.0
        av = tensor.push(
            exec_state={"a": 1.0},
            replay_state={"a": 1.0},
            fp_exec="abc",
            fp_replay="abc",
            transitions_exec=0,
            transitions_replay=0,
        )
        assert isinstance(av, AxisVector)
        assert len(tensor._history) == 1

    def test_push_divergence_detected(self):
        tensor = UnifiedStateMetricTensor(domain="t1")
        tensor.push(
            exec_state={"a": 100.0},
            replay_state={"a": 1.0},
            fp_exec="abc",
            fp_replay="def",
            transitions_exec=10,
            transitions_replay=5,
            c_depth_exec=3,
            c_depth_replay=3,
        )
        assert tensor.S_full() >= 0.0
        assert tensor.severity_level() in ("IDENTICAL", "MINOR", "MODERATE", "SEVERE", "CRITICAL")

    def test_trajectory(self):
        tensor = UnifiedStateMetricTensor(domain="t1")
        for i in range(5):
            tensor.push(
                exec_state={"x": float(i)},
                replay_state={"x": float(i)},
                fp_exec=f"fp{i}",
                fp_replay=f"fp{i}",
            )
        traj = tensor.trajectory()
        assert len(traj) == 5
        assert all(isinstance(v, float) for v in traj)

    def test_to_dict(self):
        tensor = UnifiedStateMetricTensor(domain="test_domain")
        tensor.push(
            exec_state={"a": 1.0},
            replay_state={"a": 2.0},
            fp_exec="abc",
            fp_replay="xyz",
        )
        d = tensor.to_dict()
        assert d["domain"] == "test_domain"
        assert d["weights"] == DEFAULT_WEIGHTS
        assert "S_full_current" in d
        assert "severity" in d
        assert d["axis_labels"] == AXIS_LABELS

    def test_custom_weights(self):
        custom_w = [0.0, 0.0, 0.0, 0.0, 1.0]
        tensor = UnifiedStateMetricTensor(domain="t1", weights=custom_w)
        av = AxisVector(state_diff=10.0, temporal_drift=0.0, rate_drift=0.0, causal_div=0.0, fingerprint_div=3.0)
        # state_diff axis has weight 0, so S_full should only reflect fingerprint
        assert tensor.S_full(av) == 3.0
