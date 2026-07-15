"""trading/mode.py — ATOM-PRODUCTION: Trading Mode System
=============================================================="""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TradingMode(Enum):
    BACKTEST = "BACKTEST"
    PAPER = "PAPER"
    LIVE_LIMITED = "LIVE_LIMITED"
    LIVE_FULL = "LIVE_FULL"


@dataclass
class ModeLimits:
    max_position_pct: float
    max_total_exposure_pct: float
    allow_market_orders: bool
    allow_limit_orders: bool
    allow_options: bool
    allow_short: bool
    require_risk_review: bool
    max_orders_per_day: int
    kill_switch_strict: bool


MODE_LIMITS = {
    TradingMode.BACKTEST: ModeLimits(
        1.0, 1.0, True, True, True, True, False, 10_000, False
    ),
    TradingMode.PAPER: ModeLimits(
        0.50, 1.0, True, True, False, False, False, 100, False
    ),
    TradingMode.LIVE_LIMITED: ModeLimits(
        0.20, 0.50, True, True, False, False, True, 10, True
    ),
    TradingMode.LIVE_FULL: ModeLimits(
        0.30, 0.80, True, True, True, True, True, 50, True
    ),
}


class ModeEnforcer:
    def __init__(self, mode: TradingMode = TradingMode.BACKTEST):
        self.mode = mode
        self.limits = MODE_LIMITS[mode]
        self._order_count_today = 0

    def check_order(
        self, proposed_size_pct, is_market, is_limit, is_option, is_short, equity
    ):
        limits = self.limits
        if proposed_size_pct > limits.max_position_pct:
            return (
                False,
                f"POSITION_SIZE: {proposed_size_pct:.2%} > limit={limits.max_position_pct:.2%}",
            )
        if is_market and not limits.allow_market_orders:
            return False, f"MARKET_ORDERS_DISABLED in mode={self.mode.value}"
        if is_limit and not limits.allow_limit_orders:
            return False, f"LIMIT_ORDERS_DISABLED in mode={self.mode.value}"
        if is_option and not limits.allow_options:
            return False, f"OPTIONS_DISABLED in mode={self.mode.value}"
        if is_short and not limits.allow_short:
            return False, f"SHORT_DISABLED in mode={self.mode.value}"
        if self._order_count_today >= limits.max_orders_per_day:
            return (
                False,
                f"ORDER_COUNT: {self._order_count_today} >= max={limits.max_orders_per_day}",
            )
        return True, "OK"

    def check_exposure(self, total_exposure_pct):
        if total_exposure_pct > self.limits.max_total_exposure_pct:
            return False, self.limits.max_total_exposure_pct
        return True, total_exposure_pct

    def record_order(self):
        self._order_count_today += 1

    def reset_daily_count(self):
        self._order_count_today = 0

    def set_mode(self, mode: TradingMode):
        self.mode = mode
        self.limits = MODE_LIMITS[mode]
        self._order_count_today = 0

    def can_live_trade(self):
        return self.mode in (TradingMode.LIVE_LIMITED, TradingMode.LIVE_FULL)


if __name__ == "__main__":
    enforcer = ModeEnforcer(TradingMode.BACKTEST)
    ok, _ = enforcer.check_order(1.0, True, True, True, True, 100_000)
    assert ok
    print("  Test 1 (BACKTEST full): PASSED")
    enforcer2 = ModeEnforcer(TradingMode.PAPER)
    ok, _ = enforcer2.check_order(0.30, True, True, False, True, 100_000)
    assert not ok
    print("  Test 2 (PAPER restrictions): PASSED")
    enforcer3 = ModeEnforcer(TradingMode.LIVE_LIMITED)
    ok, _ = enforcer3.check_order(0.25, True, False, False, False, 100_000)
    assert not ok
    print("  Test 3 (LIVE_LIMITED cap): PASSED")
    print("ModeEnforcer: all tests passed")
