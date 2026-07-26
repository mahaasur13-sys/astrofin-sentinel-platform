"""meta_rl/inference.py — Runtime Meta-RL ensemble routing (F1)."""

from __future__ import annotations

import logging
import time
from typing import Any

from meta_rl.checkpoint import load_checkpoint, is_checkpoint_fresh

logger = logging.getLogger(__name__)

# Fallback static weights (AGENTS.md: Agent Board)
STATIC_WEIGHTS: dict[str, float] = {
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
    "GannAgent": 0.03,
    "CycleAgent": 0.05,
    "TimeWindowAgent": 0.02,
}

_CACHED_WEIGHTS: dict[str, float] | None = None
_CACHE_TS: float = 0.0
CACHE_TTL: float = 60.0  # seconds


def _load_weights() -> dict[str, float]:
    """Load weights: Meta-RL checkpoint > static fallback."""
    if is_checkpoint_fresh():
        checkpoint = load_checkpoint("latest")
        if checkpoint and "weights" in checkpoint:
            w = checkpoint["weights"]
            if isinstance(w, dict) and w:
                logger.info("loaded Meta-RL weights from checkpoint: %d agents", len(w))
                return w

    logger.info("using static fallback weights (%d agents)", len(STATIC_WEIGHTS))
    return STATIC_WEIGHTS.copy()


def get_agent_weights(use_cache: bool = True) -> dict[str, float]:
    """Return current agent weights with optional in-memory cache."""
    global _CACHED_WEIGHTS, _CACHE_TS

    if use_cache and _CACHED_WEIGHTS is not None:
        if time.monotonic() - _CACHE_TS < CACHE_TTL:
            return _CACHED_WEIGHTS

    t0 = time.monotonic()
    _CACHED_WEIGHTS = _load_weights()
    _CACHE_TS = time.monotonic()
    elapsed_ms = (time.monotonic() - t0) * 1000
    logger.debug("weights loaded in %.1fms", elapsed_ms)
    return _CACHED_WEIGHTS


def apply_weights_to_decisions(
    decisions: list[dict[str, Any]],
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Apply Meta-RL weights to agent decisions and produce ensemble result."""
    if weights is None:
        weights = get_agent_weights()

    total_weight = 0.0
    weighted_signal: float = 0.0
    contribs: dict[str, float] = {}

    for d in decisions:
        agent_name = d.get("agent", "unknown")
        w = weights.get(agent_name, 0.0)
        if w <= 0:
            continue

        signal_map = {"BUY": 1.0, "LONG": 1.0, "SELL": -1.0, "SHORT": -1.0, "HOLD": 0.0, "NEUTRAL": 0.0}
        signal = signal_map.get(str(d.get("signal", "NEUTRAL")).upper(), 0.0)
        confidence = float(d.get("confidence", 0)) / 100.0

        score = signal * confidence * w
        weighted_signal += score
        total_weight += w
        contribs[agent_name] = score

    if total_weight > 0:
        weighted_signal /= total_weight

    if weighted_signal > 0.15:
        final_signal = "BUY"
    elif weighted_signal < -0.15:
        final_signal = "SELL"
    else:
        final_signal = "HOLD"

    return {
        "signal": final_signal,
        "weighted_score": round(weighted_signal, 4),
        "agent_contributions": contribs,
        "meta_rl_active": bool(is_checkpoint_fresh()),
    }
