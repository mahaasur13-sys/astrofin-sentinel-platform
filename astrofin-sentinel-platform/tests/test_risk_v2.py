"""tests/test_risk_v2.py — ATOM-PRODUCTION: Risk Engine V2 Tests
======================================================================
Tests:
  1. Drawdown kill switch triggers at threshold
  2. Exposure cap per asset enforced
  3. Volatility targeting adjusts position size
  4. Sanity checks reject bad orders
  5. Mode gating works
"""

from __future__ import annotations

import math
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading.execution.sanity import (
    ExecutionSanityChecker,
    MarketState,
    OrderRequest,
    SanityConfig,
    ValidationStatus,
)
from trading.mode import ModeEnforcer, TradingMode
from trading.risk_v2 import AssetPosition, RiskConfigV2, RiskEngineV2


class TestDrawdownKillSwitch:
    def test_kill_triggers_at_threshold(self):
        engine = RiskEngineV2(RiskConfigV2(max_drawdown=0.10, kill_switch_enabled=True))
        engine.update_equity(100_000)
        engine.update_equity(88_000)
        ok, dd, msg = engine.check_kill_switch()
        assert not ok, f"Kill should trigger at 12% DD, got dd={dd:.2%}"
        assert "DRAWDOWN KILL" in msg

    def test_kill_not_trigger_below_threshold(self):
        engine = RiskEngineV2(RiskConfigV2(max_drawdown=0.10))
        engine.update_equity(100_000)
        engine.update_equity(94_000)
        ok, dd, _ = engine.check_kill_switch()
        assert ok, f"Kill should NOT trigger at 6% DD, got dd={dd:.2%}"

    def test_kill_disabled(self):
        engine = RiskEngineV2(
            RiskConfigV2(max_drawdown=0.05, kill_switch_enabled=False)
        )
        engine.update_equity(100_000)
        engine.update_equity(88_000)
        ok, _, _ = engine.check_kill_switch()
        assert ok

    def test_kill_switch_in_pre_trade(self):
        engine = RiskEngineV2(RiskConfigV2(max_drawdown=0.05))
        engine.update_equity(100_000)
        engine.update_equity(88_000)
        status, size, msg = engine.pre_trade_check("BTC", 10_000, 0.15, "NORMAL")
        assert status == "REJECTED"
        assert "KILL_SWITCH" in msg


class TestExposureControl:
    def test_rejects_over_exposure_per_asset(self):
        engine = RiskEngineV2(RiskConfigV2(max_exposure_per_asset=0.30))
        engine.update_equity(100_000)
        engine.update_position(AssetPosition("BTC", 20_000, 50_000, 48_000))
        # ETH: 40k/100k = 40% > 30% limit
        ok, size, msg = engine.check_exposure("ETH", 40_000)
        assert not ok, "Expected rejection: ETH 40k/100k = 40% > 30%"
        assert "EXPOSURE" in msg

    def test_approves_within_limit(self):
        engine = RiskEngineV2(RiskConfigV2(max_exposure_per_asset=0.30))
        engine.update_equity(100_000)
        engine.update_position(AssetPosition("BTC", 20_000, 50_000, 48_000))
        ok, size, _ = engine.check_exposure("ETH", 10_000)
        assert ok

    def test_pre_trade_checks_exposure(self):
        engine = RiskEngineV2(RiskConfigV2(max_exposure_per_asset=0.20))
        engine.update_equity(100_000)
        engine.update_position(AssetPosition("BTC", 25_000, 50_000, 48_000))
        status, size, msg = engine.pre_trade_check("ETH", 30_000, 0.15, "NORMAL")
        assert status in ("REDUCED", "REJECTED"), f"Got {status}: {msg}"


class TestVolatilityTargeting:
    def test_high_vol_reduces_size(self):
        engine = RiskEngineV2(RiskConfigV2(target_volatility=0.15))
        size = engine.compute_vol_adjusted_size(10_000, 0.30, "HIGH")
        expected = 10_000 * (0.15 / 0.30) * 0.50
        assert abs(size - expected) < 1, f"Expected {expected}, got {size}"

    def test_low_vol_increases_size(self):
        engine = RiskEngineV2(RiskConfigV2(target_volatility=0.15))
        size = engine.compute_vol_adjusted_size(10_000, 0.05, "LOW")
        expected = 10_000 * (0.15 / 0.05) * 1.0
        assert abs(size - expected) < 1, f"Expected {expected}, got {size}"

    def test_nan_vol_uses_target(self):
        engine = RiskEngineV2(RiskConfigV2(target_volatility=0.15))
        size = engine.compute_vol_adjusted_size(10_000, float("nan"), "NORMAL")
        assert 0 < size < 100_000 and not math.isnan(size)

    def test_vol_scalar_clamped(self):
        engine = RiskEngineV2(RiskConfigV2(target_volatility=0.15))
        size = engine.compute_vol_adjusted_size(10_000, 0.015, "NORMAL")
        expected = 10_000 * 5.0 * 0.75
        assert abs(size - expected) < 1


class TestNaNSafety:
    def test_nan_equity_not_crash(self):
        engine = RiskEngineV2(RiskConfigV2())
        engine.update_equity(float("nan"))
        state = engine.get_state()
        assert not math.isnan(state.total_equity)

    def test_inf_size_clamped(self):
        engine = RiskEngineV2(RiskConfigV2())
        size = engine.compute_vol_adjusted_size(float("inf"), 0.15, "NORMAL")
        assert size <= 10_000_000.0


class TestSlippageThreshold:
    def test_rejects_high_slippage(self):
        checker = ExecutionSanityChecker(SanityConfig(max_slippage_bps=50.0))
        market = MarketState("BTC", 50_000, 49_990, 50_005, 10, 1e9, 0.02, "NORMAL")
        order = OrderRequest(
            "BTC", "BUY", 0.5, 50_000, "MARKET", slippage_bp_estimate=75.0
        )
        result = checker.validate(order, market)
        assert result.status == ValidationStatus.REJECTED
        assert "SLIPPAGE" in result.reason

    def test_approves_normal_slippage(self):
        checker = ExecutionSanityChecker(SanityConfig(max_slippage_bps=50.0))
        market = MarketState("BTC", 50_000, 49_990, 50_005, 10, 1e9, 0.02, "NORMAL")
        order = OrderRequest(
            "BTC", "BUY", 0.5, 50_000, "MARKET", slippage_bp_estimate=5.0
        )
        result = checker.validate(order, market)
        assert result.status == ValidationStatus.APPROVED


class TestLiquidityCheck:
    def test_scales_large_order(self):
        checker = ExecutionSanityChecker(SanityConfig(max_adv_participation=0.05))
        market = MarketState("XXX", 1000, 999, 1001, 20, 100_000, 0.05, "NORMAL")
        order = OrderRequest("XXX", "BUY", 10.0, 1000, "MARKET", 3.0)
        result = checker.validate(order, market)
        assert result.status == ValidationStatus.SCALED
        assert result.adjusted_qty is not None and result.adjusted_qty < 10.0

    def test_small_order_approved(self):
        checker = ExecutionSanityChecker(SanityConfig(max_adv_participation=0.05))
        market = MarketState("BTC", 50_000, 49_990, 50_005, 10, 1e9, 0.02, "NORMAL")
        order = OrderRequest("BTC", "BUY", 0.1, 50_000, "MARKET", 5.0)
        result = checker.validate(order, market)
        assert result.status == ValidationStatus.APPROVED


class TestSpreadFilter:
    def test_rejects_wide_spread(self):
        checker = ExecutionSanityChecker(SanityConfig(max_spread_bps=100.0))
        market = MarketState("YYY", 500, 490, 510, 400, 10_000_000, 0.03, "NORMAL")
        order = OrderRequest("YYY", "BUY", 1.0, 500, "MARKET", 2.0)
        result = checker.validate(order, market)
        assert result.status == ValidationStatus.REJECTED
        assert "SPREAD" in result.reason


class TestVolRegime:
    def test_rejects_extreme_regime(self):
        checker = ExecutionSanityChecker(SanityConfig(max_vol_regime="HIGH"))
        market = MarketState("BTC", 50_000, 49_990, 50_010, 40, 2e9, 0.10, "EXTREME")
        order = OrderRequest("BTC", "BUY", 0.1, 50_000, "MARKET", 5.0)
        result = checker.validate(order, market)
        assert result.status == ValidationStatus.REJECTED
        assert "VOL_REGIME" in result.reason

    def test_allows_high_regime(self):
        checker = ExecutionSanityChecker(SanityConfig(max_vol_regime="HIGH"))
        market = MarketState("BTC", 50_000, 49_990, 50_010, 40, 2e9, 0.05, "HIGH")
        order = OrderRequest("BTC", "BUY", 0.1, 50_000, "MARKET", 5.0)
        result = checker.validate(order, market)
        assert result.status == ValidationStatus.APPROVED


class TestSanityNaNSafety:
    def test_nan_qty_rejected(self):
        checker = ExecutionSanityChecker()
        market = MarketState("BTC", 50_000, 49_990, 50_005, 10, 1e9, 0.02, "NORMAL")
        order = OrderRequest("BTC", "BUY", float("nan"), 50_000, "MARKET", 5.0)
        result = checker.validate(order, market)
        assert result.status == ValidationStatus.REJECTED

    def test_zero_price_rejected(self):
        checker = ExecutionSanityChecker()
        market = MarketState("BTC", 0, 0, 0, 10, 1e9, 0.02, "NORMAL")
        order = OrderRequest("BTC", "BUY", 1.0, 0, "MARKET", 5.0)
        result = checker.validate(order, market)
        assert result.status == ValidationStatus.REJECTED


class TestModeGating:
    def test_backtest_allows_all(self):
        enforcer = ModeEnforcer(TradingMode.BACKTEST)
        ok, _ = enforcer.check_order(1.0, True, True, True, True, 100_000)
        assert ok

    def test_paper_blocks_short(self):
        enforcer = ModeEnforcer(TradingMode.PAPER)
        ok, msg = enforcer.check_order(0.30, True, True, False, True, 100_000)
        assert not ok and "SHORT" in msg

    def test_paper_blocks_options(self):
        enforcer = ModeEnforcer(TradingMode.PAPER)
        ok, msg = enforcer.check_order(0.30, True, True, True, False, 100_000)
        assert not ok and "OPTIONS" in msg

    def test_live_limited_position_cap(self):
        enforcer = ModeEnforcer(TradingMode.LIVE_LIMITED)
        ok, _ = enforcer.check_order(0.25, True, False, False, False, 100_000)
        assert not ok
        ok, _ = enforcer.check_order(0.15, True, True, False, False, 100_000)
        assert ok

    def test_live_limited_exposure_cap(self):
        enforcer = ModeEnforcer(TradingMode.LIVE_LIMITED)
        ok, capped = enforcer.check_exposure(0.70)
        assert not ok and capped == 0.50

    def test_daily_order_limit(self):
        enforcer = ModeEnforcer(TradingMode.LIVE_LIMITED)
        for _ in range(10):
            enforcer.record_order()
        ok, msg = enforcer.check_order(0.05, True, False, False, False, 100_000)
        assert not ok and "ORDER_COUNT" in msg

    def test_can_live_trade(self):
        enforcer_live = ModeEnforcer(TradingMode.LIVE_LIMITED)
        assert enforcer_live.can_live_trade()
        enforcer_backtest = ModeEnforcer(TradingMode.BACKTEST)
        assert not enforcer_backtest.can_live_trade()

    def test_mode_switch(self):
        enforcer = ModeEnforcer(TradingMode.PAPER)
        enforcer.set_mode(TradingMode.LIVE_FULL)
        assert enforcer.mode == TradingMode.LIVE_FULL


class TestIntegration:
    def test_full_pipeline(self):
        enforcer = ModeEnforcer(TradingMode.LIVE_LIMITED)
        engine = RiskEngineV2(
            RiskConfigV2(max_drawdown=0.10, max_exposure_per_asset=0.20)
        )
        checker = ExecutionSanityChecker(
            SanityConfig(max_slippage_bps=50, max_spread_bps=100)
        )

        engine.update_equity(100_000)
        engine.update_equity(95_000)
        market = MarketState("BTC", 50_000, 49_990, 50_005, 15, 1e9, 0.03, "NORMAL")
        order = OrderRequest(
            "BTC", "BUY", 0.5, 50_000, "MARKET", slippage_bp_estimate=10.0
        )

        ok, _ = enforcer.check_order(0.15, True, False, False, False, 100_000)
        assert ok
        status, size, msg = engine.pre_trade_check(
            "BTC", 0.15 * 100_000, 0.03, "NORMAL"
        )
        assert status in ("APPROVED", "REDUCED"), f"Got {status}: {msg}"
        result = checker.validate(order, market)
        assert result.status == ValidationStatus.APPROVED

    def test_kill_switch_blocks_all(self):
        engine = RiskEngineV2(RiskConfigV2(max_drawdown=0.05))
        engine.update_equity(100_000)
        engine.update_equity(88_000)
        status, size, msg = engine.pre_trade_check("BTC", 100_000, 0.15, "NORMAL")
        assert status == "REJECTED" and "KILL_SWITCH" in msg


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
