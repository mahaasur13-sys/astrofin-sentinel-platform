"""
Signal classifier — grouping + conflict detection.

Extracted from synthesis_agent.py (v1.0.0).
Used by SynthesisAgent.analyze() for categorisation and conflict resolution.
"""
from __future__ import annotations

from agents._impl.synthesis.weights import ASTRO_REDUCTION, FUNDAMENTAL_BOOST, QUANT_BOOST


CATEGORY_MAP: dict[str, str] = {
    "AstroCouncil": "astro",
    "ElectoralAgent": "astro",
    "BradleyAgent": "astro",
    "TimeWindowAgent": "astro",
    "GannAgent": "astro",
    "ElliotWaveAgent": "astro",
    "CycleAgent": "astro",
    "SolarAgent": "astro",
    "LunarAgent": "astro",
    "PlanetaryAgent": "astro",
    "MuhurtaAgent": "astro",
    "ElectionAgent": "astro",
    "DignityAgent": "astro",
    "FundamentalAgent": "fundamental",
    "InsiderAgent": "fundamental",
    "MacroAgent": "macro",
    "QuantAgent": "quant",
    "MLPredictorAgent": "quant",
    "OptionsFlowAgent": "options",
    "BullResearcher": "sentiment",
    "BearResearcher": "sentiment",
    "SentimentAgent": "sentiment",
    "TechnicalAgent": "technical",
    "MarketAnalyst": "technical",
}

CATEGORY_NAMES = ["astro", "fundamental", "macro", "quant", "options", "sentiment", "technical"]


def group_by_category(signals: list, get_signal_attr) -> dict[str, list]:
    """Group signals by category using CATEGORY_MAP."""
    categories: dict[str, list] = {c: [] for c in CATEGORY_NAMES}

    for sig in signals:
        agent = get_signal_attr(sig, "agent_name", "")
        cat = CATEGORY_MAP.get(agent, "other")
        if cat in categories:
            categories[cat].append(sig)

    return categories


def detect_conflicts(categories: dict[str, list], get_signal_attr) -> list[dict]:
    """Detect inter-category conflicts (e.g. Astro vs Fundamental+Quant)."""
    conflicts: list[dict] = []

    def get_direction(signals: list) -> str:
        if not signals:
            return "NEUTRAL"
        votes = [get_signal_attr(s, "signal", "NEUTRAL").upper() for s in signals]
        long_v = votes.count("LONG") + votes.count("BUY") + votes.count("STRONG_BUY")
        short_v = votes.count("SHORT") + votes.count("SELL") + votes.count("STRONG_SELL")
        if long_v > short_v:
            return "LONG"
        if short_v > long_v:
            return "SHORT"
        return "NEUTRAL"

    astro_dir = get_direction(categories.get("astro", []))
    fund_dir = get_direction(categories.get("fundamental", []))
    quant_dir = get_direction(categories.get("quant", []))

    if astro_dir != "NEUTRAL":
        other = [fund_dir, quant_dir]
        non_neutral = [d for d in other if d != "NEUTRAL"]
        if non_neutral and astro_dir != non_neutral[0]:
            conflicts.append({
                "type": "astro_vs_fundamental_quant",
                "astro": astro_dir,
                "fundamental": fund_dir,
                "quant": quant_dir,
                "resolution": "reduce_astro_weight_by_30pct",
            })

    return conflicts


def apply_conflict_weights(
    categories: dict[str, list],
    conflicts: list[dict],
    cat_weights: dict[str, float],
) -> dict[str, float]:
    """Adjust category weights based on detected conflicts."""
    eff = dict(cat_weights)
    for c in conflicts:
        if c["type"] == "astro_vs_fundamental_quant":
            eff["astro"] = eff.get("astro", 0.25) * (1 - ASTRO_REDUCTION)
            eff["fundamental"] = eff.get("fundamental", 0.15) * (1 + FUNDAMENTAL_BOOST)
            eff["quant"] = eff.get("quant", 0.20) * (1 + QUANT_BOOST)
    return eff
