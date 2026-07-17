"""
AstroFin Sentinel v5 — Vedic Astrology Core
Nakshatras, Choghadiya, Muhurta calculations.
Based on sidereal zodiac and lunar mansions.
"""

from __future__ import annotations


import math
from datetime import datetime, timedelta

# ─── Nakshatras (27 Lunar Mansions) ──────────────────────────────────────────

NAKSHATRAS = [
    {
        "name": "Ashwini",
        "quality": "excellent",
        "deity": "Aswins",
        "ruling_planet": "Ketu",
    },
    {"name": "Bharani", "quality": "bad", "deity": "Yama", "ruling_planet": "Venus"},
    {"name": "Krittika", "quality": "neutral", "deity": "Agni", "ruling_planet": "Sun"},
    {
        "name": "Rohini",
        "quality": "excellent",
        "deity": "Brahma",
        "ruling_planet": "Moon",
    },
    {"name": "Mrigashira", "quality": "good", "deity": "Soma", "ruling_planet": "Mars"},
    {"name": "Ardra", "quality": "bad", "deity": "Rudra", "ruling_planet": "Rahu"},
    {
        "name": "Punarvasu",
        "quality": "good",
        "deity": "Aditi",
        "ruling_planet": "Jupiter",
    },
    {
        "name": "Pushya",
        "quality": "excellent",
        "deity": "Saturn",
        "ruling_planet": "Saturn",
    },
    {
        "name": "Ashlesha",
        "quality": "worst",
        "deity": "Naga",
        "ruling_planet": "Mercury",
    },
    {"name": "Magha", "quality": "neutral", "deity": "Pitris", "ruling_planet": "Ketu"},
    {
        "name": "Purva Phalguni",
        "quality": "good",
        "deity": "Bhaga",
        "ruling_planet": "Venus",
    },
    {
        "name": "Uttara Phalguni",
        "quality": "good",
        "deity": "Aryaman",
        "ruling_planet": "Sun",
    },
    {
        "name": "Hasta",
        "quality": "excellent",
        "deity": "Savitar",
        "ruling_planet": "Moon",
    },
    {
        "name": "Chitra",
        "quality": "neutral",
        "deity": "Tvashtar",
        "ruling_planet": "Mars",
    },
    {"name": "Swati", "quality": "good", "deity": "Vayu", "ruling_planet": "Rahu"},
    {
        "name": "Vishakha",
        "quality": "neutral",
        "deity": "Indra",
        "ruling_planet": "Jupiter",
    },
    {
        "name": "Anuradha",
        "quality": "good",
        "deity": "Mitra",
        "ruling_planet": "Saturn",
    },
    {
        "name": "Jyeshtha",
        "quality": "bad",
        "deity": "Nirriti",
        "ruling_planet": "Mercury",
    },
    {"name": "Mula", "quality": "neutral", "deity": "Nirriti", "ruling_planet": "Ketu"},
    {
        "name": "Purva Ashadha",
        "quality": "good",
        "deity": "Apo",
        "ruling_planet": "Venus",
    },
    {
        "name": "Uttara Ashadha",
        "quality": "excellent",
        "deity": "Vishwa",
        "ruling_planet": "Sun",
    },
    {"name": "Shravana", "quality": "good", "deity": "Vishnu", "ruling_planet": "Moon"},
    {
        "name": "Dhanishtha",
        "quality": "neutral",
        "deity": "Vasu",
        "ruling_planet": "Mars",
    },
    {
        "name": "Shatabhisha",
        "quality": "neutral",
        "deity": "Varuna",
        "ruling_planet": "Rahu",
    },
    {
        "name": "Purva Bhadrapada",
        "quality": "neutral",
        "deity": "Aja",
        "ruling_planet": "Jupiter",
    },
    {
        "name": "Uttara Bhadrapada",
        "quality": "good",
        "deity": "Ahirbudhnya",
        "ruling_planet": "Saturn",
    },
    {
        "name": "Revati",
        "quality": "excellent",
        "deity": "Pushan",
        "ruling_planet": "Mercury",
    },
]


# ─── Choghadiya (8 Periods of ~90 min each) ─────────────────────────────────

# Each day has 8 Choghadiyas (daytime: sunrise + 7 more, nighttime: sunset + 7 more)
# Day is divided into 8 parts, Night is divided into 8 parts

CHOGHADIYA_TYPES = {
    # Daytime Choghadiyas
    0: {
        "name": "Amrita",
        "quality": "excellent",
        "description": "Nectar time — most auspicious",
    },
    1: {
        "name": "Chandra",
        "quality": "good",
        "description": "Moon time — good for romance",
    },
    2: {
        "name": "Kaala",
        "quality": "bad",
        "description": "Black time — avoid important work",
    },
    3: {
        "name": "Shubha",
        "quality": "good",
        "description": "Auspicious — good for business",
    },
    4: {
        "name": "Amrita",
        "quality": "excellent",
        "description": "Nectar time — most auspicious",
    },
    5: {
        "name": "Marana",
        "quality": "worst",
        "description": "Death time — inauspicious",
    },
    6: {"name": "Kaala", "quality": "bad", "description": "Black time — avoid"},
    7: {
        "name": "Labha",
        "quality": "good",
        "description": "Profit time — good for gains",
    },
    # Nighttime Choghadiyas
    8: {"name": "Shubha", "quality": "good", "description": "Auspicious"},
    9: {"name": "Amrita", "quality": "excellent", "description": "Nectar time"},
    10: {"name": "Marana", "quality": "worst", "description": "Death time"},
    11: {"name": "Kaala", "quality": "bad", "description": "Black time"},
    12: {"name": "Labha", "quality": "good", "description": "Profit time"},
    13: {"name": "Chandra", "quality": "good", "description": "Moon time"},
    14: {"name": "Kaala", "quality": "bad", "description": "Black time"},
    15: {"name": "Shubha", "quality": "good", "description": "Auspicious"},
}

# Which Choghadiya types are good/bad for trading
GOOD_CHOGHADIYA = {"Amrita", "Shubha", "Labha", "Chandra"}
BAD_CHOGHADIYA = {"Marana", "Kaala"}


# ─── Main Functions ────────────────────────────────────────────────────────────


def get_sidereal_longitude(jd: float) -> float:
    """
    Calculate sidereal longitude of Moon (simplified).

    Uses astronomical calculations for true Moon position.
    In production, use Swiss Ephemeris or ep包的.
    """
    # Simplified lunar longitude calculation
    # T = Julian centuries from J2000.0
    T = (jd - 2451545.0) / 36525.0

    # Mean elements of Moon's orbit
    L = 218.3164477 + 481267.88123421 * T  # Mean longitude
    l = 134.9633964 + 477198.8675055 * T  # Mean anomaly
    357.5291092 + 35999.0502909 * T  # Sun's mean anomaly

    # Simplified latitude (in radians)
    moon_long = L + 6.289 * math.sin(math.radians(l))

    # Sidereal correction (ayanamsa ~ 24° in 2026)
    ayanamsa = 24.0  # Approximate for 2026
    sidereal_long = moon_long - ayanamsa

    return sidereal_long % 360


def get_moon_sign(dt: datetime) -> str:
    """Get zodiac sign where Moon is located."""
    # Simplified: use approximate lunar speed
    jd = _datetime_to_jd(dt)
    moon_long = get_sidereal_longitude(jd)

    signs = [
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

    sign_index = int(moon_long // 30)
    return signs[sign_index]


def get_current_nakshatra(dt: datetime) -> dict:
    """
    Get current Nakshatra (lunar mansion) and pada (quarter).

    Returns dict with name, pada (1-4), quality, deity, ruling_planet.
    """
    jd = _datetime_to_jd(dt)
    moon_long = get_sidereal_longitude(jd)

    # Each Nakshatra = 360/27 = 13°20'
    nakshatra_index = int(moon_long // (360 / 27))
    nakshatra_index = nakshatra_index % 27

    # Pada (quarter within nakshatra) = 360/27/4 = 3°20'
    nakshatra_size = 360 / 27
    pada = int((moon_long % nakshatra_size) / (nakshatra_size / 4)) + 1
    pada = min(pada, 4)

    nak = NAKSHATRAS[nakshatra_index]

    return {
        "name": nak["name"],
        "pada": pada,
        "quality": nak["quality"],
        "deity": nak["deity"],
        "ruling_planet": nak["ruling_planet"],
        "longitude": moon_long,
    }


def get_choghadiya(dt: datetime) -> dict:
    """
    Calculate current Choghadiya period.

    Each day has 8 daytime Choghadiyas (from sunrise) and 8 nighttime (from sunset).
    Each period = (sunrise to sunset) / 8  OR  (sunset to sunrise) / 8
    """
    # Simplified: assume equal 90-min periods
    # In production: calculate exact sunrise/sunset for location

    sunrise_hour = 6.0  # Simplified

    # Total minutes since midnight
    total_minutes = dt.hour * 60 + dt.minute

    # Daytime vs nighttime
    sunset_hour = 18.0
    sunrise_minutes = sunrise_hour * 60
    sunset_minutes = sunset_hour * 60

    if sunrise_minutes <= total_minutes < sunset_minutes:
        # Daytime
        period_length = (sunset_minutes - sunrise_minutes) / 8  # ~90 min
        offset = (total_minutes - sunrise_minutes) / period_length
        choghadiya_index = int(offset) % 8
    else:
        # Nighttime
        period_length = 540 / 8  # 12 hours / 8 = 90 min
        if total_minutes >= sunset_minutes:
            offset = (total_minutes - sunset_minutes) / period_length
        else:
            offset = (total_minutes + 1440 - sunset_minutes) / period_length
        choghadiya_index = (int(offset) % 8) + 8  # Nighttime indices start at 8

    choghadiya_index = choghadiya_index % 16
    ch_type = CHOGHADIYA_TYPES[choghadiya_index]

    # Calculate end time
    period_minutes = int(period_length)
    end_time = dt + timedelta(minutes=period_minutes)

    return {
        "name": ch_type["name"],
        "quality": ch_type["quality"],
        "description": ch_type["description"],
        "period_index": choghadiya_index,
        "end_time": end_time.strftime("%H:%M"),
        "is_good_for_trading": ch_type["name"] in GOOD_CHOGHADIYA,
        "is_bad_for_trading": ch_type["name"] in BAD_CHOGHADIYA,
        "score": _choghadiya_to_score(ch_type["name"]),
    }


def _choghadiya_to_score(name: str) -> float:
    """Convert Choghadiya name to 0-10 score."""
    scores = {
        "Amrita": 9.0,
        "Shubha": 7.5,
        "Labha": 7.0,
        "Chandra": 6.5,
        "Kaala": 3.0,
        "Marana": 1.0,
        "Vyatipata": 2.5,
        "Parivesha": 2.0,
    }
    return scores.get(name, 5.0)


def _datetime_to_jd(dt: datetime) -> float:
    """Convert datetime to Julian Date."""
    from datetime import timezone

    utc = dt.replace(tzinfo=timezone.utc)
    a = (14 - utc.month) // 12
    y = utc.year + 4800 - a
    m = utc.month + 12 * a - 3
    jdn = utc.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    jd = jdn + (utc.hour + utc.minute / 60.0 + utc.second / 3600.0 - 12) / 24.0
    return jd


# ─── Convenience functions ────────────────────────────────────────────────────


def get_muhurta_score(dt: datetime) -> float:
    """Get overall Muhurta score 0-10 for datetime."""
    nakshatra = get_current_nakshatra(dt)
    choghadiya = get_choghadiya(dt)

    score = 5.0
    score += _choghadiya_to_score(choghadiya["name"]) - 5.0

    nak_scores = {
        "excellent": +2.0,
        "good": +1.0,
        "neutral": 0,
        "bad": -1.0,
        "worst": -2.0,
    }
    score += nak_scores.get(nakshatra["quality"], 0)

    return max(0, min(10, score))


def is_trading_muhurta(dt: datetime, min_score: float = 6.0) -> tuple[bool, str]:
    """
    Check if datetime is good for trading.

    Returns (is_good, reason).
    """
    ch = get_choghadiya(dt)
    nak = get_current_nakshatra(dt)
    score = get_muhurta_score(dt)

    if ch["name"] in BAD_CHOGHADIYA:
        return False, f"Bad Choghadiya: {ch['name']}"

    if ch["name"] == "Marana":
        return False, "Marana period — absolutely avoid"

    if score < min_score:
        return False, f"Muhurta score {score:.1f} below threshold {min_score}"

    if nak["quality"] in ("worst", "bad"):
        return False, f"Bad Nakshatra: {nak['name']}"

    return True, f"Good for trading. Choghadiya: {ch['name']}, Nakshatra: {nak['name']}"


# ─── Public API ────────────────────────────────────────────────────────────────

__all__ = [
    "get_moon_sign",
    "get_current_nakshatra",
    "get_choghadiya",
    "get_muhurta_score",
    "is_trading_muhurta",
    "NAKSHATRAS",
    "CHOGHADIYA_TYPES",
]
