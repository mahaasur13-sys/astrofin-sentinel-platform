"""
v6.8 — System Coherence Invariant (S-CI).

HARD GATE: system FAILS FAST if any coherence bound is violated.

S-CI invariant:
  For all t within window W:
    |SelfModel(t) − Reality(t)| ≤ ε_drift
    AND lattice_divergence(t) ≤ ε_lattice
    AND objective_oscillation(t) ≤ ε_oscillation

If any bound is violated → raise CoherenceViolation (assert/exception).

This is NOT logging. This is a hard execution gate.

Integration:
  - Runtime: called every tick from the MetaCoherenceController pipeline
  - Offline: verified by test suite (S-CI verifier)

Usage:
    sci = SystemCoherenceInvariant()
    sci.begin_window()
    # ... run ticks ...
    sci.check_invariants()  # raises CoherenceViolation if violated
    sci.end_window()
"""

from __future__ import annotations

import time
from dataclasses import dataclass

__all__ = ["CoherenceBounds", "CoherenceViolation", "SystemCoherenceInvariant"]


# ── Default bounds ─────────────────────────────────────────────────────────────

@dataclass
class CoherenceBounds:
    """Tunable S-CI thresholds."""
    drift_epsilon: float = 0.40          # |SelfModel − Reality| ≤ ε
    lattice_epsilon: float = 0.30        # max allowed lattice divergence
    oscillation_epsilon: float = 0.25   # max allowed oscillation strength
    coherence_min: float = 0.30           # minimum coherence_score to be coherent
    convergence_window_ticks: int = 10    # W: ticks over which convergence is measured
    # Model version divergence: max allowed gap between model version and reality version
    model_version_epsilon: int = 3


@dataclass
class CoherenceViolation(Exception):
    """Raised when S-CI is violated (hard gate triggered)."""
    invariant_name: str          # "drift" | "lattice" | "oscillation" | "coherence" | "convergence"
    message: str
    observed_value: float
    bound: float
    tick: int
    ts: float
    severity: str = "HARD_FAILURE"


class SystemCoherenceInvariant:
    """
    System-wide Coherence Invariant (S-CI) — hard gate.

    S-CI is checked every tick in the coherence pipeline.
    A CoherenceViolation exception is raised immediately if any
    bound is violated.

    This provides formal bounded self-consistency guarantees:
      - drift is bounded: |SelfModel − Reality| ≤ ε_drift
      - lattice is stable: divergence ≤ ε_lattice
      - objective is stable: oscillation ≤ ε_oscillation
      - coherence score is above minimum threshold
      - model and reality converge over the window W

    Parameters
    ----------
    bounds : CoherenceBounds, optional
        Explicit bounds. If None, uses defaults.
    fail_fast : bool
        If True (default), raises CoherenceViolation on violation.
        If False, logs but does not raise (for offline testing).
    """

    def __init__(
        self,
        bounds: CoherenceBounds | None = None,
        fail_fast: bool = True,
    ) -> None:
        self._bounds = bounds or CoherenceBounds()
        self._fail_fast = fail_fast

        self._tick = 0
        self._window_start_tick = 0
        self._window_start_time = time.monotonic()

        # Per-tick tracking for convergence check
        self._drift_history: list[float] = []
        self._lattice_div_history: list[float] = []
        self._oscillation_history: list[float] = []
        self._coherence_history: list[float] = []

        # Accumulated violations within current window
        self._violations_in_window: list[CoherenceViolation] = []

        # Last verified snapshot
        self._last_verified_tick = 0

    def begin_window(self) -> None:
        """Start a new convergence measurement window W."""
        self._window_start_tick = self._tick
        self._window_start_time = time.monotonic()
        self._violations_in_window.clear()

    def check(
        self,
        drift_score: float,
        lattice_divergence: float,
        oscillation_strength: float,
        coherence_score: float,
        model_version: int,
        reality_version: int | None = None,
    ) -> None:
        """
        Check all S-CI bounds. Raises CoherenceViolation on fail_fast=True.

        Parameters
        ----------
        drift_score : float
            Current |SelfModel − Reality| distance.
        lattice_divergence : float
            Lattice transition instability measure (0..1).
        oscillation_strength : float
            Decision oscillation strength from TemporalSmoother (0..1).
        coherence_score : float
            Overall coherence score from MetaCoherenceController (0..1).
        model_version : int
            Current self-model version.
        reality_version : int, optional
            Current observed reality version (if available).
        """
        self._tick += 1
        b = self._bounds

        # Track histories for convergence measurement
        self._drift_history.append(drift_score)
        self._lattice_div_history.append(lattice_divergence)
        self._oscillation_history.append(oscillation_strength)
        self._coherence_history.append(coherence_score)

        # Keep last W + buffer
        window_limit = b.convergence_window_ticks * 2
        self._drift_history = self._drift_history[-window_limit:]
        self._lattice_div_history = self._lattice_div_history[-window_limit:]
        self._oscillation_history = self._oscillation_history[-window_limit:]
        self._coherence_history = self._coherence_history[-window_limit:]

        violations: list[CoherenceViolation] = []

        # ── Bound checks ────────────────────────────────────────────────────

        # 1. Drift bound
        if drift_score > b.drift_epsilon:
            violations.append(CoherenceViolation(
                invariant_name="drift",
                message=(
                    f"S-CI VIOLATED: drift={drift_score:.4f} > ε={b.drift_epsilon:.4f}"
                ),
                observed_value=drift_score,
                bound=b.drift_epsilon,
                tick=self._tick,
                ts=time.time(),
            ))

        # 2. Lattice divergence bound
        if lattice_divergence > b.lattice_epsilon:
            violations.append(CoherenceViolation(
                invariant_name="lattice",
                message=(
                    f"S-CI VIOLATED: lattice_divergence={lattice_divergence:.4f}"
                    f" > ε={b.lattice_epsilon:.4f}"
                ),
                observed_value=lattice_divergence,
                bound=b.lattice_epsilon,
                tick=self._tick,
                ts=time.time(),
            ))

        # 3. Oscillation bound
        if oscillation_strength > b.oscillation_epsilon:
            violations.append(CoherenceViolation(
                invariant_name="oscillation",
                message=(
                    f"S-CI VIOLATED: oscillation={oscillation_strength:.4f}"
                    f" > ε={b.oscillation_epsilon:.4f}"
                ),
                observed_value=oscillation_strength,
                bound=b.oscillation_epsilon,
                tick=self._tick,
                ts=time.time(),
            ))

        # 4. Minimum coherence score
        if coherence_score < b.coherence_min:
            violations.append(CoherenceViolation(
                invariant_name="coherence",
                message=(
                    f"S-CI VIOLATED: coherence_score={coherence_score:.4f}"
                    f" < min={b.coherence_min:.4f}"
                ),
                observed_value=coherence_score,
                bound=b.coherence_min,
                tick=self._tick,
                ts=time.time(),
            ))

        # 5. Convergence window check (checked only when window is filled)
        if self._tick - self._window_start_tick >= b.convergence_window_ticks:
            conv_violation = self._check_convergence()
            if conv_violation:
                violations.append(conv_violation)

        # 6. Model-reality version divergence
        if (
            reality_version is not None
            and abs(model_version - reality_version) > b.model_version_epsilon
        ):
            violations.append(CoherenceViolation(
                invariant_name="convergence",
                message=(
                    f"S-CI VIOLATED: model_version={model_version} vs reality={reality_version}"
                    f" gap > ε={b.model_version_epsilon}"
                ),
                observed_value=float(abs(model_version - reality_version)),
                bound=float(b.model_version_epsilon),
                tick=self._tick,
                ts=time.time(),
            ))

        self._violations_in_window.extend(violations)
        self._last_verified_tick = self._tick

        # ── Fail fast ──────────────────────────────────────────────────────
        if violations and self._fail_fast:
            # Raise the first (highest severity) violation
            raise violations[0]

    def _check_convergence(self) -> CoherenceViolation | None:
        """
        Check that model and reality converge over the window W.

        Convergence means: drift trend is not growing continuously.
        We require that the average drift in the second half of the window
        is ≤ the average drift in the first half.

        Returns CoherenceViolation if not converging, else None.
        """
        b = self._bounds
        W = b.convergence_window_ticks
        history = self._drift_history[-W:] if len(self._drift_history) >= W else self._drift_history

        if len(history) < W:
            return None

        half = W // 2
        first_half_avg = sum(history[:half]) / half
        second_half_avg = sum(history[half:]) / (W - half)

        if second_half_avg > first_half_avg + 0.05:
            return CoherenceViolation(
                invariant_name="convergence",
                message=(
                    f"S-CI VIOLATED: drift not converging in W={W} ticks"
                    f" (first_half={first_half_avg:.4f} > second_half={second_half_avg:.4f})"
                ),
                observed_value=second_half_avg,
                bound=first_half_avg + 0.05,
                tick=self._tick,
                ts=time.time(),
            )
        return None

    def verify_offline(
        self,
        tick_drift_scores: list[float],
        tick_lattice_divs: list[float],
        tick_oscillations: list[float],
        tick_coherence_scores: list[float],
    ) -> dict:
        """
        Offline invariant verification over a full run.

        Returns dict with:
          - all_violations: list of (tick, invariant, observed, bound)
          - passed: bool
          - total_ticks: int
          - coherence_min/max/avg: statistics
        """
        violations: list[dict] = []
        b = self._bounds

        for i, (drift, latt_div, osc, coh) in enumerate(
            zip(tick_drift_scores, tick_lattice_divs, tick_oscillations, tick_coherence_scores)
        ):
            tick_violations = []

            if drift > b.drift_epsilon:
                tick_violations.append({
                    "tick": i + 1,
                    "invariant": "drift",
                    "observed": drift,
                    "bound": b.drift_epsilon,
                })
            if latt_div > b.lattice_epsilon:
                tick_violations.append({
                    "tick": i + 1,
                    "invariant": "lattice",
                    "observed": latt_div,
                    "bound": b.lattice_epsilon,
                })
            if osc > b.oscillation_epsilon:
                tick_violations.append({
                    "tick": i + 1,
                    "invariant": "oscillation",
                    "observed": osc,
                    "bound": b.oscillation_epsilon,
                })
            if coh < b.coherence_min:
                tick_violations.append({
                    "tick": i + 1,
                    "invariant": "coherence",
                    "observed": coh,
                    "bound": b.coherence_min,
                })

            violations.extend(tick_violations)

        n = len(tick_coherence_scores)
        return {
            "passed": len(violations) == 0,
            "total_ticks": n,
            "violation_count": len(violations),
            "all_violations": violations,
            "coherence_min": min(tick_coherence_scores) if n else None,
            "coherence_max": max(tick_coherence_scores) if n else None,
            "coherence_avg": sum(tick_coherence_scores) / n if n else None,
            "bounds": {
                "drift_epsilon": b.drift_epsilon,
                "lattice_epsilon": b.lattice_epsilon,
                "oscillation_epsilon": b.oscillation_epsilon,
                "coherence_min": b.coherence_min,
                "convergence_window_ticks": b.convergence_window_ticks,
            },
        }

    def get_violations_in_window(self) -> list[CoherenceViolation]:
        return list(self._violations_in_window)

    def summary(self) -> dict:
        return {
            "tick": self._tick,
            "last_verified_tick": self._last_verified_tick,
            "violations_in_window": len(self._violations_in_window),
            "drift_history_len": len(self._drift_history),
            "coherence_min": min(self._coherence_history) if self._coherence_history else None,
            "coherence_avg": (
                sum(self._coherence_history) / len(self._coherence_history)
                if self._coherence_history else None
            ),
            "bounds": {
                "drift_epsilon": self._bounds.drift_epsilon,
                "lattice_epsilon": self._bounds.lattice_epsilon,
                "oscillation_epsilon": self._bounds.oscillation_epsilon,
                "coherence_min": self._bounds.coherence_min,
            },
            "fail_fast": self._fail_fast,
        }
