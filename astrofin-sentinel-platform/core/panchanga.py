"""Panchanga calculations — Choghadiya, Muhurta, Nakshatra, Tithi, Yoga, Karana."""
from datetime import datetime, timedelta, timezone

import swisseph as swe

SAMARA_LAT = 53.20
SAMARA_LON = 50.15
SAMARA_TZ = timezone(timedelta(hours=4))

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
    "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
    "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishtha", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury", "Ketu",
    "Venus", "Sun", "Moon", "Mars", "Rahu",
    "Jupiter", "Saturn", "Mercury", "Ketu", "Venus",
    "Sun", "Moon", "Mars", "Rahu", "Jupiter",
    "Saturn", "Mercury",
]

NAKSHATRA_GRADES = {
    "Ashwini": 85, "Bharani": 60, "Krittika": 65, "Rohini": 95, "Mrigashira": 80,
    "Ardra": 35, "Punarvasu": 85, "Pushya": 95, "Ashlesha": 55, "Magha": 70,
    "Purva Phalguni": 80, "Uttara Phalguni": 90, "Hasta": 90, "Chitra": 75, "Swati": 80,
    "Vishakha": 65, "Anuradha": 85, "Jyeshtha": 50, "Mula": 40, "Purva Ashadha": 75,
    "Uttara Ashadha": 85, "Shravana": 90, "Dhanishtha": 80, "Shatabhisha": 60,
    "Purva Bhadrapada": 65, "Uttara Bhadrapada": 85, "Revati": 95,
}

NAKSHATRA_MULTIPLIERS = {
    "Ashwini": 1.0, "Bharani": 0.8, "Krittika": 0.9, "Rohini": 1.2, "Mrigashira": 1.0,
    "Ardra": 0.6, "Punarvasu": 1.0, "Pushya": 1.2, "Ashlesha": 0.7, "Magha": 0.9,
    "Purva Phalguni": 1.0, "Uttara Phalguni": 1.1, "Hasta": 1.1, "Chitra": 0.9, "Swati": 1.0,
    "Vishakha": 0.8, "Anuradha": 1.0, "Jyeshtha": 0.7, "Mula": 0.6, "Purva Ashadha": 0.9,
    "Uttara Ashadha": 1.0, "Shravana": 1.1, "Dhanishtha": 1.0, "Shatabhisha": 0.8,
    "Purva Bhadrapada": 0.8, "Uttara Bhadrapada": 1.0, "Revati": 1.2,
}

TITHI_NAMES = [
    ("Prathama", 1), ("Dwitiya", 2), ("Tritiya", 3), ("Chaturthi", 4), ("Panchami", 5),
    ("Shashthi", 6), ("Saptami", 7), ("Ashtami", 8), ("Navami", 9), ("Dashami", 10),
    ("Ekadashi", 11), ("Dwadashi", 12), ("Trayodashi", 13), ("Chaturdashi", 14), ("Purnima", 1),
    ("Prathama", 1), ("Dwitiya", 2), ("Tritiya", 3), ("Chaturthi", 4), ("Panchami", 5),
    ("Shashthi", 6), ("Saptami", 7), ("Ashtami", 8), ("Navami", 9), ("Dashami", 10),
    ("Ekadashi", 11), ("Dwadashi", 12), ("Trayodashi", 13), ("Chaturdashi", 14), ("Amavasya", 15),
]

YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarma", "Dhriti", "Shoola", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyana", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Indra", "Vaidhriti",
]

KARANA_NAMES = [
    "Bava", "Balava", "Kaulava", "Taitila", "Gara",
    "Vanija", "Vishti", "Shakuni",
]

_CHOGHADIYA_TABLE = {
    "Sun": ["Udveg", "Charj", "Labh", "Amrit", "Kaal", "Shubh", "Mando", "Kaal"],
    "Mon": ["Amrit", "Vyaghata", "Shubh", "Mando", "Charj", "Labh", "Kaal", "Kaal"],
    "Tue": ["Mando", "Amrit", "Kaal", "Labh", "Kaal", "Charj", "Kaal", "Udveg"],
    "Wed": ["Shubh", "Amrit", "Charj", "Labh", "Kaal", "Kaal", "Kaal", "Mando"],
    "Thu": ["Labh", "Kaal", "Shubh", "Vyaghata", "Kaal", "Amrit", "Kaal", "Mando"],
    "Fri": ["Kaal", "Mando", "Kaal", "Amrit", "Kaal", "Shubh", "Kaal", "Charj"],
    "Sat": ["Amrit", "Charj", "Kaal", "Labh", "Kaal", "Kaal", "Mando", "Shubh"],
}

_DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

CHOGHADIYA_QUALITY = {
    "Amrit": "auspicious", "Shubh": "auspicious", "Labh": "profitable",
    "Charj": "energetic", "Kaal": "inauspicious", "Udveg": "anxious",
    "Vyaghata": "difficult", "Mando": "slow",
}

CHOGHADIYA_ICONS = {
    "Amrit": "🌊", "Shubh": "✅", "Labh": "💰", "Charj": "⚡",
    "Kaal": "⛔", "Udveg": "🔴", "Vyaghata": "⚠️", "Mando": "🐌",
}


def _julday(dt: datetime) -> float:
    """DateTime UTC -> Julian day via pyswisseph."""
    return swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0 + dt.second / 3600.0)


def _sunrise_sunset(dt_local: datetime) -> tuple[datetime, datetime]:
    """Return sunrise & sunset as SAMARA timezone datetimes using pyswisseph."""
    utc = dt_local.astimezone(timezone.utc)
    jd = _julday(utc)

    geo = (SAMARA_LON, SAMARA_LAT, 0)
    flags = swe.FLG_SWIEPH

    rise_res, rise_ret = swe.rise_trans(jd, swe.SUN, swe.CALC_RISE, geo, 0, 0, flags)
    set_res, set_ret = swe.rise_trans(jd, swe.SUN, swe.CALC_SET, geo, 0, 0, flags)

    if rise_res != 0:
        raise RuntimeError(f"Sunrise not found for {dt_local.date()}")
    if set_res != 0:
        raise RuntimeError(f"Sunset not found for {dt_local.date()}")

    jd_rise = rise_ret[0]
    jd_set = set_ret[0]

    rise_utc = _jd_to_utc(jd_rise)
    set_utc = _jd_to_utc(jd_set)

    return rise_utc.astimezone(SAMARA_TZ), set_utc.astimezone(SAMARA_TZ)


def _jd_to_utc(jd: float) -> datetime:
    """Julian day -> UTC datetime."""
    year, month, day, ut = swe.revjul(jd)
    hours = int(ut)
    minutes = int((ut - hours) * 60)
    seconds = int(((ut - hours) * 60 - minutes) * 60)
    return datetime(year, month, day, hours, minutes, seconds, tzinfo=timezone.utc)


def calculate_panchanga(dt: datetime, moon_lon: float, sun_lon: float = 0.0) -> dict:
    """Calculate full panchanga for given datetime and moon longitude."""
    nakshatra = get_nakshatra(moon_lon)
    tithi = get_tithi(moon_lon, sun_lon) if sun_lon else {"name": "—", "number": 0, "is_waxing": True, "paksha": "—"}
    yoga = get_yoga(moon_lon, sun_lon) if sun_lon else {"name": "—", "number": 0}
    karana = get_karana(moon_lon)

    choghadiya_slots = get_choghadiya(dt)
    current_slot = None
    for slot in choghadiya_slots:
        start_h, start_m = [int(x) for x in slot["start"].split(":")]
        end_h, end_m = [int(x) for x in slot["end"].split(":")]
        slot_start = dt.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
        slot_end = dt.replace(hour=end_h, minute=end_m, second=0, microsecond=0)
        if slot_start <= dt < slot_end:
            current_slot = slot
            break
    if not current_slot and choghadiya_slots:
        current_slot = choghadiya_slots[0]

    return {
        "timestamp": dt.isoformat(),
        "nakshatra": nakshatra,
        "tithi": tithi,
        "yoga": yoga,
        "karana": karana,
        "choghadiya_current": current_slot or {},
        "choghadiya_slots": choghadiya_slots,
    }


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
        "name": name, "number": num,
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
    """Return Choghadiya periods for the day using real sunrise/sunset (pyswisseph, Samara coords)."""
    try:
        sunrise, sunset = _sunrise_sunset(dt)
    except RuntimeError:
        sunrise = dt.replace(hour=4, minute=38, second=0, microsecond=0, tzinfo=SAMARA_TZ)
        sunset = dt.replace(hour=20, minute=53, second=0, microsecond=0, tzinfo=SAMARA_TZ)

    # Next sunrise for night Choghadiya
    next_dt = dt + timedelta(days=1)
    try:
        next_sunrise, _ = _sunrise_sunset(next_dt)
    except RuntimeError:
        next_sunrise = dt.replace(hour=4, minute=38, second=0, microsecond=0, tzinfo=SAMARA_TZ) + timedelta(days=1)

    day_secs = (sunset - sunrise).total_seconds()
    night_secs = (next_sunrise - sunset).total_seconds()
    day_period_secs = day_secs / 8
    night_period_secs = night_secs / 8

    day_of_week_idx = dt.weekday()
    day_name = _DAY_NAMES[day_of_week_idx]
    periods = _CHOGHADIYA_TABLE[day_name]

    results = []

    # Day Choghadiya (8 periods: sunrise → sunset)
    for i in range(8):
        ps = sunrise + timedelta(seconds=day_period_secs * i)
        pe = sunrise + timedelta(seconds=day_period_secs * (i + 1))
        chog_name = periods[i]
        quality = CHOGHADIYA_QUALITY.get(chog_name, "neutral")
        icon = CHOGHADIYA_ICONS.get(chog_name, "❓")
        results.append({
            "period": i + 1,
            "name": chog_name,
            "start": ps.strftime("%H:%M"),
            "end": pe.strftime("%H:%M"),
            "quality": quality,
            "icon": icon,
            "recommended": quality == "auspicious",
        })

    # Night Choghadiya (8 periods: sunset → next sunrise)
    for i in range(8):
        ps = sunset + timedelta(seconds=night_period_secs * i)
        pe = sunset + timedelta(seconds=night_period_secs * (i + 1))
        chog_name = periods[(i + 8) % 8] if i < 8 else periods[i]
        quality = CHOGHADIYA_QUALITY.get(chog_name, "neutral")
        icon = CHOGHADIYA_ICONS.get(chog_name, "❓")
        results.append({
            "period": i + 9,
            "name": chog_name,
            "start": ps.strftime("%H:%M"),
            "end": pe.strftime("%H:%M"),
            "quality": quality,
            "icon": icon,
            "recommended": quality == "auspicious",
            "night": True,
        })

    return results


def get_muhurta_score(
    choghadiya_name: str, nakshatra: dict, tithi: dict, yoga: dict
) -> dict:
    """Calculate overall muhurta score (0-100)."""
    base = {
        "Amrit": 90, "Shubh": 80, "Labh": 70, "Charj": 50,
        "Kaal": 20, "Udveg": 15, "Vyaghata": 25, "Mando": 30,
    }
    choghadiya_score = base.get(choghadiya_name, 40)

    nakshatra_grade = NAKSHATRA_GRADES.get(nakshatra.get("name", ""), 50)
    nakshatra_mult = NAKSHATRA_MULTIPLIERS.get(nakshatra.get("name", ""), 1.0)

    final = int(choghadiya_score * 0.4 + nakshatra_grade * 0.5 + 10 * 0.1)
    final = min(100, max(0, final))

    return {
        "score": final,
        "choghadiya_score": choghadiya_score,
        "nakshatra_grade": nakshatra_grade,
        "nakshatra_multiplier": nakshatra_mult,
        "breakdown": f"Choghadiya({choghadiya_name}):{choghadiya_score} + Nakshatra({nakshatra.get('name','?')}):{nakshatra_grade}",
    }


def get_election_grade(nakshatra_name: str) -> int:
    """Return favorable grade (0-100) for this nakshatra for trading."""
    return NAKSHATRA_GRADES.get(nakshatra_name, 50)


def get_nakshatra_multiplier(nakshatra_name: str) -> float:
    """Return multiplier for astro signal based on nakshatra."""
    return NAKSHATRA_MULTIPLIERS.get(nakshatra_name, 1.0)
