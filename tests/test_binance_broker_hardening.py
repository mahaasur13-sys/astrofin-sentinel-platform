"""BinanceBroker hardening (no network, mocked ccxt exchange) + RiskConfigV2 validation.

1) get_order_status: real order type, unknown side -> None (never silent SELL);
2) get_positions: stablecoins skipped, non-USDT quote fallback, still fail-closed;
3) get_account_balance when disconnected -> BalanceUnavailableError (not zero);
4) RiskConfigV2: ValueError (not assert), max_drawdown in (0, 1).
"""
from __future__ import annotations

import asyncio
from unittest import mock

import pytest

import orchestration.council_orchestrator as co
import trading.broker.binance as bmod
from core.base_agent import AgentResponse, SignalDirection
from trading.broker.base import BalanceUnavailableError, OrderSide, OrderStatus, OrderType
from trading.broker.binance import BinanceBroker, MarketPriceUnavailableError
from trading.risk_v2 import RiskConfigV2
from trading.safety_gate import SafetyGate


def _broker(monkeypatch, ex, connected=True):
    monkeypatch.setattr(bmod, "HAS_CCXT", True)
    b = BinanceBroker.__new__(BinanceBroker)
    b.paper = False
    b.connected = connected
    b.exchange = ex
    return b


# ── 1) get_order_status ───────────────────────────────────────────────────────

def _status(monkeypatch, **kw):
    o = {"id": "1", "symbol": "BTC/USDT", "side": "buy", "type": "market", "amount": 1.0,
         "price": 100.0, "status": "closed", "filled": 1.0, "average": 100.0}
    o.update(kw)
    ex = mock.MagicMock()
    ex.fetch_order.return_value = o
    return _broker(monkeypatch, ex).get_order_status("1")


@pytest.mark.parametrize("raw,expected", [
    ("market", OrderType.MARKET), ("limit", OrderType.LIMIT), ("LIMIT", OrderType.LIMIT),
    ("limit_maker", OrderType.LIMIT), ("stop_loss", OrderType.STOP),
    ("stop_loss_limit", OrderType.STOP_LIMIT), ("take_profit_limit", OrderType.STOP_LIMIT),
])
def test_order_status_type_from_exchange(monkeypatch, raw, expected):
    assert _status(monkeypatch, type=raw).order_type is expected


@pytest.mark.parametrize("raw", [None, "", "weird"])
def test_order_status_unknown_type_not_market(monkeypatch, raw):
    o = _status(monkeypatch, type=raw)
    assert o is not None and o.order_type is None and "type unknown" in o.notes
    assert o.status is OrderStatus.FILLED


@pytest.mark.parametrize("raw,expected", [("buy", OrderSide.BUY), ("sell", OrderSide.SELL), ("SELL", OrderSide.SELL)])
def test_order_status_side(monkeypatch, raw, expected):
    assert _status(monkeypatch, side=raw).side is expected


@pytest.mark.parametrize("raw", [None, "", "short", 1])
def test_order_status_unknown_side_fail_closed(monkeypatch, raw):
    assert _status(monkeypatch, side=raw) is None


# ── 2) get_positions ──────────────────────────────────────────────────────────

def _ex(total, tickers):
    ex = mock.MagicMock()
    ex.fetch_balance.return_value = {"total": total}

    def _t(pair):
        if pair not in tickers:
            raise RuntimeError(f"BadSymbol {pair}")
        return {"last": tickers[pair]}

    ex.fetch_ticker.side_effect = _t
    return ex


def test_positions_stablecoins_are_not_positions(monkeypatch):
    ex = _ex({"USDT": 5, "USDC": 7, "FDUSD": 3, "BUSD": 1, "BTC": 0.1}, {"BTC/USDT": 50_000.0})
    ps = _broker(monkeypatch, ex).get_positions()
    assert [p.symbol for p in ps] == ["BTC"]
    pairs = [c.args[0] for c in ex.fetch_ticker.call_args_list]
    assert pairs == ["BTC/USDT"]  # no USDC/USDT etc. lookups


def test_positions_fallback_quote_when_no_usdt_pair(monkeypatch):
    ex = _ex({"XYZ": 10.0}, {"XYZ/USDC": 2.0})
    ps = _broker(monkeypatch, ex).get_positions()
    assert len(ps) == 1 and ps[0].symbol == "XYZ" and ps[0].current_price == 2.0


def test_positions_no_market_anywhere_still_raises(monkeypatch):
    ex = _ex({"BTC": 0.1, "DUST": 0.0001}, {"BTC/USDT": 50_000.0})
    with pytest.raises(MarketPriceUnavailableError):
        _broker(monkeypatch, ex).get_positions()


# ── 3) get_account_balance disconnected ───────────────────────────────────────

def test_balance_disconnected_raises(monkeypatch):
    b = _broker(monkeypatch, mock.MagicMock(), connected=False)
    with pytest.raises(BalanceUnavailableError):
        b.get_account_balance()
    b.exchange.fetch_balance.assert_not_called()


def test_orchestrator_disconnected_binance_denied(monkeypatch):
    b = _broker(monkeypatch, mock.MagicMock(), connected=False)
    o = co.CouncilOrchestrator(mock.MagicMock(), safety_gate=SafetyGate())
    o.adjust_through_risk = lambda base, r: (0.1, "ok")
    sig = AgentResponse(agent_name="AstroCouncil", signal=SignalDirection.LONG, confidence=90, reasoning="t")
    with mock.patch.object(co, "get_broker", return_value=b):
        out = asyncio.run(o.execute_trading_cycle([], sig, config={"symbol": "BTCUSDT", "current_price": 50_000.0}))
    assert out["action"] == "DENIED" and out["blocked_reason"] in ("broker_not_connected", "no_equity")
    b.exchange.create_order.assert_not_called()


def test_orchestrator_balance_unavailable_is_no_equity(monkeypatch):
    b = _broker(monkeypatch, mock.MagicMock(), connected=True)
    o = co.CouncilOrchestrator(mock.MagicMock(), safety_gate=SafetyGate())
    o.adjust_through_risk = lambda base, r: (0.1, "ok")
    sig = AgentResponse(agent_name="AstroCouncil", signal=SignalDirection.LONG, confidence=90, reasoning="t")
    with mock.patch.object(co, "get_broker", return_value=b), \
         mock.patch.object(BinanceBroker, "get_account_balance", side_effect=BalanceUnavailableError("x")):
        out = asyncio.run(o.execute_trading_cycle([], sig, config={"symbol": "BTCUSDT", "current_price": 50_000.0}))
    assert out["blocked_reason"] == "no_equity"
    b.exchange.create_order.assert_not_called()


# ── 4) RiskConfigV2 validation ────────────────────────────────────────────────

@pytest.mark.parametrize("kw", [
    {"max_drawdown": 1.0}, {"max_drawdown": 0}, {"max_drawdown": -0.1}, {"max_drawdown": float("nan")},
    {"max_drawdown": "0.1"}, {"max_exposure_per_asset": 0}, {"max_exposure_per_asset": 1.5},
    {"correlation_limit": 0}, {"correlation_limit": float("nan")}, {"target_volatility": 0},
    {"target_volatility": float("inf")},
])
def test_riskconfig_invalid_raises_valueerror(kw):
    with pytest.raises(ValueError):
        RiskConfigV2(**kw)


def test_riskconfig_valid_boundaries():
    RiskConfigV2(max_drawdown=0.99, max_exposure_per_asset=1.0, correlation_limit=1.0)
