"""trading/execution/order_book.py — ATOM-STEP-10: Order Book & Market Impact Model"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import logging
log = logging.getLogger(__name__)



@dataclass
class OrderBookLevel:
    price: float
    quantity: float
    orders: int = 1  # number of orders at this level


@dataclass
class OrderBookSnapshot:
    """Full order book state."""

    bids: list[OrderBookLevel]  # sorted descending by price
    asks: list[OrderBookLevel]  # sorted ascending by price
    spread: float = field(init=False)
    mid_price: float = field(init=False)
    depth_bid_10: float = field(init=False)  # total bid qty in top 10 levels
    depth_ask_10: float = field(init=False)  # total ask qty in top 10 levels

    def __post_init__(self):
        best_bid = self.bids[0].price if self.bids else 0.0
        best_ask = self.asks[0].price if self.asks else 0.0
        self.spread = best_ask - best_bid
        self.mid_price = (best_bid + best_ask) / 2 if best_bid and best_ask else 0.0
        self.depth_bid_10 = sum(l.quantity for l in self.bids[:10])
        self.depth_ask_10 = sum(l.quantity for l in self.asks[:10])


@dataclass
class MarketImpactResult:
    """Estimated market impact of a trade."""

    base_price: float  # mid-price before trade
    slippage_bps: float  # slippage in basis points
    slippage_cost: float  # absolute slippage cost
    market_impact_cost: float  # market impact cost
    total_cost: float  # total execution cost
    price_after_trade: float  # expected price after trade
    filled_qty: float  # actual filled quantity
    participation_rate: float  # order size relative to ADV


class OrderBookSimulator:
    """Simulates order book dynamics with market impact.

    Uses Almgren-Chriss model for market impact estimation.
    """

    def __init__(
        self,
        mid_price: float = 100.0,
        spread_bps: float = 5.0,
        depth_per_level: float = 100.0,
        num_levels: int = 20,
        volatility_bps: float = 100.0,
        adv: float = 10000.0,
        gamma: float = 0.5,  # market impact nonlinearity [0,1]
    ):
        self.mid_price = mid_price
        self.spread_bps = spread_bps
        self.depth_per_level = depth_per_level
        self.num_levels = num_levels
        self.volatility_bps = volatility_bps
        self.adv = adv  # Average Daily Volume
        self.gamma = gamma  # impact nonlinearity

    def build_snapshot(self, base_price: float | None = None) -> OrderBookSnapshot:
        """Build an order book snapshot around base_price."""
        price = base_price or self.mid_price
        half_spread = self.spread_bps / 10000 * price / 2

        bids = []
        asks = []
        for i in range(self.num_levels):
            # Bids: price decreases away from mid
            bid_price = max(price - half_spread - i * 0.01 * price, 0.01)
            bid_qty = self.depth_per_level * math.exp(-i * 0.1)
            bids.append(OrderBookLevel(price=round(bid_price, 4), quantity=bid_qty))

            # Asks: price increases away from mid
            ask_price = price + half_spread + i * 0.01 * price
            ask_qty = self.depth_per_level * math.exp(-i * 0.1)
            asks.append(OrderBookLevel(price=round(ask_price, 4), quantity=ask_qty))

        return OrderBookSnapshot(bids=bids, asks=asks)

    def estimate_market_impact(
        self,
        side: str,  # "buy" or "sell"
        qty: float,
        num_slices: int = 10,
        base_price: float | None = None,
        _time_horizon_minutes: float = 60.0,
    ) -> MarketImpactResult:
        """Estimate market impact using Almgren-Chriss model.

        Args:
            side: "buy" or "sell"
            qty: total quantity to execute
            num_slices: number of TWAP slices
            base_price: reference price (defaults to mid_price)
            time_horizon_minutes: expected execution time

        Returns:
            MarketImpactResult with detailed cost breakdown
        """
        price = base_price or self.mid_price
        slice_qty = qty / num_slices

        # ── Temporary impact (instantaneous) ────────────────────────────────
        # Temporary impact = eta * (v / ADV)^psi
        # where v = order qty, ADV = average daily volume
        participation = qty / self.adv if self.adv > 0 else 1.0
        eta = 0.5 * self.volatility_bps / 10000  # temporary impact coeff
        psi = self.gamma  # nonlinearity

        # Temporary impact per slice (linear in slice size)
        temp_impact_bps = eta * (participation / num_slices) ** psi * 10000
        temp_impact_bps / 10000 * price

        # ── Permanent impact (information leakage) ───────────────────────────
        # Permanent impact = gamma * (v / ADV)
        gamma_perm = eta * 2  # permanent impact coefficient
        perm_impact_bps = gamma_perm * participation * 10000
        perm_impact_bps / 10000 * price

        # ── Spread cost ────────────────────────────────────────────────────
        spread_cost_bps = self.spread_bps / 2
        spread_cost_bps / 10000 * price

        # ── Total ───────────────────────────────────────────────────────────
        total_bps = abs(temp_impact_bps) + abs(perm_impact_bps) + spread_cost_bps
        total_cost = (
            (total_bps / 10000) * price * slice_qty * num_slices / qty if qty else 0
        )
        slippage_bps = abs(temp_impact_bps) + spread_cost_bps

        # ── Price after trade ───────────────────────────────────────────────
        if side == "buy":
            price_after = price * (1 + total_bps / 10000)
        else:
            price_after = price * (1 - total_bps / 10000)

        return MarketImpactResult(
            base_price=price,
            slippage_bps=slippage_bps,
            slippage_cost=slippage_bps / 10000 * price * qty,
            market_impact_cost=(abs(temp_impact_bps) + abs(perm_impact_bps))
            / 10000
            * price
            * qty,
            total_cost=total_cost if qty else 0,
            price_after_trade=round(price_after, 4),
            filled_qty=qty,
            participation_rate=participation,
        )

    def execute_slice(
        self,
        side: str,
        qty: float,
        base_price: float | None = None,
        流动性_factor: float = 1.0,
    ) -> tuple[float, float, float]:
        """Simulate executing a single slice against the order book.

        Returns:
            (exec_price, fill_qty, slippage_bps)
        """
        price = base_price or self.mid_price
        impact = self.estimate_market_impact(side, qty, base_price=price)
        slip = impact.slippage_bps

        if side == "buy":
            exec_price = price * (1 + slip / 10000)
        else:
            exec_price = price * (1 - slip / 10000)

        # Adjust qty if book depth is insufficient
        fill_qty = qty
        if side == "buy":
            available = sum(l.quantity for l in self.build_snapshot(price).asks[:3])
            if qty > available * 0.5:
                fill_qty = min(qty, available * 0.5 + available * 0.1)
        else:
            available = sum(l.quantity for l in self.build_snapshot(price).bids[:3])
            if qty > available * 0.5:
                fill_qty = min(qty, available * 0.5 + available * 0.1)

        fill_qty = max(fill_qty, qty * 流动性_factor)
        return exec_price, fill_qty, slip


# ── Market Impact Model (standalone) ───────────────────────────────────────────


class MarketImpactModel:
    """Standalone market impact calculator (Almgren-Chriss).

    Usage:
        model = MarketImpactModel(volatility_bps=100, adv=50000)
        cost = model.estimate("buy", qty=1000, price=50000)
    """

    def __init__(
        self,
        volatility_bps: float = 100.0,
        adv: float = 10000.0,
        permanent_frac: float = 0.5,  # permanent vs temporary impact ratio
        spread_bps: float = 5.0,
    ):
        self.volatility_bps = volatility_bps
        self.adv = adv
        self.eta = 0.5 * volatility_bps / 10000
        self.gamma = (
            self.eta * permanent_frac / (1 - permanent_frac)
            if permanent_frac < 1
            else self.eta
        )
        self.spread_bps = spread_bps

    def estimate(self, side: str, qty: float, price: float) -> dict:
        """Estimate market impact for a trade.

        Returns dict with:
            - participation_rate: order qty relative to ADV
            - slippage_bps: slippage in bps
            - impact_cost: absolute cost in quote currency
            - price_after: expected price post-trade
        """
        participation = qty / self.adv if self.adv > 0 else 1.0

        # Temporary impact
        temp_bps = self.eta * participation * 10000

        # Permanent impact
        perm_bps = self.gamma * participation * 10000

        # Spread cost
        spread_cost_bps = self.spread_bps / 2

        total_bps = temp_bps + perm_bps + spread_cost_bps

        if side == "buy":
            price_after = price * (1 + total_bps / 10000)
            impact_cost = total_bps / 10000 * price * qty
        else:
            price_after = price * (1 - total_bps / 10000)
            impact_cost = total_bps / 10000 * price * qty

        return {
            "participation_rate": round(participation * 100, 3),  # percent
            "slippage_bps": round(total_bps, 4),
            "market_impact_bps": round(temp_bps + perm_bps, 4),
            "spread_cost_bps": round(spread_cost_bps, 4),
            "impact_cost": round(impact_cost, 2),
            "price_after": round(price_after, 4),
            "price_before": price,
        }

    def __repr__(self) -> str:
        return f"MarketImpactModel(vol={self.volatility_bps}bps, ADV={self.adv}, eta={self.eta:.4f})"


if __name__ == "__main__":
    log.info("=== OrderBookSimulator ===")
    sim = OrderBookSimulator(
        mid_price=50000, spread_bps=5, depth_per_level=500, adv=10000
    )
    book = sim.build_snapshot()
    log.info(f"  Mid price: {book.mid_price}, Spread: {book.spread:.2f}")
    log.info(f"  Top 3 bids: {[round(l.price, 2) for l in book.bids[:3]]}")
    log.info(f"  Top 3 asks: {[round(l.price, 2) for l in book.asks[:3]]}")

    impact = sim.estimate_market_impact("buy", qty=500, num_slices=5, base_price=50000)
    log.info("\n  Market Impact (buy 500 BTC, 5 slices):")
    log.info(f"    Slippage: {impact.slippage_bps:.2f} bps")
    log.info(f"    Impact cost: ${impact.market_impact_cost:.2f}")
    log.info(f"    Price after: ${impact.price_after_trade}")

    log.info("\n=== MarketImpactModel ===")
    m = MarketImpactModel(volatility_bps=100, adv=50000)
    for side, qty in [("buy", 100), ("buy", 1000), ("sell", 500)]:
        r = m.estimate(side, qty, 50000)
        log.info(
            f"  {side.upper()} {qty} units: {r['slippage_bps']:.2f}bps, "
            f"${r['impact_cost']:.2f} cost, participation={r['participation_rate']:.1f}%"
        )
