"""
test_core_aspects.py — Tests for core/aspects.py (Aspect engine)

Phase 1 (R9): Add coverage for critical core/aspects module.
Tests cover AspectType enum, Aspect dataclass, AspectReport helpers,
essential_dignity(), and AspectsEngine.compute() with both major and
minor aspect configurations.
"""
from __future__ import annotations

import pytest

from core.aspects import (
    Aspect,
    AspectReport,
    AspectsEngine,
    AspectType,
    _angle_diff,
    _normalize_angle,
    _sign_index,
    _sign_name,
    essential_dignity,
)
from core.ephemeris import PlanetPosition


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _planet(name: str, lon: float, retrograde: bool = False) -> PlanetPosition:
    return PlanetPosition(
        planet=name,
        longitude=lon,
        speed=-0.5 if retrograde else 1.0,
        retrograde=retrograde,
    )


@pytest.fixture
def three_planets() -> dict[str, PlanetPosition]:
    """Sun/Venus conjunction (0°), Sun/Jupiter trine (120°), Mars square Sun (90°)."""
    return {
        "sun": _planet("sun", 10.0),
        "venus": _planet("venus", 12.0),  # 2° from Sun → conjunction
        "jupiter": _planet("jupiter", 130.0),  # 120° from Sun → trine
        "mars": _planet("mars", 100.0),  # 90° from Sun → square
    }


# ─── Helper functions ─────────────────────────────────────────────────────────


class TestAngleHelpers:
    def test_normalize_angle_within_range(self):
        assert _normalize_angle(45.0) == 45.0

    def test_normalize_angle_over_360(self):
        assert _normalize_angle(370.0) == 10.0

    def test_normalize_angle_zero(self):
        assert _normalize_angle(0.0) == 0.0

    def test_angle_diff_same_longitude(self):
        assert _angle_diff(45.0, 45.0) == 0.0

    def test_angle_diff_across_zero(self):
        # 350° and 10° → 20° (smallest angular distance)
        assert _angle_diff(350.0, 10.0) == 20.0

    def test_angle_diff_opposition(self):
        assert _angle_diff(0.0, 180.0) == 180.0

    def test_angle_diff_max_range_capped(self):
        # 0° vs 270° → 90° (not 270°)
        assert _angle_diff(0.0, 270.0) == 90.0

    def test_sign_index_aries(self):
        assert _sign_index(0.0) == 0

    def test_sign_index_pisces(self):
        assert _sign_index(359.0) == 11

    def test_sign_index_overflow(self):
        assert _sign_index(360.0) == 0  # wraps to Aries

    def test_sign_name_sun_in_leo(self):
        assert _sign_name(135.0) == "Leo"  # 135° → Leo (4 * 30 + 15)

    def test_sign_name_overflow(self):
        assert _sign_name(720.0) == "Aries"


# ─── Essential dignity ────────────────────────────────────────────────────────


class TestEssentialDignity:
    def test_sun_in_leo_domicile_plus5(self):
        # 135° → Leo
        assert essential_dignity("sun", 135.0) == 5

    def test_sun_in_aries_exaltation_plus4(self):
        # 0° → Aries
        assert essential_dignity("sun", 0.0) == 4

    def test_sun_in_aquarius_detriment_minus5(self):
        # 300° → Aquarius
        assert essential_dignity("sun", 300.0) == -5

    def test_sun_in_libra_fall_minus4(self):
        # 180° → Libra
        assert essential_dignity("sun", 180.0) == -4

    def test_unknown_planet_returns_zero(self):
        # chiron not in dignities table
        assert essential_dignity("chiron", 0.0) == 0


# ─── Aspect dataclass ─────────────────────────────────────────────────────────


class TestAspectDataclass:
    def test_aspect_creation(self):
        a = Aspect(
            aspect_type=AspectType.TRINE,
            planet1="sun",
            planet2="jupiter",
            orb=2.5,
            exact_angle=120.0,
            applies=True,
            signature="Sun △ Jupiter",
        )
        assert a.aspect_type == AspectType.TRINE
        assert a.orb == 2.5
        assert a.applies is True

    def test_aspect_equality_by_field(self):
        # dataclass equality
        a1 = Aspect(AspectType.CONJUNCTION, "sun", "moon", 1.0, 0.0, True, "Sun ☌ Moon")
        a2 = Aspect(AspectType.CONJUNCTION, "sun", "moon", 1.0, 0.0, True, "Sun ☌ Moon")
        assert a1 == a2


# ─── AspectReport helpers ─────────────────────────────────────────────────────


class TestAspectReportHelpers:
    @pytest.fixture
    def report(self) -> AspectReport:
        return AspectReport(
            aspects=[
                Aspect(AspectType.CONJUNCTION, "sun", "venus", 2.0, 0.0, True, "Sun ☌ Venus"),
                Aspect(AspectType.TRINE, "sun", "jupiter", 1.0, 120.0, True, "Sun △ Jupiter"),
                Aspect(AspectType.SQUARE, "mars", "saturn", 3.0, 90.0, False, "Mars □ Saturn"),
                Aspect(AspectType.OPPOSITION, "sun", "moon", 4.0, 180.0, False, "Sun ☍ Moon"),
                Aspect(AspectType.TRINE, "venus", "jupiter", 1.0, 120.0, True, "Venus △ Jupiter"),
            ],
            summary={"count": 5},
        )

    def test_by_planet_filters_correctly(self, report):
        sun_aspects = report.by_planet("sun")
        assert len(sun_aspects) == 3  # Sun with Venus, Jupiter, Moon

    def test_by_planet_returns_empty_for_unknown(self, report):
        assert report.by_planet("pluto") == []

    def test_applying_filters_applying_only(self, report):
        applying = report.applying()
        assert len(applying) == 3  # 3 aspects with applies=True

    def test_by_type_filters_correctly(self, report):
        trines = report.by_type(AspectType.TRINE)
        assert len(trines) == 2

    def test_has_returns_true_when_aspect_present(self, report):
        assert report.has(AspectType.CONJUNCTION, "sun", "venus") is True

    def test_has_unordered_pair(self, report):
        # should match regardless of pair order
        assert report.has(AspectType.CONJUNCTION, "venus", "sun") is True

    def test_has_returns_false_when_missing(self, report):
        assert report.has(AspectType.SEXTILE, "sun", "venus") is False


# ─── AspectsEngine.compute() ──────────────────────────────────────────────────


class TestAspectsEngineCompute:
    def test_conjunction_detected(self, three_planets):
        engine = AspectsEngine()
        report = engine.compute(three_planets)
        # Sun-Venus at 2° → conjunction (within 8° orb)
        assert report.has(AspectType.CONJUNCTION, "sun", "venus")

    def test_trine_detected(self, three_planets):
        engine = AspectsEngine()
        report = engine.compute(three_planets)
        assert report.has(AspectType.TRINE, "sun", "jupiter")

    def test_square_detected(self, three_planets):
        engine = AspectsEngine()
        report = engine.compute(three_planets)
        assert report.has(AspectType.SQUARE, "sun", "mars")

    def test_minor_aspects_excluded_by_default(self, three_planets):
        engine = AspectsEngine(include_minor=False)
        report = engine.compute(three_planets)
        semisquares = report.by_type(AspectType.SEMISQUARE)
        assert semisquares == []

    def test_minor_aspects_when_enabled(self):
        # Sun at 0°, Venus at 45° → semisquare
        positions = {
            "sun": _planet("sun", 0.0),
            "venus": _planet("venus", 45.0),
        }
        engine = AspectsEngine(include_minor=True)
        report = engine.compute(positions)
        semisquares = report.by_type(AspectType.SEMISQUARE)
        assert len(semisquares) == 1

    def test_out_of_orb_aspect_excluded(self):
        # Sun at 0°, Venus at 50° → no aspect within default orbs
        # (closest aspect: trine at 70° away from 120°, 11° over trine orb of 7°)
        positions = {
            "sun": _planet("sun", 0.0),
            "venus": _planet("venus", 50.0),
        }
        engine = AspectsEngine()
        report = engine.compute(positions)
        # No aspect should be reported — closest is 60° (sextile) at 10° from actual
        # sextile orb is 6° → excluded; trine at 70° diff = 50° from 120° → excluded
        assert len(report.aspects) == 0

    def test_planets_subset_filter(self, three_planets):
        engine = AspectsEngine()
        report = engine.compute(three_planets, planets=["sun", "venus"])
        # Only Sun-Venus pair considered
        for asp in report.aspects:
            assert {asp.planet1, asp.planet2} <= {"sun", "venus"}

    def test_missing_planet_in_subset_skipped(self):
        positions = {"sun": _planet("sun", 0.0)}  # no mars
        engine = AspectsEngine()
        report = engine.compute(positions, planets=["sun", "mars"])
        # Mars not in positions → no aspects
        assert report.aspects == []

    def test_retrograde_marks_applying(self):
        # Sun direct, Venus retrograde → aspect flagged as applying
        positions = {
            "sun": _planet("sun", 0.0, retrograde=False),
            "venus": _planet("venus", 2.0, retrograde=True),
        }
        engine = AspectsEngine()
        report = engine.compute(positions)
        conj = report.by_type(AspectType.CONJUNCTION)
        assert len(conj) == 1
        assert conj[0].applies is True

    def test_signature_includes_symbol(self, three_planets):
        engine = AspectsEngine()
        report = engine.compute(three_planets)
        sigs = [a.signature for a in report.aspects]
        # Signature format: "Planet <symbol> Planet" — symbol must be non-empty
        for sig in sigs:
            assert " ☌ " in sig or " △ " in sig or " □ " in sig or " ☍ " in sig

    def test_empty_positions_returns_empty_report(self):
        engine = AspectsEngine()
        report = engine.compute({})
        assert report.aspects == []
        assert isinstance(report.summary, dict)

    def test_single_planet_returns_empty_report(self):
        engine = AspectsEngine()
        report = engine.compute({"sun": _planet("sun", 0.0)})
        assert report.aspects == []

    def test_custom_orb_overrides(self):
        # Sun 0°, Venus 4° → outside default conjunction orb (8°) but inside
        # if we widen to 10°
        positions = {
            "sun": _planet("sun", 0.0),
            "venus": _planet("venus", 4.0),
        }
        # With default orb, 4° < 8° so conjunction still detected
        engine_default = AspectsEngine()
        report_default = engine_default.compute(positions)
        assert report_default.has(AspectType.CONJUNCTION, "sun", "venus")

        # With tight orb of 3°, 4° is outside → excluded
        engine_tight = AspectsEngine(orbs={AspectType.CONJUNCTION: 3.0})
        report_tight = engine_tight.compute(positions)
        assert not report_tight.has(AspectType.CONJUNCTION, "sun", "venus")