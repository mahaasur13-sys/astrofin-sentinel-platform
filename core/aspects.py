"""
Aspects engine for AstroFin Sentinel V5.

Calculates angular relationships between planets using ecliptic longitude
coordinates from Swiss Ephemeris (Skyfield DE421). Supports major and minor
aspects with configurable orbs.

Receives PlanetPosition dicts from core.ephemeris and returns structured
AspectReport objects.
"""

from dataclasses import dataclass, field
from enum import Enum

from core.ephemeris import PlanetPosition

# ── Aspect types ──────────────────────────────────────────────────────────────


class AspectType(Enum):
    CONJUNCTION = "conjunction"  # 0°
    SEXTILE = "sextile"  # 60°
    SQUARE = "square"  # 90°
    TRINE = "trine"  # 120°
    OPPOSITION = "opposition"  # 180°
    SEMISQUARE = "semisquare"  # 45°
    SESQUIQUADRATE = "sesquiquadrate"  # 135°
    QUINCUNX = "quincunx"  # 150°
    SEMISEXTILE = "semisextile"  # 30°


# Exact angles per aspect type (degrees)
_ASPECT_ANGLES: dict[AspectType, float] = {
    AspectType.CONJUNCTION: 0,
    AspectType.SEXTILE: 60,
    AspectType.SQUARE: 90,
    AspectType.TRINE: 120,
    AspectType.OPPOSITION: 180,
    AspectType.SEMISQUARE: 45,
    AspectType.SESQUIQUADRATE: 135,
    AspectType.QUINCUNX: 150,
    AspectType.SEMISEXTILE: 30,
}

# Default allowed orbs (degrees) — aligned with Swiss Ephemeris conventions
_DEFAULT_ORBS: dict[AspectType, float] = {
    AspectType.CONJUNCTION: 8.0,
    AspectType.SEXTILE: 6.0,
    AspectType.SQUARE: 7.0,
    AspectType.TRINE: 7.0,
    AspectType.OPPOSITION: 8.0,
    AspectType.SEMISQUARE: 4.0,
    AspectType.SESQUIQUADRATE: 4.0,
    AspectType.QUINCUNX: 5.0,
    AspectType.SEMISEXTILE: 4.0,
}


# ── Dataclasses ───────────────────────────────────────────────────────────────


@dataclass
class Aspect:
    aspect_type: AspectType
    planet1: str
    planet2: str
    orb: float  # deviation from exact angle (degrees)
    exact_angle: float  # ideal angle for this aspect type
    applies: bool  # True if within orb (applying aspect)
    signature: str  # e.g. "Sun ☌ Venus" or "Mars △ Jupiter"


@dataclass
class AspectReport:
    aspects: list[Aspect] = field(default_factory=list)
    summary: dict = field(default_factory=dict)

    def by_planet(self, planet: str) -> list[Aspect]:
        return [a for a in self.aspects if planet in (a.planet1, a.planet2)]

    def applying(self) -> list[Aspect]:
        return [a for a in self.aspects if a.applies]

    def by_type(self, aspect_type: AspectType) -> list[Aspect]:
        return [a for a in self.aspects if a.aspect_type == aspect_type]

    def has(self, aspect_type: AspectType, p1: str, p2: str) -> bool:
        return any(a.aspect_type == aspect_type and {a.planet1, a.planet2} == {p1, p2} for a in self.aspects)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _normalize_angle(a: float) -> float:
    return a % 360


def _angle_diff(a: float, b: float) -> float:
    """Smallest angular distance between two longitudes (0–180°)."""
    diff = abs(_normalize_angle(a) - _normalize_angle(b)) % 360
    return min(diff, 360 - diff)


def _sign_index(d: float) -> int:
    """Zodiac sign index: 0=Aries … 11=Pisces."""
    return int(d // 30) % 12


_ZODIAC_NAMES = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]


def _sign_name(d: float) -> str:
    return _ZODIAC_NAMES[_sign_index(d)]


# ── Aspect symbols ─────────────────────────────────────────────────────────────

_ASPECT_SYMBOLS: dict[AspectType, str] = {
    AspectType.CONJUNCTION: "☌",
    AspectType.SEXTILE: "⚹",
    AspectType.SQUARE: "□",
    AspectType.TRINE: "△",
    AspectType.OPPOSITION: "☍",
    AspectType.SEMISQUARE: "⚻",
    AspectType.SESQUIQUADRATE: "⚻",
    AspectType.QUINCUNX: "⚻",
    AspectType.SEMISEXTILE: "⚺",
}

_ASPECT_NAMES: dict[AspectType, str] = {
    AspectType.CONJUNCTION: "Conjunction",
    AspectType.SEXTILE: "Sextile",
    AspectType.SQUARE: "Square",
    AspectType.TRINE: "Trine",
    AspectType.OPPOSITION: "Opposition",
    AspectType.SEMISQUARE: "Semisquare",
    AspectType.SESQUIQUADRATE: "Sesquiquadrate",
    AspectType.QUINCUNX: "Quincunx",
    AspectType.SEMISEXTILE: "Semisextile",
}


# ── Essential dignities ───────────────────────────────────────────────────────

# rulership: +5 per sign listed (first = domicile, second = detrient when -5)
_DIGNITIES_RULER: dict[str, dict[str, int]] = {
    "sun": {"leo": 5, "aquarius": -5},
    "moon": {"cancer": 5, "capricorn": -5},
    "mercury": {"gemini": 5, "virgo": 5, "sagittarius": -5, "pisces": -5},
    "venus": {"taurus": 5, "libra": 5, "aries": -5, "scorpio": -5},
    "mars": {"aries": 5, "scorpio": 5, "libra": -5, "cancer": -5},
    "jupiter": {"sagittarius": 5, "pisces": 5, "gemini": -5, "virgo": -5},
    "saturn": {"capricorn": 5, "aquarius": 5, "aries": -5, "cancer": -5},
    "uranus": {"aquarius": 5},
    "neptune": {"pisces": 5},
    "pluto": {"scorpio": 5},
}

_EXALTATION: dict[str, str] = {
    "sun": "aries",
    "moon": "taurus",
    "jupiter": "cancer",
    "venus": "pisces",
    "mars": "capricorn",
    "saturn": "libra",
    "mercury": "virgo",
}

_FALL: dict[str, str] = {
    "sun": "libra",
    "moon": "scorpio",
    "jupiter": "capricorn",
    "venus": "virgo",
    "mars": "cancer",
    "saturn": "aries",
}


def essential_dignity(planet: str, longitude: float) -> int:
    """Return essential dignity score for a planet at given longitude.

    rulership: +5, detriment: -5, exaltation: +4, fall: -4
    """
    sign = _sign_name(longitude).lower()
    score = 0

    if planet in _DIGNITIES_RULER:
        ruler = _DIGNITIES_RULER[planet]
        if sign in ruler:
            score += ruler[sign]
        elif planet in _DIGNITIES_RULER and sign not in ruler:
            # Check detriment (sign listed with negative value, but fallback)
            pass

    if _EXALTATION.get(planet) == sign:
        score += 4
    elif _FALL.get(planet) == sign:
        score -= 4

    return score


# ── AspectEngine ───────────────────────────────────────────────────────────────


class AspectsEngine:
    """
    Computes aspects between planets using ecliptic coordinates from Swiss
    Ephemeris.

    Parameters
    ----------
    orbs : dict[AspectType, float] | None
        Custom orb per aspect type. Defaults to _DEFAULT_ORBS.
    include_minor : bool
        Include semi-square, sesquiquadrate, quincunx, semisextile.
        Default False.
    """

    def __init__(
        self,
        orbs: dict[AspectType, float] | None = None,
        include_minor: bool = False,
    ):
        self.orbs = orbs or _DEFAULT_ORBS.copy()
        self.include_minor = include_minor
        self._aspect_types: list[AspectType] = [
            a
            for a in _ASPECT_ANGLES
            if a
            not in (
                AspectType.SEMISQUARE,
                AspectType.SESQUIQUADRATE,
                AspectType.QUINCUNX,
                AspectType.SEMISEXTILE,
            )
            or include_minor
        ]

    def compute(
        self,
        positions: dict[str, PlanetPosition],
        planets: list[str] | None = None,
    ) -> AspectReport:
        """
        Calculate aspects between specified planets.

        For each planet pair, finds the nearest aspect type (the one whose
        exact angle is closest to the actual angular distance). Only reports
        that aspect if it falls within its orb.

        Parameters
        ----------
        positions : dict[str, PlanetPosition]
            Planet positions from core.ephemeris.
        planets : list[str] | None
            Subset of planets to consider. Defaults to all keys in positions.

        Returns
        -------
        AspectReport
        """
        if planets is None:
            planets = list(positions.keys())

        aspects: list[Aspect] = []
        seen: set[tuple[str, str]] = set()

        for i, p1 in enumerate(planets):
            if p1 not in positions:
                continue
            pos1 = positions[p1]

            for p2 in planets[i + 1 :]:
                if p2 not in positions:
                    continue
                if (p1, p2) in seen or (p2, p1) in seen:
                    continue

                pos2 = positions[p2]
                diff = _angle_diff(pos1.longitude, pos2.longitude)

                # Find nearest aspect type within orb
                best_aspect: AspectType | None = None
                best_delta = 360.0
                for atype in self._aspect_types:
                    orb_limit = self.orbs.get(atype, 6.0)
                    delta = abs(diff - _ASPECT_ANGLES[atype])
                    # Map to 0-180 range (aspect repeats every 180° for most)
                    delta = min(delta, 180 - delta)
                    if delta <= orb_limit and delta < best_delta:
                        best_delta = delta
                        best_aspect = atype

                if best_aspect is not None:
                    # Applying vs separating: based on relative speeds
                    # Simplified: if either is retrograde → applying
                    applies = pos1.retrograde or pos2.retrograde
                    symbol = _ASPECT_SYMBOLS.get(best_aspect, "⚬")
                    sig = f"{p1.capitalize()} {symbol} {p2.capitalize()}"

                    aspects.append(
                        Aspect(
                            aspect_type=best_aspect,
                            planet1=p1,
                            planet2=p2,
                            orb=round(best_delta, 2),
                            exact_angle=_ASPECT_ANGLES[best_aspect],
                            applies=applies,
                            signature=sig,
                        )
                    )
                    seen.add((p1, p2))

        summary = self._summarize(aspects)
        return AspectReport(aspects=aspects, summary=summary)

    def _summarize(self, aspects: list[Aspect]) -> dict:
        by_type: dict[str, int] = {}
        for a in aspects:
            name = _ASPECT_NAMES[a.aspect_type]
            by_type[name] = by_type.get(name, 0) + 1

        return {
            "total": len(aspects),
            "by_type": by_type,
            "applying": sum(1 for a in aspects if a.applying),
            "orbs_sum": round(sum(a.orb for a in aspects), 2),
        }


# ── Convenience function ───────────────────────────────────────────────────────


def calculate_aspects(
    positions: dict[str, PlanetPosition],
    planets: list[str] | None = None,
    include_minor: bool = False,
) -> AspectReport:
    """
    One-shot aspect calculation.

    Examples
    --------
    >>> from core.ephemeris import get_planetary_positions
    >>> from core.aspects import calculate_aspects
    >>> from datetime import datetime
    >>> pos = get_planetary_positions(datetime(2026, 3, 26))
    >>> report = calculate_aspects(pos)
    >>> for a in report.aspects:
    ...     print(a.signature, a.orb, "°")
    """
    engine = AspectsEngine(include_minor=include_minor)
    return engine.compute(positions, planets)


__all__ = [
    "AspectType",
    "Aspect",
    "AspectReport",
    "AspectsEngine",
    "calculate_aspects",
    "essential_dignity",
]
