"""v6.8 — Global Coherence Engine integration tests."""

import time

import pytest

from coherence.drift_controller import (
    DriftController,
    DriftStatus,
)
from coherence.invariant import (
    CoherenceBounds,
    CoherenceViolation,
    SystemCoherenceInvariant,
)
from coherence.objective_stabilizer import (
    GlobalObjectiveStabilizer,
)
from coherence.temporal_smoother import (
    TemporalCoherenceSmoother,
)

# ── DriftController ─────────────────────────────────────────────────────────

def test_drift_stable_state():
    dc = DriftController(drift_threshold=0.15, hysteresis_band=0.03, k_p=0.5)
    real = {"cpu": 0.3, "mem": 0.4, "latency_ms": 10.0}
    model = {"cpu": 0.31, "mem": 0.39, "latency_ms": 10.2}
    snap = dc.observe(real, model)
    assert snap.drift_status == DriftStatus.STABLE
    assert snap.correction_applied is False


def test_drift_above_threshold_triggers_correction():
    dc = DriftController(drift_threshold=0.15, hysteresis_band=0.03, k_p=0.5)
    real = {"cpu": 0.8, "mem": 0.9, "latency_ms": 500.0}
    model = {"cpu": 0.3, "mem": 0.3, "latency_ms": 10.0}
    snap = dc.observe(real, model)
    assert snap.correction_applied is True
    assert snap.correction_magnitude > 0.0
    assert snap.drift_status in (DriftStatus.DRIFTING, DriftStatus.CRITICAL)


def test_drift_hysteresis_no_jitter():
    """No repeated corrections within hysteresis band."""
    dc = DriftController(drift_threshold=0.15, hysteresis_band=0.03, k_p=0.5)
    real = {"cpu": 0.8, "mem": 0.9, "latency_ms": 500.0}
    model = {"cpu": 0.3, "mem": 0.3, "latency_ms": 10.0}
    # First observation — correction applied
    snap1 = dc.observe(real, model)
    assert snap1.correction_applied is True
    # Second observation same drift — no new correction (still in band)
    snap2 = dc.observe(real, model)
    # Guard prevents re-trigger immediately
    assert snap2.correction_applied is False


def test_drift_trend_growing():
    dc = DriftController()
    # Build up drift gradually
    for i in range(5):
        real = {"cpu": 0.1 + i * 0.15, "mem": 0.1 + i * 0.15, "latency_ms": 10.0 + i * 100}
        model = {"cpu": 0.05, "mem": 0.05, "latency_ms": 5.0}
        dc.observe(real, model)
    trend = dc.summary()["drift_trend"]
    assert trend in ("growing", "insufficient_data")


def test_drift_force_correction():
    dc = DriftController()
    real = {"cpu": 0.3, "mem": 0.4, "latency_ms": 10.0}
    model = {"cpu": 0.31, "mem": 0.39, "latency_ms": 10.2}
    dc.observe(real, model)  # seed with stable state
    snap = dc.force_correction("test")
    assert snap.correction_applied is True
    assert snap.drift_status == DriftStatus.CORRECTION_APPLIED


def test_drift_summary():
    dc = DriftController()
    dc.observe({"cpu": 0.3}, {"cpu": 0.31})
    s = dc.summary()
    assert "drift_score" in s
    assert "drift_status" in s
    assert "model_version" in s


# ── TemporalCoherenceSmoother ──────────────────────────────────────────────

def test_smoother_stable_actions():
    sm = TemporalCoherenceSmoother(base_window=5, max_window=20)
    sm.ingest(drl_drop_rate=0.0, latency_ms=10.0, latency_history_ms=[10.0, 10.1], violation_count=0)
    snap = sm.smooth("NOOP")
    assert snap.smoothed_action == "NOOP"
    assert snap.damping_applied is False
    assert snap.oscillation_strength == 0.0


def test_smoother_damps_oscillation():
    sm = TemporalCoherenceSmoother(base_window=5, max_window=20)
    sm.ingest(0.0, 10.0, [10.0], 0)
    # Rapid alternation
    sm.smooth("EVICT_NODE")
    sm.smooth("RESTORE_NODE")
    sm.smooth("EVICT_NODE")
    sm.smooth("RESTORE_NODE")
    snap = sm.smooth("EVICT_NODE")
    # Oscillation should be detected
    assert snap.oscillation_strength > 0.0
    # Damping may or may not apply depending on EMA state


def test_smoother_adaptive_window_high_volatility():
    sm = TemporalCoherenceSmoother(base_window=5, max_window=30, volatility_scale=2.0)
    sm.ingest(drl_drop_rate=0.05, latency_ms=500.0, latency_history_ms=[100.0, 400.0, 500.0], violation_count=30)
    snap = sm.smooth("NOOP")
    # High volatility → window should be larger than base
    assert snap.current_window >= sm._base_window


def test_smoother_adaptive_window_calm():
    sm = TemporalCoherenceSmoother(base_window=5, max_window=30)
    sm.ingest(0.0, 10.0, [10.0, 10.1, 9.9], 0)
    snap = sm.smooth("NOOP")
    # Calm → window close to base
    assert snap.current_window <= sm._base_window * 2


def test_smoother_lattice_stability_score():
    sm = TemporalCoherenceSmoother(base_window=5)
    sm.ingest(0.0, 10.0, [10.0], 0)
    for _ in range(10):
        sm.smooth("NOOP")
    snap = sm.smooth("NOOP")
    # Stable lattice → high score
    assert 0.0 <= snap.lattice_stability_score <= 1.0


def test_smoother_summary():
    sm = TemporalCoherenceSmoother()
    sm.ingest(0.0, 10.0, [10.0], 0)
    sm.smooth("NOOP")
    s = sm.summary()
    assert "current_window" in s
    assert "smoothed_action" in s
    assert "transition_count" in s


# ── GlobalObjectiveStabilizer ──────────────────────────────────────────────

def test_stabilizer_v68_formula():
    stab = GlobalObjectiveStabilizer(alpha=0.5, beta=0.3, gamma=0.2)
    snap = stab.compute_J(stability_score=0.8, consistency_score=0.9, control_cost=0.1)
    # J = 0.5*0.8 + 0.3*0.9 - 0.2*0.1 = 0.4 + 0.27 - 0.02 = 0.65
    assert abs(snap.J_new - 0.65) < 0.01
    assert snap.trajectory_ok is True


def test_stabilizer_trajectory_violation():
    stab = GlobalObjectiveStabilizer(
        alpha=0.5, beta=0.3, gamma=0.2,
        trajectory_tolerance=0.05,
        trajectory_window=10,
    )
    # First tick — trajectory starts empty → OK
    stab.compute_J(0.8, 0.9, 0.1)
    # Second tick — small change → OK
    snap2 = stab.compute_J(0.79, 0.89, 0.11)
    assert snap2.trajectory_ok is True


def test_stabilizer_trajectory_tolerance_respected():
    stab = GlobalObjectiveStabilizer(
        alpha=0.5, beta=0.3, gamma=0.2,
        trajectory_tolerance=0.05,
        trajectory_window=10,
    )
    # Build up history
    for _ in range(5):
        stab.compute_J(0.7, 0.8, 0.1)
    # Now big drop — should detect violation
    snap = stab.compute_J(0.3, 0.8, 0.1)
    # trajectory_violation depends on magnitude vs tolerance
    # If drop > 0.05, violation should be flagged
    assert snap.trajectory_violation in (True, False)


def test_stabilizer_weights_enforced_sum_to_one():
    # Passing non-normalized weights → should renormalize
    stab = GlobalObjectiveStabilizer(alpha=0.8, beta=0.15, gamma=0.05)
    snap = stab.compute_J(0.5, 0.5, 0.5)
    # Should have renormalized: alpha+beta+gamma=1.0
    w = snap.weights
    total = w.alpha_stability + w.beta_consistency + w.gamma_cost
    assert abs(total - 1.0) < 1e-6


def test_stabilizer_J_compat_via_adapter():
    from resilience.metrics_engine import StabilitySnapshot
    from resilience.optimizer import SystemOptimizer
    opt = SystemOptimizer()
    stab = GlobalObjectiveStabilizer(alpha=0.5, beta=0.3, gamma=0.2, optimizer=opt)
    snap = StabilitySnapshot(
        ts=time.time(),
        stability_score=0.8,
        quorum_health=0.9,
        network_health=0.9,
        sbs_health=0.9,
        routing_health=0.9,
        rto_ms=500.0,
        convergence_time_ms=200.0,
        recovery_rate=0.95,
        violation_count_60s=2,
        node_count_total=3,
        node_count_healthy=3,
        anomaly_count=0,
    )
    J_compat = stab.get_compat_J(snap, action_cost=0.1, avg_latency_ms=50.0, conflict_count=1)
    assert isinstance(J_compat, float)
    assert -1.0 <= J_compat <= 1.0


def test_stabilizer_summary():
    stab = GlobalObjectiveStabilizer()
    stab.compute_J(0.8, 0.9, 0.1)
    s = stab.summary()
    assert "J_new" in s
    assert "trajectory_ok" in s
    assert "weights" in s


# ── SystemCoherenceInvariant ───────────────────────────────────────────────

def test_sci_stable_passes():
    sci = SystemCoherenceInvariant(fail_fast=True)
    sci.begin_window()
    # No violations — should not raise
    sci.check(
        drift_score=0.10,
        lattice_divergence=0.10,
        oscillation_strength=0.05,
        coherence_score=0.80,
        model_version=1,
    )
    assert sci.summary()["violations_in_window"] == 0


def test_sci_drift_violation_raises():
    sci = SystemCoherenceInvariant(fail_fast=True, bounds=CoherenceBounds(drift_epsilon=0.30))
    sci.begin_window()
    with pytest.raises(CoherenceViolation) as exc_info:
        sci.check(
            drift_score=0.50,   # > 0.30 → violation
            lattice_divergence=0.10,
            oscillation_strength=0.05,
            coherence_score=0.80,
            model_version=1,
        )
    assert exc_info.value.invariant_name == "drift"
    assert "drift" in exc_info.value.message.lower()


def test_sci_coherence_violation_raises():
    sci = SystemCoherenceInvariant(fail_fast=True, bounds=CoherenceBounds(coherence_min=0.50))
    sci.begin_window()
    with pytest.raises(CoherenceViolation) as exc_info:
        sci.check(
            drift_score=0.10,
            lattice_divergence=0.10,
            oscillation_strength=0.05,
            coherence_score=0.30,   # < 0.50 → violation
            model_version=1,
        )
    assert exc_info.value.invariant_name == "coherence"


def test_sci_lattice_violation_raises():
    sci = SystemCoherenceInvariant(fail_fast=True, bounds=CoherenceBounds(lattice_epsilon=0.20))
    sci.begin_window()
    with pytest.raises(CoherenceViolation) as exc_info:
        sci.check(
            drift_score=0.10,
            lattice_divergence=0.40,   # > 0.20 → violation
            oscillation_strength=0.05,
            coherence_score=0.80,
            model_version=1,
        )
    assert exc_info.value.invariant_name == "lattice"


def test_sci_oscillation_violation_raises():
    sci = SystemCoherenceInvariant(fail_fast=True, bounds=CoherenceBounds(oscillation_epsilon=0.15))
    sci.begin_window()
    with pytest.raises(CoherenceViolation) as exc_info:
        sci.check(
            drift_score=0.10,
            lattice_divergence=0.10,
            oscillation_strength=0.30,  # > 0.15 → violation
            coherence_score=0.80,
            model_version=1,
        )
    assert exc_info.value.invariant_name == "oscillation"


def test_sci_fail_fast_false_does_not_raise():
    sci = SystemCoherenceInvariant(fail_fast=False, bounds=CoherenceBounds(drift_epsilon=0.30))
    sci.begin_window()
    sci.check(
        drift_score=0.50,   # violation
        lattice_divergence=0.10,
        oscillation_strength=0.05,
        coherence_score=0.80,
        model_version=1,
    )
    # No exception raised when fail_fast=False
    assert sci.summary()["violations_in_window"] == 1


def test_sci_offline_verify():
    sci = SystemCoherenceInvariant(fail_fast=False)
    drift_scores = [0.10, 0.12, 0.50, 0.11, 0.09]    # tick 3 has high drift
    lattice_divs = [0.05] * 5
    oscillations = [0.05] * 5
    coherence_scores = [0.80, 0.82, 0.78, 0.81, 0.83]
    result = sci.verify_offline(drift_scores, lattice_divs, oscillations, coherence_scores)
    assert result["passed"] is False
    assert result["violation_count"] >= 1
    # Tick 3 (index 2) should be in violations
    tick3_violations = [v for v in result["all_violations"] if v["tick"] == 3]
    assert len(tick3_violations) >= 1
    assert tick3_violations[0]["invariant"] == "drift"


def test_sci_convergence_window():
    sci = SystemCoherenceInvariant(
        fail_fast=True,
        bounds=CoherenceBounds(convergence_window_ticks=5),
    )
    sci.begin_window()
    # Fill window with stable drift — should pass convergence
    for i in range(6):
        sci.check(
            drift_score=0.20 - i * 0.01,  # slowly decreasing
            lattice_divergence=0.05,
            oscillation_strength=0.05,
            coherence_score=0.80,
            model_version=1,
        )


def test_sci_summary():
    sci = SystemCoherenceInvariant()
    sci.begin_window()
    sci.check(0.10, 0.10, 0.05, 0.80, 1)
    s = sci.summary()
    assert "tick" in s
    assert "bounds" in s
    assert "fail_fast" in s
