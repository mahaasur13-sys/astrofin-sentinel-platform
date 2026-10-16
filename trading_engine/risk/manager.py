"""Risk Manager — Dynamic position sizing based on volatility regime."""

import logging

logger = logging.getLogger("trading_engine.risk.manager")

# Regime-based risk percentages
REGIME_RISK = {
    "LOW": 3.0,
    "NORMAL": 2.0,
    "HIGH": 1.0,
    "EXTREME": 0.5,
}

# Kelly multiplier per regime
KELLY_MULT = {
    "LOW": 1.0,
    "NORMAL": 0.75,
    "HIGH": 0.50,
    "EXTREME": 0.20,
}


class RiskManager:
    """Dynamic risk sizing with volatility regime, max position, and drawdown caps."""

    def __init__(self, max_position_pct: float = 10.0, max_drawdown_pct: float = 15.0):
        self.max_position_pct = max_position_pct
        self.max_drawdown_pct = max_drawdown_pct

    def compute_risk_pct(self, regime: str, confidence: float) -> float:
        base = REGIME_RISK.get(regime, 2.0)
        kelly = KELLY_MULT.get(regime, 0.75)
        risk = base * kelly

        if confidence < 50:
            risk *= 0.5

        if risk > self.max_position_pct:
            risk = self.max_position_pct

        logger.debug(
            "RiskManager: regime=%s base=%.1f kelly=%.2f → risk=%.2f%%",
            regime, base, kelly, risk,
        )
        return round(risk, 2)
