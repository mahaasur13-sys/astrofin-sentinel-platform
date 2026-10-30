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
    "ElliotAgent": 0.03,
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


def _resolve_agent_key(name: str) -> str | None:
    """Map a short or full agent name to its AGENT_WEIGHTS key.

    'Fundamental' / 'FundamentalAgent' -> 'FundamentalAgent'; 'Technical' -> 'TechnicalAgent';
    'BullResearcher' stays as is. None if the agent is not listed.
    """
    n = str(name or "")
    for cand in (n, f"{n}Agent", n[: -len("Agent")] if n.endswith("Agent") else None):
        if cand and cand in AGENT_WEIGHTS:
            return cand
    return None


def get_agent_weight(name: str) -> float:
    """Single source of per-agent weights.

    1. AGENT_WEIGHTS by short/full name;
    2. otherwise CATEGORY_WEIGHTS of the agent's category (synthesis.classifier.CATEGORY_MAP);
    3. otherwise 0.0 and logger.error (unknown agent is excluded, never silently weighted).
    """
    key = _resolve_agent_key(name)
    if key is not None:
        return AGENT_WEIGHTS[key]
    from agents._impl.synthesis.classifier import CATEGORY_MAP  # lazy: classifier imports this module

    n = str(name or "")
    cat = CATEGORY_MAP.get(n) or CATEGORY_MAP.get(f"{n}Agent")
    if cat in CATEGORY_WEIGHTS:
        return CATEGORY_WEIGHTS[cat]
    logger.error("unknown_agent_weight", extra={"agent_name": n})
    return 0.0


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
