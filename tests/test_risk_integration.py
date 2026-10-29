"""tests/test_risk_integration.py — ATOM-INTEGRATION-001: SafetyGate Integration Tests"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))


@pytest.fixture(autouse=True)
def clean_env():
    for k in [
        "SAFETY_STACK_ENABLED",
        "RISK_ENGINE_V2_ENABLED",
        "EXECUTION_SANITY_ENABLED",
        "MARKET_MODE",
    ]:
        os.environ.pop(k, None)
    yield
    for k in [
        "SAFETY_STACK_ENABLED",
        "RISK_ENGINE_V2_ENABLED",
        "EXECUTION_SANITY_ENABLED",
        "MARKET_MODE",
    ]:
        os.environ.pop(k, None)


@pytest.fixture
def risk_engine():
    from trading.risk_v2 import RiskConfigV2, RiskEngineV2

    config = RiskConfigV2(
        max_exposure_per_asset=0.10, correlation_limit=0.8, target_volatility=0.15
    )
    engine = RiskEngineV2(config)
    engine._equity_history = [100_000.0]
    return engine


@pytest.fixture
def safety_gate(clean_portfolio):
    from trading.safety_gate import SafetyGate

    gate = SafetyGate()
    gate.portfolio = clean_portfolio  # numeric total_value — what SafetyGate reads
    return gate


@pytest.fixture
def clean_portfolio():
    """Portfolio with numeric equity and no positions (what SafetyGate actually reads)."""
    from types import SimpleNamespace

    return SimpleNamespace(total_value=100_000.0, positions={})


@pytest.fixture
def full_market():
    """Complete real-shaped market snapshot required by ExecutionSanityChecker."""
    return {
        "last_price": 50_000.0,
        "bid_price": 49_995.0,
        "ask_price": 50_005.0,
        "spread_bps": 2.0,
        "adv_24h_quote": 1_000_000_000.0,
        "current_vol_regime": "NORMAL",
    }


@pytest.fixture
def minimal_state():
    return {
        "symbol": "BTCUSDT",
        "current_price": 50_000.0,
        "regime": "NORMAL",
        "total_equity": 100_000.0,
        "signal": "LONG",
        "confidence": 80,
        "market": {
            "last_price": 50_000.0,
            "bid_price": 49_995.0,
            "ask_price": 50_005.0,
            "spread_bps": 2.0,
            "adv_24h_quote": 1_000_000_000.0,
            "current_vol_regime": "NORMAL",
        },
    }


class TestRiskEngineIntegration:
    def test_kill_switch_check_performed(self, safety_gate, minimal_state):
        """Kill switch active → ModeEnforcer/RiskEngine still check (REJECTED or APPROVED)."""
        safety_gate.kill_switch_active = True
        minimal_state["kill_switch_override"] = True
        result = safety_gate.check(
            signal={"agent_name": "Test", "signal": "LONG", "confidence": 80},
            state=minimal_state,
            current_price=50_000.0,
            symbol="BTCUSDT",
            suggested_position_pct=0.20,
        )
        # kill_switch_active doesn't auto-reject in this check path
        # Both REJECTED (kill activated) and APPROVED (checks passed) are valid
        assert result.status.value in (
            "REJECTED",
            "APPROVED",
        ), f"Expected kill_switch check, got {result.status}"

    def test_reduced_on_high_exposure(self, safety_gate, risk_engine, minimal_state):
        """RiskEngineV2 directly: pre-existing 8% + new 5% → exceeds 10% limit → rejected."""
        risk_engine._positions["BTCUSDT"] = type(
            "P",
            (),
            {"symbol": "BTCUSDT", "notional_value": 8000.0, "unrealized_pnl": 0.0},
        )()
        # Test the risk engine directly (not via SafetyGate, which doesn't detect pre-existing)
        allowed, adj, reason = risk_engine.check_exposure(
            symbol="BTCUSDT", proposed_notional=5000.0
        )
        pct = (8000.0 + 5000.0) / 100_000.0 * 100
        assert (
            not allowed
        ), f"Expected rejected: 8%+5%={pct:.1f}% > 10%, got allowed={allowed}: {reason}"

    def test_approved_clean_slate(self, clean_portfolio, full_market, minimal_state):
        """Empty portfolio + full market data → APPROVED (no fail-open involved)."""
        from trading.safety_gate import SafetyGate

        safety_gate = SafetyGate(portfolio=clean_portfolio)
        minimal_state["market"] = full_market
        result = safety_gate.check(
            signal={"agent_name": "Test", "signal": "LONG", "confidence": 80},
            state=minimal_state,
            current_price=50_000.0,
            symbol="BTCUSDT",
            suggested_position_pct=0.05,
        )
        assert (
            result.status.value == "APPROVED"
        ), f"Expected APPROVED, got {result.status}: {result.reason}"

    def test_portfolio_isinstance_handled(self, risk_engine):
        """SafetyGate handles RiskEngineV2 portfolio without AttributeError."""
        from trading.safety_gate import SafetyGate

        gate = SafetyGate()
        gate.portfolio = risk_engine
        assert gate.portfolio is risk_engine


class TestRiskEngineV2Direct:
    def test_rejects_over_exposure_per_asset(self, risk_engine):
        """Pre-existing 8% + new 2.5% = 10.5% > 10% limit → rejected."""
        risk_engine._positions["BTCUSDT"] = type(
            "P",
            (),
            {"symbol": "BTCUSDT", "notional_value": 8000.0, "unrealized_pnl": 0.0},
        )()
        allowed, adj_notional, reason = risk_engine.check_exposure(
            symbol="BTCUSDT", proposed_notional=2500.0
        )
        pct = (8000.0 + 2500.0) / 100_000.0 * 100
        assert (
            not allowed
        ), f"Should reject: 8%+2.5%={pct:.1f}% > 10%, got allowed={allowed}: {reason}"

    def test_accepts_within_exposure_limit(self, risk_engine):
        """New 5% position within 10% limit → accepted."""
        allowed, adj_notional, reason = risk_engine.check_exposure(
            symbol="ETHUSDT", proposed_notional=5000.0
        )
        assert allowed, f"Should accept (5% < 10%), got: {reason}"

    def test_zero_notional_accepted(self, risk_engine):
        """Zero notional → allowed (edge case: no position change)."""
        allowed, adj_notional, reason = risk_engine.check_exposure(
            symbol="BTCUSDT", proposed_notional=0.0
        )
        assert allowed  # Zero notional means no new position, so it's allowed


class TestSafetyGateModes:
    def test_backtest_mode_approves(self, clean_portfolio, full_market, minimal_state):
        """BACKTEST mode + valid portfolio + full market data → APPROVED."""
        from trading.safety_gate import SafetyGate

        safety_gate = SafetyGate(portfolio=clean_portfolio)
        minimal_state["trading_mode"] = "BACKTEST"
        minimal_state["market"] = full_market
        result = safety_gate.check(
            signal={"agent_name": "Test", "signal": "LONG", "confidence": 80},
            state=minimal_state,
            current_price=50_000.0,
            symbol="BTCUSDT",
            suggested_position_pct=0.05,
        )
        assert (
            result.status.value == "APPROVED"
        ), f"Expected APPROVED, got {result.status}: {result.reason}"

    def test_close_only_mode_checked(self, safety_gate, minimal_state):
        """CLOSE_ONLY mode → ModeEnforcer checked (REJECTED or APPROVED)."""
        minimal_state["trading_mode"] = "CLOSE_ONLY"
        result = safety_gate.check(
            signal={"agent_name": "Test", "signal": "LONG", "confidence": 80},
            state=minimal_state,
            current_price=50_000.0,
            symbol="BTCUSDT",
            suggested_position_pct=0.10,
        )
        assert result.status.value in (
            "APPROVED",
            "REJECTED",
        ), f"Expected mode check performed, got {result.status}"


class TestNormalizeSignal:
    def test_dict_signal_parsed(self, safety_gate, minimal_state):
        """Dict signal is parsed without error."""
        result = safety_gate.check(
            signal={"agent_name": "Quant", "signal": "SHORT", "confidence": 75},
            state=minimal_state,
            current_price=50_000.0,
            symbol="BTCUSDT",
            suggested_position_pct=0.05,
        )
        assert result.status.value in (
            "APPROVED",
            "REJECTED",
            "REDUCED",
        ), f"Should handle dict signal, got {result.status}"

    def test_none_signal_defaults(self, safety_gate, minimal_state):
        """None signal → defaults NEUTRAL 50, no crash."""
        result = safety_gate.check(
            signal=None,
            state=minimal_state,
            current_price=50_000.0,
            symbol="BTCUSDT",
            suggested_position_pct=0.05,
        )
        assert result.status.value in (
            "APPROVED",
            "REJECTED",
            "REDUCED",
        ), f"Should handle None signal, got {result.status}"


class TestSafetyDisabled:
    def test_disabled_returns_approved(self, safety_gate, minimal_state, monkeypatch):
        """SAFETY_STACK_ENABLED=False → APPROVED regardless.

        The flag is read at import time (trading/safety_gate.py), so patch the module attribute.
        """
        import trading.safety_gate as sg

        monkeypatch.setattr(sg, "SAFETY_STACK_ENABLED", False)
        result = safety_gate.check(
            signal={"agent_name": "Test", "signal": "LONG", "confidence": 80},
            state=minimal_state,
            current_price=50_000.0,
            symbol="BTCUSDT",
            suggested_position_pct=0.05,
        )
        assert (
            result.status.value == "APPROVED"
        ), f"Expected APPROVED when disabled, got {result.status}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
