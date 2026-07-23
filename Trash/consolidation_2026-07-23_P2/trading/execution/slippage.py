"""trading/execution/slippage.py — ATOM-STEP-10: Slippage Models"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class SlippageResult:
    slippage_bps: float
    slippage_cost: float
    exec_price: float
    price_after: float
    is_adverse: bool
    model: str


class SlippageModel:
    """Fixed-percent slippage model — no market intelligence.

    slippage_bps is constant regardless of order size or market conditions.
    """

    def __init__(self, slippage_bps: float = 5.0, spread_bps: float = 2.5):
        self.slippage_bps = slippage_bps
        self.spread_bps = spread_bps

    def calculate(self, side: str, qty: float, price: float) -> SlippageResult:
        """Calculate slippage for a trade.

        Args:
            side: "buy" or "sell"
            qty: order quantity
            price: reference price

        Returns:
            SlippageResult with cost breakdown
        """
        total_bps = self.slippage_bps + self.spread_bps
        slippage_cost = total_bps / 10000 * price * qty

        if side == "buy":
            exec_price = price * (1 + total_bps / 10000)
            adverse = total_bps > self.spread_bps
        else:
            exec_price = price * (1 - total_bps / 10000)
            adverse = total_bps > self.spread_bps

        return SlippageResult(
            slippage_bps=total_bps,
            slippage_cost=round(slippage_cost, 4),
            exec_price=round(exec_price, 4),
            price_after=round(exec_price, 4),
            is_adverse=adverse,
            model="fixed",
        )

    def __repr__(self) -> str:
        return f"SlippageModel(slippage={self.slippage_bps}bps, spread={self.spread_bps}bps)"


class AdaptiveSlippageModel:
    """Slippage model with market microstructure intelligence.

    Accounts for:
    - Order size relative to ADV (volume participation)
    - Volatility regime (high-vol = more slippage)
    - Liquidity conditions (spread proxy)
    - Side adverse selection (buy vs sell in different regimes)
    """

    def __init__(
        self,
        base_slippage_bps: float = 3.0,
        vol_coefficient: float = 0.5,  # how much volatility matters
        size_coefficient: float = 0.4,  # how much order size matters
        liquidity_coefficient: float = 0.2,
        adverse_selection_factor: float = 1.2,
    ):
        self.base_slippage_bps = base_slippage_bps
        self.vol_coefficient = vol_coefficient
        self.size_coefficient = size_coefficient
        self.liquidity_coefficient = liquidity_coefficient
        self.adverse_selection_factor = adverse_selection_factor

    def calculate(
        self,
        side: str,
        qty: float,
        price: float,
        volatility_bps: float = 50.0,
        spread_bps: float = 5.0,
        adv: float = 10000.0,
        market_regime: str = "normal",  # "low", "normal", "high", "extreme"
        orderbook_depth: float = 500.0,  # depth at top of book
    ) -> SlippageResult:
        """Adaptive slippage calculation.

        Args:
            side: "buy" or "sell"
            qty: order quantity
            price: reference price
            volatility_bps: current volatility in bps
            spread_bps: current bid-ask spread in bps
            adv: average daily volume
            market_regime: "low", "normal", "high", "extreme"
            orderbook_depth: quantity available at top of book

        Returns:
            SlippageResult with adaptive slippage
        """
        # Volume participation rate
        participation = qty / adv if adv > 0 else 1.0

        # Regime multipliers
        regime_mult = {
            "low": 0.7,
            "normal": 1.0,
            "high": 1.8,
            "extreme": 3.0,
        }.get(market_regime, 1.0)

        # Volume impact: nonlinear in participation
        # Small orders (<1% ADV): minimal impact
        # Large orders (>10% ADV): severe impact
        size_impact = self.size_coefficient * math.sqrt(max(participation, 0.0001)) * 100

        # Vol impact: proportional to realized volatility
        vol_impact = self.vol_coefficient * volatility_bps / 100

        # Liquidity impact: inverse depth
        depth_ratio = orderbook_depth / qty if qty > 0 else 1.0
        liq_impact = self.liquidity_coefficient * max(0, (1 - depth_ratio)) * 50

        # Base
        base = self.base_slippage_bps * regime_mult

        # Total slippage in bps
        total_bps = base + size_impact + vol_impact + liq_impact + spread_bps / 2

        # Side adverse selection: in trending markets, one side is worse
        if market_regime in ("high", "extreme"):
            # In trending market, joining trend is more costly (adverse selection)
            # vs fighting the trend (rebounds tend to revert)
            if side == "buy" and market_regime == "extreme":
                total_bps *= self.adverse_selection_factor
            elif side == "sell" and market_regime == "extreme":
                total_bps *= self.adverse_selection_factor

        slippage_cost = total_bps / 10000 * price * qty

        if side == "buy":
            exec_price = price * (1 + total_bps / 10000)
            adverse = total_bps > self.base_slippage_bps * 1.5
        else:
            exec_price = price * (1 - total_bps / 10000)
            adverse = total_bps > self.base_slippage_bps * 1.5

        return SlippageResult(
            slippage_bps=round(total_bps, 4),
            slippage_cost=round(slippage_cost, 4),
            exec_price=round(exec_price, 4),
            price_after=round(exec_price, 4),
            is_adverse=adverse,
            model="adaptive",
        )

    def __repr__(self) -> str:
        return (
            f"AdaptiveSlippageModel(base={self.base_slippage_bps}bps, "
            f"vol={self.vol_coefficient}, size={self.size_coefficient})"
        )


if __name__ == "__main__":
    print("=== SlippageModel (fixed) ===")
    m = SlippageModel(slippage_bps=5, spread_bps=2.5)
    for side, qty in [("buy", 100), ("sell", 100)]:
        r = m.calculate(side, qty, 50000)
        print(
            f"  {side.upper()} {qty} units: {r.slippage_bps:.2f}bps, "
            f"cost=${r.slippage_cost:.2f}, exec=${r.exec_price:.2f}"
        )

    print("\n=== AdaptiveSlippageModel ===")
    a = AdaptiveSlippageModel()
    for regime, vol, qty in [
        ("low", 30, 500),
        ("normal", 80, 500),
        ("high", 200, 500),
        ("extreme", 500, 500),
    ]:
        r = a.calculate("buy", qty, 50000, volatility_bps=vol, market_regime=regime)
        print(
            f"  [{regime.upper():8s}] vol={vol:4d}bps, qty={qty}: "
            f"{r.slippage_bps:.2f}bps, cost=${r.slippage_cost:.2f}, "
            f"exec=${r.exec_price:.2f}"
        )
