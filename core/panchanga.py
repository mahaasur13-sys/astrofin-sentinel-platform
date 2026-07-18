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
# Standard Choghadiya names (same sequence as _CHOGHADIYA_TABLE["Sunrise"])
CHOGHADIYA_BASE = ["Amrit", "Kala", "Shubh", "Roga", "Udveg", "Chara", "Labh"]

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

# Weekday → day lord name → offset in CHOGHADIYA_BASE
_DAY_LORD_NAMES: dict[int, str] = {
    0: "Amrit",   # Monday (Moon)
    1: "Roga",    # Tuesday (Mars)
    2: "Labh",    # Wednesday (Mercury)
    3: "Shubh",   # Thursday (Jupiter)
    4: "Chara",   # Friday (Venus)
    5: "Kala",    # Saturday (Saturn)
    6: "Udveg",   # Sunday (Sun)
}

def _day_choghadiya_names(weekday: int) -> list[str]:
    """Return 8 Choghadiya names for the day, starting from day lord."""
    idx = CHOGHADIYA_BASE.index(_DAY_LORD_NAMES.get(weekday, "Amrit"))
    result: list[str] = [CHOGHADIYA_BASE[(idx + i) % 7] for i in range(7)]
    result.append(CHOGHADIYA_BASE[idx])  # 8th period = day lord repeat
    return result

def _night_choghadiya_names(weekday: int) -> list[str]:
    """Return 8 Choghadiya names for night, offset from day lord + 5."""
    idx = CHOGHADIYA_BASE.index(_DAY_LORD_NAMES.get(weekday, "Amrit"))
    night_idx = (idx + 5) % 7
    result: list[str] = [CHOGHADIYA_BASE[(night_idx + i) % 7] for i in range(7)]
    result.append(CHOGHADIYA_BASE[night_idx])  # 8th period = night lord repeat
    return result

# CHOGHADIYA quality/icon/scores maps (name → value)
_CHOG_QUALITY: dict[str, str] = {
    "Amrit": "auspicious", "Shubh": "auspicious", "Labh": "profitable",
    "Chara": "neutral", "Kala": "inauspicious",
    "Udveg": "inauspicious", "Roga": "inauspicious",
}
_CHOG_ICON: dict[str, str] = {
    "Amrit": "🌊", "Shubh": "✅", "Labh": "💰", "Chara": "⚡",
    "Kala": "⛔", "Udveg": "🔴", "Roga": "⚠️",
}
_CHOG_SCORE: dict[str, int] = {
    "Amrit": 90, "Shubh": 85, "Labh": 75, "Chara": 70,
    "Kala": 20, "Udveg": 15, "Roga": 25,
}



def _get_tz_offset_hours(dt: datetime) -> float:
    """Return UTC offset in hours from a timezone-aware datetime, else 0."""
    if dt.tzinfo is not None:
        off = dt.tzinfo.utcoffset(dt)
        if off is not None:
            return off.total_seconds() / 3600.0
    return 0.0


def _sunrise(dt: datetime, lat: float = 25.20, lon: float = 55.27) -> datetime:
    """Astronomical sunrise for given location — defaults Dubai. NOAA solar calculator."""
    return _solar_event(dt, lat, lon, is_sunrise=True)


def _sunset(dt: datetime, lat: float = 25.20, lon: float = 55.27) -> datetime:
    """Astronomical sunset for given location — defaults Dubai."""
    return _solar_event(dt, lat, lon, is_sunrise=False)


def _solar_event(dt, lat, lon, is_sunrise, tz_offset_hours: float = 4.0):
    y, m, d_ = dt.year, dt.month, dt.day
    if m <= 2:
        y -= 1; m += 12
    jd = int(365.25*(y+4716))+int(30.6001*(m+1))+d_+2-int(y/100)+int(y/400)-1524.5
    jc = (jd-2451545.0)/36525.0
    gl = (280.46646+jc*(36000.76983+jc*0.0003032))%360
    ga = 357.52911+jc*(35999.05029-0.0001537*jc)
    ec = 0.016708634-jc*(0.000042037+0.0000001267*jc)
    ar = _m.radians(ga)
    eqc = _m.sin(ar)*(1.914602-jc*(0.004817+0.000014*jc))+_m.sin(2*ar)*(0.019993-0.000101*jc)+_m.sin(3*ar)*0.000289
    tl = gl+eqc
    om = 125.04-1934.136*jc
    al = tl-0.00569-0.00478*_m.sin(_m.radians(om))
    obq = 23+(26+((21.448-jc*(46.815+jc*(0.00059-jc*0.001813))))/60)/60
    obc = obq+0.00256*_m.cos(_m.radians(om))
    decl = _m.degrees(_m.asin(_m.sin(_m.radians(obc))*_m.sin(_m.radians(al))))
    yf = _m.tan(_m.radians(obc/2))**2
    et = 4*_m.degrees(yf*_m.sin(2*_m.radians(gl))-2*ec*_m.sin(ar)+4*ec*yf*_m.sin(ar)*_m.cos(2*_m.radians(gl))-0.5*yf**2*_m.sin(4*_m.radians(gl))-1.25*ec**2*_m.sin(2*ar))
    zen = 90.833
    cha = (_m.cos(_m.radians(zen))-_m.sin(_m.radians(lat))*_m.sin(_m.radians(decl)))/(_m.cos(_m.radians(lat))*_m.cos(_m.radians(decl)))
    cha = max(-1.0, min(1.0, cha))
    ha = _m.degrees(_m.acos(cha))
    sn = 12.0-et/60.0-lon/15.0
    ute = sn-ha/15.0 if is_sunrise else sn+ha/15.0
    ute %= 24
    sh = (ute + tz_offset_hours) % 24
    h = int(sh); mi = int((sh - h) * 60); s = int(((sh - h) * 60 - mi) * 60)
    return dt.replace(hour=h, minute=mi, second=s, microsecond=0, tzinfo=timezone(timedelta(hours=tz_offset_hours)))


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
        "degree_in_nakshatra": round((moon_degree * 27 / 360 - nak_num) * (360 / 27), 2),
    }


def get_tithi(moon_degree: float, sun_degree: float) -> dict:
    """Return tithi from moon and sun degrees."""
    diff = moon_degree - sun_degree
    if diff < 0:
        diff += 360
    tithi_num = int(diff * 30 / 360)
    tithi_num = min(tithi_num, 29)
    name = TITHI_NAMES[tithi_num]
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


def get_choghadiya(dt: datetime, lat: float = 25.20, lon: float = 55.27) -> list[dict]:
    """Return Choghadiya periods for the day (sunrise to sunset, 8 periods).
    
    Defaults to Dubai (25.20°N, 55.27°E).  Pass lat/lon for other locations.
    """
    tz_off = _get_tz_offset_hours(dt)
    sunrise = _sunrise(dt, lat, lon, tz_off)
    sunset = _sunset(dt, lat, lon, tz_off)
    day_seconds = (sunset - sunrise).total_seconds()
    period_seconds = max(60, day_seconds / 8)
    results = []
    day_names = _day_choghadiya_names(dt.weekday())
    for i in range(8):
        period_start = sunrise + timedelta(seconds=i * period_seconds)
        period_end = period_start + timedelta(seconds=period_seconds)
        chog_name = day_names[i]
        quality = _CHOG_QUALITY.get(chog_name, "neutral")
        icons = _CHOG_ICON.get(chog_name, "❓")
        results.append(
            {
                "period": i + 1,
                "name": chog_name,
                "start": period_start.strftime("%H:%M"),
                "end": period_end.strftime("%H:%M"),
                "quality": quality,
                "icon": icons,
                "recommended": quality == "auspicious",
            }
        )
    return results


# ─── Night Choghadiya Support ────────────────────────────────────────────────

def _night_start_end(dt: datetime, lat: float = 25.20, lon: float = 55.27) -> tuple[datetime, datetime]:
    """Return night period bracket: today sunset → tomorrow sunrise."""
    tz_off = _get_tz_offset_hours(dt)
    today_sunset = _sunset(dt, lat, lon, tz_off)
    tomorrow_sunrise = _sunrise(dt + timedelta(days=1), lat, lon, tz_off)
    return today_sunset, tomorrow_sunrise


def get_night_choghadiya(dt: datetime, lat: float = 25.20, lon: float = 55.27) -> list[dict]:
    """Return Night Choghadiya periods (sunset → next sunrise, 8 periods)."""
    night_start, night_end = _night_start_end(dt, lat, lon)
    night_duration = (night_end - night_start).total_seconds()
    period_seconds = night_duration / 8
    wday = dt.weekday()
    seq = _night_choghadiya_names(wday)
    results = []
    for i in range(8):
        start = night_start + timedelta(seconds=i * period_seconds)
        end = night_start + timedelta(seconds=(i + 1) * period_seconds)
        name = seq[i]
        quality = _CHOG_QUALITY.get(name, "neutral")
        results.append({
            "period": i + 1,
            "name": name,
            "start": start.strftime("%H:%M"),
            "end": end.strftime("%H:%M"),
            "quality": quality,
            "icon": _CHOG_ICON.get(name, "❓"),
            "recommended": quality == "auspicious",
        })
    return results


def get_all_choghadiya(dt: datetime) -> dict[str, list[dict]]:
    """Return both day and night Choghadiya periods."""
    return {
        "day": get_choghadiya(dt),
        "night": get_night_choghadiya(dt),
    }


def get_muhurta_score(choghadiya_name: str, nakshatra: dict, tithi: dict, yoga: dict) -> dict:
    """Calculate overall muhurta score (0-100)."""
    base = _CHOG_SCORE.get(choghadiya_name, 50)
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
    """Calculate full panchanga for a given datetime and location.  Defaults to Dubai (25.20°N, 55.27°E)."""
    from core.ephemeris import get_planetary_positions

    pos = get_planetary_positions(dt)
    moon_deg = pos.get("Moon", {"degrees": 0})["degrees"]
    sun_deg = pos.get("Sun", {"degrees": 0})["degrees"]
    moon_sign = int(moon_deg / 30) % 12 % 12  # clamp for 360.0
    rashi = TROPICAL_RASHI[moon_sign]
    nak = get_nakshatra(moon_deg)
    tit = get_tithi(moon_deg, sun_deg)
    yog = get_yoga(moon_deg, sun_deg)
    kar = get_karana(moon_deg, sun_deg)
    choghadiya = get_choghadiya(dt, lat, lon)
    night_choghadiya = get_night_choghadiya(dt, lat, lon)

    # Active Choghadiya at dt (not just period 1)
    all_chog = choghadiya + night_choghadiya
    active_chog = next(
        (c for c in all_chog if c["start"] <= dt.strftime("%H:%M") < c["end"]),
        choghadiya[0] if choghadiya else None,
    )
    muhurta_score = get_muhurta_score(active_chog["name"], nak, tit, yog) if active_chog else {"score": 50}

    # Best muhurta — only auspicious, or None
    auspicious = [c for c in all_chog if c["name"] in ("Amrit", "Shubh", "Labh")]
    best_muhurta = max(
        auspicious,
        key=lambda x: {"Amrit": 4, "Shubh": 3, "Labh": 2}.get(x["name"], 0),
    ) if auspicious else None

    return {
        "datetime": dt.isoformat(),
        "location": {"lat": lat, "lon": lon},
        "nakshatra": nak,
        "tithi": tit,
        "yoga": yog,
        "karana": kar,
        "moon_rashi": rashi,
        "choghadiya": choghadiya,
        "night_choghadiya": night_choghadiya,
        "best_muhurta": best_muhurta,
        "muhurta_score": muhurta_score,
    }
# test
