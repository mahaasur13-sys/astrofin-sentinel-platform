"""
Synthesis weights — single source of truth for agent/category weights.

Constants extracted from synthesis_agent.py (v1.0.0).
Loaded from agents/weights.yaml with fallback to hardcoded defaults.
"""
from __future__ import annotations

import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

MIN_AGENTS_FALLBACK = 2
MAX_CONFIDENCE = 90
MIN_CONFIDENCE = 30

# Conflict resolution parameters
ASTRO_REDUCTION = 0.30
FUNDAMENTAL_BOOST = 0.18
QUANT_BOOST = 0.12

# Default agent weights
AGENT_WEIGHTS: dict[str, float] = {
    "FundamentalAgent": 0.20,
    "QuantAgent": 0.20,
    "MacroAgent": 0.15,
    "OptionsFlowAgent": 0.15,
    "SentimentAgent": 0.10,
    "TechnicalAgent": 0.10,
    "BullResearcher": 0.05,
    "BearResearcher": 0.05,
    "ElectoralAgent": 0.03,
    "BradleyAgent": 0.03,
    "CycleAgent": 0.05,
    "TimeWindowAgent": 0.02,
    "GannAgent": 0.03,
}

# Default category weights (aggregated from agent weights)
CATEGORY_WEIGHTS: dict[str, float] = {
    "fundamental": 0.20,
    "quant": 0.20,
    "macro": 0.15,
    "options": 0.15,
    "astro": 0.16,
    "sentiment": 0.20,
    "technical": 0.10,
}


def _load_weights() -> dict:
    """Load agent weights from YAML config, falling back to defaults."""
    paths = [
        Path("agents/weights.yaml"),
        Path("config/weights.yaml"),
    ]
    for p in paths:
        if p.exists():
            try:
                with open(p) as f:
                    data = yaml.safe_load(f)
                if data and isinstance(data, dict):
                    logger.debug("weights_loaded", extra={"source": str(p)})
                    return _normalize(data, p.name)
            except Exception:
                logger.warning("weights_load_failed", extra={"path": str(p)})
    return dict(AGENT_WEIGHTS)


def _normalize(d: dict, name: str) -> dict:
    """Normalize weights to sum to 1.0 so individual values stay proportional."""
    total = sum(v for v in d.values() if isinstance(v, (int, float)))
    if total <= 0:
        logger.warning("weights_zero_sum", extra={"source": name})
        return dict(AGENT_WEIGHTS)
    return {k: v / total for k, v in d.items() if isinstance(v, (int, float))}
