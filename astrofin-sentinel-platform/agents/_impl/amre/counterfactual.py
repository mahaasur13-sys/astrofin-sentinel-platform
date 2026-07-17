"""amre/counterfactual.py — Counterfactual reasoning"""

from __future__ import annotations

from typing import Any


class CounterfactualEngine:
    def check(self, state: Any, signals: list[Any]) -> dict[str, Any]:
        state_dict = (
            state
            if isinstance(state, dict)
            else {
                "symbol": getattr(state, "symbol", ""),
                "price": getattr(state, "price", 0),
            }
        )
        issues = []
        high_conf_buy = [
            s
            for s in signals
            if (
                s.get("signal") in ("LONG", "BUY")
                if isinstance(s, dict)
                else getattr(s, "signal", "") in ("LONG", "BUY")
            )
            and (
                s.get("confidence", 50)
                if isinstance(s, dict)
                else getattr(s, "confidence", 50)
            )
            > 80
        ]
        high_conf_sell = [
            s
            for s in signals
            if (
                s.get("signal") in ("SHORT", "SELL")
                if isinstance(s, dict)
                else getattr(s, "signal", "") in ("SHORT", "SELL")
            )
            and (
                s.get("confidence", 50)
                if isinstance(s, dict)
                else getattr(s, "confidence", 50)
            )
            > 80
        ]
        if high_conf_buy and high_conf_sell:
            issues.append("Conflicting HIGH confidence signals")
        if len(signals) >= 5:
            avg_conf = sum(
                (
                    s.get("confidence", 50)
                    if isinstance(s, dict)
                    else getattr(s, "confidence", 50)
                )
                for s in signals
            ) / len(signals)
            if avg_conf > 80:
                issues.append("Unanimity without diversity check")
        regime = (
            state_dict.get("regime", "NORMAL")
            if isinstance(state_dict, dict)
            else "NORMAL"
        )
        if regime == "EXTREME" and len(signals) > 3:
            issues.append("Many signals in EXTREME regime - validate")
        passed = len(issues) == 0
        return {
            "passed": passed,
            "issues": issues,
            "confidence_adjustment": -len(issues) * 5 if not passed else 0,
        }
