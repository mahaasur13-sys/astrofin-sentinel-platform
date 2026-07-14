"""amre/hierarchical_policy.py — Hierarchical Policy + Regime Detection"""

from __future__ import annotations

from typing import Any


class HierarchicalPolicy:
    def __init__(self):
        """Function __init__."""
        self.regimes = ["LOW", "NORMAL", "HIGH", "EXTREME"]

    def detect_regime(self, state: dict[str, Any]) -> str:
        """Function detect_regime."""
        state.get("price", 0)
        n_signals = state.get("n_signals", 1)
        confs = [
            s.get("confidence", 50)
            for s in state.get("signals", [])
            if isinstance(s, dict)
        ]
        avg_conf = sum(confs) / len(confs) if confs else 50
        if n_signals >= 7 and avg_conf > 70:
            return "LOW"
        elif n_signals >= 4 and avg_conf > 55:
            return "NORMAL"
        elif n_signals >= 3 and avg_conf > 40:
            return "HIGH"
        return "EXTREME"

    def get_action(self, regime: str, amre_data: dict[str, Any]) -> dict[str, Any]:
        """Function get_action."""
        uncertainty = amre_data.get("uncertainty", {}).get("total", 0.5)
        q_star = amre_data.get("q_star", 0.5)
        if regime == "LOW" and uncertainty < 0.3:
            return {
                "action": "SCALE_IN",
                "confidence_boost": 5,
                "position_multiplier": 1.5,
            }
        elif regime == "EXTREME" or uncertainty > 0.7:
            return {
                "action": "STAND_ASIDE",
                "confidence_boost": -15,
                "position_multiplier": 0.3,
            }
        elif regime == "HIGH" and q_star > 0.6:
            return {
                "action": "REDUCE_SIZE",
                "confidence_boost": -5,
                "position_multiplier": 0.7,
            }
        elif regime == "NORMAL" and q_star > 0.65:
            return {
                "action": "HOLD_OR_ADD",
                "confidence_boost": 0,
                "position_multiplier": 1.0,
            }
        return {"action": "MAINTAIN", "confidence_boost": 0, "position_multiplier": 1.0}
