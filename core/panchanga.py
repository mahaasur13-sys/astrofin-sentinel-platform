"""core/panchanga.py — Vedic Panchanga Calculations
Muhurta, Nakshatra, Tithi, Yoga, Karana, Choghadiya
"""

from datetime import datetime, timedelta, timezone
from agents._impl.ephemeris_decorator import require_ephemeris

SIDEREAL_YEAR = 365.25636
LUNAR_MONTH = 27.3217
TROPICAL_RASHI = [
    "Ari",
    "Tau",
    "Gem",
    "Can",
    "Leo",
    "Vir",
    "Lib",
    "Sco",
    "Sag",
    "Cap",
    "Aqu",
    "Pis",
]
NAKSHATRA_NAMES = [
    "Ashwini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashira",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Ashlesha",
    "Magha",
    "Purva Phalguni",
    "Uttara Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Mula",
    "Purva Ashadha",
    "Uttara Ashadha",
    "Shravana",
    "Dhanishta",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
]
YOGA_NAMES = [
    "Vishkumbh",
    "Priti",
    "Ayushman",
    "Saubhagya",
    "Shobhana",
    "Atiganda",
    "Sukarman",
    "Driti",
    "Shula",
    "Ganda",
    "Vriddhi",
    "Dhruva",
    "Vyaghata",
    "Harshana",
    "Vajra",
    "Siddhi",
    "Vyatipata",
    "Variyana",
    "Parigha",
    "Shiva",
    "Siddha",
    "Sadhya",
    "Shubha",
    "Brahmana",
    "Indra",
    "Aindra",
    "Brahma",
    "Aushadha",
]
KARANA_NAMES = [
    "Bava",
    "Balava",
    "Kaulava",
    "Taitila",
    "Garija",
    "Vanija",
    "Vishti",
    "Sakuni",
    "Chatuspada",
    "Naga",
]
CHOGHADIYA_SEQ = [
    "Amrit",
    "Shubh",
    "Labh",
    "Charj",
    "Kaal",
    "Udveg",
    "Vyaghata",
    "Mando",
]

NAKSHATRA_LORDS = [
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
    "Ketu",
    "Venus",
    "Sun",
]
TITHI_NAMES = [
    ("Shukla Pratipad", 1),
    ("Shukla Dvitiya", 2),
    ("Shukla Tritiyaya", 3),
    ("Shukla Chaturthi", 4),
    ("Shukla Panchami", 5),
    ("Shukla Shashti", 6),
    ("Shukla Saptami", 7),
    ("Shukla Ashtami", 8),
    ("Shukla Navami", 9),
    ("Shukla Dashami", 10),
    ("Shukla Ekadashi", 11),
    ("Shukla Dvadashi", 12),
    ("Shukla Trayodashi", 13),
    ("Shukla Chaturdashi", 14),
    ("Poornima", 15),
    ("Krishna Pratipad", 16),
    ("Krishna Dvitiya", 17),
    ("Krishna Tritiyaya", 18),
    ("Krishna Chaturthi", 19),
    ("Krishna Panchami", 20),
    ("Krishna Shashti", 21),
    ("Krishna Saptami", 22),
    ("Krishna Ashtami", 23),
    ("Krishna Navami", 24),
    ("Krishna Dashami", 25),
    ("Krishna Ekadashi", 26),
    ("Krishna Dvadashi", 27),
    ("Krishna Trayodashi", 28),
    ("Krishna Chaturdashi", 29),
    ("Amavasya", 30),
]

_CHOGHADIYA_TABLE = {
    "Sunrise": [
        "Amrit",
        "Shubh",
        "Labh",
        "Charj",
        "Kaal",
        "Udveg",
        "Vyaghata",
        "Mando",
    ],
    "Sunrise+1": [
        "Shubh",
        "Labh",
        "Charj",
        "Kaal",
        "Udveg",
        "Vyaghata",
        "Mando",
        "Amrit",
    ],
    "Sunrise+2": [
        "Labh",
        "Charj",
        "Kaal",
        "Udveg",
        "Vyaghata",
        "Mando",
        "Amrit",
        "Shubh",
    ],
    "Sunrise+3": [
        "Charj",
        "Kaal",
        "Udveg",
        "Vyaghata",
        "Mando",
        "Amrit",
        "Shubh",
        "Labh",
    ],
    "Sunrise+4": [
        "Kaal",
        "Udveg",
        "Vyaghata",
        "Mando",
        "Amrit",
        "Shubh",
        "Labh",
        "Charj",
    ],
    "Sunrise+5": [
        "Udveg",
        "Vyaghata",
        "Mando",
        "Amrit",
        "Shubh",
        "Labh",
        "Charj",
        "Kaal",
    ],
    "Sunrise+6": [
        "Vyaghata",
        "Mando",
        "Amrit",
        "Shubh",
        "Labh",
        "Charj",
        "Kaal",
        "Udveg",
    ],
    "Sunrise+7": [
        "Mando",
        "Amrit",
        "Shubh",
        "Labh",
        "Charj",
        "Kaal",
        "Udveg",
        "Vyaghata",
    ],
}


def _julian_day(dt: datetime) -> float:
    """Convert datetime to Julian Day."""
    y, m, d = dt.year, dt.month, dt.day
    if m <= 2:
        y, m = y - 1, m + 12
    A = int(y / 100)
    B = 2 - A + int(A / 4)
    jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524.5
    return jd + dt.hour / 24.0 + dt.minute / 1440.0


def _sunrise(dt: datetime, lat: float = 25.20, lon: float = 55.27) -> datetime:
    """Approximate sunrise for Dubai. Returns datetime at ~06:15 GST."""
    dubai_tz = timezone(timedelta(hours=4))
    base = dt.replace(hour=6, minute=15, second=0, microsecond=0, tzinfo=dubai_tz)
    return base


def get_nakshatra(moon_degree: float) -> dict:
    """Return nakshatra for moon degree (0-360)."""
    nak_num = int(moon_degree * 27 / 360)
    nak_num = min(nak_num, 26)
    pada = int((moon_degree * 27 / 360 - nak_num) * 4) + 1
    lord = NAKSHATRA_LORDS[nak_num]
    return {
        "name": NAKSHATRA_NAMES[nak_num],
        "number": nak_num + 1,
        "lord": lord,
        "pada": pada,
        "degree_in_nakshatra": round((moon_degree * 27 / 360 - nak_num) * 360 / 13.33, 2),
    }


def get_tithi(moon_degree: float, sun_degree: float) -> dict:
    """Return tithi from moon and sun degrees."""
    diff = moon_degree - sun_degree
    if diff < 0:
        diff += 360
    tithi_num = int(diff * 30 / 360)
    tithi_num = min(tithi_num, 29)
    name, num = TITHI_NAMES[tithi_num]
    is_waxing = tithi_num < 15
    return {
        "name": name,
        "number": num,
        "is_waxing": is_waxing,
        "paksha": "Shukla" if is_waxing else "Krishna",
    }


def get_yoga(moon_degree: float, sun_degree: float) -> dict:
    """Return yoga from moon and sun degrees."""
    yoga_deg = moon_degree + sun_degree
    yoga_num = int(yoga_deg * 27 / 360) % 27
    return {"name": YOGA_NAMES[yoga_num], "number": yoga_num + 1}


def get_karana(moon_degree: float) -> dict:
    """Return karana (half of tithi)."""
    tithi = int(moon_degree * 30 / 360) % 30
    karana_num = tithi % 7
    if tithi == 0 or tithi == 14:
        karana_num = 7
    return {
        "name": KARANA_NAMES[karana_num],
        "number": karana_num + 1 if karana_num < 7 else 8,
    }


def get_choghadiya(dt: datetime) -> list[dict]:
    """Return Choghadiya periods for the day (sunrise to sunset, 8 periods)."""
    sunrise = _sunrise(dt)
    results = []
    for i in range(8):
        period_start = sunrise + timedelta(hours=i)
        period_end = period_start + timedelta(hours=1)
        chog_name = _CHOGHADIYA_TABLE["Sunrise"][i]
        quality = {
            "Amrit": "auspicious",
            "Shubh": "auspicious",
            "Labh": "profitable",
            "Charj": "energetic",
            "Kaal": "inauspicious",
            "Udveg": "anxious",
            "Vyaghata": "difficult",
            "Mando": "slow",
        }.get(chog_name, "neutral")
        icons = {
            "Amrit": "🌊",
            "Shubh": "✅",
            "Labh": "💰",
            "Charj": "⚡",
            "Kaal": "⛔",
            "Udveg": "🔴",
            "Vyaghata": "⚠️",
            "Mando": "🐌",
        }
        results.append(
            {
                "period": i + 1,
                "name": chog_name,
                "start": period_start.strftime("%H:%M"),
                "end": period_end.strftime("%H:%M"),
                "quality": quality,
                "icon": icons.get(chog_name, "❓"),
                "recommended": quality == "auspicious",
            }
        )
    return results


def get_muhurta_score(choghadiya_name: str, nakshatra: dict, tithi: dict, yoga: dict) -> dict:
    """Calculate overall muhurta score (0-100)."""
    base = {
        "Amrit": 90,
        "Shubh": 85,
        "Labh": 75,
        "Charj": 70,
        "Kaal": 20,
        "Udveg": 15,
        "Vyaghata": 25,
        "Mando": 30,
    }.get(choghadiya_name, 50)
    nak_bonus = {
        "Pushya": 15,
        "Rohini": 10,
        "Uttara Phalguni": 10,
        "Swati": 10,
        "Shravana": 10,
        "Ashwini": 5,
        "Magha": -5,
        "Mula": -5,
    }.get(nakshatra.get("name", ""), 0)
    tith_bonus = {
        "Shukla Panchami": 10,
        "Shukla Navami": -10,
        "Amavasya": -15,
        "Poornima": 10,
        "Ekadashi": -5,
    }.get(tithi.get("name", ""), 0)
    score = min(100, max(0, base + nak_bonus + tith_bonus))
    return {
        "score": score,
        "verdict": "Excellent" if score >= 85 else "Good" if score >= 70 else "Average" if score >= 50 else "Poor",
        "base_choghadiya": base,
        "nakshatra_bonus": nak_bonus,
        "tithi_bonus": tith_bonus,
    }


@require_ephemeris
def calculate_panchanga(dt: datetime) -> dict:
    """Calculate full panchanga for a given datetime in Dubai."""
    from core.ephemeris import get_planetary_positions

    pos = get_planetary_positions(dt)
    moon_deg = pos.get("Moon", {"degrees": 0})["degrees"]
    sun_deg = pos.get("Sun", {"degrees": 0})["degrees"]
    moon_sign = int(moon_deg / 30)
    rashi = TROPICAL_RASHI[moon_sign]
    nak = get_nakshatra(moon_deg)
    tit = get_tithi(moon_deg, sun_deg)
    yog = get_yoga(moon_deg, sun_deg)
    kar = get_karana(moon_deg)
    choghadiya = get_choghadiya(dt)
    muhurta_score = get_muhurta_score(choghadiya[0]["name"], nak, tit, yog) if choghadiya else {"score": 50}
    return {
        "datetime": dt.isoformat(),
        "nakshatra": nak,
        "tithi": tit,
        "yoga": yog,
        "karana": kar,
        "moon_rashi": rashi,
        "choghadiya": choghadiya,
        "best_muhurta": max(
            choghadiya,
            key=lambda x: {"Amrit": 4, "Shubh": 3, "Labh": 2}.get(x["name"], 0),
        )
        if choghadiya
        else None,
        "muhurta_score": muhurta_score,
    }
