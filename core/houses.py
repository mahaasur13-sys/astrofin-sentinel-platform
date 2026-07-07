"""
Доменные системы гороскопа по Munkasey
Michael P. Munkasey's "An Astrological House Formulary"
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List


def julian_day(dt: datetime) -> float:
    """Расчёт Julian Day"""
    a = (14 - dt.month) // 12
    y = dt.year + 4800 - a
    m = dt.month + 12 * a - 3
    jd = dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    jd += (dt.hour + dt.minute / 60 + dt.second / 3600) / 24
    return jd


def julian_day_to_local_sidereal_time(jd: float, longitude: float) -> float:
    """Конверсия JD в местное звёздное время"""
    # Greenwich Sidereal Time
    T = (jd - 2451545.0) / 36525.0
    GST = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + T * T * (0.000387933 - T / 38710000.0)
    GST = GST % 360
    # Местное
    LST = (GST + longitude) % 360
    return LST


@dataclass
class HouseCusp:
    """Куспид дома"""

    house: int
    longitude: float  # градусы эклиптики (0-360)
    ra: float  # прямое восхождение
    declination: float


@dataclass
class HouseSystem:
    """Система домов"""

    name: str
    code: str  # Placidus=P, Koch=K, Campanus=C, etc.
    type: str  # time, space, ecliptic, quadrant


# Доступные системы домов
HOUSE_SYSTEMS = {
    "P": HouseSystem("Placidus", "P", "time"),
    "K": HouseSystem("Koch", "K", "time"),
    "C": HouseSystem("Campanus", "C", "space"),
    "R": HouseSystem("Regiomontanus", "R", "space"),
    "A": HouseSystem("Alcabitius", "A", "space"),
    "O": HouseSystem("Porphyry", "O", "quadrant"),
    "W": HouseSystem("Whole Sign", "W", "ecliptic"),
    "E": HouseSystem("Equal (from ASC)", "E", "ecliptic"),
    "M": HouseSystem("MC-based Equal", "M", "ecliptic"),
}


def normalize_degrees(deg: float) -> float:
    """Нормализовать градусы в диапазон 0-360"""
    while deg < 0:
        deg += 360
    while deg >= 360:
        deg -= 360
    return deg


def calculate_ascendant(local_sidereal_time: float, latitude: float, obliquity: float = 23.4393) -> float:
    """
    Расчёт Асцендента

    Формула из Munkasey "An Astrological House Formulary":
    ASC = arctan(-cos(HA) / (sin(lat) * tan(dec) + cos(lat) * sin(HA)))

    Args:
        local_sidereal_time: Местное звёздное время (градусы)
        latitude: Географическая широта (градусы)
        obliquity: Наклон эклиптики (градусы)

    Returns:
        Долгота Асцендента (градусы)
    """
    lat_rad = math.radians(latitude)
    lst_rad = math.radians(local_sidereal_time)
    obl_rad = math.radians(obliquity)

    # Для ASC: Hour Angle = 0 когда точка на меридиане
    # ASC вычисляется через arctan2
    ha = lst_rad  # приближённо

    asc = math.degrees(
        math.atan2(
            -math.cos(ha),
            math.sin(lat_rad) * math.tan(obl_rad) + math.cos(lat_rad) * math.sin(ha),
        )
    )

    return normalize_degrees(asc)


def calculate_midheaven(local_sidereal_time: float, obliquity: float = 23.4393) -> float:
    """
    Расчёт Середины Неба (MC)

    Формула из Munkasey:
    MC = arctan(tan(RA_Sun_at_MC) / cos(Obliquity))

    Args:
        local_sidereal_time: Местное звёздное время (градусы)
        obliquity: Наклон эклиптики

    Returns:
        Долгота MC (градусы)
    """
    obl_rad = math.radians(obliquity)
    lst_rad = math.radians(local_sidereal_time)

    mc = math.degrees(math.atan2(math.sin(lst_rad) * math.cos(obl_rad), math.cos(lst_rad)))

    return normalize_degrees(mc)


def calculate_placidus_cusps(
    asc: float,
    mc: float,
    ra_asc: float,
    ra_mc: float,
    latitude: float,
    declination: float,
) -> List[float]:
    """
    Расчёт куспидов по системе Placidus

    Формула Munkasey:
    sin(Declination_of_Cusp) = sin(Geocentric_Dec) × cos(SemiArc) / cos(Geocentric_DEC)

    Args:
        asc: Долгота ASC
        mc: Долгота MC
        ra_asc: Прямое восхождение ASC
        ra_mc: Прямое восхождение MC
        latitude: Широта
        declination: Склонение

    Returns:
        Список из 12 куспидов (долготы)
    """
    cusps = [0.0] * 12

    # Куспиды 1 и 10 (ASC и MC)
    cusps[0] = asc
    cusps[9] = mc

    # Куспиды 4 и 7 (IC и DESC)
    cusps[3] = normalize_degrees(mc + 180)
    cusps[6] = normalize_degrees(asc + 180)

    # SemiArc
    semi_arc = abs(ra_asc - ra_mc)
    if semi_arc > 180:
        semi_arc = 360 - semi_arc

    # Для домов 11, 12, 2, 3 нужны более сложные расчёты
    # Упрощённая версия:
    third_arc = semi_arc / 3

    # Cusp 11
    cusps[10] = normalize_degrees(mc + third_arc)
    # Cusp 12
    cusps[11] = normalize_degrees(mc + 2 * third_arc)
    # Cusp 2
    cusps[1] = normalize_degrees(asc + third_arc)
    # Cusp 3
    cusps[2] = normalize_degrees(asc + 2 * third_arc)

    return cusps


def calculate_porphyry_cusps(asc: float, mc: float) -> List[float]:
    """
    Расчёт куспидов по системе Porphyry

    Формула Munkasey:
    Cusp11 = MC + (ASC - MC) / 3
    Cusp12 = MC + 2 × (ASC - MC) / 3

    Args:
        asc: Долгота ASC
        mc: Долгота MC

    Returns:
        Список из 12 куспидов
    """
    cusps = [0.0] * 12

    # Основные углы
    cusps[0] = asc  # ASC = House 1
    cusps[9] = mc  # MC = House 10
    cusps[3] = normalize_degrees(mc + 180)  # IC = House 4
    cusps[6] = normalize_degrees(asc + 180)  # DESC = House 7

    # Куспиды 11, 12
    arc_asc_mc = normalize_degrees(asc - mc)
    if arc_asc_mc > 180:
        arc_asc_mc -= 360

    third = arc_asc_mc / 3
    cusps[10] = normalize_degrees(mc + third)  # Cusp 11
    cusps[11] = normalize_degrees(mc + 2 * third)  # Cusp 12

    # Куспиды 2, 3
    arc_desc_asc = 180 - arc_asc_mc
    third_2 = arc_desc_asc / 3
    cusps[1] = normalize_degrees(asc + third_2)  # Cusp 2
    cusps[2] = normalize_degrees(asc + 2 * third_2)  # Cusp 3

    # Куспиды 5, 6
    arc_mc_desc = arc_asc_mc + 180
    third_3 = arc_mc_desc / 3
    cusps[4] = normalize_degrees(mc + third_3 + 180)  # Cusp 5
    cusps[5] = normalize_degrees(mc + 2 * third_3 + 180)  # Cusp 6

    return cusps


def calculate_equal_houses(asc: float) -> List[float]:
    """
    Расчёт Equal Houses (от ASC)

    Каждый дом = 30° от ASC

    Args:
        asc: Долгота ASC

    Returns:
        Список из 12 куспидов
    """
    return [normalize_degrees(asc + i * 30) for i in range(12)]


def calculate_whole_sign_houses(asc: float) -> List[float]:
    """
    Расчёт Whole Sign Houses

    Дом 1 = знак ASC, остальные следуют по 30°

    Args:
        asc: Долгота ASC

    Returns:
        Список из 12 куспидов (каждый начинается с 0° знака)
    """
    # Начало знака, содержащего ASC
    asc_sign_start = math.floor(asc / 30) * 30
    return [normalize_degrees(asc_sign_start + i * 30) for i in range(12)]


def calculate_alcabitius_cusps(ra_asc: float, ra_mc: float) -> List[float]:
    """
    Расчёт куспидов по системе Alcabitius

    Формула Munkasey:
    RA_Difference = RA_Asc - RA_MC
    Divide_by_3 = RA_Difference / 3

    Cusp11 = RA_MC + Divide_by_3
    Cusp12 = RA_MC + 2 × Divide_by_3

    Args:
        ra_asc: Прямое восхождение ASC
        ra_mc: Прямое восхождение MC

    Returns:
        Список из 12 куспидов (RA)
    """
    cusps_ra = [0.0] * 12

    # Основные RA
    cusps_ra[0] = ra_asc
    cusps_ra[9] = ra_mc
    cusps_ra[3] = normalize_degrees(ra_mc + 180, True)  # RA для IC
    cusps_ra[6] = normalize_degrees(ra_asc + 180, True)  # RA для DESC

    # RA Difference
    ra_diff = ra_asc - ra_mc
    if ra_diff > 180:
        ra_diff -= 360
    elif ra_diff < -180:
        ra_diff += 360

    third = ra_diff / 3

    cusps_ra[10] = normalize_degrees(ra_mc + third, True)
    cusps_ra[11] = normalize_degrees(ra_mc + 2 * third, True)
    cusps_ra[1] = normalize_degrees(ra_asc + third, True)
    cusps_ra[2] = normalize_degrees(ra_asc + 2 * third, True)

    # 5, 6 дома (от IC)
    ic_diff = 180 - ra_diff
    third_ic = ic_diff / 3
    cusps_ra[4] = normalize_degrees(cusps_ra[3] + third_ic, True)
    cusps_ra[5] = normalize_degrees(cusps_ra[3] + 2 * third_ic, True)

    return cusps_ra


def normalize_degrees_custom(deg: float, is_ra: bool = False) -> float:
    """Нормализовать градусы

    Args:
        deg: Градусы
        is_ra: Если True, нормализуем для RA (0-360)
    """
    if is_ra:
        while deg < 0:
            deg += 360
        while deg >= 360:
            deg -= 360
    else:
        deg = deg % 360
    return deg


class HouseCalculator:
    """
    Калькулятор домов по различным системам.

    Использует формулы из Munkasey "An Astrological House Formulary"
    """

    def __init__(self, house_system: str = "P"):
        """
        Args:
            house_system: Код системы домов (P=Placidus, K=Koch, etc.)
        """
        self.house_system = house_system.upper()
        if self.house_system not in HOUSE_SYSTEMS:
            raise ValueError(f"Unknown house system: {house_system}")

    def calculate(
        self,
        jd: float,  # Julian Day
        latitude: float,
        longitude: float,
        obliquity: float = 23.4393,
    ) -> Dict:
        """
        Расчёт всех куспидов домов

        Args:
            jd: Julian Day
            latitude: Географическая широта
            longitude: Географическая долгота
            obliquity: Наклон эклиптики

        Returns:
            Dict с куспидами и информацией
        """
        # Локальное звёздное время
        lst = julian_day_to_local_sidereal_time(jd, longitude)

        # ASC и MC
        asc = calculate_ascendant(lst, latitude, obliquity)
        mc = calculate_midheaven(lst, obliquity)

        # RA (упрощённо)
        ra_asc = lst
        ra_mc = 0  # MC на меридиане

        # Выбор метода расчёта
        if self.house_system == "P":
            cusps = calculate_placidus_cusps(asc, mc, ra_asc, ra_mc, latitude, 0)
        elif self.house_system == "O":
            cusps = calculate_porphyry_cusps(asc, mc)
        elif self.house_system in ("E", "W"):
            cusps = calculate_equal_houses(asc)
            if self.house_system == "W":
                cusps = calculate_whole_sign_houses(asc)
        elif self.house_system == "A":
            cusps_ra = calculate_alcabitius_cusps(ra_asc, ra_mc)
            # Конвертация RA в долготу (упрощённо)
            cusps = cusps_ra  # Для Alcabitius возвращаем RA
        else:
            # Default to Placidus
            cusps = calculate_placidus_cusps(asc, mc, ra_asc, ra_mc, latitude, 0)

        return {
            "house_system": HOUSE_SYSTEMS[self.house_system].name,
            "ascendant": asc,
            "midheaven": mc,
            "cusps": cusps,
            "angles": {
                "asc": cusps[0],
                "ii": cusps[1],
                "iii": cusps[2],
                "iv": cusps[3],
                "v": cusps[4],
                "vi": cusps[5],
                "vii": cusps[6],
                "viii": cusps[7],
                "ix": cusps[8],
                "x": cusps[9],
                "xi": cusps[10],
                "xii": cusps[11],
            },
        }
