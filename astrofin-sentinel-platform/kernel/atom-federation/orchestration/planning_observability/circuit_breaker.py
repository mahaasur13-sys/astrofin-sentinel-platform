"""
circuit_breaker.py — observability → actuator gateway

HARDENING PHASE 1: closes the loop between v8.1 drift detection
and the control surface (actuator / mutation_executor).

DriftProfiler.scan() → CircuitBreaker.evaluate() → actuator_signal
GovernorSignal ← CircuitBreaker.health_gate()

The circuit breaker has three states:
  CLOSED  — normal operation, mutations permitted
  OPEN    — drift severity exceeded, mutations BLOCKED
  HALF    — recovering, mutations DEFERRED until stability confirms

Transition logic:
  CLOSED → OPEN   : any drift episode with severity > open_threshold
  OPEN   → HALF   : governor signals health_score >= recovery_threshold
  HALF   → CLOSED : health >= close_threshold AND no new episodes for 2+ ticks
  HALF   → OPEN   : new drift episode while recovering
  ANY    → OPEN   : oscillation_detected = True (immediate, highest priority)

Usage:
    cb = CircuitBreaker(
        open_threshold=0.70,
        recovery_threshold=0.60,
        close_threshold=0.80,
        half_max_ticks=5,
    )

    # Each planning tick:
    episodes = profiler.scan(...)
    signal = cb.evaluate(
        drift_episodes=episodes,
        governor_signal=governor_signal,   # from StabilityGovernor
        tick=current_tick,
    )
    # signal.can_mutate → True/False
    # signal.state → CLOSED / OPEN / HALF
    # signal.block_reason → str or None
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from orchestration.v8_2a_safety_foundations import (
    GovernorDecision,
    GovernorSignal,
    StabilityGovernor,
)


class CircuitState(Enum):
    CLOSED = "closed"   # normal: mutations allowed
    OPEN   = "open"     # blocked: drift exceeded, no mutations
    HALF   = "half"     # deferred: recovering, observe only


class ActuatorSignal(Enum):
    MUTATE = "mutate"   # proceed with mutation
    BLOCK  = "block"   # hard block — governor / oscillation
    DEFER  = "defer"   # wait — in recovery zone


@dataclass
class CircuitBreakerSignal:
    """
    Output of CircuitBreaker.evaluate().
    Downstream components (actuator / mutation_executor) MUST respect this.
    """
    state: CircuitState
    actuator_signal: ActuatorSignal
    can_mutate: bool
    block_reason: str | None
    highest_severity: float
    drift_episode_count: int
    ticks_in_state: int
    recovery_ticks_remaining: int  # for HALF state


@dataclass
class CircuitBreakerConfig:
    open_threshold: float = 0.70        # severity > this → OPEN
    recovery_threshold: float = 0.60   # health >= this → allow HALF entry
    close_threshold: float = 0.80      # health >= this + stable → CLOSED
    half_max_ticks: int = 5            # max ticks in HALF before forced decision
    oscillation_immediate_open: bool = True  # oscillation → instant OPEN


class CircuitBreaker:
    """
    Observability-to-actuator gateway.

    Reads:
      - drift_episodes from DriftProfiler.scan()
      - governor_signal from StabilityGovernor

    Writes:
      - CircuitBreakerSignal for actuator / MutationExecutor

    State machine:
      CLOSED ──(severity > open_threshold)──→ OPEN
      OPEN ───(health >= recovery_threshold)──→ HALF
      HALF ───(health >= close_threshold AND stable 2+ ticks)──→ CLOSED
      HALF ───(new episode)──→ OPEN
      ANY ───(oscillation_detected)──→ OPEN (immediate)
    """

    def __init__(
        self,
        config: CircuitBreakerConfig | None = None,
        governor: StabilityGovernor | None = None,
    ):
        self.config = config or CircuitBreakerConfig()
        self.governor = governor or StabilityGovernor()

        self._state = CircuitState.CLOSED
        self._ticks_in_state = 0
        self._ticks_since_last_episode = 0
        self._last_episode_count = 0
        self._recovery_episodes_seen = 0

    # ── public API ─────────────────────────────────────────────────────────────

    def evaluate(
        self,
        drift_episodes: list,
        governor_signal: GovernorSignal,
        tick: int,
    ) -> CircuitBreakerSignal:
        """
        Main entry point. Call once per planning tick.

        Priority order:
          1. oscillation → OPEN (always, before governor)
          2. governor BLOCK/ESCALATE → OPEN
          3. state machine → CLOSED / HALF / OPEN

        Args:
            drift_episodes: output of DriftProfiler.scan()
            governor_signal: GovernorSignal from StabilityGovernor
            tick: current planning tick

        Returns:
            CircuitBreakerSignal — MUST be respected by downstream
        """
        # Count new drift episodes
        current_episode_count = len(drift_episodes)
        new_episodes = current_episode_count - self._last_episode_count
        if new_episodes > 0:
            self._ticks_since_last_episode = 0
            self._recovery_episodes_seen += new_episodes
        self._last_episode_count = current_episode_count

        highest_severity = max(
            [e.severity for e in drift_episodes],
            default=0.0,
        )

        # Priority 1: oscillation (highest — overrides everything)
        if (governor_signal.oscillation_detected
                and self.config.oscillation_immediate_open):
            return self._make_signal(
                CircuitState.OPEN,
                ActuatorSignal.BLOCK,
                "oscillation_detected",
                highest_severity,
                current_episode_count,
            )

        # Priority 2: governor hard-block
        gov_decision = self.governor.evaluate(governor_signal)
        if gov_decision in (GovernorDecision.BLOCK, GovernorDecision.ESCALATE):
            return self._make_signal(
                CircuitState.OPEN,
                ActuatorSignal.BLOCK,
                f"governor_{gov_decision.value.lower()}",
                highest_severity,
                current_episode_count,
            )

        # Priority 3: state machine (advanced tick counter)
        self._ticks_in_state += 1
        prev_state = self._state
        self._advance_state(highest_severity, governor_signal)

        # Reset tick counter on HALF entry for clean countdown
        if self._state == CircuitState.HALF and prev_state != CircuitState.HALF:
            self._ticks_in_state = 0

        # Determine actuator signal
        if self._state == CircuitState.OPEN:
            return self._make_signal(
                CircuitState.OPEN,
                ActuatorSignal.BLOCK,
                "circuit_open",
                highest_severity,
                current_episode_count,
            )
        if self._state == CircuitState.HALF:
            if governor_signal.health_score >= self.config.close_threshold:
                return self._make_signal(
                    CircuitState.HALF, ActuatorSignal.MUTATE, None,
                    highest_severity, current_episode_count,
                )
            return self._make_signal(
                CircuitState.HALF, ActuatorSignal.DEFER, "half_recovery_pending",
                highest_severity, current_episode_count,
            )
        # CLOSED
        return self._make_signal(
            CircuitState.CLOSED, ActuatorSignal.MUTATE, None,
            highest_severity, current_episode_count,
        )

    @property
    def state(self) -> CircuitState:
        return self._state

    def reset(self) -> None:
        """Reset circuit to CLOSED. For testing or operator override."""
        self._state = CircuitState.CLOSED
        self._ticks_in_state = 0
        self._ticks_since_last_episode = 0
        self._last_episode_count = 0
        self._recovery_episodes_seen = 0

    # ── state machine ───────────────────────────────────────────────────────────

    def _advance_state(
        self,
        highest_severity: float,
        governor_signal: GovernorSignal,
    ) -> None:
        cfg = self.config

        if self._state == CircuitState.CLOSED:
            if highest_severity >= cfg.open_threshold:
                self._set_state(CircuitState.OPEN)

        elif self._state == CircuitState.OPEN:
            if governor_signal.health_score >= cfg.recovery_threshold:
                self._set_state(CircuitState.HALF)

        elif self._state == CircuitState.HALF:
            # New episode during recovery → immediate OPEN
            if self._ticks_since_last_episode == 0:
                self._set_state(CircuitState.OPEN)
                return

            # Tick timeout: we've been in HALF long enough
            # CLOSED if healthy and timeout reached; else force OPEN
            if self._ticks_in_state >= cfg.half_max_ticks:
                if governor_signal.health_score >= cfg.close_threshold:
                    self._set_state(CircuitState.CLOSED)
                else:
                    self._set_state(CircuitState.OPEN)
                return

            # Normal HALF → CLOSED: healthy enough + sustained for half_max_ticks
            # (ticks_in_state already tracks continuous HALF duration)
            if governor_signal.health_score >= cfg.close_threshold:
                if self._ticks_in_state >= cfg.half_max_ticks:
                    self._set_state(CircuitState.CLOSED)

    def _set_state(self, new_state: CircuitState) -> None:
        if self._state != new_state:
            self._state = new_state
            self._ticks_in_state = 0
            if new_state == CircuitState.HALF:
                self._recovery_episodes_seen = 0
                # At least 1 recovery tick has elapsed (the one that triggered entry)
                self._ticks_since_last_episode = 1

    # ── signal builder ─────────────────────────────────────────────────────────

    def _make_signal(
        self,
        state: CircuitState,
        actuator_signal: ActuatorSignal,
        block_reason: str | None,
        highest_severity: float,
        episode_count: int,
    ) -> CircuitBreakerSignal:
        cfg = self.config
        remaining = cfg.half_max_ticks - self._ticks_in_state
        return CircuitBreakerSignal(
            state=state,
            actuator_signal=actuator_signal,
            can_mutate=(actuator_signal == ActuatorSignal.MUTATE),
            block_reason=block_reason,
            highest_severity=highest_severity,
            drift_episode_count=episode_count,
            ticks_in_state=self._ticks_in_state,
            recovery_ticks_remaining=max(0, remaining),
        )

    # ── explain ─────────────────────────────────────────────────────────────────

    def explain(self, signal: CircuitBreakerSignal) -> str:
        parts = [
            f"[{signal.state.value.upper()}]",
            f"actuator={signal.actuator_signal.value}",
            f"can_mutate={signal.can_mutate}",
        ]
        if signal.block_reason:
            parts.append(f"reason={signal.block_reason}")
        parts.append(f"severity={signal.highest_severity:.3f}")
        parts.append(f"episodes={signal.drift_episode_count}")
        if signal.state == CircuitState.HALF:
            parts.append(f"recovery_ticks_left={signal.recovery_ticks_remaining}")
        return " ".join(parts)
