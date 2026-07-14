"""
tests/test_kepler_property.py — ATOM-STEP-2: Property-Based Testing (Hypothesis)
================================================================================
Property tests for core/kepler.py using Hypothesis.
Covers: orbital mechanics invariants, convergence, periodicity, no NaN across
        wide JD ranges, Swiss Ephemeris boundary conditions, edge cases.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import hypothesis
import pytest
from hypothesis import Verbosity, given, settings
from hypothesis import strategies as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.kepler import (
    KeplerOrbit,
    OrbitalElements,
    propagate_kepler,
    validate_vs_swiss_ephemeris,
)

hypothesis.settings.register_profile("ci", deadline=None, max_examples=500)
hypothesis.settings.load_profile("ci")


# ─── Strategies ────────────────────────────────────────────────────────────────


@st.composite
def jd_range(
    draw,
    min_jd: float = 2000000.0,
    max_jd: float = 2500000.0,
) -> float:
    """Julian Date strategy covering ~300 years around J2000."""
    return draw(
        st.floats(
            min_value=min_jd,
            max_value=max_jd,
            allow_nan=False,
            allow_infinity=False,
        )
    )


@st.composite
def positive_eccentricity(draw) -> float:
    """Eccentricity strategy: 0 <= e < 1 (bound orbit)."""
    return draw(
        st.floats(
            min_value=0.0,
            max_value=0.9999,
            allow_nan=False,
            allow_infinity=False,
        )
    )


@st.composite
def mean_anomaly_360(draw) -> float:
    """Mean anomaly in [0, 360) degrees."""
    return draw(
        st.floats(
            min_value=0.0,
            max_value=359.9999,
            allow_nan=False,
            allow_infinity=False,
        )
    )


# ─── Property 1: Orbital Radius ∈ [a(1-e), a(1+e)] ────────────────────────────


@given(
    elements=st.builds(
        OrbitalElements,
        name=st.just("test_body"),
        semi_major_axis=st.floats(
            min_value=0.1, max_value=50.0, allow_nan=False, allow_infinity=False
        ),
        eccentricity=positive_eccentricity(),
        inclination=st.floats(
            min_value=0.0, max_value=180.0, allow_nan=False, allow_infinity=False
        ),
        long_ascending_node=st.floats(
            min_value=0.0, max_value=360.0, allow_nan=False, allow_infinity=False
        ),
        arg_perihelion=st.floats(
            min_value=0.0, max_value=360.0, allow_nan=False, allow_infinity=False
        ),
        long_perihelion=st.floats(
            min_value=0.0, max_value=360.0, allow_nan=False, allow_infinity=False
        ),
        mean_longitude=mean_anomaly_360(),
        mean_motion=st.floats(
            min_value=0.001, max_value=100.0, allow_nan=False, allow_infinity=False
        ),
        orbital_period=st.floats(
            min_value=1.0, max_value=100000.0, allow_nan=False, allow_infinity=False
        ),
        epoch_jd=jd_range(),
    )
)
@settings(max_examples=200, verbosity=Verbosity.verbose)
def test_radius_within_perihelion_aphelion(elements):
    """Radius r ∈ [a(1-e), a(1+e)] always holds for bound orbits."""
    orbit = KeplerOrbit(elements)
    r = orbit.radius(elements.epoch_jd)
    a = elements.semi_major_axis
    e = elements.eccentricity
    r_min = a * (1.0 - e)
    r_max = a * (1.0 + e)

    assert not math.isnan(r), f"radius is NaN: a={a}, e={e}"
    assert not math.isinf(r), f"radius is Inf: a={a}, e={e}"
    assert (
        r_min - 1e-10 <= r <= r_max + 1e-10
    ), f"radius {r} outside [{r_min:.6f}, {r_max:.6f}] for a={a}, e={e}"


# ─── Property 2: Longitude ∈ [0, 360) ─────────────────────────────────────────


@given(jd=jd_range())
@settings(max_examples=500)
def test_longitude_in_circle(jd):
    """Heliocentric longitude always ∈ [0, 360)."""
    orbit = KeplerOrbit.earth()
    lon = orbit.heliocentric_longitude(jd)

    assert not math.isnan(lon), f"longitude is NaN at JD={jd}"
    assert not math.isinf(lon), f"longitude is Inf at JD={jd}"
    assert 0.0 <= lon < 360.0, f"longitude {lon} outside [0,360) at JD={jd}"


# ─── Property 3: Mean Anomaly ∈ [0, 360) ──────────────────────────────────────


@given(jd=jd_range())
@settings(max_examples=500)
def test_mean_anomaly_in_circle(jd):
    """Mean anomaly always ∈ [0, 360)."""
    orbit = KeplerOrbit.earth()
    M = orbit.mean_anomaly_at(jd)

    assert not math.isnan(M), f"mean_anomaly is NaN at JD={jd}"
    assert not math.isinf(M), f"mean_anomaly is Inf at JD={jd}"
    assert 0.0 <= M < 360.0, f"mean_anomaly {M} outside [0,360) at JD={jd}"


# ─── Property 4: Period = 360° / mean_motion (for known real bodies) ─────────────


@given(jd=jd_range())
@settings(max_examples=100)
def test_period_motion_consistency(jd):
    """P = 360 / n for real known bodies (Earth, Jupiter, Saturn)."""
    for body, elements in [
        ("earth", OrbitalElements.earth()),
        ("jupiter", OrbitalElements.jupiter()),
        ("saturn", OrbitalElements.saturn()),
    ]:
        KeplerOrbit(elements)
        computed_period = 360.0 / elements.mean_motion

        assert not math.isnan(computed_period), f"{body}: computed period is NaN"
        assert not math.isinf(computed_period), f"{body}: computed period is Inf"
        err = abs(computed_period - elements.orbital_period) / elements.orbital_period
        assert (
            err < 0.001
        ), f"{body}: P={computed_period:.2f} differs from stored P={elements.orbital_period} by {err * 100:.2f}%"


# ─── Property 5: Newton-Raphson Convergence ≤ 20 iterations ────────────────────


@given(M=mean_anomaly_360())
@settings(max_examples=500)
def test_n_r_converges_fast(M):
    """Newton-Raphson converges in ≤ 20 iterations for all M ∈ [0,360)."""
    orbit = KeplerOrbit.earth()
    e = orbit.elements.eccentricity
    M_rad = math.radians(M)
    E = M_rad

    iterations = 0
    for _ in range(50):
        sin_E = math.sin(E)
        cos_E = math.cos(E)
        f = E - e * sin_E - M_rad
        f_prime = 1.0 - e * cos_E
        delta = f / f_prime
        E -= delta
        iterations += 1
        if abs(delta) < 1e-10:
            break

    assert iterations <= 20, f"NR did not converge in 20 iterations for M={M}° (e={e})"


# ─── Property 6: propagate_kepler raises for unknown body ─────────────────────


@given(
    body=st.text(
        min_size=1,
        max_size=30,
        alphabet=st.characters(categories=("Lu", "Ll", "Nd")),
    )
)
@settings(max_examples=200)
def test_propagate_unknown_body_raises(body):
    """Unknown body name raises ValueError."""
    if body.lower() not in ("earth", "jupiter", "saturn"):
        with pytest.raises(ValueError, match="Unknown body"):
            propagate_kepler(body, 2451545.0)


# ─── Property 7: validate_vs_swiss_ephemeris always returns required keys ─────


@given(body=st.sampled_from(["earth", "jupiter", "saturn"]), jd=jd_range())
@settings(max_examples=100)
def test_validate_returns_all_keys(body, jd):
    """validate_vs_swiss_ephemeris always returns status, message, kepler_lon keys."""
    result = validate_vs_swiss_ephemeris(body, jd)

    assert isinstance(result, dict), "result must be a dict"
    assert "status" in result, "result must contain 'status'"
    assert "message" in result, "result must contain 'message'"
    assert "kepler_lon" in result, "result must contain 'kepler_lon'"
    assert result["status"] in (
        "PASS",
        "WARN",
        "FAIL",
        "SKIP",
        "ERROR",
    ), f"status must be PASS|WARN|FAIL|SKIP|ERROR, got {result['status']}"


# ─── Property 8: No NaN across ±300 years from J2000 ─────────────────────────


@given(jd=jd_range(min_jd=2000000.0, max_jd=2500000.0))
@settings(max_examples=300)
def test_no_nan_across_300_years(jd):
    """No NaN/Inf in any orbital parameter over ±300 years from J2000."""
    orbit = KeplerOrbit.earth()
    result = orbit.at_jd(jd)

    for field_name in [
        "heliocentric_longitude",
        "radius_au",
        "mean_anomaly",
        "eccentric_anomaly",
        "true_anomaly",
        "days_to_next_return",
    ]:
        val = getattr(result, field_name)
        assert not math.isnan(val), f"NaN: {field_name} at JD={jd}: {result}"
        assert not math.isinf(val), f"Inf: {field_name} at JD={jd}: {result}"


# ─── Property 9: Known body result has all fields ─────────────────────────────


@given(jd=jd_range())
@settings(max_examples=100)
def test_known_body_result_complete(jd):
    """propagate_kepler(known_body, jd) returns KeplerResult with all fields."""
    for body in ["earth", "jupiter", "saturn"]:
        result = propagate_kepler(body, jd)
        for field in [
            "body",
            "jd",
            "heliocentric_longitude",
            "radius_au",
            "mean_anomaly",
            "eccentric_anomaly",
            "true_anomaly",
            "mean_motion",
            "orbital_period",
            "days_to_next_return",
            "is_retrograde",
            "speed_deg_per_day",
        ]:
            assert hasattr(result, field), f"{body} result missing field '{field}'"


# ─── Property 10: Circular orbit (e=0) → E = M ───────────────────────────────


@given(M=mean_anomaly_360())
@settings(max_examples=200)
def test_circular_orbit_eccentric_anomaly_equals_mean(M):
    """For e=0, eccentric anomaly E should equal mean anomaly M exactly."""
    from dataclasses import replace

    earth_elements = OrbitalElements.earth()
    circular_elements = replace(earth_elements, eccentricity=0.0)
    orbit = KeplerOrbit(circular_elements)
    E = orbit.eccentric_anomaly(M)

    diff = abs(E - M) % 360.0
    diff = min(diff, 360.0 - diff)
    assert diff < 0.1, f"e=0: E={E}° should equal M={M}° (diff={diff}°)"


# ─── Property 11: Swiss validation SKIP/ERROR always has kepler_lon ───────────


@given(jd=jd_range())
@settings(max_examples=50)
def test_validate_skips_gracefully(jd):
    """SKIP/ERROR status always includes valid kepler_lon in result."""
    result = validate_vs_swiss_ephemeris("earth", jd)
    assert "kepler_lon" in result
    assert isinstance(result["kepler_lon"], float)
    assert 0.0 <= result["kepler_lon"] < 360.0


# ─── Property 12: Longitude periodic with orbital period (real bodies only) ─────


@pytest.mark.unit
def test_longitude_periodic_real_bodies():
    """After exactly one orbital period, heliocentric longitude returns to same position.

    For a real body with consistent mean_motion = 360°/P:
    λ = Ω + ω + ν(M(JD+P))
    Since M increases by exactly 360° after one period, ν is unchanged,
    so λ should be unchanged modulo 360.
    """
    for name, elements in [
        ("earth", OrbitalElements.earth()),
        ("jupiter", OrbitalElements.jupiter()),
        ("saturn", OrbitalElements.saturn()),
    ]:
        orbit = KeplerOrbit(elements)
        jd0 = elements.epoch_jd
        jd1 = jd0 + elements.orbital_period

        lon0 = orbit.heliocentric_longitude(jd0)
        lon1 = orbit.heliocentric_longitude(jd1)

        delta = abs(lon1 - lon0) % 360.0
        delta = min(delta, 360.0 - delta)

        assert (
            delta < 0.5
        ), f"{name}: longitude changed by {delta}° after exactly one period (P={elements.orbital_period:.2f}d)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
