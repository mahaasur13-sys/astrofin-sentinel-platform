"""BinanceBroker: full-equity valuation (one path with get_positions), fail-closed
get_positions when disconnected, validated reconcile-by-clientOrderId. No network."""
from __future__ import annotations

import asyncio
from unittest import mock

import pytest

import orchestration.council_orchestrator as co
import trading.broker.binance as bmod
from core.base_agent import AgentResponse, SignalDirection
from trading.broker.base import BalanceUnavailableError, OrderSide, OrderStatus, OrderType
from trading.broker.binance import BinanceBroker
from trading.safety_gate import SafetyGate


def _broker(monkeypatch, ex, connected=True):
    monkeypatch.setattr(bmod, "HAS_CCXT", True)
    b = BinanceBroker.__new__(BinanceBroker)
    b.paper = False
    b.connected = connected
    b.exchange = ex
    return b


def _ex(total, free=None, tickers=None):
    ex = mock.MagicMock()
    ex.fetch_balance.return_value = {"total": total, "free": free or {}}
    tickers = tickers or {}

    def _t(pair):
        if pair not in tickers:
            raise RuntimeError(f"BadSymbol {pair}")
        return {"last": tickers[pair]}

    ex.fetch_ticker.side_effect = _t
    return ex


# ── 1) equity ─────────────────────────────────────────────────────────────────

def test_equity_includes_stables_and_assets(monkeypatch):
    ex = _ex({"USDT": 100.0, "USDC": 50.0, "FDUSD": 25.0, "BUSD": 5.0, "BTC": 0.1, "ETH": 2.0},
             free={"USDT": 60.0, "BTC": 0.05},
             tickers={"BTC/USDT": 50_000.0, "ETH/USDT": 3_000.0})
    bal = _broker(monkeypatch, ex).get_account_balance()
    assert bal.total_equity == pytest.approx(100 + 50 + 25 + 5 + 5_000 + 6_000)
    assert bal.available_cash == 60.0  # free USDT only
    assert bal.positions_value == pytest.approx(bal.total_equity - 60.0)


def test_equity_matches_positions_exposure(monkeypatch):
    ex = _ex({"USDT": 10.0, "BTC": 0.2}, tickers={"BTC/USDT": 40_000.0})
    b = _broker(monkeypatch, ex)
    exposure = sum(p.quantity * p.current_price for p in b.get_positions())
    assert b.get_account_balance().total_equity == pytest.approx(10.0 + exposure)


def test_equity_fallback_quote(monkeypatch):
    ex = _ex({"XYZ": 10.0}, tickers={"XYZ/USDC": 2.0})
    assert _broker(monkeypatch, ex).get_account_balance().total_equity == pytest.approx(20.0)


def test_equity_unpriceable_asset_fail_closed(monkeypatch):
    ex = _ex({"USDT": 100.0, "DUST": 1.0}, tickers={})
    with pytest.raises(BalanceUnavailableError):
        _broker(monkeypatch, ex).get_account_balance()


def _cycle(broker):
    o = co.CouncilOrchestrator(mock.MagicMock(), safety_gate=SafetyGate())
    o.adjust_through_risk = lambda base, r: (0.1, "ok")
    sig = AgentResponse(agent_name="AstroCouncil", signal=SignalDirection.LONG, confidence=90, reasoning="t")
    with mock.patch.object(co, "get_broker", return_value=broker):
        return asyncio.run(o.execute_trading_cycle([], sig, config={"symbol": "BTCUSDT", "current_price": 50_000.0}))


def test_orchestrator_unpriceable_asset_is_no_equity(monkeypatch):
    ex = _ex({"USDT": 100.0, "DUST": 1.0}, tickers={})
    out = _cycle(_broker(monkeypatch, ex))
    assert out["action"] == "DENIED" and out["blocked_reason"] == "no_equity"
    ex.create_order.assert_not_called()


# ── 2) get_positions disconnected / no client ─────────────────────────────────

def test_positions_disconnected_raises(monkeypatch):
    b = _broker(monkeypatch, mock.MagicMock(), connected=False)
    with pytest.raises(BalanceUnavailableError):
        b.get_positions()


@pytest.mark.parametrize("has_ccxt", [True, False])
def test_positions_no_client_raises(monkeypatch, has_ccxt):
    b = _broker(monkeypatch, None)
    monkeypatch.setattr(bmod, "HAS_CCXT", has_ccxt)
    with pytest.raises(BalanceUnavailableError):
        b.get_positions()


def test_orchestrator_positions_error_is_positions_unavailable(monkeypatch):
    b = _broker(monkeypatch, _ex({"USDT": 1000.0}))
    with mock.patch.object(BinanceBroker, "get_positions", side_effect=BalanceUnavailableError("x")):
        out = _cycle(b)
    assert out["blocked_reason"] == "positions_unavailable"
    b.exchange.create_order.assert_not_called()


# ── 3) reconcile by clientOrderId ─────────────────────────────────────────────

class _Timeout(Exception):
    pass


def _reconcile(monkeypatch, resp, side=OrderSide.BUY, otype=OrderType.MARKET):
    ex = mock.MagicMock()
    ex.fetch_order.return_value = resp
    b = _broker(monkeypatch, ex)
    o = b._reconcile_by_client_id("af-r1", "BTC/USDT", side, otype, 0.01, None, _Timeout("t"))
    ex.create_order.assert_not_called()  # never resubmitted
    return o, ex


@pytest.mark.parametrize("filled", [None, "x", float("nan"), -1])
def test_reconcile_invalid_filled_is_unknown(monkeypatch, filled):
    o, _ = _reconcile(monkeypatch, {"id": "7", "status": "closed", "filled": filled, "amount": 0.01})
    assert o.status is OrderStatus.UNKNOWN and o.filled_qty == 0.0
    assert o.client_order_id == "af-r1"


def test_reconcile_invalid_average_not_invented(monkeypatch):
    o, _ = _reconcile(monkeypatch, {"id": "7", "status": "closed", "filled": 0.01, "amount": 0.01,
                                    "average": "abc"})
    assert o.status is OrderStatus.FILLED and o.avg_fill_price == 0.0


def test_reconcile_type_and_side_from_response(monkeypatch):
    o, _ = _reconcile(monkeypatch, {"id": "7", "status": "open", "filled": 0.0, "amount": 0.01,
                                    "side": "buy", "type": "limit"})
    assert o.order_type is OrderType.LIMIT and o.side is OrderSide.BUY and o.status is OrderStatus.PENDING


@pytest.mark.parametrize("raw", ["sell", "weird"])
def test_reconcile_side_mismatch_is_unknown(monkeypatch, raw):
    o, _ = _reconcile(monkeypatch, {"id": "7", "status": "closed", "filled": 0.01, "amount": 0.01, "side": raw})
    assert o.status is OrderStatus.UNKNOWN and "side mismatch" in o.notes


def test_reconcile_lookup_uses_same_client_id(monkeypatch):
    _, ex = _reconcile(monkeypatch, {"id": "7", "status": "closed", "filled": 0.01, "amount": 0.01})
    args = ex.fetch_order.call_args
    assert {"origClientOrderId": "af-r1"} in list(args.args) + list(args.kwargs.values())
