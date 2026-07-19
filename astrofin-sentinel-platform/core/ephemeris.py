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

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable

from acos_contracts.deterministic import utc_now_deterministic

# ─── Swiss Ephemeris availability check ─────────────────────────────────────
try:
    import swisseph as swe  # type: ignore[import-untyped]

    HAS_SWISS_EPHEMERIS = True
except ImportError:
    HAS_SWISS_EPHEMERIS = False
    swe = None  # type: ignore[assignment]


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

    def is_available(self) -> bool:
        return self._available

    def julian_day(self, dt: datetime) -> float:
        return _julian_day(dt)

    def calculate_planet(self, name: str, jd: float, flags: int = 1) -> PlanetPosition:
        planet_id = PLANETS.get(name.lower(), 0)
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
                pass
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
        latitude: float = 53.2,
        longitude: float = 50.1,
        sidereal: bool = False,
    ) -> dict[str, PlanetPosition]:
        flags = 1
        if sidereal and self._available and self._swe is not None:
            import swisseph as _swe; flags |= _swe.FLG_SIDEREAL
            try:
                self._swe.set_sid_mode(1)
            except Exception:
                pass
        return {
            name: self.calculate_planet(name, self.julian_day(dt), flags)
            for name in PLANETS
        }


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
    return NatalChart(
        planets=planets,
        houses=houses,
        timestamp=birth_time,
        latitude=latitude,
        longitude=longitude,
    )


def get_current_positions(
    latitude: float = 55.7558, longitude: float = 37.6173, use_sidereal: bool = False
) -> NatalChart:
    """Get current planetary positions for electional astrology.

    Now uses `common.deterministic.utc_now_deterministic()` so that
    shadow-run / replay tests get a stable timestamp instead of wall-clock.
    """
    now = utc_now_deterministic()
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


__all__ = [
    "PlanetPosition",
    "HouseCusps",
    "NatalChart",
    "EphemerisProtocol",
    "SwissEphemerisProvider",
    "SimpleEphemerisProvider",
    "calculate_planet",
    "calculate_houses",
    "calculate_natal_chart",
    "get_current_positions",
    "get_planetary_positions",
    "get_provider",
    "set_provider",
    "HAS_SWISS_EPHEMERIS",
]


# ─── Cached natal chart (legacy hooks) ──────────────────────────────────────
_natal_cache: dict[str, Any] = {}
