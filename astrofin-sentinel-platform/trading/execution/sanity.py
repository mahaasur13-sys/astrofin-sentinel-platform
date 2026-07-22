"""trading/execution/sanity.py — ATOM-PRODUCTION: Execution Sanity Layer
========================================================================"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

import logging
log = logging.getLogger(__name__)



class ValidationStatus(Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SCALED = "SCALED"


@dataclass
class MarketState:
    symbol: str
    last_price: float
    bid_price: float
    ask_price: float
    spread_bps: float
    adv_24h: float
    realized_vol_20d: float
    current_vol_regime: str


@dataclass
class OrderRequest:
    symbol: str
    side: str
    qty: float
    price: float
    order_type: str
    slippage_bp_estimate: float = 0.0


@dataclass
class SanityResult:
    status: ValidationStatus
    reason: str
    adjusted_qty: float | None = None


@dataclass
class SanityConfig:
    max_slippage_bps: float = 50.0
    max_adv_participation: float = 0.05
    max_spread_bps: float = 100.0
    max_vol_regime: str = "HIGH"
    scale_instead_of_reject: bool = True


class ExecutionSanityChecker:
    def __init__(self, config: SanityConfig | None = None):
        self.config = config or SanityConfig()

    def validate(self, order: OrderRequest, market: MarketState) -> SanityResult:
        if not self._is_valid(order.qty) or order.qty <= 0:
            return SanityResult(ValidationStatus.REJECTED, f"INVALID_QTY: {order.qty}")
        if not self._is_valid(market.last_price) or market.last_price <= 0:
            return SanityResult(
                ValidationStatus.REJECTED, f"INVALID_PRICE: {market.last_price}"
            )
        vol_rank = {"LOW": 0, "NORMAL": 1, "HIGH": 2, "EXTREME": 3}
        regime_level = vol_rank.get(market.current_vol_regime, 1)
        max_level = vol_rank.get(self.config.max_vol_regime, 2)
        if regime_level > max_level:
            return SanityResult(
                ValidationStatus.REJECTED,
                f"VOL_REGIME: {market.current_vol_regime} > {self.config.max_vol_regime}",
            )
        if market.spread_bps > self.config.max_spread_bps:
            return SanityResult(
                ValidationStatus.REJECTED,
                f"SPREAD_FILTER: {market.spread_bps:.1f}bps > {self.config.max_spread_bps:.1f}bps",
            )
        if order.slippage_bp_estimate > self.config.max_slippage_bps:
            return SanityResult(
                ValidationStatus.REJECTED,
                f"SLIPPAGE: {order.slippage_bp_estimate:.1f}bps > {self.config.max_slippage_bps:.1f}bps",
            )
        if market.adv_24h > 0:
            order_notional = order.qty * market.last_price
            participation = order_notional / market.adv_24h
            if participation > self.config.max_adv_participation:
                if self.config.scale_instead_of_reject:
                    scaled = (
                        market.adv_24h
                        * self.config.max_adv_participation
                        / market.last_price
                    )
                    scaled = max(0.0, scaled)
                    return SanityResult(
                        ValidationStatus.SCALED,
                        f"LIQUIDITY_SCALED: {participation:.2%} > limit",
                        scaled,
                    )
                else:
                    return SanityResult(
                        ValidationStatus.REJECTED,
                        f"LIQUIDITY: {participation:.2%} > limit",
                    )
        return SanityResult(ValidationStatus.APPROVED, "OK")

    @staticmethod
    def _is_valid(value) -> bool:
        return not (math.isnan(value) or math.isinf(value))


if __name__ == "__main__":
    checker = ExecutionSanityChecker()
    m = MarketState("BTC", 50000, 49990, 50005, 10, 1e9, 0.02, "NORMAL")
    o = OrderRequest("BTC", "BUY", 0.5, 50000, "MARKET", 5.0)
    r = checker.validate(o, m)
    assert r.status == ValidationStatus.APPROVED
    log.info("  Test 1: APPROVED")
    o2 = OrderRequest("BTC", "BUY", 0.5, 50000, "MARKET", 75.0)
    r2 = checker.validate(o2, m)
    assert r2.status == ValidationStatus.REJECTED and "SLIPPAGE" in r2.reason
    log.info("  Test 2: REJECTED (slippage)")
    m3 = MarketState("XXX", 1000, 999, 1001, 20, 100_000, 0.05, "NORMAL")
    o3 = OrderRequest("XXX", "BUY", 10.0, 1000, "MARKET", 3.0)
    r3 = checker.validate(o3, m3)
    assert r3.status == ValidationStatus.SCALED and r3.adjusted_qty < 10.0
    log.info("  Test 3: SCALED (liquidity)")
    log.info("SanityChecker: all tests passed")
