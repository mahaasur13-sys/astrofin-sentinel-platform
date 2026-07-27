"""
Synthesis voter — weighted voting, synthesis, and guard logic.

Extracted from synthesis_agent.py (v1.0.0).
"""
from __future__ import annotations

from core.base_agent import SignalDirection
from agents._impl.synthesis.weights import CATEGORY_WEIGHTS, MAX_CONFIDENCE, MIN_CONFIDENCE


def vote(
    categories: dict[str, list],
    get_signal_attr,
    eff: dict[str, float] | None = None,
) -> tuple[SignalDirection, int, str]:
    """Weighted vote across categories with EC-01 hubris cap."""
    cat_weights = eff if eff is not None else CATEGORY_WEIGHTS
    long_w = 0.0
    short_w = 0.0
    neutral_w = 0.0

    for cat, signals in categories.items():
        if not signals:
            continue
        w = cat_weights.get(cat, 0.10)
        for sig in signals:
            conf = get_signal_attr(sig, "confidence", 50)
            direction = get_signal_attr(sig, "signal", "NEUTRAL").upper()
            if direction in ("LONG", "BUY", "STRONG_BUY"):
                long_w += conf * w
            elif direction in ("SHORT", "SELL", "STRONG_SELL"):
                short_w += conf * w
            else:
                neutral_w += conf * w

    total = long_w + short_w + neutral_w
    if total > 0:
        long_pct = long_w / total
        short_pct = short_w / total
    else:
        long_pct = short_pct = 0.5

    if long_pct > 0.55:
        direction = SignalDirection.LONG
        confidence = min(MAX_CONFIDENCE, 50 + int(long_pct * 40))
        reasoning = f"Long consensus: {long_pct * 100:.0f}% weighted votes"
    elif short_pct > 0.55:
        direction = SignalDirection.SHORT
        confidence = min(MAX_CONFIDENCE, 50 + int(short_pct * 40))
        reasoning = f"Short consensus: {short_pct * 100:.0f}% weighted votes"
    else:
        direction = SignalDirection.NEUTRAL
        confidence = 50
        reasoning = f"No strong consensus: Long {long_pct * 100:.0f}% | Short {short_pct * 100:.0f}%"

    confidence, guard = apply_guards(direction, confidence)
    if guard:
        reasoning += f" [{guard}]"

    return direction, confidence, reasoning


def apply_guards(direction: SignalDirection, confidence: int) -> tuple[int, str | None]:
    """Apply EC-01 hubris cap and MIN_CONFIDENCE floor."""
    adjusted = min(confidence, MAX_CONFIDENCE)
    if adjusted < MIN_CONFIDENCE:
        return MIN_CONFIDENCE, "GUARD-TRIGGERED-NEUTRAL"
    return adjusted, None
