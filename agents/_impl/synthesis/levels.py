"""
Price level calculation — entry zones, stops, targets.

Extracted from synthesis_agent.py (v1.0.0).
Uses dynamic risk_pct from VolatilityEngine (R-07).
"""
from __future__ import annotations

from core.base_agent import SignalDirection


def calculate_levels(
    direction: SignalDirection,
    price: float,
    risk_pct: float,
) -> dict:
    """Calculate entry zones, stop-loss, and take-profit targets.

    Args:
        direction: LONG, SHORT, or NEUTRAL
        price: current price
        risk_pct: dynamic risk percentage from VolatilityEngine

    Returns:
        dict with entry_zone, stop_loss, targets, position_size, risk_pct_used
    """
    rr_ratio = 2.5
    stop_dist = risk_pct * 1.5
    tp_dist = risk_pct * rr_ratio

    if direction == SignalDirection.LONG:
        entry_low = price * (1 - risk_pct * 0.5)
        entry_high = price * (1 + risk_pct * 0.5)
        stop = price * (1 - stop_dist)
        targets = [price * (1 + tp_dist * i) for i in [1, 2, 3]]
        position = risk_pct / 2
    elif direction == SignalDirection.SHORT:
        entry_low = price * (1 - risk_pct * 0.5)
        entry_high = price * (1 + risk_pct * 0.5)
        stop = price * (1 + stop_dist)
        targets = [price * (1 - tp_dist * i) for i in [1, 2, 3]]
        position = risk_pct / 2
    else:
        entry_low = price * (1 - risk_pct * 0.25)
        entry_high = price * (1 + risk_pct * 0.25)
        stop = price * (1 - stop_dist * 0.5)
        targets = [
            price * (1 + risk_pct * 0.5),
            price * (1 + risk_pct),
            price * (1 + risk_pct * 1.5),
        ]
        position = risk_pct / 3

    return {
        "entry_zone": (round(entry_low, 2), round(entry_high, 2)),
        "stop_loss": round(stop, 2),
        "targets": [round(t, 2) for t in targets],
        "position_size": round(position, 4),
        "risk_pct_used": risk_pct,
    }
