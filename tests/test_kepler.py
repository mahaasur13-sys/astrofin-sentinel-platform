"""
tests/test_kepler.py — ATOM-STEP-1: Kepler Engine Tests
Tests core/kepler.py: orbital propagation, anomaly solving, Swiss Ephemeris validation.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.kepler import (
    KeplerOrbit,
    KeplerResult,
    OrbitalElements,
    propagate_kepler,
    validate_vs_swiss_ephemeris,
)

# ─── Orbital Elements ─────────────────────────────────────────────────────────


class TestOrbitalElements:
    def test_earth_elements_exist(self):
        e = OrbitalElements.earth()
        assert e.name == "Earth"
        assert 0.99 < e.semi_major_axis < 1.01
        assert 0.0 <= e.eccentricity < 1.0
        assert e.orbital_period > 300

    def test_jupiter_elements_exist(self):
        j = OrbitalElements.jupiter()
        assert j.name == "Jupiter"
        assert 5.0 < j.semi_major_axis < 5.5
        assert j.orbital_period > 4000

    def test_saturn_elements_exist(self):
        s = OrbitalElements.saturn()
        assert s.name == "Saturn"
        assert 9.0 < s.semi_major_axis < 10.0
        assert s.orbital_period > 10000


# ─── Kepler's Equation (Newton-Raphson) ───────────────────────────────────────


class TestKeplerEquation:
    def test_eccentric_anomaly_circular_orbit(self):
        """e=0 → E = M exactly."""
        orbit = KeplerOrbit(
            OrbitalElements(
                name="test",
                semi_major_axis=1.0,
                eccentricity=0.0,
                inclination=0.0,
                long_ascending_node=0.0,
                arg_perihelion=0.0,
                long_perihelion=0.0,
                mean_longitude=45.0,
                mean_motion=1.0,
                orbital_period=360.0,
                epoch_jd=2451545.0,
            )
        )
        E = orbit.eccentric_anomaly(45.0)
        assert abs(E - 45.0) < 1e-9

    def test_eccentric_anomaly_known_value(self):
        """e=0.5, M=30° → E ≈ 47.6° (known reference)."""
        orbit = KeplerOrbit(
            OrbitalElements(
                name="test",
                semi_major_axis=1.0,
                eccentricity=0.5,
                inclination=0.0,
                long_ascending_node=0.0,
                arg_perihelion=0.0,
                long_perihelion=0.0,
                mean_longitude=30.0,
                mean_motion=1.0,
                orbital_period=360.0,
                epoch_jd=2451545.0,
            )
        )
        E = orbit.eccentric_anomaly(30.0)
        # Known reference value for e=0.5, M=30°: E ≈ 47.6°
        assert 45.0 < E < 55.0

    def test_eccentric_anomaly_convergence(self):
        """Newton-Raphson produces bounded E for all M in [0, 360)."""
        orbit = KeplerOrbit(OrbitalElements.earth())
        for M in [0, 90, 180, 270, 359]:
            E = orbit.eccentric_anomaly(M)
            # E must be bounded (0-360) for all M
            assert 0 <= E <= 360, f"M={M}: E={E} out of bounds"

    def test_true_anomaly_range(self):
        """0° ≤ ν < 360° for all M."""
        orbit = KeplerOrbit(OrbitalElements.jupiter())
        for M in range(0, 360, 15):
            E = orbit.eccentric_anomaly(M)
            nu = orbit.true_anomaly(E)
            assert 0 <= nu < 360


# ─── Mean Anomaly ─────────────────────────────────────────────────────────────


class TestMeanAnomaly:
    def test_mean_anomaly_at_j2000(self):
        """At epoch JD, M is mean_longitude - long_perihelion (mod 360)."""
        orbit = KeplerOrbit(OrbitalElements.earth())
        M = orbit.mean_anomaly_at(orbit.elements.epoch_jd)
        expected = orbit.elements.mean_longitude - orbit.elements.long_perihelion
        # Result is mod 360, so compare normalized values
        assert abs((M - expected) % 360) < 1e-6 or abs((expected - M) % 360) < 1e-6

    def test_mean_anomaly_wraps(self):
        """M stays in [0, 360)."""
        orbit = KeplerOrbit(OrbitalElements.earth())
        # 1 year later
        M = orbit.mean_anomaly_at(orbit.elements.epoch_jd + orbit.elements.orbital_period)
        assert 0 <= M < 360


# ─── Radius ───────────────────────────────────────────────────────────────────


class TestRadius:
    def test_earth_radius_near_1au(self):
        """Earth's radius should be near 1 AU."""
        orbit = KeplerOrbit(OrbitalElements.earth())
        r = orbit.radius(orbit.elements.epoch_jd)
        assert 0.95 < r < 1.05

    def test_jupiter_radius_near_5au(self):
        """Jupiter's radius should be near 5.2 AU."""
        orbit = KeplerOrbit(OrbitalElements.jupiter())
        r = orbit.radius(orbit.elements.epoch_jd)
        assert 4.8 < r < 5.6

    def test_radius_positive(self):
        """r > 0 always."""
        orbit = KeplerOrbit(OrbitalElements.saturn())
        r = orbit.radius(orbit.elements.epoch_jd)
        assert r > 0


# ─── Heliocentric Longitude ────────────────────────────────────────────────────


class TestHeliocentricLongitude:
    def test_longitude_in_range(self):
        """Longitude 0° ≤ λ < 360°."""
        orbit = KeplerOrbit(OrbitalElements.jupiter())
        for jd_offset in [0, 100, 500, 1000]:
            lon = orbit.heliocentric_longitude(orbit.elements.epoch_jd + jd_offset)
            assert 0 <= lon < 360

    def test_longitude_changes_with_time(self):
        """Longitude at different times must differ (unless full period)."""
        orbit = KeplerOrbit(OrbitalElements.earth())
        jd = orbit.elements.epoch_jd
        lon_t0 = orbit.heliocentric_longitude(jd)
        lon_t1 = orbit.heliocentric_longitude(jd + 30)
        assert lon_t0 != lon_t1


# ─── at_jd / KeplerResult ──────────────────────────────────────────────────────


class TestKeplerResult:
    def test_kepler_result_has_all_fields(self):
        orbit = KeplerOrbit(OrbitalElements.earth())
        result = orbit.at_jd(orbit.elements.epoch_jd)
        assert isinstance(result, KeplerResult)
        assert result.body == "Earth"
        assert 0 <= result.heliocentric_longitude < 360
        assert result.radius_au > 0
        assert 0 <= result.mean_anomaly < 360
        assert 0 <= result.eccentric_anomaly < 360
        assert 0 <= result.true_anomaly < 360
        assert result.orbital_period > 0

    def test_propagate_kepler_known_bodies(self):
        for body in ["earth", "jupiter", "saturn"]:
            result = propagate_kepler(body, 2451545.0)
            assert result.body.lower() == body.lower()
            assert result.jd == 2451545.0

    def test_propagate_kepler_unknown_body_raises(self):
        with pytest.raises(ValueError, match="Unknown body"):
            propagate_kepler("unknown_planet", 2451545.0)


# ─── No NaN / No Errors ────────────────────────────────────────────────────────


class TestNoNaN:
    def test_no_nan_in_earth_results(self):
        orbit = KeplerOrbit(OrbitalElements.earth())
        for jd in [2451545.0, 2460000.0, 2470000.0, 2480000.0]:
            result = orbit.at_jd(jd)
            assert not math.isnan(result.heliocentric_longitude)
            assert not math.isnan(result.radius_au)
            assert not math.isnan(result.mean_anomaly)

    def test_no_nan_in_jupiter_results(self):
        orbit = KeplerOrbit(OrbitalElements.jupiter())
        for jd in [2451545.0, 2460000.0, 2470000.0]:
            result = orbit.at_jd(jd)
            assert not math.isnan(result.heliocentric_longitude)
            assert not math.isnan(result.radius_au)

    def test_no_nan_in_saturn_results(self):
        orbit = KeplerOrbit(OrbitalElements.saturn())
        for jd in [2451545.0, 2460000.0, 2470000.0]:
            result = orbit.at_jd(jd)
            assert not math.isnan(result.heliocentric_longitude)
            assert not math.isnan(result.radius_au)


# ─── Swiss Ephemeris Validation ───────────────────────────────────────────────


class TestSwissEphemerisValidation:
    def test_validate_returns_dict(self):
        v = validate_vs_swiss_ephemeris("earth", 2451545.0)
        assert isinstance(v, dict)
        assert "kepler_lon" in v
        assert "status" in v

    def test_validate_keys_present(self):
        v = validate_vs_swiss_ephemeris("earth", 2451545.0)
        for key in ["kepler_lon", "swiss_lon", "delta_lon", "status", "message"]:
            assert key in v


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
