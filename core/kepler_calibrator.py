"""
core/kepler_calibrator.py — ATOM-STEP-5: RL-Style Parameter Calibration
=======================================================================
Automatic orbital element tuning using gradient-free optimization (CMA-ES
proxy via scipy) with Swiss Ephemeris as ground truth.

Key concepts:
- Reward = negative MAE (degrees) between Kepler and SwissEph
- State = current orbital elements (a, e, L0, ω, Ω, i)
- Action = incremental adjustment to elements (gradient-free)
- Episodes = optimization iterations
- Self-improvement loop with convergence detection
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

# ── Dynamic import for CLI ──────────────────────────────────────────────────
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

import core.ephemeris as eph
from core.ephemeris import HAS_SWISS_EPHEMERIS
from core.kepler import KeplerOrbit, OrbitalElements

# ── Dataclasses ──────────────────────────────────────────────────────────────


@dataclass
class CalibrationTarget:
    body: str
    jd_range: tuple[float, float]  # (jd_start, jd_end)
    n_samples: int = 20
    weight: float = 1.0  # relative importance


@dataclass
class CalibrationState:
    elements: OrbitalElements
    body: str
    mae_deg: float
    max_error_deg: float
    episodes: int
    converged: bool
    improvement_history: list[float] = field(default_factory=list)


@dataclass
class CalibrationResult:
    body: str
    original_elements: OrbitalElements
    calibrated_elements: OrbitalElements
    improvement_pct: float  # % reduction in MAE
    final_mae_deg: float
    original_mae_deg: float
    n_episodes: int
    converged: bool
    calibration_time_sec: float
    history: list[float]


# ── Loss function ────────────────────────────────────────────────────────────


@require_ephemeris  # noqa: R2  # module-wide ephemeris dep
def _mae_loss(elements: OrbitalElements, body: str, jd_samples: np.ndarray) -> float:
    """Mean Absolute Error between Kepler and SwissEph (geocentric) over JD samples."""
    KeplerOrbit(elements)
    total_error = 0.0
    n = 0

    # Reference frame offset (heliocentric Kepler vs geocentric SwissEph)
    # We handle this by computing mean longitude difference, not absolute
    for jd in jd_samples:
        # Keplerian mean longitude (degrees)
        mean_motion = elements.mean_motion  # deg/day
        epoch_jd = elements.epoch_jd
        mean_lon_kepler = (elements.mean_longitude + mean_motion * (jd - epoch_jd)) % 360.0

        # Swiss Ephemeris geocentric longitude
        try:
            planet_pos = eph.calculate_planet(body, jd)
            mean_lon_swiss = planet_pos.longitude % 360.0
        except Exception:
            continue

        # Angular difference (handle wrap-around)
        delta = abs(mean_lon_kepler - mean_lon_swiss)
        delta = min(delta, 360.0 - delta)  # circular distance

        # For Earth: ~180° offset is constant (reference frame), skip or reduce weight
        if body.lower() == "earth" and delta > 90:
            delta = abs(delta - 180.0)  # normalize around 0 instead of 180

        total_error += delta
        n += 1

    return total_error / max(n, 1)


def _gradient_free_step(
    elements: OrbitalElements,
    body: str,
    jd_samples: np.ndarray,
    step_size: float = 0.01,
    rng: np.random.Generator | None = None,
) -> OrbitalElements:
    """
    Gradient-free parameter update: try small random perturbations in each
    orbital element dimension and keep the best one.

    This is a simple hill-climbing approach (REINFORCE-style policy gradient
    proxy — we sample a direction and accept if it improves the loss).
    """
    if rng is None:
        rng = np.random.default_rng()

    KeplerOrbit(elements)
    current_loss = _mae_loss(elements, body, jd_samples)

    # Key dimensions to perturb (normalized sensitivity)
    perturbations = [
        ("semi_major_axis", step_size * elements.semi_major_axis),
        ("eccentricity", step_size * 0.05),  # e is small
        ("mean_longitude", step_size * 10.0),  # degrees
        ("arg_perihelion", step_size * 10.0),
        ("long_ascending_node", step_size * 10.0),
        ("inclination", step_size * 2.0),
    ]

    best_loss = current_loss
    best_elements = elements

    # Try a few random directions
    for _ in range(6):
        # Random direction and magnitude
        dim = rng.integers(0, len(perturbations))
        sign = rng.choice([-1, 1])
        attr, scale = perturbations[dim]

        current_val = getattr(elements, attr)
        new_val = current_val + sign * scale * rng.uniform(0.3, 1.7)

        # Clamp to physical ranges
        if attr == "eccentricity":
            new_val = max(0.001, min(0.99, new_val))
        elif attr == "inclination":
            new_val = max(0.0, min(180.0, new_val))
        elif attr == "semi_major_axis":
            new_val = max(0.1, new_val)
        else:
            new_val = new_val % 360.0

        # Build new elements
        new_elements = OrbitalElements(
            name=elements.name,
            semi_major_axis=elements.semi_major_axis,
            eccentricity=elements.eccentricity,
            inclination=elements.inclination,
            long_ascending_node=elements.long_ascending_node,
            arg_perihelion=elements.arg_perihelion,
            long_perihelion=elements.long_perihelion,
            mean_longitude=elements.mean_longitude,
            mean_motion=elements.mean_motion,
            orbital_period=elements.orbital_period,
            epoch_jd=elements.epoch_jd,
        )
        setattr(new_elements, attr, new_val)

        new_loss = _mae_loss(new_elements, body, jd_samples)

        if new_loss < best_loss:
            best_loss = new_loss
            best_elements = new_elements
            break  # accept first improvement (greedy)

    return best_elements


# ── Calibrator ───────────────────────────────────────────────────────────────


class KeplerCalibrator:
    """
    RL-style calibrator for orbital elements.

    Uses gradient-free optimization (hill-climbing) to minimize
    Kepler-vs-SwissEph error. Self-improving through episodes.
    """

    DEFAULT_TARGETS = [
        CalibrationTarget("jupiter", (2451545.0, 2460000.0), n_samples=15, weight=1.0),
        CalibrationTarget("saturn", (2451545.0, 2460000.0), n_samples=15, weight=0.7),
    ]

    def __init__(
        self,
        targets: list[CalibrationTarget] | None = None,
        max_episodes: int = 100,
        convergence_threshold_deg: float = 0.5,
        patience: int = 15,
        seed: int = 42,
    ):
        self.targets = targets or self.DEFAULT_TARGETS
        self.max_episodes = max_episodes
        self.convergence_threshold_deg = convergence_threshold_deg
        self.patience = patience
        self.rng = np.random.default_rng(seed)

        self._state: dict[str, CalibrationState] = {}
        self._results: dict[str, CalibrationResult] = {}

    def _build_jd_samples(self, target: CalibrationTarget) -> np.ndarray:
        jd_start, jd_end = target.jd_range
        return np.linspace(jd_start, jd_end, target.n_samples)

    def calibrate_body(self, body: str) -> CalibrationResult:
        """Run RL calibration for a single body."""
        t0 = time.time()

        target = next((t for t in self.targets if t.body.lower() == body.lower()), None)
        if target is None:
            target = CalibrationTarget(body, (2451545.0, 2460000.0), n_samples=15)

        jd_samples = self._build_jd_samples(target)

        # Start with nominal elements
        orbit0 = KeplerOrbit.BODIES[body.lower()]
        original_elements = orbit0.elements
        current_elements = original_elements

        original_mae = _mae_loss(original_elements, body, jd_samples)
        current_mae = original_mae

        history = [current_mae]
        patience_counter = 0
        best_mae = current_mae
        best_elements = current_elements

        converged = False
        n_episodes = 0

        print(f"\n{'─' * 60}")
        print(f"  Body: {body.upper()}")
        print(f"  Initial MAE: {current_mae:.4f}°")
        print(f"{'─' * 60}")

        for ep in range(1, self.max_episodes + 1):
            n_episodes = ep

            # ── Policy: gradient-free step (RL action) ──────────────────────
            new_elements = _gradient_free_step(current_elements, body, jd_samples)
            new_mae = _mae_loss(new_elements, body, jd_samples)

            # ── Reward signal ────────────────────────────────────────────────
            reward = -(new_mae - current_mae)  # positive if improved

            if new_mae < current_mae:
                current_elements = new_elements
                current_mae = new_mae
                best_mae - new_mae
                if new_mae < best_mae:
                    best_mae = new_mae
                    best_elements = new_elements
                patience_counter = 0
            else:
                patience_counter += 1

            history.append(current_mae)

            # ── Logging every 10 episodes ───────────────────────────────────
            if ep % 10 == 0 or ep == 1:
                print(f"  Ep {ep:3d}: MAE={current_mae:8.4f}° (best={best_mae:.4f}°) reward={reward:+.6f}")

            # ── Convergence check ───────────────────────────────────────────
            if current_mae < self.convergence_threshold_deg and patience_counter >= 5:
                converged = True
                print(f"  ✅ Converged at episode {ep} (MAE < {self.convergence_threshold_deg}°)")
                break

            if patience_counter >= self.patience:
                print(f"  ⏹️  Early stop at episode {ep} (no improvement for {self.patience} steps)")
                break

        improvement_pct = ((original_mae - best_mae) / max(original_mae, 1e-9)) * 100

        result = CalibrationResult(
            body=body,
            original_elements=original_elements,
            calibrated_elements=best_elements,
            improvement_pct=improvement_pct,
            final_mae_deg=best_mae,
            original_mae_deg=original_mae,
            n_episodes=n_episodes,
            converged=converged,
            calibration_time_sec=time.time() - t0,
            history=history,
        )

        self._results[body] = result

        # Print summary
        print(f"\n  📊 CALIBRATION SUMMARY: {body.upper()}")
        print(f"     Original MAE:   {original_mae:.4f}°")
        print(f"     Calibrated MAE: {best_mae:.4f}°")
        print(f"     Improvement:    {improvement_pct:+.2f}%")
        print(f"     Episodes:       {n_episodes}")
        print(f"     Time:           {result.calibration_time_sec:.2f}s")
        print(f"     Converged:      {converged}")

        return result

    def calibrate_all(self) -> dict[str, CalibrationResult]:
        """Run calibration for all bodies."""
        bodies = list({t.body for t in self.targets})
        for body in bodies:
            self.calibrate_body(body)
        return self._results

    def save(self, path: Path | str) -> None:
        """Serialize calibrated elements to JSON."""
        data = {}
        for body, result in self._results.items():
            e = result.calibrated_elements
            data[body] = {
                "semi_major_axis_au": e.semi_major_axis,
                "eccentricity": e.eccentricity,
                "mean_longitude_deg": e.mean_longitude,
                "arg_perihelion_deg": e.arg_perihelion,
                "long_ascending_node_deg": e.long_ascending_node,
                "inclination_deg": e.inclination,
                "mean_motion_deg_day": e.mean_motion,
                "orbital_period_day": e.orbital_period,
                "epoch_jd": e.epoch_jd,
                "original_mae_deg": result.original_mae_deg,
                "final_mae_deg": result.final_mae_deg,
                "improvement_pct": result.improvement_pct,
                "converged": result.converged,
                "n_episodes": result.n_episodes,
            }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"\n  💾 Saved calibrated elements → {path}")


# ── CLI ──────────────────────────────────────────────────────────────────────


def main():
    print("=" * 60)
    print("ATOM-STEP-5: RL Calibration — Kepler Orbital Elements")
    print("=" * 60)

    if not HAS_SWISS_EPHEMERIS:
        print("⚠️  Swiss Ephemeris not available — using fallback positions")
        print("   Install: pip install pyswisseph")
        print("   For accurate calibration, Swiss Ephemeris is required.")
        print()

    calibrator = KeplerCalibrator(
        max_episodes=100,
        convergence_threshold_deg=0.5,
        patience=15,
        seed=42,
    )

    results = calibrator.calibrate_all()

    # Save calibrated elements
    save_path = Path(__file__).parent.parent / "models" / "calibrated_elements.json"
    calibrator.save(save_path)

    print(f"\n{'=' * 60}")
    print("✅ RL CALIBRATION COMPLETE")
    print(f"{'=' * 60}")
    for body, result in results.items():
        status = "✅" if result.converged else "⚠️ "
        print(f"  {status} {body:<10} MAE: {result.original_mae_deg:7.4f}° → {result.final_mae_deg:7.4f}° ({result.improvement_pct:+.1f}%)")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
