"""Focused tests for the explicit ephemeris provenance contract in ``core``.

Everything here is deterministic and offline: the low-level Swiss/Simple
providers are controlled with fakes, and no ephemeris data files, network
calls or repository writes are involved.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import core.ephemeris as core_ephemeris  # noqa: E402
from core.ephemeris import (  # noqa: E402
    PLANETS,
    SOURCE_SIMPLE_EPHEMERIS,
    SOURCE_SWISS_EPHEMERIS,
    EphemerisBatch,
    EphemerisBatchError,
    EphemerisCalculationError,
    EphemerisDependencyError,
    PlanetPosition,
    SimpleEphemerisProvider,
    SwissEphemerisProvider,
    _julian_day,
    _simple_position,
)

REQUESTED = ["sun", "moon", "mars"]
MOMENT = datetime(2026, 3, 21, 12, 0, 0, tzinfo=timezone.utc)

SWISS_LON = 10.0
SIMPLE_LON = 99.0


def _position(name: str, longitude: float) -> PlanetPosition:
    return PlanetPosition(planet=name, longitude=longitude, speed=1.0, retrograde=False)


def _strict_ok(self, name, jd, flags=1):
    return _position(name, SWISS_LON)


def _strict_fail_on(target: str, recorder: list | None = None):
    def _fail(self, name, jd, flags=1):
        if recorder is not None:
            recorder.append((name, jd, flags))
        if name == target:
            raise EphemerisCalculationError(f"strict swiss failed for {name}")
        return _position(name, SWISS_LON)

    return _fail


def _strict_returns_invalid(target: str):
    def _invalid(self, name, jd, flags=1):
        if name == target:
            return None
        return _position(name, SWISS_LON)

    return _invalid


def _simple_recorder(recorder: list, value=SIMPLE_LON, explode=False):
    def _simple(self, name, jd, flags=1):
        recorder.append((name, jd, flags))
        if explode:
            raise RuntimeError("simple provider exploded")
        if value is None:
            return None
        return _position(name, value)

    return _simple


# ── strict Swiss success ─────────────────────────────────────────────────


def test_strict_swiss_success_returns_swiss_batch(monkeypatch):
    provider = SwissEphemerisProvider()
    monkeypatch.setattr(SwissEphemerisProvider, "calculate_planet_strict", _strict_ok)

    batch = provider.get_planetary_batch(MOMENT, planets=REQUESTED)

    assert isinstance(batch, EphemerisBatch)
    assert batch.source == SOURCE_SWISS_EPHEMERIS
    assert list(batch.positions) == REQUESTED
    assert all(p.longitude == SWISS_LON for p in batch.positions.values())


def test_strict_path_never_calls_simple_position(monkeypatch):
    provider = SwissEphemerisProvider()
    monkeypatch.setattr(SwissEphemerisProvider, "calculate_planet_strict", _strict_ok)
    monkeypatch.setattr(
        core_ephemeris,
        "_simple_position",
        lambda planet, jd: pytest.fail("strict path must not use _simple_position"),
    )

    batch = provider.get_planetary_batch(MOMENT, planets=REQUESTED)

    assert batch.source == SOURCE_SWISS_EPHEMERIS


def test_default_request_covers_every_planet(monkeypatch):
    provider = SwissEphemerisProvider()
    monkeypatch.setattr(SwissEphemerisProvider, "calculate_planet_strict", _strict_ok)

    batch = provider.get_planetary_batch(MOMENT)

    assert list(batch.positions) == list(PLANETS)


# ── any strict failure discards the whole batch ──────────────────────────


@pytest.mark.parametrize("target", [REQUESTED[0], REQUESTED[1], REQUESTED[-1]])
def test_first_middle_last_failure_recomputes_full_request(monkeypatch, target):
    provider = SwissEphemerisProvider()
    strict_calls: list = []
    simple_calls: list = []

    monkeypatch.setattr(
        SwissEphemerisProvider,
        "calculate_planet_strict",
        _strict_fail_on(target, strict_calls),
    )
    monkeypatch.setattr(
        SimpleEphemerisProvider,
        "calculate_planet",
        _simple_recorder(simple_calls),
    )

    batch = provider.get_planetary_batch(MOMENT, planets=REQUESTED)

    assert batch.source == SOURCE_SIMPLE_EPHEMERIS
    assert [name for name, _, _ in simple_calls] == REQUESTED
    assert all(p.longitude == SIMPLE_LON for p in batch.positions.values())


def test_partial_swiss_values_are_not_returned_as_swiss(monkeypatch):
    provider = SwissEphemerisProvider()
    monkeypatch.setattr(
        SwissEphemerisProvider,
        "calculate_planet_strict",
        _strict_fail_on("mars"),
    )
    monkeypatch.setattr(
        SimpleEphemerisProvider,
        "calculate_planet",
        _simple_recorder([]),
    )

    batch = provider.get_planetary_batch(MOMENT, planets=REQUESTED)

    assert batch.source == SOURCE_SIMPLE_EPHEMERIS
    assert all(p.longitude == SIMPLE_LON for p in batch.positions.values())
    assert SWISS_LON not in {p.longitude for p in batch.positions.values()}


def test_invalid_strict_result_triggers_full_simple_retry(monkeypatch):
    provider = SwissEphemerisProvider()
    simple_calls: list = []
    monkeypatch.setattr(
        SwissEphemerisProvider,
        "calculate_planet_strict",
        _strict_returns_invalid("moon"),
    )
    monkeypatch.setattr(
        SimpleEphemerisProvider,
        "calculate_planet",
        _simple_recorder(simple_calls),
    )

    batch = provider.get_planetary_batch(MOMENT, planets=REQUESTED)

    assert batch.source == SOURCE_SIMPLE_EPHEMERIS
    assert [name for name, _, _ in simple_calls] == REQUESTED


# ── the retry receives identical inputs ──────────────────────────────────


def test_simple_retry_receives_identical_inputs(monkeypatch):
    provider = SwissEphemerisProvider()
    strict_calls: list = []
    simple_calls: list = []

    monkeypatch.setattr(
        SwissEphemerisProvider,
        "calculate_planet_strict",
        _strict_fail_on("mars", strict_calls),
    )
    monkeypatch.setattr(
        SimpleEphemerisProvider,
        "calculate_planet",
        _simple_recorder(simple_calls),
    )

    provider.get_planetary_batch(MOMENT, sidereal=True, planets=REQUESTED)

    expected_jd = _julian_day(MOMENT)
    assert [name for name, _, _ in simple_calls] == REQUESTED
    assert {jd for _, jd, _ in simple_calls} == {expected_jd}
    assert {jd for _, jd, _ in strict_calls} == {expected_jd}
    assert {flags for _, _, flags in simple_calls} == {flags for _, _, flags in strict_calls}
    # sidereal=True must reach both branches as SIDM_LAHIRI on the shared flags.
    sidereal_bit = provider._swe.SIDM_LAHIRI
    assert all(flags & sidereal_bit for _, _, flags in simple_calls)


# ── Simple exhaustion and dependency absence ─────────────────────────────


def test_simple_failure_raises_typed_batch_error(monkeypatch):
    provider = SwissEphemerisProvider()
    monkeypatch.setattr(
        SwissEphemerisProvider,
        "calculate_planet_strict",
        _strict_fail_on("mars"),
    )
    monkeypatch.setattr(
        SimpleEphemerisProvider,
        "calculate_planet",
        _simple_recorder([], explode=True),
    )

    with pytest.raises(EphemerisBatchError) as excinfo:
        provider.get_planetary_batch(MOMENT, planets=REQUESTED)

    assert isinstance(excinfo.value.__cause__, RuntimeError)


def test_incomplete_simple_batch_raises_typed_batch_error(monkeypatch):
    provider = SwissEphemerisProvider()
    monkeypatch.setattr(
        SwissEphemerisProvider,
        "calculate_planet_strict",
        _strict_fail_on("mars"),
    )
    monkeypatch.setattr(
        SimpleEphemerisProvider,
        "calculate_planet",
        _simple_recorder([], value=None),
    )

    with pytest.raises(EphemerisBatchError):
        provider.get_planetary_batch(MOMENT, planets=REQUESTED)


def test_missing_dependency_raises_and_never_uses_simple(monkeypatch):
    provider = SwissEphemerisProvider()
    provider._available = False
    provider._swe = None
    simple_calls: list = []
    monkeypatch.setattr(
        SimpleEphemerisProvider,
        "calculate_planet",
        _simple_recorder(simple_calls),
    )

    with pytest.raises(EphemerisDependencyError):
        provider.get_planetary_batch(MOMENT, planets=REQUESTED)

    assert simple_calls == []


def test_programming_error_is_not_masked_by_fallback(monkeypatch):
    provider = SwissEphemerisProvider()
    simple_calls: list = []

    def _boom(self, name, jd, flags=1):
        raise TypeError("programming bug in caller")

    monkeypatch.setattr(SwissEphemerisProvider, "calculate_planet_strict", _boom)
    monkeypatch.setattr(
        SimpleEphemerisProvider,
        "calculate_planet",
        _simple_recorder(simple_calls),
    )

    with pytest.raises(TypeError):
        provider.get_planetary_batch(MOMENT, planets=REQUESTED)

    assert simple_calls == []


def test_strict_calculation_error_uses_concrete_library_boundary(monkeypatch):
    provider = SwissEphemerisProvider()
    import swisseph as swe

    class _FailingSwe:
        Error = swe.Error
        SIDM_LAHIRI = swe.SIDM_LAHIRI

        @staticmethod
        def calc(jd, planet_id, flags):
            raise swe.Error("library failure")

    provider._swe = _FailingSwe()
    provider._available = True

    with pytest.raises(EphemerisCalculationError) as excinfo:
        provider.calculate_planet_strict("sun", 2451545.0)

    assert isinstance(excinfo.value.__cause__, swe.Error)


# ── legacy compatibility paths are unchanged ─────────────────────────────


def test_calculate_planet_keeps_per_planet_simple_fallback(monkeypatch):
    provider = SwissEphemerisProvider()
    import swisseph as swe

    class _FailingSwe:
        Error = swe.Error

        @staticmethod
        def calc(jd, planet_id, flags):
            raise swe.Error("library failure")

    provider._swe = _FailingSwe()
    provider._available = True

    position = provider.calculate_planet("sun", 2451545.0)
    expected_lon, expected_speed = _simple_position("sun", 2451545.0)

    assert position.longitude == expected_lon
    assert position.speed == expected_speed


def test_get_planetary_positions_returns_every_planet(monkeypatch):
    provider = SwissEphemerisProvider()
    seen: list = []

    def _record(self, name, jd, flags=1):
        seen.append(name)
        return _position(name, SWISS_LON)

    monkeypatch.setattr(SwissEphemerisProvider, "calculate_planet", _record)

    result = provider.get_planetary_positions(MOMENT)

    assert list(result) == list(PLANETS)
    assert seen == list(PLANETS)


def test_module_level_batch_delegates_to_active_provider(monkeypatch):
    sentinel = EphemerisBatch(positions={"sun": _position("sun", 1.0)}, source=SOURCE_SIMPLE_EPHEMERIS)
    captured: dict = {}

    class _FakeProvider:
        def get_planetary_batch(self, dt, latitude=53.2, longitude=50.1, sidereal=False, planets=None):
            captured["dt"] = dt
            captured["planets"] = planets
            return sentinel

    monkeypatch.setattr(core_ephemeris, "_default_provider", _FakeProvider())

    batch = core_ephemeris.get_planetary_batch(MOMENT, planets=REQUESTED)

    assert batch is sentinel
    assert captured["dt"] == MOMENT
    assert captured["planets"] == REQUESTED


# ── provenance constants have a single source of truth ───────────────────


def test_facade_source_constants_match_core_constants():
    from api.services.astro import SOURCE_SIMPLE, SOURCE_SWISS

    assert SOURCE_SWISS == SOURCE_SWISS_EPHEMERIS
    assert SOURCE_SIMPLE == SOURCE_SIMPLE_EPHEMERIS


# ── explicit empty planets: invalid caller input, never a batch ──────────


def test_explicit_empty_planets_is_rejected_before_any_provider_work(monkeypatch):
    provider = SwissEphemerisProvider()
    strict_calls: list = []
    simple_calls: list = []
    constructions: list = []
    jd_calls: list = []

    real_swiss_init = SwissEphemerisProvider.__init__
    real_simple_init = SimpleEphemerisProvider.__init__
    real_julian_day = SwissEphemerisProvider.julian_day

    def _counting_julian_day(self, dt):
        jd_calls.append(dt)
        return real_julian_day(self, dt)

    def _counting_swiss_init(self, *args, **kwargs):
        constructions.append("swiss")
        return real_swiss_init(self, *args, **kwargs)

    def _counting_simple_init(self, *args, **kwargs):
        constructions.append("simple")
        return real_simple_init(self, *args, **kwargs)

    monkeypatch.setattr(SwissEphemerisProvider, "__init__", _counting_swiss_init)
    monkeypatch.setattr(SwissEphemerisProvider, "julian_day", _counting_julian_day)
    monkeypatch.setattr(SimpleEphemerisProvider, "__init__", _counting_simple_init)
    monkeypatch.setattr(
        SwissEphemerisProvider,
        "calculate_planet_strict",
        _strict_fail_on("__never_requested__", strict_calls),
    )
    monkeypatch.setattr(
        SimpleEphemerisProvider,
        "calculate_planet",
        _simple_recorder(simple_calls),
    )

    with pytest.raises(ValueError) as excinfo:
        provider.get_planetary_batch(MOMENT, planets=[])

    assert str(excinfo.value) == "planets must not be empty"
    assert excinfo.value.__cause__ is None
    assert not isinstance(excinfo.value, (EphemerisBatchError, EphemerisDependencyError))
    assert strict_calls == []
    assert simple_calls == []
    assert constructions == []
    assert jd_calls == []


def test_explicit_empty_planets_without_dependency_never_touches_simple(monkeypatch):
    provider = SwissEphemerisProvider()
    provider._available = False
    strict_calls: list = []
    simple_calls: list = []

    monkeypatch.setattr(
        SwissEphemerisProvider,
        "calculate_planet_strict",
        _strict_fail_on("__never_requested__", strict_calls),
    )
    monkeypatch.setattr(
        SimpleEphemerisProvider,
        "calculate_planet",
        _simple_recorder(simple_calls),
    )

    with pytest.raises(ValueError) as excinfo:
        provider.get_planetary_batch(MOMENT, planets=[])

    assert str(excinfo.value) == "planets must not be empty"
    assert strict_calls == []
    assert simple_calls == []


def test_none_planets_still_follows_the_canonical_default_set(monkeypatch):
    provider = SwissEphemerisProvider()
    strict_calls: list = []

    monkeypatch.setattr(
        SwissEphemerisProvider,
        "calculate_planet_strict",
        _strict_fail_on("__never_requested__", strict_calls),
    )

    batch = provider.get_planetary_batch(MOMENT, planets=None)

    assert [name for name, _, _ in strict_calls] == list(PLANETS)
    assert list(batch.positions) == list(PLANETS)
    assert batch.source == SOURCE_SWISS_EPHEMERIS


def test_none_planets_falls_back_over_the_canonical_default_set(monkeypatch):
    provider = SwissEphemerisProvider()
    simple_calls: list = []

    monkeypatch.setattr(
        SwissEphemerisProvider,
        "calculate_planet_strict",
        _strict_fail_on("mars"),
    )
    monkeypatch.setattr(
        SimpleEphemerisProvider,
        "calculate_planet",
        _simple_recorder(simple_calls),
    )

    batch = provider.get_planetary_batch(MOMENT, planets=None)

    assert batch.source == SOURCE_SIMPLE_EPHEMERIS
    assert [name for name, _, _ in simple_calls] == list(PLANETS)
    assert list(batch.positions) == list(PLANETS)
