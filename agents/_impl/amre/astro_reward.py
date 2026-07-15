"""amre/astro_reward.py - ATOM-021: Astro-enhanced Reward Function"""

"""Astronomically-informed reward for KARL trading decisions."""

from typing import Any

from .trajectory import MarketState

LUNAR_PHASES = [
    (0, "New Moon", "caution"),
    (45, "Waxing Crescent", "opportunity"),
    (90, "First Quarter", "neutral"),
    (135, "Waxing Gibbous", "momentum"),
    (180, "Full Moon", "peak"),
    (225, "Waning Gibbous", "momentum"),
    (270, "Last Quarter", "neutral"),
    (315, "Waning Crescent", "caution"),
]

PLANETARY_ASPECTS = {
    "conjunction": {"weight": 1.0, "description": "intensification"},
    "sextile": {"weight": 0.6, "description": "opportunity"},
    "square": {"weight": -0.8, "description": "tension"},
    "trine": {"weight": 0.8, "description": "harmony"},
    "opposition": {"weight": -0.6, "description": "conflict"},
}

ZODIAC_ARC = {
    "Aries": {"nature": "aggressive", "element": "fire", "score": 0.7},
    "Taurus": {"nature": "stable", "element": "earth", "score": 0.6},
    "Gemini": {"nature": "volatile", "element": "air", "score": 0.5},
    "Cancer": {"nature": "sensitive", "element": "water", "score": 0.4},
    "Leo": {"nature": "bold", "element": "fire", "score": 0.8},
    "Virgo": {"nature": "analytical", "element": "earth", "score": 0.5},
    "Libra": {"nature": "balanced", "element": "air", "score": 0.6},
    "Scorpio": {"nature": "intense", "element": "water", "score": 0.7},
    "Sagittarius": {"nature": "expansive", "element": "fire", "score": 0.8},
    "Capricorn": {"nature": "disciplined", "element": "earth", "score": 0.9},
    "Aquarius": {"nature": "revolutionary", "element": "air", "score": 0.5},
    "Pisces": {"nature": "intuitive", "element": "water", "score": 0.4},
}

NAKSHATRA_SCORES = [
    0.8,
    0.7,
    0.6,
    0.9,
    0.5,
    0.4,
    0.7,
    0.8,
    0.6,
    0.5,
    0.9,
    0.4,
    0.8,
    0.7,
    0.6,
    0.5,
    0.9,
    0.4,
    0.7,
    0.8,
    0.6,
    0.5,
    0.4,
    0.9,
    0.7,
    0.8,
]


def get_lunar_phase_score(moon_longitude: float) -> float:
    phase_angle = moon_longitude % 180
    nearest = min(LUNAR_PHASES, key=lambda x: abs(x[0] - phase_angle))
    nature = nearest[2]
    scores = {
        "caution": 0.5,
        "neutral": 0.7,
        "opportunity": 0.8,
        "momentum": 0.9,
        "peak": 0.6,
    }
    return scores.get(nature, 0.7)


def get_planetary_aspect_score(aspects: list[dict[str, Any]]) -> float:
    if not aspects:
        return 1.0
    total_score = 0.0
    total_weight = 0.0
    for aspect in aspects:
        aspect_type = aspect.get("aspect_type", "").lower()
        if aspect_type in PLANETARY_ASPECTS:
            config = PLANETARY_ASPECTS[aspect_type]
            weight = config["weight"]
            is_benefic = aspect.get("planet", "") in ["Jupiter", "Venus", "Mercury"]
            is_malefic = aspect.get("planet", "") in ["Mars", "Saturn", "Rahu", "Ketu"]
            modifier = 1.0
            if is_benefic and weight > 0:
                modifier = 1.2
            elif is_malefic and weight < 0:
                modifier = 1.3
            total_score += weight * modifier
            total_weight += abs(weight)
    if total_weight == 0:
        return 1.0
    normalized = 1.0 + (total_score / total_weight) * 0.5
    return max(0.5, min(1.5, normalized))


def get_nakshatra_score(nakshatra_longitude: float) -> float:
    nak_index = int(nakshatra_longitude / 13.3333) % 27
    return NAKSHATRA_SCORES[int(nak_index)]


def compute_astro_reward(
    state: MarketState,
    moon_longitude: float,
    aspects: list[dict[str, Any]],
    nakshatra_longitude: float,
    base_reward: float,
) -> dict[str, float]:
    lunar_score = get_lunar_phase_score(moon_longitude)
    aspect_score = get_planetary_aspect_score(aspects)
    nakshatra_score = get_nakshatra_score(nakshatra_longitude)
    astro_score = lunar_score * 0.3 + aspect_score * 0.4 + nakshatra_score * 0.3
    regime_multipliers = {"LOW": 1.2, "NORMAL": 1.0, "HIGH": 0.7, "EXTREME": 0.3}
    regime = getattr(state, "regime", "NORMAL")
    regime_mult = regime_multipliers.get(regime, 1.0)
    signal = getattr(state, "signal", None)
    if signal in ("LONG", "BUY"):
        is_waxing = moon_longitude < 180
        lunar_direction_bonus = 1.1 if is_waxing else 0.95
    elif signal in ("SHORT", "SELL"):
        is_waning = moon_longitude >= 180
        lunar_direction_bonus = 1.1 if is_waning else 0.95
    else:
        lunar_direction_bonus = 1.0
    final_reward = base_reward * astro_score * regime_mult * lunar_direction_bonus
    confidence_boost = 0
    if astro_score > 1.1:
        confidence_boost = 5
    elif astro_score < 0.8:
        confidence_boost = -5
    return {
        "base_reward": round(base_reward, 4),
        "lunar_score": round(lunar_score, 3),
        "aspect_score": round(aspect_score, 3),
        "nakshatra_score": round(nakshatra_score, 3),
        "astro_score": round(astro_score, 3),
        "regime_mult": regime_mult,
        "lunar_direction_bonus": round(lunar_direction_bonus, 3),
        "final_reward": round(final_reward, 4),
        "confidence_boost": confidence_boost,
        "regime": regime,
    }


def get_astro_market_phase(moon_longitude: float, sun_longitude: float = 0) -> dict[str, Any]:
    lunar_day = int(moon_longitude / 12) % 30
    if lunar_day < 5:
        phase, sentiment, momentum = "New Moon Cycle", "cautious", "building"
    elif lunar_day < 10:
        phase, sentiment, momentum = "Waxing Crescent", "opportunistic", "increasing"
    elif lunar_day < 15:
        phase, sentiment, momentum = "First Quarter", "volatile", "strong"
    elif lunar_day < 20:
        phase, sentiment, momentum = "Waxing Gibbous", "bullish", "high"
    elif lunar_day < 25:
        phase, sentiment, momentum = "Full Moon", "peak", "maximum"
    else:
        phase, sentiment, momentum = "Waning Phase", "corrective", "declining"
    return {
        "phase": phase,
        "sentiment": sentiment,
        "momentum": momentum,
        "lunar_day": lunar_day,
        "favorable_for": "LONG" if "Waxing" in phase else "SHORT" if "Waning" in phase else "NEUTRAL",
    }
