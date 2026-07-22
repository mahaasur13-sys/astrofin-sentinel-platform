"""
Muhurtha — Electoral Astrology Calculator
Based on B.V. Raman's "Muhurtha" principles.
Implements Panchanga (Tithi, Nakshatra, Yoga) + Ascendant calculation.
"""

import logging
from datetime import datetime

import swisseph as swe

log = logging.getLogger(__name__)


# ======================================================
#  SETTINGS — customize before use
# ======================================================

EPHE_PATH = "/home/workspace/AstroFinSentinelV5/ephe"
LAT, LON = 55.75, 37.62  # Moscow. Change to your coordinates
AYANAMSA = swe.SIDM_LAHIRI  # Lahiri (Raman standard)

# ======================================================
#  CONSTANTS
# ======================================================

TITHIS = [
    "Пратипат",
    "Двитья",
    "Тритья",
    "Чатуртхи",
    "Панчами",
    "Шаштхи",
    "Саптами",
    "Аштами",
    "Навами",
    "Дашими",
    "Экадаши",
    "Двадаши",
    "Траядаши",
    "Чатурдаши",
    "Пурнима / Амавасья",
]

NAKSHATRAS = [
    "Ашвини",
    "Бхарани",
    "Криттика",
    "Рохини",
    "Мригашира",
    "Ардра",
    "Пунарвасу",
    "Пушья",
    "Ашлеша",
    "Магха",
    "Пурва-Пхалгуни",
    "Уттара-Пхалгуни",
    "Хаста",
    "Читра",
    "Свати",
    "Вишакха",
    "Анурадха",
    "Джешта",
    "Мула",
    "Пурва-Ашадха",
    "Уттара-Ашадха",
    "Шравана",
    "Дхништа",
    "Шатабхиша",
    "Пурва-Бхадра",
    "Уттара-Бхадра",
    "Ревати",
]

YOGAS = [
    "Вишкамбха",
    "Прити",
    "Аюшман",
    "Саубхагья",
    "Шобхана",
    "Атиганда",
    "Суккарман",
    "Дхрити",
    "Шула",
    "Ганда",
    "Вриддхи",
    "Дхрува",
    "Вьягхата",
    "Харшана",
    "Ваджра",
    "Сиддхи",
    "Вьятипата",
    "Вариян",
    "Паригха",
    "Шива",
    "Сиддха",
    "Садхья",
    "Шубха",
    "Шукла",
    "Брахма",
    "Индра",
    "Вайдхрити",
]

# ======================================================
#  INIT
# ======================================================

swe.set_ephe_path(EPHE_PATH)
swe.set_sid_mode(AYANAMSA)


def jd_from_datetime(dt_utc: datetime) -> float:
    return swe.julday(
        dt_utc.year,
        dt_utc.month,
        dt_utc.day,
        dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600,
    )


def get_panchang(jd: float) -> dict:
    sun_lon, *_ = swe.calc_ut(jd, swe.SUN)[0]
    moon_lon, *_ = swe.calc_ut(jd, swe.MOON)[0]

    # Tithi
    diff = (moon_lon - sun_lon + 360) % 360
    tithi_num = (int(diff / 12) % 15) + 1
    tithi_name = TITHIS[tithi_num - 1]

    # Nakshatra
    nakshatra_num = int(moon_lon / 13.333333) % 27
    nakshatra = NAKSHATRAS[nakshatra_num]

    # Yoga
    yoga_num = int((sun_lon + moon_lon) / 13.333333) % 27
    yoga = YOGAS[yoga_num]

    return {
        "tithi_name": tithi_name,
        "tithi_num": tithi_num,
        "nakshatra": nakshatra,
        "nakshatra_num": nakshatra_num,
        "yoga": yoga,
        "yoga_num": yoga_num,
        "sun_lon": sun_lon,
        "moon_lon": moon_lon,
    }


def get_houses(jd: float, lat: float, lon: float) -> dict:
    houses = swe.houses(jd, lat, lon, b"P")[0]
    asc = houses[0]
    # House cusps 1-12
    cusps = list(houses[0:12])
    return {"asc": asc, "cusps": cusps}


def print_muhurtha(dt_utc: datetime, lat: float = LAT, lon: float = LON):
    jd = jd_from_datetime(dt_utc)
    p = get_panchang(jd)
    h = get_houses(jd, lat, lon)

    log.info(f"\n{'=' * 60}")
    log.info(f"  МУХУРТА  —  {dt_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    log.info(f"{'=' * 60}")
    log.info(f"  Титхи     : {p['tithi_name']} ({p['tithi_num']}/15)")
    log.info(f"  Накшатра  : {p['nakshatra']} ({p['nakshatra_num']}+1/27)")
    log.info(f"  Йога       : {p['yoga']}")
    log.info(f"  Асцендент : {h['asc']:.4f}°")
    log.info(f"  Солнце    : {p['sun_lon']:.4f}°")
    log.info(f"  Луна      : {p['moon_lon']:.4f}°")
    log.info(f"{'=' * 60}")
    return {"panchang": p, "houses": h}


# ======================================================
#  USAGE
# ======================================================

if __name__ == "__main__":
    now = datetime.now()
    print_muhurtha(now)

    # Example: check a specific time
    # test = datetime(2026, 3, 25, 10, 30, 0)
    # print_muhurtha(test)
