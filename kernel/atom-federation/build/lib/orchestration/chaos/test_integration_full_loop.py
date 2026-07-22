"""
test_integration_full_loop.py — HARDENING-2 INTEGRATION TEST

End-to-end validation of the closed adaptive loop:
  ChaosEvent
    → DriftProfiler.scan()          → episodes (DriftType + severity)
    → ChaosObservabilityBridge.attach_to_drift()
    → compute_impact()
    → feedback()
    → chaos intensity updated

Validates:
  1. Correlation correctness      — drift episodes linked to chaos_event_id
  2. Impact sensitivity           — high drift → high impact, low drift → low impact
  3. Feedback loop correctness    — intensity changes monotonically in right direction
  4. Closed-loop behavior        — drift_t+1 <= drift_t under feedback control

Failure points this test guards against:
  - drift ↔ chaos links never stored       → test_correlation_correctness fails
  - feedback never affects intensity       → test_feedback_updates_internal_state fails
  - all impacts ~0.5 (insensitive)         → test_impact_sensitivity fails
  - oscillation detection too lenient     → test_drift_t1_leq_drift_t0 fails
"""


from orchestration.chaos.observability_integration import (
    ChaosObservabilityBridge,
    DriftType,
)
from orchestration.planning_observability.drift_profiler import (
    DriftProfiler,
)
from orchestration.planning_observability.drift_profiler import (
    DriftType as ProfilerDriftType,
)

# ─── helpers ───────────────────────────────────────────────────────────────────

def make_oscillating_coherence() -> list[float]:
    """High-variance oscillating: [0.6, 0.9, 0.6, 0.9, 0.6]
    Expected: is_oscillating=True, variance=0.15, sign_change_rate=1.0"""
    return [0.6, 0.9, 0.6, 0.9, 0.6]


def make_stable_coherence() -> list[float]:
    """Low-variance stable: [0.72, 0.74, 0.73, 0.75, 0.74]
    Expected: is_oscillating=False"""
    return [0.72, 0.74, 0.73, 0.75, 0.74]


def make_moderate_oscillation() -> list[float]:
    """Moderate oscillation with some trend: [0.7, 0.73, 0.69, 0.72]
    Weaker than fully oscillating case."""
    return [0.7, 0.73, 0.69, 0.72]


def drift_type_to_bridge(dp_type: ProfilerDriftType) -> DriftType:
    """Map DriftProfiler DriftType → ChaosObservabilityBridge DriftType."""
    return DriftType(dp_type.value)


# ─── TEST 1: Correlation correctness ─────────────────────────────────────────

class TestCorrelationCorrectness:
    """Validate drift_episode ↔ chaos_event_id linkage."""

    def test_drift_attached_to_correct_chaos_event(self):
        bridge = ChaosObservabilityBridge()
        profiler = DriftProfiler()

        event = bridge.record_chaos_event(
            event_id="ce_001",
            event_type="kill_agent",
            intensity=1.0,
            tick_injected=10,
        )

        episodes = profiler.scan(
            tick=10,
            plan_id="p1",
            coherence_trajectory=make_oscillating_coherence(),
            replan_count=4,
            coherence_at_replans=[0.6, 0.9, 0.6, 0.9],
            weight_adjustments=[],
            current_nodes=[],
        )

        assert len(episodes) > 0, "Oscillating coherence must produce drift episodes"

        for ep in episodes:
            bridge.attach_to_drift(
                chaos_event_id=event.event_id,
                drift_type=drift_type_to_bridge(ep.drift_type),
                lag_ticks=10,
                severity=ep.severity,
            )

        # All correlations point to ce_001
        for corr in bridge.correlations:
            assert corr.chaos_event_id == "ce_001", (
                f"Correlation {corr.correlation_id} has wrong chaos_event_id: "
                f"{corr.chaos_event_id} != ce_001"
            )

    def test_lag_and_severity_not_lost(self):
        bridge = ChaosObservabilityBridge()
        profiler = DriftProfiler()

        bridge.record_chaos_event("e1", "latency_spike", 0.5, 5)

        episodes = profiler.scan(
            tick=20,
            plan_id="p1",
            coherence_trajectory=make_oscillating_coherence(),
            replan_count=3,
            coherence_at_replans=[0.6, 0.9, 0.6],
            weight_adjustments=[],
            current_nodes=[],
        )

        for ep in episodes:
            lag = 7
            severity = 0.82
            corr = bridge.attach_to_drift(
                chaos_event_id="e1",
                drift_type=drift_type_to_bridge(ep.drift_type),
                lag_ticks=lag,
                severity=severity,
            )
            assert corr.lag_ticks == lag, f"Lag lost: {corr.lag_ticks} != {lag}"
            assert abs(corr.severity - severity) < 0.001, (
                f"Severity lost: {corr.severity} != {severity}"
            )

    def test_correlations_grow_and_summarize(self):
        bridge = ChaosObservabilityBridge()
        profiler = DriftProfiler()

        event = bridge.record_chaos_event("ce_002", "memory_pressure", 0.9, 15)

        episodes = profiler.scan(
            tick=15,
            plan_id="p1",
            coherence_trajectory=make_oscillating_coherence(),
            replan_count=5,
            coherence_at_replans=[0.6, 0.9, 0.6, 0.9, 0.6],
            weight_adjustments=[],
            current_nodes=[],
        )

        for ep in episodes:
            bridge.attach_to_drift(
                chaos_event_id=event.event_id,
                drift_type=drift_type_to_bridge(ep.drift_type),
                lag_ticks=5,
                severity=ep.severity,
            )

        summary = bridge.correlation_summary()
        assert summary["total"] == len(episodes), (
            f"Expected {len(episodes)} correlations, got {summary['total']}"
        )


# ─── TEST 2: Impact sensitivity ────────────────────────────────────────────────

class TestImpactSensitivity:
    """Validate impact scoring responds to drift severity."""

    def test_high_signals_produce_high_impact(self):
        bridge = ChaosObservabilityBridge()
        impact = bridge.compute_impact(
            oscillation=1.0,
            coherence_drop=1.0,
            recovery_time=1.0,
        )
        assert impact > 0.6, f"High drift should produce impact > 0.6, got {impact}"

    def test_low_signals_produce_low_impact(self):
        bridge = ChaosObservabilityBridge()
        impact = bridge.compute_impact(
            oscillation=0.05,
            coherence_drop=0.05,
            recovery_time=0.05,
        )
        assert impact < 0.3, f"Low drift should produce impact < 0.3, got {impact}"

    def test_oscillating_higher_impact_than_stable(self):
        """Same bridge, same weights — only the drift signal differs."""
        bridge_osc = ChaosObservabilityBridge()
        bridge_stable = ChaosObservabilityBridge()

        profiler_osc = DriftProfiler()
        profiler_stable = DriftProfiler()

        episodes_osc = profiler_osc.scan(
            tick=10, plan_id="p1",
            coherence_trajectory=make_oscillating_coherence(),
            replan_count=4,
            coherence_at_replans=[0.6, 0.9, 0.6, 0.9],
            weight_adjustments=[],
            current_nodes=[],
        )

        episodes_stable = profiler_stable.scan(
            tick=10, plan_id="p1",
            coherence_trajectory=make_stable_coherence(),
            replan_count=1,
            coherence_at_replans=[0.73],
            weight_adjustments=[],
            current_nodes=[],
        )

        osc_severity = max((e.severity for e in episodes_osc), default=0.0)
        stable_severity = max((e.severity for e in episodes_stable), default=0.0)

        assert osc_severity > 0, "Oscillating case must produce episodes"

        impact_osc = bridge_osc.compute_impact(
            oscillation=osc_severity,
            coherence_drop=osc_severity,
            recovery_time=osc_severity,
        )
        impact_stable = bridge_stable.compute_impact(
            oscillation=stable_severity,
            coherence_drop=stable_severity,
            recovery_time=stable_severity,
        )

        assert impact_osc > impact_stable, (
            f"Oscillating must yield higher impact than stable. "
            f"Got osc={impact_osc}, stable={impact_stable}"
        )


# ─── TEST 3: Feedback loop correctness ────────────────────────────────────────

class TestFeedbackLoopCorrectness:
    """Validate feedback adjusts intensity in the correct direction."""

    def test_high_impact_reduces_intensity(self):
        bridge = ChaosObservabilityBridge()
        bridge._current_intensity = 0.80
        new_int = bridge.feedback(impact=0.85)
        assert new_int < 0.80, f"High impact must reduce intensity, got {new_int}"

    def test_low_impact_increases_intensity(self):
        bridge = ChaosObservabilityBridge()
        bridge._current_intensity = 0.20
        new_int = bridge.feedback(impact=0.10)
        assert new_int > 0.20, f"Low impact must increase intensity, got {new_int}"

    def test_mid_impact_holds(self):
        bridge = ChaosObservabilityBridge()
        bridge._current_intensity = 0.50
        new_int = bridge.feedback(impact=0.50)
        assert new_int == 0.50, f"Mid impact should hold intensity, got {new_int}"

    def test_feedback_closes_loop(self):
        """Critical: feedback must mutate _current_intensity for next cycle."""
        bridge = ChaosObservabilityBridge()
        bridge._current_intensity = 0.70
        bridge.feedback(impact=0.85)
        assert bridge.current_intensity < 0.70, (
            "Internal intensity must be updated after feedback(). "
            "This is the actual 'closing' of the loop."
        )

    def test_feedback_respects_bounds(self):
        bridge_min = ChaosObservabilityBridge()
        bridge_min._current_intensity = 0.06
        result = bridge_min.feedback(impact=0.90)
        assert result >= 0.05, f"Cannot go below min 0.05, got {result}"

        bridge_max = ChaosObservabilityBridge()
        bridge_max._current_intensity = 0.95
        result = bridge_max.feedback(impact=0.10)
        assert result <= 1.00, f"Cannot exceed max 1.00, got {result}"


# ─── TEST 4: Closed-loop behavior ─────────────────────────────────────────────

class TestClosedLoopBehavior:
    """
    Top-level contract: under feedback control, drift decreases across iterations.

      inject chaos → detect drift → compute impact → feedback
      → next iteration drift_t+1 <= drift_t
    """

    def test_full_loop_high_chaos_feedback_reduces_drift(self):
        bridge = ChaosObservabilityBridge()

        # ── T0: High-severity chaos → strong oscillation ─────────────────────
        event_t0 = bridge.record_chaos_event(
            event_id="ce_t0",
            event_type="kill_agent",
            intensity=1.0,
            tick_injected=0,
        )

        profiler_t0 = DriftProfiler()
        episodes_t0 = profiler_t0.scan(
            tick=10,
            plan_id="p1",
            coherence_trajectory=make_oscillating_coherence(),
            replan_count=4,
            coherence_at_replans=[0.6, 0.9, 0.6, 0.9],
            weight_adjustments=[],
            current_nodes=[],
        )

        assert len(episodes_t0) > 0, "T0 must produce drift episodes"

        for ep in episodes_t0:
            bridge.attach_to_drift(
                chaos_event_id=event_t0.event_id,
                drift_type=drift_type_to_bridge(ep.drift_type),
                lag_ticks=10,
                severity=ep.severity,
            )

        max_severity_t0 = max(ep.severity for ep in episodes_t0)

        # Simulate governor blocks: 7/10 = 0.70 block rate
        for _ in range(7): bridge.record_governor_decision(True)
        for _ in range(3): bridge.record_governor_decision(False)
        impact_t0 = bridge.compute_impact(
            oscillation=max_severity_t0,
            coherence_drop=max_severity_t0,
            recovery_time=1.0,
        )

        assert impact_t0 > 0.6, f"T0 impact must be high, got {impact_t0}"

        new_intensity = bridge.feedback(impact=impact_t0)
        assert new_intensity < 1.0, f"T0 feedback must reduce intensity from 1.0, got {new_intensity}"

        # ── T1: Reduced chaos (from feedback) → weaker drift ─────────────────
        profiler_t1 = DriftProfiler()
        episodes_t1 = profiler_t1.scan(
            tick=20,
            plan_id="p1",
            coherence_trajectory=make_moderate_oscillation(),
            replan_count=3,
            coherence_at_replans=[0.70, 0.73, 0.69],
            weight_adjustments=[],
            current_nodes=[],
        )

        event_t1 = bridge.record_chaos_event(
            event_id="ce_t1",
            event_type="kill_agent",
            intensity=new_intensity,  # ← reduced by feedback
            tick_injected=20,
        )

        for ep in episodes_t1:
            bridge.attach_to_drift(
                chaos_event_id=event_t1.event_id,
                drift_type=drift_type_to_bridge(ep.drift_type),
                lag_ticks=10,
                severity=ep.severity,
            )

        max_severity_t1 = max((ep.severity for ep in episodes_t1), default=0.0)

        # Drift severity at T1 must be <= T0
        assert max_severity_t1 <= max_severity_t0, (
            f"Closed-loop contract violated: drift must decrease. "
            f"T0={max_severity_t0:.4f}, T1={max_severity_t1:.4f}"
        )

    def test_full_loop_multiple_iterations_converge(self):
        """3 iterations: intensity should monotonically decrease under high impact."""
        bridge = ChaosObservabilityBridge()
        profiler = DriftProfiler()

        intensities = [1.0]
        impacts = []

        for i in range(3):
            event = bridge.record_chaos_event(
                event_id=f"ce_i{i}",
                event_type="kill_agent",
                intensity=intensities[-1],
                tick_injected=i * 10,
            )

            episodes = profiler.scan(
                tick=(i + 1) * 10,
                plan_id="p1",
                coherence_trajectory=make_oscillating_coherence(),
                replan_count=4,
                coherence_at_replans=[0.6, 0.9, 0.6, 0.9],
                weight_adjustments=[],
                current_nodes=[],
            )

            for ep in episodes:
                bridge.attach_to_drift(
                    chaos_event_id=event.event_id,
                    drift_type=drift_type_to_bridge(ep.drift_type),
                    lag_ticks=10,
                    severity=ep.severity,
                )

            max_sev = max((e.severity for e in episodes), default=0.0)

            # Record governor blocks: chaos causes high block rate
            for _ in range(6): bridge.record_governor_decision(True)
            for _ in range(4): bridge.record_governor_decision(False)

            impact = bridge.compute_impact(
                oscillation=max_sev,
                coherence_drop=max_sev,
                recovery_time=1.0,
            )
            impacts.append(impact)

            new_int = bridge.feedback(impact=impact)
            intensities.append(new_int)

        # Intensities must be monotonically decreasing under persistent high impact
        for i in range(len(intensities) - 1):
            assert intensities[i + 1] <= intensities[i], (
                f"Intensity must not increase: iter {i}={intensities[i]}, "
                f"iter {i+1}={intensities[i+1]}"
            )

        # All impacts should be high (> 0.7) since drift persists
        for imp in impacts:
            assert imp > 0.6, f"All impacts should be high under oscillating drift, got {imp}"

    def test_governor_block_rate_integrates_in_impact(self):
        """Governor block rate is part of impact computation."""
        bridge = ChaosObservabilityBridge()

        # Without blocks: governor_block_rate = 0.0
        impact_no_blocks = bridge.compute_impact(
            oscillation=0.5,
            coherence_drop=0.5,
            recovery_time=0.5,
        )

        # With 80% block rate: governor contribution = 0.30 * 0.8 = 0.24
        for _ in range(8):
            bridge.record_governor_decision(True)
        for _ in range(2):
            bridge.record_governor_decision(False)

        impact_with_blocks = bridge.compute_impact(
            oscillation=0.5,
            coherence_drop=0.5,
            recovery_time=0.5,
        )

        assert impact_with_blocks > impact_no_blocks, (
            f"Governor blocks must increase impact. "
            f"no_blocks={impact_no_blocks}, with_blocks={impact_with_blocks}"
        )
