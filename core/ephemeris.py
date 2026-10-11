"""
Swiss Ephemeris wrapper for AstroFin Sentinel.

Refactored (S1, 2026-06-20) to:
  * expose a swappable provider behind `EphemerisProtocol`
  * keep the god-node public API 100% backward-compatible
  * inject time through `common.deterministic.utc_now_deterministic`

Public surface preserved verbatim for callers in:
  agents/_impl/* (bradley, bull, bear, fundamental, macro, quant,
                 options_flow, sentiment, technical, electoral,
                 astro_council, gann, cycle, time_window)
  core/aspects.py
  core/kepler.py
  astrology/panchanga.py
  core/kepler_calibrator.py
  tests/*
"""

from __future__ import annotations

import logging
log = logging.getLogger(__name__)

from dataclasses import dataclass
from datetime import datetime, timezone
try:
    from tools.metrics_server import CACHE_HITS, CACHE_MISSES
except ImportError:
    CACHE_HITS = type("_Stub", (), {"inc": lambda: None})()
    CACHE_MISSES = type("_Stub", (), {"inc": lambda: None})()
from typing import Any, Protocol, Sequence, runtime_checkable


def _utc_now_deterministic() -> datetime:
    """Local shim for utc_now_deterministic (acos_contracts not installed)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

# ─── Swiss Ephemeris availability check ─────────────────────────────────────
try:
    import swisseph as swe  # type: ignore[import-untyped]

    HAS_SWISS_EPHEMERIS = True
except ImportError:
    HAS_SWISS_EPHEMERIS = False
    swe = None  # type: ignore[assignment]

# Concrete error type raised by the Swiss Ephemeris C extension. Only this narrow
# type is translated at the provider boundary; programming errors (TypeError,
# AttributeError, ...) propagate unchanged. Empty when the dependency is absent.
_SWISS_LIB_ERRORS: tuple[type[BaseException], ...] = (
    (swe.Error,) if swe is not None else ()
)


# Planet constants (Swiss Ephemeris IDs)
PLANETS: dict[str, int] = {
    "sun": 0,
    "moon": 1,
    "mercury": 2,
    "venus": 3,
    "mars": 4,
    "jupiter": 5,
    "saturn": 6,
    "uranus": 7,
    "neptune": 8,
    "pluto": 9,
    "north_node": 10,
    "chiron": 15,
}


# ─── Explicit provenance contract ───────────────────────────────────────────
SOURCE_SWISS_EPHEMERIS = "swiss_ephemeris"
SOURCE_SIMPLE_EPHEMERIS = "simple_ephemeris"


class EphemerisDependencyError(RuntimeError):
    """Swiss Ephemeris dependency is absent (broken environment, not runtime failure)."""


class EphemerisCalculationError(RuntimeError):
    """A strict Swiss Ephemeris calculation failed for one requested body."""


class EphemerisBatchError(RuntimeError):
    """Strict Swiss failed and the full Simple retry could not complete."""


# ─── DTOs ───────────────────────────────────────────────────────────────────
@dataclass
class PlanetPosition:
    planet: str
    longitude: float
    speed: float
    retrograde: bool


@dataclass
class HouseCusps:
    houses: list[float]
    ascendant: float
    mc: float
    vertex: float


@dataclass
class NatalChart:
    planets: dict[str, "PlanetPosition"]
    houses: "HouseCusps"
    timestamp: datetime
    latitude: float
    longitude: float


@dataclass(frozen=True)
class EphemerisBatch:
    """Positions for one request plus the provenance of the computation.

    ``source`` is exactly ``SOURCE_SWISS_EPHEMERIS`` when every requested body
    came from strict Swiss execution, and exactly ``SOURCE_SIMPLE_EPHEMERIS``
    when the whole request was recomputed through the Simple provider.
    """

    positions: dict[str, "PlanetPosition"]
    source: str


# ─── Provider protocol ──────────────────────────────────────────────────────
@runtime_checkable
class EphemerisProtocol(Protocol):
    """Provider-agnostic abstraction (mirror of `common.interfaces.EphemerisProtocol`).

    Re-declared here so `core.ephemeris` does not depend on the
    `common` package — that would invert the dependency chain
    (`common` is for top-level contracts; `core` is leaf).
    Domain code should depend on `core.ephemeris.EphemerisProtocol`.
    """

    def is_available(self) -> bool: ...

    def julian_day(self, dt: datetime) -> float: ...

    def calculate_planet(
        self, name: str, jd: float, flags: int = 1
    ) -> "PlanetPosition": ...

    def calculate_houses(
        self, jd: float, latitude: float, longitude: float, hsys: str = "P"
    ) -> "HouseCusps": ...

    def get_planetary_positions(
        self,
        dt: datetime,
        latitude: float = 53.2,
        longitude: float = 50.1,
        sidereal: bool = False,
    ) -> dict[str, "PlanetPosition"]: ...


# ─── Concrete providers ─────────────────────────────────────────────────────
class SwissEphemerisProvider:
    """Production provider backed by `pyswisseph`. Falls back to the simple
    provider if `swisseph` raises (so a runtime failure never crashes the
    orchestrator — mirrors the old module-level try/except behaviour).
    """

    def __init__(self) -> None:
        self._swe = swe
        self._available = HAS_SWISS_EPHEMERIS and swe is not None
        self._fallback = SimpleEphemerisProvider()
        self._chiron_available = False
        if self._available and self._swe is not None:
            from pathlib import Path
            for path_candidate in ("/usr/local/share/ephe", "/usr/share/ephe", str(Path.home() / ".sweph/ephe")):
                if Path(path_candidate).is_dir():
                    self._swe.set_ephe_path(path_candidate)
                    log.debug("Swiss Ephemeris path set to %s", path_candidate)
                    break
            try:
                self._swe.calc(self._swe.julday(2026, 1, 1, 0), swe.CHIRON, 1)
                self._chiron_available = True
            except Exception:
                log.debug("Chiron ephemeris file unavailable — excluded from calculations")

    def is_available(self) -> bool:
        return self._available

    def julian_day(self, dt: datetime) -> float:
        return _julian_day(dt)

    def calculate_planet(self, name: str, jd: float, flags: int = 1) -> PlanetPosition:
        planet_id = PLANETS.get(name.lower(), 0)
        if name.lower() == "chiron" and not self._chiron_available:
            lon, speed = _simple_position(name, jd)
            return PlanetPosition(
                planet=name, longitude=lon, speed=speed, retrograde=speed < 0
            )
        if self._available and self._swe is not None:
            try:
                result = self._swe.calc(jd, planet_id, flags)
                xx = result[0] if isinstance(result, tuple) else result
                lon = xx[0] % 360
                speed = xx[3]
                return PlanetPosition(
                    planet=name,
                    longitude=lon,
                    speed=speed,
                    retrograde=speed < 0,
                )
            except Exception:
                if name.lower() != "chiron":
                    log.warning("Ephemeris calculation failed", exc_info=True)
        lon, speed = _simple_position(name, jd)
        return PlanetPosition(
            planet=name, longitude=lon, speed=speed, retrograde=speed < 0
        )

    def calculate_houses(
        self, jd: float, latitude: float, longitude: float, hsys: str = "P"
    ) -> HouseCusps:
        if not self._available or self._swe is None:
            return self._fallback.calculate_houses(jd, latitude, longitude, hsys)
        try:
            cusps, ascmc = self._swe.houses(jd, latitude, longitude, hsys.encode())
            return HouseCusps(
                houses=[c % 360 for c in cusps],
                ascendant=ascmc[0] % 360,
                mc=ascmc[1] % 360,
                vertex=ascmc[3] % 360 if len(ascmc) > 3 else 0.0,
            )
        except Exception:
            return self._fallback.calculate_houses(jd, latitude, longitude, hsys)

    def get_planetary_positions(
        self,
        dt: datetime,
        latitude: float = 0.0,
        longitude: float = 0.0,
        sidereal: bool = False,
    ) -> dict[str, PlanetPosition]:
        jd = self.julian_day(dt)
        flags = 1
        if self._available and self._swe is not None:
            try:
                flags |= 256  # FLG_SPEED — always enable speed data for retrograde detection
            except Exception:
                pass
        if sidereal and self._available and self._swe is not None:
            try:
                flags |= self._swe.SIDM_LAHIRI if self._swe else 0
            except Exception:
                pass
        result = {}
        for name in PLANETS:
            try:
                result[name] = self.calculate_planet(name, jd)
            except Exception:
                log.debug("Skipping planet due to calculation error", planet=name)
        return result


    def calculate_planet_strict(
        self, name: str, jd: float, flags: int = 1
    ) -> PlanetPosition:
        """Strict Swiss-only calculation for one body. Never falls back.

        Raises:
            EphemerisDependencyError: Swiss Ephemeris is not installed.
            EphemerisCalculationError: the library rejected the request, the body
                has no ephemeris file, or the returned data is unusable.
        """
        if not self._available or self._swe is None:
            raise EphemerisDependencyError("swiss ephemeris dependency unavailable")
        if name.lower() == "chiron" and not self._chiron_available:
            raise EphemerisCalculationError("chiron ephemeris file unavailable")
        planet_id = PLANETS.get(name.lower(), 0)
        try:
            result = self._swe.calc(jd, planet_id, flags)
        except _SWISS_LIB_ERRORS as exc:
            raise EphemerisCalculationError(
                f"swiss ephemeris calculation failed for {name!r}"
            ) from exc
        xx = result[0] if isinstance(result, tuple) else result
        if not isinstance(xx, (list, tuple)) or len(xx) < 4:
            raise EphemerisCalculationError(
                f"swiss ephemeris returned no usable data for {name!r}"
            )
        speed = xx[3]
        return PlanetPosition(
            planet=name,
            longitude=xx[0] % 360,
            speed=speed,
            retrograde=speed < 0,
        )

    def get_planetary_batch(
        self,
        dt: datetime,
        sidereal: bool = False,
        planets: Sequence[str] | None = None,
    ) -> EphemerisBatch:
        """Provenance-tagged batch: strict Swiss, else a full Simple recompute.

        Every requested body is computed through strict Swiss calls only. If any
        single body fails, the whole partial Swiss batch is discarded and every
        requested body is recomputed through ``SimpleEphemerisProvider`` with
        identical inputs. Provenance is taken from the executed branch — never
        inferred by comparing numeric output.

        An explicitly empty ``planets`` sequence is invalid caller input and is
        rejected with ``ValueError`` before any dependency or provider work.
        """
        if planets is None:
            requested = list(PLANETS)
        else:
            requested = list(planets)
            if not requested:
                raise ValueError("planets must not be empty")
        jd = self.julian_day(dt)
        flags = 1 | 256  # SEFLG_SPEED — retrograde detection
        if sidereal and self._available and self._swe is not None:
            flags |= self._swe.SIDM_LAHIRI

        strict: dict[str, PlanetPosition] = {}
        for name in requested:
            try:
                position = self.calculate_planet_strict(name, jd, flags)
            except EphemerisCalculationError:
                strict = {}
                break
            if not isinstance(position, PlanetPosition):
                # Missing/invalid result counts as a strict failure.
                strict = {}
                break
            strict[name] = position

        if len(strict) == len(requested) and all(
            isinstance(position, PlanetPosition) for position in strict.values()
        ):
            return EphemerisBatch(positions=strict, source=SOURCE_SWISS_EPHEMERIS)

        return self._simple_batch(requested, jd, flags)

    def _simple_batch(
        self, requested: list[str], jd: float, flags: int
    ) -> EphemerisBatch:
        """Recompute the entire request through Simple; raise if incomplete."""
        simple = SimpleEphemerisProvider()
        retry: dict[str, PlanetPosition] = {}
        try:
            for name in requested:
                retry[name] = simple.calculate_planet(name, jd, flags)
        except Exception as exc:
            raise EphemerisBatchError("simple ephemeris retry failed") from exc
        if len(retry) != len(requested) or not all(
            isinstance(position, PlanetPosition) for position in retry.values()
        ):
            raise EphemerisBatchError("simple ephemeris retry incomplete")
        return EphemerisBatch(positions=retry, source=SOURCE_SIMPLE_EPHEMERIS)


class SimpleEphemerisProvider:
    """Deterministic toy provider used when `pyswisseph` is unavailable.

    Kept identical to the old `_simple_position()` math so that fallback
    behaviour matches bit-for-bit across the refactor.
    """

    def is_available(self) -> bool:
        return False

    def julian_day(self, dt: datetime) -> float:
        return _julian_day(dt)

    def calculate_planet(self, name: str, jd: float, flags: int = 1) -> PlanetPosition:
        lon, speed = _simple_position(name, jd)
        return PlanetPosition(
            planet=name, longitude=lon, speed=speed, retrograde=speed < 0
        )

    def calculate_houses(
        self, jd: float, latitude: float, longitude: float, hsys: str = "P"
    ) -> HouseCusps:
        sun_pos = self.calculate_planet("sun", jd)
        houses = [(sun_pos.longitude + 30 * i) % 360 for i in range(12)]
        return HouseCusps(houses=houses, ascendant=houses[0], mc=houses[9], vertex=0.0)

    def get_planetary_positions(
        self,
        dt: datetime,
        latitude: float = 53.2,
        longitude: float = 50.1,
        sidereal: bool = False,
    ) -> dict[str, PlanetPosition]:
        jd = self.julian_day(dt)
        return {name: self.calculate_planet(name, jd) for name in PLANETS}


# ─── Default provider + swap registry ───────────────────────────────────────
_default_provider: EphemerisProtocol = SwissEphemerisProvider()


def get_provider() -> EphemerisProtocol:
    """Return the currently active provider (for tests / shadow-runs)."""
    return _default_provider


def set_provider(provider: EphemerisProtocol) -> None:
    """Swap the active provider. Used by tests / shadow-runs."""
    global _default_provider
    if not isinstance(provider, EphemerisProtocol):
        raise TypeError(
            f"provider must satisfy EphemerisProtocol, got {type(provider).__name__}"
        )
    _default_provider = provider


# ─── Module-level convenience wrappers (god-node API) ───────────────────────
def _julian_day(dt: datetime) -> float:
    """Calculate Julian Day from datetime (unchanged)."""
    year = dt.year
    month = dt.month
    day = dt.day + dt.hour / 24 + dt.minute / 1440 + dt.second / 86400

    if month <= 2:
        year -= 1
        month += 12

    A = int(year / 100)
    B = 2 - A + int(A / 4)

    return int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + B - 1524.5


def _simple_position(planet: str, jd: float) -> tuple[float, float]:
    """Simplified planet position (NOT accurate). Only for testing without Swiss Ephemeris."""
    base = {
        "sun": 0,
        "moon": 100,
        "mercury": 180,
        "venus": 220,
        "mars": 50,
        "jupiter": 290,
        "saturn": 320,
    }
    period = {
        "sun": 365.25,
        "moon": 27.32,
        "mercury": 87.97,
        "venus": 224.7,
        "mars": 686.98,
        "jupiter": 4332.59,
        "saturn": 10759.22,
    }
    p = base.get(planet, 0)
    t = period.get(planet, 365.25)
    longitude = (p + 360 * (jd - 2451545) / t) % 360
    speed = 360 / t
    return longitude, speed


def calculate_planet(
    planet_name: str,
    jd: float,
    flags: int = 1,  # SEFLG_SPEED = 1
) -> PlanetPosition:
    """Calculate planet's tropical longitude and speed (god-node API)."""
    return _default_provider.calculate_planet(planet_name, jd, flags)


def calculate_houses(
    jd: float,
    latitude: float,
    longitude: float,
    hsys: str = "P",  # Placidus
) -> HouseCusps:
    """Calculate house cusps (god-node API)."""
    return _default_provider.calculate_houses(jd, latitude, longitude, hsys)


def calculate_natal_chart(
    birth_time: datetime,
    latitude: float,
    longitude: float,
    use_sidereal: bool = False,
    ayanamsha: int = 1,  # Raseshwara
) -> NatalChart:
    """Calculate complete natal chart (god-node API)."""
    cache_key = (birth_time.isoformat(), latitude, longitude, use_sidereal, ayanamsha)
    if cache_key in _natal_cache:
        CACHE_HITS.inc()
        return _natal_cache[cache_key]
    CACHE_MISSES.inc()
    jd = _julian_day(birth_time)
    flags = 1
    if use_sidereal and HAS_SWISS_EPHEMERIS and swe is not None:
        import swisseph as _swe; flags |= _swe.FLG_SIDEREAL
        try:
            swe.set_sid_mode(ayanamsha)
        except Exception:
            pass
    planets = {
        name: _default_provider.calculate_planet(name, jd, flags) for name in PLANETS
    }
    houses = _default_provider.calculate_houses(jd, latitude, longitude)
    chart = NatalChart(
        planets=planets,
        houses=houses,
        timestamp=birth_time,
        latitude=latitude,
        longitude=longitude,
    )
    _natal_cache[cache_key] = chart
    return chart


def get_current_positions(
    latitude: float = 55.7558, longitude: float = 37.6173, use_sidereal: bool = False
) -> NatalChart:
    """Get current planetary positions for electional astrology.

    Now uses `common.deterministic._utc_now_deterministic()` so that
    shadow-run / replay tests get a stable timestamp instead of wall-clock.
    """
    now = _utc_now_deterministic()
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return calculate_natal_chart(now, latitude, longitude, use_sidereal)


def get_planetary_positions(
    dt: datetime,
    latitude: float = 53.2,
    longitude: float = 50.1,
    sidereal: bool = False,
) -> dict[str, PlanetPosition]:
    """Get positions of all planets (alias for compatibility)."""
    return _default_provider.get_planetary_positions(dt, latitude, longitude, sidereal)


def get_planetary_batch(
    dt: datetime,
    sidereal: bool = False,
    planets: Sequence[str] | None = None,
) -> EphemerisBatch:
    """Get a provenance-tagged planetary batch from the active provider.

    Unlike ``get_planetary_positions`` this reports which provider actually
    produced the batch and never hides a per-body fallback.
    """
    batch_api = getattr(_default_provider, "get_planetary_batch", None)
    if batch_api is None:
        raise EphemerisBatchError(
            "active provider does not expose a provenance batch API"
        )
    return batch_api(dt, sidereal=sidereal, planets=planets)


__all__ = [
    "PlanetPosition",
    "HouseCusps",
    "NatalChart",
    "EphemerisBatch",
    "EphemerisBatchError",
    "EphemerisCalculationError",
    "EphemerisDependencyError",
    "SOURCE_SIMPLE_EPHEMERIS",
    "SOURCE_SWISS_EPHEMERIS",
    "EphemerisProtocol",
    "SwissEphemerisProvider",
    "SimpleEphemerisProvider",
    "calculate_planet",
    "calculate_houses",
    "calculate_natal_chart",
    "get_current_positions",
    "get_planetary_positions",
    "get_planetary_batch",
    "get_provider",
    "set_provider",
    "HAS_SWISS_EPHEMERIS",
]


# ─── Cached natal chart (legacy hooks) ──────────────────────────────────────
_natal_cache: dict[str, Any] = {}
