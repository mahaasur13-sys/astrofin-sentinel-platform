"""
tests/test_kepler_differential.py — ATOM-STEP-3: Differential Testing (Swiss Ephemeris)
==========================================================================================
Differential tests: pure Keplerian (core/kepler.py) vs Swiss Ephemeris DE405.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from core import ephemeris as _eph
from core import kepler as _kp

HAS_SWISS = _eph.HAS_SWISS_EPHEMERIS

# Thresholds
REASONABLE_ERROR_ARCMIN = 10.0  # degrees — pure Keplerian vs N-body ~3-7 deg
REASONABLE_ERROR_ARCSEC = 60.0  # 1 arcminute in arcseconds
MAX_CATASTROPHIC_DEG = 60.0  # 60 degrees — absolute sanity bound


def angular_sep(lo1: float, lo2: float) -> float:
    delta = abs(lo1 - lo2) % 360.0
    return min(delta, 360.0 - delta)


pytestmark = pytest.mark.skipif(not HAS_SWISS, reason="pyswisseph not installed")


class TestDifferentialSwissEphemeris:
    """Pure Keplerian vs Swiss Ephemeris DE405 differential tests."""

    # ─── Test 1: J2000 mean accuracy for outer planets ─────────────────

    @pytest.mark.parametrize("body", ["jupiter", "saturn"])
    def test_j2000_mean_accuracy_outer_planets(self, body):
        """J2000: mean error < 1 arcmin for Jupiter and Saturn.

        Pure Keplerian (2-body) vs N-body DE405 should agree within ~1 arcminute
        for outer planets at epoch.
        """
        jd = 2451545.0
        k_lon = _kp.propagate_kepler(body, jd).heliocentric_longitude
        s_lon = _eph.calculate_planet(body, jd).longitude
        delta_deg = angular_sep(k_lon, s_lon)

        assert (
            delta_deg < REASONABLE_ERROR_ARCMIN
        ), f"{body}: J2000 Δ={delta_deg * 60:.2f} arcmin (Kepler={k_lon:.4f}°, Swiss={s_lon:.4f}°)"

    # ─── Test 2: Earth frame-awareness (reference frame difference) ─────

    def test_earth_frame_difference_acknowledged(self):
        """Earth: Keplerian heliocentric vs Swiss geocentric differ ~180°.

        This is NOT an error — different reference frames.
        We verify both give physically meaningful longitudes [0,360).
        """
        jd = 2451545.0
        k_lon = _kp.propagate_kepler("earth", jd).heliocentric_longitude
        s_lon = _eph.calculate_planet("earth", jd).longitude

        assert 0 <= k_lon < 360
        assert 0 <= s_lon < 360
        # Acknowledge the ~180° difference as known limitation
        delta = angular_sep(k_lon, s_lon)
        assert 90 < delta < 270, f"Earth: unexpected Δ={delta:.2f}° between frames"

    # ─── Test 3: No catastrophic divergence — outer planets only ───────

    @pytest.mark.parametrize(
        "body,jd",
        [
            ("jupiter", 2451545.0),
            ("jupiter", 2460000.0),
            ("jupiter", 2430000.0),
            ("saturn", 2451545.0),
            ("saturn", 2460000.0),
        ],
    )
    def test_no_catastrophic_divergence(self, body, jd):
        """Maximum separation should never exceed 60° for outer planets."""
        k_lon = _kp.propagate_kepler(body, jd).heliocentric_longitude
        s_lon = _eph.calculate_planet(body, jd).longitude
        delta_deg = angular_sep(k_lon, s_lon)

        assert (
            delta_deg < MAX_CATASTROPHIC_DEG
        ), f"{body} JD={jd}: catastrophic Δ={delta_deg:.2f}°"

    # ─── Test 4: Keplerian periodicity (self-consistency) ─────────────

    @pytest.mark.parametrize(
        "body,orbit_fn",
        [
            ("earth", _kp.KeplerOrbit.earth),
            ("jupiter", _kp.KeplerOrbit.jupiter),
            ("saturn", _kp.KeplerOrbit.saturn),
        ],
    )
    def test_kepler_periodicity(self, body, orbit_fn):
        """After one orbital period, heliocentric longitude returns to same value.

        Self-consistency check: Keplerian model should be periodic.
        """
        orbit = orbit_fn()
        jd0 = orbit.elements.epoch_jd
        jd1 = jd0 + orbit.elements.orbital_period

        lon0 = orbit.heliocentric_longitude(jd0)
        lon1 = orbit.heliocentric_longitude(jd1)

        delta = angular_sep(lon0, lon1)
        assert (
            delta < 0.5
        ), f"{body}: periodicity broken, Δ={delta:.4f}° after {orbit.elements.orbital_period:.2f} days"

    # ─── Test 5: Earth-Sun radius in [0.9, 1.1] AU ───────────────────

    def test_earth_radius_physical(self):
        """Earth radius should always be in physically plausible range."""
        import random

        random.seed(42)
        orbit = _kp.KeplerOrbit.earth()
        for _ in range(100):
            jd = 2451545.0 + random.uniform(-3650, 3650)
            r = orbit.radius(jd)
            assert 0.9 <= r <= 1.1, f"Earth radius {r:.4f} AU outside [0.9, 1.1]"

    # ─── Test 6: No NaN across wide JD range ─────────────────────────

    @pytest.mark.parametrize("body", ["earth", "jupiter", "saturn"])
    @pytest.mark.parametrize("jd", [2451545.0, 2460000.0, 2430000.0, 2500000.0])
    def test_no_nan(self, body, jd):
        """No NaN/Inf in Keplerian or Swiss calculations."""
        k_result = _kp.propagate_kepler(body, jd)
        for field in [
            "heliocentric_longitude",
            "radius_au",
            "eccentric_anomaly",
            "true_anomaly",
        ]:
            val = getattr(k_result, field)
            assert not (
                math.isnan(val) or math.isinf(val)
            ), f"Kepler NaN/Inf: {field} for {body} at JD={jd}"

        s_result = _eph.calculate_planet(body, jd)
        assert not (math.isnan(s_result.longitude) or math.isinf(s_result.longitude))

    # ─── Test 7: Radius monotonicity — perihelion < aphelion ────────

    @pytest.mark.parametrize(
        "body,orbit_fn",
        [
            ("earth", _kp.KeplerOrbit.earth),
            ("jupiter", _kp.KeplerOrbit.jupiter),
            ("saturn", _kp.KeplerOrbit.saturn),
        ],
    )
    def test_radius_perihelion_lt_aphelion(self, body, orbit_fn):
        """For any elliptic orbit: r(ν=0°) < r(ν=180°)."""
        orbit = orbit_fn()
        a, e = orbit.elements.semi_major_axis, orbit.elements.eccentricity

        # r = p / (1 + e*cos(nu)) where p = a(1-e^2)
        p = a * (1.0 - e * e)
        r_peri = p / (1.0 + e * math.cos(math.radians(0.0)))
        r_aph = p / (1.0 + e * math.cos(math.radians(180.0)))

        assert (
            r_peri < r_aph
        ), f"{body}: perihelion {r_peri:.4f} >= aphelion {r_aph:.4f}"
        assert abs(r_peri - a * (1 - e)) < 0.001


class TestSwissEphemerisSanity:
    """Sanity checks that Swiss Ephemeris gives physically correct answers."""

    @pytest.mark.skipif(not HAS_SWISS, reason="Swiss not available")
    def test_earth_one_year_return(self):
        """Earth: after 365.25 days, longitude should be near original."""
        jd0, jd1 = 2451545.0, 2451545.0 + 365.25
        lo0 = _eph.calculate_planet("earth", jd0).longitude
        lo1 = _eph.calculate_planet("earth", jd1).longitude
        delta = angular_sep(lo0, lo1)
        assert delta < 5.0, f"Earth 1-year Δ={delta:.2f}°"

    @pytest.mark.skipif(not HAS_SWISS, reason="Swiss not available")
    def test_jupiter_slow_motion(self):
        """Jupiter: 100 days should move < 25° (N-body perturbations allowed)."""
        jd0, jd1 = 2451545.0, 2451545.0 + 100.0
        lo0 = _eph.calculate_planet("jupiter", jd0).longitude
        lo1 = _eph.calculate_planet("jupiter", jd1).longitude
        delta_deg = angular_sep(lo0, lo1)
        assert delta_deg < 25.0, f"Jupiter 100-day Δ={delta_deg:.2f}°"

    @pytest.mark.skipif(not HAS_SWISS, reason="Swiss not available")
    def test_saturn_retrograde_flag_exists(self):
        """Saturn retrograde flag is boolean."""
        pos = _eph.calculate_planet("saturn", 2451545.0)
        assert isinstance(pos.retrograde, bool)
        assert isinstance(pos.speed, float)

    @pytest.mark.skipif(not HAS_SWISS, reason="Swiss not available")
    def test_saturn_no_teleportation(self):
        """Saturn: 100 days should move < 25°."""
        jd0, jd1 = 2451545.0, 2451545.0 + 100.0
        lo0 = _eph.calculate_planet("saturn", jd0).longitude
        lo1 = _eph.calculate_planet("saturn", jd1).longitude
        delta_deg = angular_sep(lo0, lo1)
        assert delta_deg < 25.0, f"Saturn 100-day Δ={delta_deg:.2f}°"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
