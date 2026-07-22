"""trading/vedic/nakshatra_risk.py — Nakshatra Risk Multiplier + Elective Logic

Sprint 6: Production Readiness & Ensemble Logic.
Каждая Nakshatra имеет "энергетику" — множитель риска от 0.6 до 1.4.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ElectionGrade(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    NEUTRAL = "neutral"
    CAUTION = "caution"
    AVOID = "avoid"


DANGEROUS_NAKSHATRAS: frozenset[str] = frozenset({
    "Mula", "Jyeshtha", "Ardra", "Ashlesha", "Shatabhisha",
    "Purva Bhadrapada", "Krittika",
})
FAVORABLE_NAKSHATRAS: frozenset[str] = frozenset({
    "Pushya", "Uttara Bhadrapada", "Shravana", "Rohini",
    "Hasta", "Uttara Phalguni", "Swati", "Anuradha",
    "Punarvasu", "Revati", "Ashwini", "Mrigashira",
})

NAKSHATRA_RISK: dict[str, float] = {
    "Ashwini":            1.15,
    "Bharani":            0.85,
    "Krittika":           1.25,
    "Rohini":             1.10,
    "Mrigashira":         0.95,
    "Ardra":              1.30,
    "Punarvasu":          0.90,
    "Pushya":             0.75,
    "Ashlesha":           1.20,
    "Magha":              1.05,
    "Purva Phalguni":     1.25,
    "Uttara Phalguni":    0.80,
    "Hasta":              0.85,
    "Chitra":             1.15,
    "Swati":              0.95,
    "Vishakha":           1.10,
    "Anuradha":           0.90,
    "Jyeshtha":           1.35,
    "Mula":               1.40,
    "Purva Ashadha":      1.20,
    "Uttara Ashadha":     0.85,
    "Shravana":           0.80,
    "Dhanishta":          1.10,
    "Shatabhisha":        1.25,
    "Purva Bhadrapada":   1.30,
    "Uttara Bhadrapada":  0.75,
    "Revati":             0.90,
}

NAKSHATRA_ELECTION: dict[str, ElectionGrade] = {
    "Pushya":             ElectionGrade.EXCELLENT,
    "Uttara Bhadrapada":  ElectionGrade.EXCELLENT,
    "Shravana":           ElectionGrade.EXCELLENT,
    "Rohini":             ElectionGrade.GOOD,
    "Hasta":              ElectionGrade.GOOD,
    "Uttara Phalguni":    ElectionGrade.GOOD,
    "Swati":              ElectionGrade.GOOD,
    "Anuradha":           ElectionGrade.GOOD,
    "Punarvasu":          ElectionGrade.GOOD,
    "Revati":             ElectionGrade.GOOD,
    "Ashwini":            ElectionGrade.NEUTRAL,
    "Bharani":            ElectionGrade.NEUTRAL,
    "Mrigashira":         ElectionGrade.NEUTRAL,
    "Magha":              ElectionGrade.NEUTRAL,
    "Chitra":             ElectionGrade.NEUTRAL,
    "Vishakha":           ElectionGrade.NEUTRAL,
    "Purva Ashadha":      ElectionGrade.NEUTRAL,
    "Uttara Ashadha":     ElectionGrade.NEUTRAL,
    "Dhanishta":          ElectionGrade.NEUTRAL,
    "Purva Phalguni":     ElectionGrade.CAUTION,
    "Krittika":           ElectionGrade.CAUTION,
    "Shatabhisha":        ElectionGrade.CAUTION,
    "Ashlesha":           ElectionGrade.CAUTION,
    "Ardra":              ElectionGrade.AVOID,
    "Jyeshtha":           ElectionGrade.AVOID,
    "Mula":               ElectionGrade.AVOID,
    "Purva Bhadrapada":   ElectionGrade.AVOID,
}


def get_nakshatra_multiplier(nakshatra: str) -> float:
    return NAKSHATRA_RISK.get(nakshatra, 1.0)


def get_election_grade(nakshatra: str) -> ElectionGrade:
    return NAKSHATRA_ELECTION.get(nakshatra, ElectionGrade.NEUTRAL)


def is_dangerous_nakshatra(nakshatra: str) -> bool:
    return nakshatra in DANGEROUS_NAKSHATRAS


def is_favorable_nakshatra(nakshatra: str) -> bool:
    return nakshatra in FAVORABLE_NAKSHATRAS


def format_nakshatra_explanation(nakshatra: str) -> str:
    mult = get_nakshatra_multiplier(nakshatra)
    grade = get_election_grade(nakshatra)
    danger = "⚠️ Опасная" if is_dangerous_nakshatra(nakshatra) else ""
    favor = "✅ Благоприятная" if is_favorable_nakshatra(nakshatra) else ""
    tags = " ".join(filter(None, [danger, favor]))
    return (
        f"{nakshatra}: множитель ×{mult:.2f} | "
        f"grade={grade.value} | {tags}"
    ).strip()
