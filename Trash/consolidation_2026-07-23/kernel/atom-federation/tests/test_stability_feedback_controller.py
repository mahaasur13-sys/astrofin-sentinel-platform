"""
Tests for StabilityFeedbackController — v7.4
Oscillation prevention and damped feedback for actuator layer.
"""

import pytest

from actuator.stability_feedback_controller import (
    GainAdjustment,
    OscillationMode,
    StabilityFeedbackController,
    StabilityState,
)


class TestStabilityFeedbackControllerBasics:
    """Basic initialization and reset."""

    def test_default_init(self):
        c = StabilityFeedbackController()
        assert c.damping_coeff == 0.7
        assert c.oscillation_window == 8
        assert c.overshoot_threshold == 1.2
        assert c.undershoot_threshold == 0.3
        assert c.convergence_threshold == 0.02
        assert c.max_damping_factor == 1.0
        assert c.min_damping_factor == 0.1

    def test_custom_init(self):
        c = StabilityFeedbackController(
            damping_coeff=0.5,
            oscillation_window=16,
            overshoot_threshold=1.5,
            undershoot_threshold=0.2,
        )
        assert c.damping_coeff == 0.5
        assert c.oscillation_window == 16
        assert c.overshoot_threshold == 1.5
        assert c.undershoot_threshold == 0.2

    def test_initial_state(self):
        c = StabilityFeedbackController()
        s = c.state
        assert s.mode == OscillationMode.NORMAL
        assert s.oscillation_index == 0.0
        assert s.damping_factor == 1.0
        assert s.adaptive_gain == 1.0
        assert s.overshoot_count == 0
        assert s.undershoot_count == 0

    def test_reset(self):
        c = StabilityFeedbackController()
        c.observe(0.1, 0.15, 0.9, 0.5, 1000)
        c.reset()
        s = c.state
        assert s.mode == OscillationMode.NORMAL
        assert s.oscillation_index == 0.0
        assert s.adaptive_gain == 1.0
        assert len(c._gain_history) == 0


class TestOscillationDetection:
    """Oscillation index computation and mode detection."""

    def test_stable_observations(self):
        """Gain ratio near 1.0 → stable."""
        c = StabilityFeedbackController(oscillation_window=5)
        for i in range(5):
            c.observe(
                expected_gain=0.1,
                actual_gain=0.1 + (i % 2) * 0.01,  # near 1.0 ratio
                current_coherence=0.9,
                control_saturation=0.3,
                timestamp_ms=1000 + i * 100,
            )
        assert c.state.oscillation_index < 0.2
        assert c.state.mode == OscillationMode.NORMAL

    def test_oscillating_observations(self):
        """Alternating overshoot/undershoot → oscillating."""
        c = StabilityFeedbackController(oscillation_window=8, overshoot_threshold=1.2, undershoot_threshold=0.3)
        # alternating: gain_ratio = 1.4, 0.2, 1.4, 0.2 ...
        for i in range(8):
            ratio = 1.4 if i % 2 == 0 else 0.2
            c.observe(
                expected_gain=0.1,
                actual_gain=0.1 * ratio,
                current_coherence=0.85,
                control_saturation=0.3,
                timestamp_ms=1000 + i * 100,
            )
        assert c.state.oscillation_index >= 0.4
        assert c.state.mode in (OscillationMode.OSCILLATING, OscillationMode.COLLAPSED)

    def test_overshoot_counting(self):
        c = StabilityFeedbackController(overshoot_threshold=1.2)
        c.observe(0.1, 0.15, 0.9, 0.3, 1000)  # ratio 1.5 > 1.2 → overshoot
        assert c.state.overshoot_count == 1
        c.observe(0.1, 0.14, 0.9, 0.3, 1100)  # ratio 1.4 > 1.2 → overshoot
        assert c.state.overshoot_count == 2

    def test_undershoot_counting(self):
        c = StabilityFeedbackController(undershoot_threshold=0.3)
        c.observe(0.1, 0.02, 0.9, 0.3, 1000)  # ratio 0.2 < 0.3 → undershoot
        assert c.state.undershoot_count == 1

    def test_saturation_mode(self):
        """High control saturation → SATURATED mode."""
        c = StabilityFeedbackController()
        c.observe(0.1, 0.05, 0.6, 0.97, 1000)  # saturation 0.97 >= 0.95
        assert c.state.mode == OscillationMode.SATURATED


class TestComputeGainAdjustment:
    """Gain adjustment computation in each mode."""

    def test_normal_mode_no_adjustment(self):
        c = StabilityFeedbackController()
        c.state.mode = OscillationMode.NORMAL
        c.state.adaptive_gain = 1.0
        c.state.damping_factor = 1.0
        adj = c.compute_gain_adjustment([], expected_total_gain=0.1)
        assert adj.oscillation_mode == OscillationMode.NORMAL
        assert adj.apply_to_commands is False
        assert adj.new_adaptive_gain == 1.0

    def test_oscillating_mode_reduces_gain(self):
        c = StabilityFeedbackController(damping_coeff=0.7)
        c.state.mode = OscillationMode.OSCILLATING
        c.state.adaptive_gain = 1.0
        c.state.damping_factor = 0.5
        adj = c.compute_gain_adjustment([], expected_total_gain=0.1)
        assert adj.oscillation_mode == OscillationMode.OSCILLATING
        assert adj.apply_to_commands is True
        assert adj.new_adaptive_gain == 1.0 * 0.7  # damping_coeff reduction

    def test_warning_mode_reduces_gain_moderately(self):
        c = StabilityFeedbackController(damping_coeff=0.7)
        c.state.mode = OscillationMode.WARNING
        c.state.adaptive_gain = 1.0
        c.state.damping_factor = 0.8
        adj = c.compute_gain_adjustment([], expected_total_gain=0.1)
        assert adj.oscillation_mode == OscillationMode.WARNING
        assert adj.apply_to_commands is True
        # warning uses sqrt(damping_coeff)
        assert adj.new_adaptive_gain == 1.0 * (0.7 ** 0.5)

    def test_saturated_mode_reduces_gain_significantly(self):
        c = StabilityFeedbackController()
        c.state.mode = OscillationMode.SATURATED
        c.state.adaptive_gain = 1.0
        c.state.damping_factor = 0.9
        adj = c.compute_gain_adjustment([], expected_total_gain=0.1)
        assert adj.oscillation_mode == OscillationMode.SATURATED
        assert adj.apply_to_commands is True
        assert adj.new_adaptive_gain == 1.0 * 0.5  # fixed 0.5 reduction

    def test_collapsed_mode_zero_gain(self):
        c = StabilityFeedbackController()
        c.state.mode = OscillationMode.COLLAPSED
        c.state.adaptive_gain = 1.0
        adj = c.compute_gain_adjustment([], expected_total_gain=0.1)
        assert adj.oscillation_mode == OscillationMode.COLLAPSED
        assert adj.new_adaptive_gain == 0.0
        assert adj.damping_factor == 0.1


class TestAdaptiveGainRestoration:
    """Adaptive gain converges toward 1.0 when stable."""

    def test_gain_restores_when_normal(self):
        c = StabilityFeedbackController(damping_coeff=0.7)
        c.state.mode = OscillationMode.NORMAL
        c.state.adaptive_gain = 0.6  # below 1.0
        c.state.damping_factor = 0.9
        adj = c.compute_gain_adjustment([], expected_total_gain=0.1)
        # restores with factor 1.05
        assert adj.new_adaptive_gain == pytest.approx(0.6 * 1.05, rel=0.01)

    def test_gain_caps_at_1_0(self):
        c = StabilityFeedbackController()
        c.state.mode = OscillationMode.NORMAL
        c.state.adaptive_gain = 0.99
        c.state.damping_factor = 1.0
        adj = c.compute_gain_adjustment([], expected_total_gain=0.1)
        assert adj.new_adaptive_gain == 1.0

    def test_gain_reduces_when_oscillating(self):
        c = StabilityFeedbackController(damping_coeff=0.7)
        c.state.mode = OscillationMode.OSCILLATING
        c.state.adaptive_gain = 0.8
        c.state.damping_factor = 0.5
        adj = c.compute_gain_adjustment([], expected_total_gain=0.1)
        # rapid reduction: damping_coeff applied once (not squared) in compute_gain_adjustment
        assert adj.new_adaptive_gain == pytest.approx(0.8 * 0.7, rel=0.01)


class TestApplyGainToCommands:
    """Gain adjustment applied to command magnitudes."""

    def _make_cmd(self):
        from actuator.causal_actuation_engine import ActuatorCommand
        return ActuatorCommand(
            target_worker="w1",
            axis="S_full",
            command_type="shift_state",
            delta=0.5,
            causal_depth=1,
            priority=2,
            reason="test",
            expected_coherence_gain=0.1,
            timestamp_ms=1000,
        )

    def test_noop_when_apply_false(self):
        c = StabilityFeedbackController()
        cmd = self._make_cmd()
        adj = GainAdjustment(
            new_adaptive_gain=0.5,
            damping_factor=0.5,
            oscillation_mode=OscillationMode.NORMAL,
            reasoning="test",
            apply_to_commands=False,
        )
        modified = c.apply_gain_to_commands([cmd], adj)
        assert len(modified) == 1
        assert modified[0].delta == 0.5  # unchanged

    def test_scales_delta_when_apply_true(self):
        c = StabilityFeedbackController()
        cmd = self._make_cmd()
        adj = GainAdjustment(
            new_adaptive_gain=0.5,
            damping_factor=0.4,
            oscillation_mode=OscillationMode.OSCILLATING,
            reasoning="test",
            apply_to_commands=True,
        )
        modified = c.apply_gain_to_commands([cmd], adj)
        assert len(modified) == 1
        # factor = 0.5 * 0.4 = 0.2
        assert modified[0].delta == pytest.approx(0.5 * 0.5 * 0.4, rel=0.01)
        # other fields preserved
        assert modified[0].target_worker == "w1"
        assert modified[0].expected_coherence_gain == pytest.approx(0.1 * 0.5 * 0.4, rel=0.01)

    def test_multiple_commands(self):
        from actuator.causal_actuation_engine import ActuatorCommand
        c = StabilityFeedbackController()
        cmds = [
            ActuatorCommand("w1", "axis1", "shift_state", 0.5, 1, 2, "a", 0.1, 1000),
            ActuatorCommand("w2", "axis2", "rebalance",  0.3, 2, 3, "b", 0.05, 1000),
        ]
        adj = GainAdjustment(0.5, 0.5, OscillationMode.WARNING, "test", True)
        modified = c.apply_gain_to_commands(cmds, adj)
        assert len(modified) == 2
        assert modified[0].delta == pytest.approx(0.5 * 0.5 * 0.5)
        assert modified[1].delta == pytest.approx(0.3 * 0.5 * 0.5)


class TestStabilityStateFields:
    """StabilityState dataclass fields."""

    def test_stability_state_defaults(self):
        s = StabilityState()
        assert s.mode == OscillationMode.NORMAL
        assert s.oscillation_index == 0.0
        assert s.damping_factor == 1.0
        assert s.adaptive_gain == 1.0
        assert s.overshoot_count == 0
        assert s.undershoot_count == 0
        assert s.last_gain_adjustment == 0.0
        assert s.correction_saturation == 0.0

    def test_stability_state_explicit(self):
        s = StabilityState(
            mode=OscillationMode.OSCILLATING,
            oscillation_index=0.7,
            damping_factor=0.3,
            adaptive_gain=0.5,
            overshoot_count=5,
            undershoot_count=2,
            last_gain_adjustment=-0.2,
            correction_saturation=0.8,
        )
        assert s.mode == OscillationMode.OSCILLATING
        assert s.oscillation_index == 0.7
        assert s.damping_factor == 0.3
        assert s.adaptive_gain == 0.5
        assert s.overshoot_count == 5
        assert s.undershoot_count == 2
        assert s.last_gain_adjustment == -0.2
        assert s.correction_saturation == 0.8


class TestOscillationModeEnum:
    """OscillationMode enum values."""

    def test_all_modes_present(self):
        modes = list(OscillationMode)
        assert OscillationMode.NORMAL in modes
        assert OscillationMode.WARNING in modes
        assert OscillationMode.OSCILLATING in modes
        assert OscillationMode.SATURATED in modes
        assert OscillationMode.COLLAPSED in modes

    def test_modes_are_distinct(self):
        values = {m.value for m in OscillationMode}
        assert len(values) == len(OscillationMode)


class TestDampingBounds:
    """Damping factor stays within bounds."""

    def test_damping_never_below_min(self):
        c = StabilityFeedbackController(min_damping_factor=0.1)
        for i in range(20):
            c.observe(
                expected_gain=0.1,
                actual_gain=0.1 * (1.5 if i % 2 == 0 else 0.1),
                current_coherence=0.8,
                control_saturation=0.3,
                timestamp_ms=1000 + i * 100,
            )
        assert c.state.damping_factor >= 0.1

    def test_damping_never_above_max(self):
        c = StabilityFeedbackController(max_damping_factor=1.0)
        for i in range(5):
            c.observe(
                expected_gain=0.1,
                actual_gain=0.1,
                current_coherence=0.9,
                control_saturation=0.1,
                timestamp_ms=1000 + i * 100,
            )
        assert c.state.damping_factor <= 1.0


class TestHistoryManagement:
    """Rolling history doesn't grow unbounded."""

    def test_gain_history_max_length(self):
        c = StabilityFeedbackController(oscillation_window=4)
        for i in range(20):
            c.observe(0.1, 0.1, 0.9, 0.3, 1000 + i)
        assert len(c._gain_history) <= 4

    def test_coherence_history_max_length(self):
        c = StabilityFeedbackController(oscillation_window=4)
        for i in range(30):
            c.observe(0.1, 0.1, 0.9, 0.3, 1000 + i)
        # coherence_history has 2x window limit
        assert len(c._coherence_history) <= 8

    def test_saturation_history_max_length(self):
        c = StabilityFeedbackController(oscillation_window=4)
        for i in range(20):
            c.observe(0.1, 0.1, 0.9, 0.3, 1000 + i)
        assert len(c._saturation_history) <= 4
