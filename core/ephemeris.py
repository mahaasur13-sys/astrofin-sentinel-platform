"""
Swiss Ephemeris wrapper for AstroFin Sentinel.
Handles planetary positions, houses, and aspect calculation.

Merged from AstroFin-Sentinel (better calculations) + sentinel-v4.
"""

from dataclasses import dataclass
from datetime import datetime, timezone

# Swiss Ephemeris — try pyswisseph first, fallback to simple
try:
    import swisseph as swe

    HAS_SWISS_EPHEMERIS = True
except ImportError:
    HAS_SWISS_EPHEMERIS = False
    swe = None


# Planet constants (Swiss Ephemeris IDs)
PLANETS = {
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


@dataclass
class PlanetPosition:
    planet: str
    longitude: float  # degrees 0-360
    speed: float  # daily motion in degrees
    retrograde: bool


@dataclass
class HouseCusps:
    houses: list[float]  # 12 houses, 0-indexed (house 1 = houses[0])
    ascendant: float
    mc: float  # Medium Coeli / Midheaven
    vertex: float


@dataclass
class NatalChart:
    planets: dict[str, PlanetPosition]
    houses: HouseCusps
    timestamp: datetime
    latitude: float
    longitude: float


def _julian_day(dt: datetime) -> float:
    """Calculate Julian Day from datetime."""
    year = dt.year
    month = dt.month
    day = dt.day + dt.hour / 24 + dt.minute / 1440 + dt.second / 86400

    if month <= 2:
        year -= 1
        month += 12

    A = int(year / 100)
    B = 2 - A + int(A / 4)

    return int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + B - 1524.5


def calculate_planet(
    planet_name: str,
    jd: float,
    flags: int = 1,  # SEFLG_SPEED = 1
) -> PlanetPosition:
    """Calculate planet's tropical longitude and speed."""
    planet_id = PLANETS.get(planet_name.lower(), 0)

    if HAS_SWISS_EPHEMERIS and swe is not None:
        try:
            result = swe.calc(jd, planet_id, flags)
            if isinstance(result, tuple):
                xx = result[0]
            else:
                xx = result
            lon = xx[0] % 360
            speed = xx[3]
        except Exception:
            lon, speed = _simple_position(planet_name, jd)
    else:
        lon, speed = _simple_position(planet_name, jd)

    retrograde = speed < 0

    return PlanetPosition(planet=planet_name, longitude=lon, speed=speed, retrograde=retrograde)


def _simple_position(planet: str, jd: float) -> tuple:
    """
    Simplified planet position (NOT accurate).
    Only for testing without Swiss Ephemeris.
    """

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


def calculate_houses(
    jd: float,
    latitude: float,
    longitude: float,
    hsys: str = "P",  # Placidus
) -> HouseCusps:
    """Calculate house cusps using Placidus or Whole Sign."""
    if not HAS_SWISS_EPHEMERIS or swe is None:
        # Fallback: rough approximation
        sun_pos = calculate_planet("sun", jd)
        houses = [(sun_pos.longitude + 30 * i) % 360 for i in range(12)]
        return HouseCusps(houses=houses, ascendant=houses[0], mc=houses[9], vertex=0.0)

    try:
        cusps, ascmc = swe.houses(jd, latitude, longitude, hsys.encode())
        return HouseCusps(
            houses=[c % 360 for c in cusps],
            ascendant=ascmc[0] % 360,
            mc=ascmc[1] % 360,
            vertex=ascmc[3] % 360 if len(ascmc) > 3 else 0.0,
        )
    except Exception:
        sun_pos = calculate_planet("sun", jd)
        houses = [(sun_pos.longitude + 30 * i) % 360 for i in range(12)]
        return HouseCusps(houses=houses, ascendant=houses[0], mc=houses[9], vertex=0.0)


def calculate_natal_chart(
    birth_time: datetime,
    latitude: float,
    longitude: float,
    use_sidereal: bool = False,
    ayanamsha: int = 1,  # Raseshwara
) -> NatalChart:
    """Calculate complete natal chart."""
    jd = _julian_day(birth_time)

    flags = 1  # SEFLG_SPEED
    if use_sidereal and HAS_SWISS_EPHEMERIS and swe is not None:
        flags |= 256  # SEFLG_SIDEREAL
        try:
            swe.set_sid_mode(ayanamsha)
        except Exception:
            pass

    # Calculate planets
    planets = {}
    for name in PLANETS:
        planets[name] = calculate_planet(name, jd, flags)

    # Calculate houses
    houses = calculate_houses(jd, latitude, longitude)

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
    """Get current planetary positions for electional astrology."""
    now = datetime.now(timezone.utc)
    return calculate_natal_chart(now, latitude, longitude, use_sidereal)


# Alias for compatibility with astrology/ephemeris.py
def get_planetary_positions(
    dt: datetime,
    latitude: float = 53.2,
    longitude: float = 50.1,
    sidereal: bool = False,
) -> dict[str, PlanetPosition]:
    """Get positions of all planets (alias for compatibility)."""
    chart = calculate_natal_chart(dt, latitude, longitude, sidereal)
    return chart.planets


__all__ = [
    "PlanetPosition",
    "HouseCusps",
    "NatalChart",
    "calculate_planet",
    "calculate_houses",
    "calculate_natal_chart",
    "get_current_positions",
    "get_planetary_positions",
    "HAS_SWISS_EPHEMERIS",
]

# ─── Кешируемая натальная карта ──────────────────────────────────────────────

_natal_cache = {}


# def calculate_natal_chart(date_str: str) -> dict:
#    """Возвращает натальную карту с кешированием."""
#    if date_str in _natal_cache:
#        CACHE_HITS.inc()
#        return _natal_cache[date_str]
#    CACHE_MISSES.inc()
#    result = _calculate_natal_chart_uncached(date_str)
#    _natal_cache[date_str] = result
#    return result
#
#
# def _calculate_natal_chart_uncached(date_str: str) -> dict:
#    """Тяжёлая операция (заглушка)."""
#    return {"sun": 0.0, "moon": 1.0, "planets": []}
