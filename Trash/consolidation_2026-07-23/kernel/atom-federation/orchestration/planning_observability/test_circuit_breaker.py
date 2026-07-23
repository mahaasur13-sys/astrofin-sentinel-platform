"""
test_circuit_breaker.py — HARDENING PHASE 1
Circuit breaker: observability → actuator gateway
"""
from orchestration.planning_observability.circuit_breaker import (
    ActuatorSignal,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
)
from orchestration.planning_observability.drift_profiler import (
    DriftEpisode,
    DriftType,
)
from orchestration.v8_2a_safety_foundations import (
    GovernorSignal,
    GovernorThresholds,
    StabilityGovernor,
)


def _drift_episode(severity: float) -> DriftEpisode:
    return DriftEpisode(
        drift_type=DriftType.OSCILLATING_PLAN,
        start_tick=0,
        end_tick=10,
        severity=severity,
        description="test",
        evidence={},
    )


def _gov_signal(
    health: float = 0.8,
    drift_severity: float = 0.2,
    oscillation: bool = False,
    mutation_density: float = 0.1,
) -> GovernorSignal:
    return GovernorSignal(
        health_score=health,
        plan_stability_index=0.85,
        coherence_drop_rate=0.1,
        drift_severity=drift_severity,
        oscillation_detected=oscillation,
        recent_mutation_density=mutation_density,
    )


class TestCircuitBreakerClosed:
    """Circuit starts CLOSED and stays CLOSED under healthy conditions."""

    def test_initial_state_is_closed(self):
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED

    def test_healthy_signal_stays_closed(self):
        cb = CircuitBreaker()
        sig = _gov_signal(health=0.8, drift_severity=0.2)
        result = cb.evaluate([], sig, tick=1)
        assert result.state == CircuitState.CLOSED
        assert result.can_mutate is True

    def test_low_severity_stays_closed(self):
        cb = CircuitBreaker(CircuitBreakerConfig(open_threshold=0.70))
        sig = _gov_signal(health=0.8)
        result = cb.evaluate([_drift_episode(0.3), _drift_episode(0.4)], sig, tick=1)
        assert result.state == CircuitState.CLOSED
        assert result.can_mutate is True


class TestCircuitBreakerOpen:
    """Circuit opens when drift severity exceeds threshold."""

    def test_high_severity_opens_circuit(self):
        cb = CircuitBreaker(CircuitBreakerConfig(open_threshold=0.70))
        sig = _gov_signal(health=0.8)
        result = cb.evaluate([_drift_episode(0.75)], sig, tick=1)
        assert result.state == CircuitState.OPEN
        assert result.can_mutate is False
        assert result.block_reason == "circuit_open"

    def test_oscillation_immediate_open(self):
        cb = CircuitBreaker()
        sig = _gov_signal(health=0.8, oscillation=True)
        result = cb.evaluate([], sig, tick=1)
        assert result.state == CircuitState.OPEN
        assert result.can_mutate is False
        assert result.block_reason == "oscillation_detected"

    def test_governor_block_triggers_open(self):
        cb = CircuitBreaker()
        gov = StabilityGovernor(GovernorThresholds(health_block=0.5))
        cb.governor = gov
        sig = _gov_signal(health=0.2)  # below health_block
        result = cb.evaluate([], sig, tick=1)
        assert result.state == CircuitState.OPEN
        assert result.actuator_signal == ActuatorSignal.BLOCK


class TestCircuitBreakerHalf:
    """Recovery: OPEN → HALF → CLOSED path."""

    def test_open_to_half_on_recovery_health(self):
        cb = CircuitBreaker(CircuitBreakerConfig(
            open_threshold=0.60,
            recovery_threshold=0.60,
            close_threshold=0.80,
            half_max_ticks=5,
        ))
        # Push to OPEN
        sig1 = _gov_signal(health=0.8)
        cb.evaluate([_drift_episode(0.75)], sig1, tick=1)
        assert cb.state == CircuitState.OPEN

        # Recover health → HALF
        sig2 = _gov_signal(health=0.65)
        result = cb.evaluate([], sig2, tick=2)
        assert result.state == CircuitState.HALF

    def test_half_closes_when_health_recovered_and_stable(self):
        cb = CircuitBreaker(CircuitBreakerConfig(
            open_threshold=0.60,
            recovery_threshold=0.60,
            close_threshold=0.80,
            half_max_ticks=3,  # 3 HALF ticks with health → CLOSED
        ))
        # OPEN
        sig1 = _gov_signal(health=0.8)
        cb.evaluate([_drift_episode(0.75)], sig1, tick=1)
        # HALF (tick_in_state=0 after transition)
        sig2 = _gov_signal(health=0.65)
        cb.evaluate([], sig2, tick=2)
        # Stable and healthy: HALF for 3 ticks → CLOSED
        sig3 = _gov_signal(health=0.85)
        cb.evaluate([], sig3, tick=3)   # HALF tics=1
        cb.evaluate([], sig3, tick=4)   # HALF tics=2
        cb.evaluate([], sig3, tick=5)   # HALF tics=3 >= half_max_ticks(3) + healthy → CLOSED
        assert cb.state == CircuitState.CLOSED

    def test_half_reopens_on_new_episode(self):
        cb = CircuitBreaker(CircuitBreakerConfig(
            open_threshold=0.60,
            recovery_threshold=0.60,
            close_threshold=0.80,
            half_max_ticks=5,
        ))
        # OPEN
        sig1 = _gov_signal(health=0.8)
        cb.evaluate([_drift_episode(0.75)], sig1, tick=1)
        # HALF
        sig2 = _gov_signal(health=0.65)
        cb.evaluate([], sig2, tick=2)
        # New episode while HALF → back to OPEN
        sig3 = _gov_signal(health=0.65)
        result = cb.evaluate([_drift_episode(0.4)], sig3, tick=3)
        assert result.state == CircuitState.OPEN

    def test_half_forces_close_on_tick_timeout(self):
        cb = CircuitBreaker(CircuitBreakerConfig(
            open_threshold=0.60,
            recovery_threshold=0.50,
            close_threshold=0.80,
            half_max_ticks=3,  # force-close fires when remaining <= 0
        ))
        sig1 = _gov_signal(health=0.8)
        cb.evaluate([_drift_episode(0.75)], sig1, tick=1)  # OPEN
        sig2 = _gov_signal(health=0.60)
        cb.evaluate([], sig2, tick=2)  # HALF (tick_in_state=0)
        cb.evaluate([], sig2, tick=3)  # HALF (tick_in_state=1, remaining=2)
        cb.evaluate([], sig2, tick=4)  # HALF (tick_in_state=2, remaining=1)
        sig5 = _gov_signal(health=0.60)  # health < close_threshold=0.80
        cb.evaluate([], sig5, tick=5)  # HALF(3) remaining=0 → force OPEN
        assert cb.state == CircuitState.OPEN


class TestCircuitBreakerSignal:
    """CircuitBreakerSignal carries correct metadata."""

    def test_signal_reflects_highest_severity(self):
        cb = CircuitBreaker(CircuitBreakerConfig(open_threshold=0.50))
        sig = _gov_signal(health=0.8)
        result = cb.evaluate([_drift_episode(0.3), _drift_episode(0.7)], sig, tick=1)
        assert result.highest_severity == 0.7

    def test_signal_tracks_episode_count(self):
        cb = CircuitBreaker(CircuitBreakerConfig(open_threshold=0.50))
        sig = _gov_signal(health=0.8)
        result = cb.evaluate([_drift_episode(0.3), _drift_episode(0.5), _drift_episode(0.7)], sig, tick=1)
        assert result.drift_episode_count == 3

    def test_recovery_ticks_remaining_decrements(self):
        cb = CircuitBreaker(CircuitBreakerConfig(
            open_threshold=0.60,
            recovery_threshold=0.60,
            close_threshold=0.80,
            half_max_ticks=5,
        ))
        sig1 = _gov_signal(health=0.8)
        cb.evaluate([_drift_episode(0.75)], sig1, tick=1)
        sig2 = _gov_signal(health=0.65)
        result = cb.evaluate([], sig2, tick=2)
        assert result.state == CircuitState.HALF
        assert result.recovery_ticks_remaining == 5


class TestCircuitBreakerExplain:
    def test_explain_closed(self):
        cb = CircuitBreaker()
        sig = _gov_signal(health=0.8)
        result = cb.evaluate([], sig, tick=1)
        explanation = cb.explain(result)
        assert "CLOSED" in explanation
        assert "mutate" in explanation

    def test_explain_open(self):
        cb = CircuitBreaker()
        sig = _gov_signal(health=0.8, oscillation=True)
        result = cb.evaluate([], sig, tick=1)
        explanation = cb.explain(result)
        assert "OPEN" in explanation
        assert "oscillation" in explanation


class TestCircuitBreakerReset:
    def test_reset_returns_to_closed(self):
        cb = CircuitBreaker(CircuitBreakerConfig(open_threshold=0.60))
        sig = _gov_signal(health=0.8)
        cb.evaluate([_drift_episode(0.75)], sig, tick=1)
        assert cb.state == CircuitState.OPEN
        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb._ticks_in_state == 0
