"""core/reward/astro_reward.py — ATOM-REWARD-001: Astro-Based Reward

Astro-based reward component (simplified sandbox version).
Returns value in [-1, 1] range.

Signals:
  +0.2: Abhijit Muhurta (most auspicious)
  +0.1: Amrita Yoga active
  +0.05 per positive nakshatra
  -0.1: Rahu Kaal active
  -0.2: High volatility regime
  -0.05 per malefic aspect
  0.0: neutral

All clamped to [-1, 1].
"""

from __future__ import annotations


def compute_astro_reward(
    muhurta: str = "neutral",
    yoga: str = "neutral",
    nakshatra: str = "neutral",
    rahu_kaal_active: bool = False,
    regime: str = "NORMAL",
    aspects: list[str] = None,
    moon_sign: str = "",
    tithi: int = 0,
) -> float:
    """
    Compute astro-based reward component.

    Parameters
    ----------
    muhurta : str
        Current muhurta name (e.g. "abhijit", "amrita", "rauda")
    yoga : str
        Current yoga name (e.g. "siddhi", "shakti")
    nakshatra : str
        Current nakshatra name (e.g. "ashwini", "swati")
    rahu_kaal_active : bool
        True during Rahu Kaal (most inauspicious)
    regime : str
        Market regime: LOW, NORMAL, HIGH, EXTREME
    aspects : list
        List of active planetary aspects (e.g. ["sun_trine_moon", "mars_square_venus"])
    moon_sign : str
        Current moon zodiac sign (e.g. "aries", "virgo")
    tithi : int
        Lunar day (1-30)

    Returns
    -------
    float
        Astro reward in [-1.0, 1.0]
    """
    score = 0.0
    aspects = aspects or []

    # ── Muhurta (electional timing) ────────────────────────────────────────
    if muhurta in ("abhijit",):
        score += 0.2  # Most auspicious — victory, success
    elif muhurta in ("amrita", "siddhi", "shakti"):
        score += 0.1  # Good for prosperity
    elif muhurta in ("rauda", "v不利"):
        score -= 0.1  # Inauspicious

    # ── Nakshatra ───────────────────────────────────────────────────────────
    # Pushing nakshatras: Ashwini, Mrigashira, Swati, Hasta, Revati
    pushing = {"ashwini", "mrigashira", "swati", "hasta", "revati", "punarvasu"}
    # Difficult nakshatras: Jyeshtha, Moola, Ashlesha
    difficult = {"jyeshtha", "moola", "ashlesha", "megha"}
    if nakshatra.lower() in pushing:
        score += 0.1
    elif nakshatra.lower() in difficult:
        score -= 0.1

    # ── Rahu Kaal ────────────────────────────────────────────────────────────
    if rahu_kaal_active:
        score -= 0.15

    # ── Regime ──────────────────────────────────────────────────────────────
    if regime == "EXTREME":
        score -= 0.2  # High risk — reduce position
    elif regime == "HIGH":
        score -= 0.1
    elif regime == "LOW":
        score += 0.05  # Low vol — favorable for precision plays

    # ── Planetary aspects ───────────────────────────────────────────────────
    # Positive aspects
    positive_aspects = {
        "sun_trine_moon",
        "sun_trine_venus",
        "sun_trine_jupiter",
        "venus_trine_jupiter",
        "moon_trine_venus",
        "moon_trine_jupiter",
        "jupiter_trine_saturn",
        "venus_conjunct_jupiter",
    }
    # Challenging aspects
    challenging_aspects = {
        "mars_square_saturn",
        "mars_conjunct_saturn",
        "sun_square_saturn",
        "moon_square_saturn",
        "venus_square_saturn",
        "mercury_square_neptune",
    }

    for aspect in aspects:
        aspect_lower = aspect.lower()
        if aspect_lower in positive_aspects:
            score += 0.05
        elif aspect_lower in challenging_aspects:
            score -= 0.05

    # ── Moon sign ───────────────────────────────────────────────────────────
    # Strong signs for trading: Taurus, Cancer, Libra, Capricorn
    strong_moon = {"taurus", "cancer", "libra", "capricorn", "sagittarius"}
    # Weak signs: Aries, Scorpio, Aquarius (impulsive/volatile)
    weak_moon = {"aries", "scorpio", "aquarius", "leo"}
    if moon_sign.lower() in strong_moon:
        score += 0.05
    elif moon_sign.lower() in weak_moon:
        score -= 0.05

    # ── Tithi (lunar day) ───────────────────────────────────────────────────
    # Shukla Paksha (1-15) generally favorable for new ventures
    # Krishna Paksha (16-30) favorable for introspection/consolidation
    if 1 <= tithi <= 15:
        score += 0.05  # Waxing moon favorable

    return max(-1.0, min(1.0, score))
