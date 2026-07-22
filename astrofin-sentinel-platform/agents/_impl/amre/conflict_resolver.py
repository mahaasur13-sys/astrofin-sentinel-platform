"""agents/_impl/amre/conflict_resolver.py — Bull/Bear conflict resolution engine.

P2-04 refactoring: extracted from agents/karl_synthesis.py.
Resolves conflicts between opposing agent signals (Bull ↔ Bear) using:
  - Weight reduction for conflicting agents
  - Regime-aware prioritization
  - Confidence dampening based on disagreement severity
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

CONFLICT_THRESHOLD = 0.35  # 35% signal divergence triggers conflict
WEIGHT_REDUCTION = 0.10    # Reduce each conflicting agent's weight by 10%


def resolve_conflict(agent_a, agent_b) -> None:
    """Resolve conflict between two agents by reducing both weights.

    Original from agents/karl_synthesis.py:resolve_conflict().
    Kept backward-compatible — both agents modified in-place.
    """
    agent_a.metadata["weight"] = max(
        0.0, agent_a.metadata.get("weight", 0.10) - WEIGHT_REDUCTION
    )
    agent_b.metadata["weight"] = max(
        0.0, agent_b.metadata.get("weight", 0.10) - WEIGHT_REDUCTION
    )


def detect_bull_bear_conflict(
    signals: list, threshold: float = CONFLICT_THRESHOLD
) -> tuple[bool, float]:
    """Detect if there's a significant Bull/Bear conflict among agent signals.

    Returns (has_conflict, divergence_score).
    """
    if not signals:
        return False, 0.0
    long_count = sum(
        1 for s in signals
        if _sig_str(s) in ("LONG", "BUY", "STRONG_BUY")
    )
    short_count = sum(
        1 for s in signals
        if _sig_str(s) in ("SHORT", "SELL", "STRONG_SELL")
    )
    total = len(signals)
    if total == 0:
        return False, 0.0
    long_pct = long_count / total
    short_pct = short_count / total
    if long_pct > threshold and short_pct > threshold:
        divergence = long_pct - short_pct
        return True, abs(divergence)
    return False, abs(long_pct - short_pct)


def resolve_bull_bear_conflict(
    signals: list, max_confidence_penalty: int = 20
) -> dict:
    """Full conflict resolution: detect conflict → reduce weight → adjust confidence.

    Returns dict with keys:
      - has_conflict: bool
      - divergence: float
      - confidence_penalty: int
      - resolved_signals: list (weights adjusted)
    """
    has_conflict, divergence = detect_bull_bear_conflict(signals)
    if not has_conflict:
        return {
            "has_conflict": False,
            "divergence": divergence,
            "confidence_penalty": 0,
            "resolved_signals": signals,
        }
    penalty = min(max_confidence_penalty, int(divergence * 100))
    logger.info(
        f"[ConflictResolver] Bull/Bear conflict: divergence={divergence:.2f}, "
        f"penalty={penalty}"
    )
    reduced = list(signals)
    for s in reduced:
        if hasattr(s, "metadata"):
            s.metadata["weight"] = max(
                0.0, s.metadata.get("weight", 0.10) - WEIGHT_REDUCTION
            )
        elif isinstance(s, dict):
            s["metadata"] = s.get("metadata", {})
            s["metadata"]["weight"] = max(
                0.0, s["metadata"].get("weight", 0.10) - WEIGHT_REDUCTION
            )
    return {
        "has_conflict": True,
        "divergence": divergence,
        "confidence_penalty": penalty,
        "resolved_signals": reduced,
    }


def _sig_str(s) -> str:
    """Extract signal string from AgentResponse or dict."""
    if hasattr(s, "signal"):
        return str(getattr(s, "signal")).upper()
    if isinstance(s, dict):
        return str(s.get("signal", "NEUTRAL")).upper()
    return "NEUTRAL"
