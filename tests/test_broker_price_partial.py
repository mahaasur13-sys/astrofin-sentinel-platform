"""Binance broker: no 0.0 price on errors; no invented FILLED on partial/unknown fills (offline)."""
from __future__ import annotations

import asyncio
import math
from unittest import mock

import pytest

from trading.broker.base import OrderSide, OrderStatus, OrderType
from trading.broker.binance import BinanceBroker


def _broker(exchange):
    b = BinanceBroker(paper=False)
    b.connected = True
    b.exchange = exchange
    return b


@pytest.fixture(autouse=True)
def _ccxt_on():
    with mock.patch("trading.broker.binance.HAS_CCXT", True), \
         mock.patch("trading.broker.binance._is_definite_reject", lambda e: True):
        yield


# ── get_market_price ─────────────────────────────────────────────────────

def test_price_not_connected_raises():
    b = BinanceBroker(paper=False)
    b.connected = False
    b.exchange = mock.MagicMock()
    with pytest.raises(RuntimeError):
        b.get_market_price("BTCUSDT")
    b.exchange.fetch_ticker.assert_not_called()


def test_price_ticker_error_raises():
    ex = mock.MagicMock()
    ex.fetch_ticker.side_effect = Exception("boom")
    with pytest.raises(RuntimeError):
        _broker(ex).get_market_price("BTCUSDT")


@pytest.mark.parametrize("last", [None, 0, 0.0, -1.0, float("nan"), float("inf"), "abc", True])
def test_price_invalid_last_raises(last):
    ex = mock.MagicMock()
    ex.fetch_ticker.return_value = {"last": last}
    with pytest.raises(RuntimeError):
        _broker(ex).get_market_price("BTCUSDT")


def test_price_missing_last_raises():
    ex = mock.MagicMock()
    ex.fetch_ticker.return_value = {}
    with pytest.raises(RuntimeError):
        _broker(ex).get_market_price("BTCUSDT")


def test_price_valid():
    ex = mock.MagicMock()
    ex.fetch_ticker.return_value = {"last": "65000.5"}
    assert _broker(ex).get_market_price("BTCUSDT") == 65000.5


# ── place_order ──────────────────────────────────────────────────────────

def _place(resp, qty=1.0):
    ex = mock.MagicMock()
    ex.create_order.return_value = resp
    return _broker(ex).place_order("BTCUSDT", OrderSide.BUY, OrderType.MARKET, qty, client_order_id="af-t1")


def test_closed_full_fill_is_filled():
    o = _place({"id": "1", "status": "closed", "amount": 1.0, "filled": 1.0, "average": 100.0})
    assert o.status is OrderStatus.FILLED and o.filled_qty == 1.0 and o.avg_fill_price == 100.0


def test_closed_partial_is_partial_with_real_filled():
    o = _place({"id": "1", "status": "closed", "amount": 1.0, "filled": 0.4, "average": 100.0})
    assert o.status is OrderStatus.PARTIAL and o.filled_qty == 0.4


def test_open_partial_is_partial():
    o = _place({"id": "1", "status": "open", "amount": 1.0, "filled": 0.3, "average": 100.0})
    assert o.status is OrderStatus.PARTIAL and o.filled_qty == 0.3


def test_open_unfilled_is_pending():
    o = _place({"id": "1", "status": "open", "amount": 1.0, "filled": 0.0})
    assert o.status is OrderStatus.PENDING and o.filled_qty == 0.0 and o.avg_fill_price == 0.0


@pytest.mark.parametrize("filled", [None, "x", float("nan")])
def test_closed_without_filled_not_invented(filled):
    resp = {"id": "1", "status": "closed", "amount": 1.0, "average": 100.0}
    if filled is not None:
        resp["filled"] = filled
    o = _place(resp)
    assert o.status is OrderStatus.UNKNOWN and o.filled_qty == 0.0


def test_missing_status_is_unknown():
    o = _place({"id": "1", "amount": 1.0, "filled": 1.0, "average": 100.0})
    assert o.status is OrderStatus.UNKNOWN


def test_closed_zero_filled_is_unknown():
    o = _place({"id": "1", "status": "closed", "amount": 1.0, "filled": 0.0})
    assert o.status is OrderStatus.UNKNOWN and o.filled_qty == 0.0


def test_canceled_unfilled_is_cancelled():
    o = _place({"id": "1", "status": "canceled", "amount": 1.0, "filled": 0.0})
    assert o.status is OrderStatus.CANCELLED


def test_avg_price_from_price_and_not_invented():
    o = _place({"id": "1", "status": "closed", "amount": 1.0, "filled": 1.0, "price": 99.0})
    assert o.avg_fill_price == 99.0
    o = _place({"id": "1", "status": "closed", "amount": 1.0, "filled": 1.0})
    assert o.avg_fill_price == 0.0


def test_fee_none_does_not_crash():
    o = _place({"id": "1", "status": "closed", "amount": 1.0, "filled": 1.0, "average": 1.0, "fee": None})
    assert o.status is OrderStatus.FILLED and o.commission == 0.0


# ── orchestrator ─────────────────────────────────────────────────────────

def _orch(order=None, price_exc=None, price=None):
    import orchestration.council_orchestrator as co
    from core.base_agent import AgentResponse, SignalDirection
    from trading.safety_gate import SafetyGate
    market = {"last_price": 50000.0, "bid_price": 49999.0, "ask_price": 50001.0, "spread_bps": 0.4,
              "adv_24h_quote": 5e9, "current_vol_regime": "NORMAL"}
    cfg = {"symbol": "BTCUSDT", "equity": 10000.0, "trading_mode": "PAPER", "market": market}
    b = mock.MagicMock()
    b.name = "stub"
    b.connected = True
    if price_exc is not None:
        b.get_market_price.side_effect = price_exc
    else:
        b.get_market_price.return_value = 50000.0 if price is None else price
    if order is not None:
        b.place_order.return_value = order
    o = co.CouncilOrchestrator(mock.MagicMock(), safety_gate=SafetyGate())
    o.adjust_through_risk = lambda b_, r: (0.1, "ok")
    sig = AgentResponse(agent_name="AstroCouncil", signal=SignalDirection.LONG, confidence=75, reasoning="t")
    with mock.patch.object(co, "get_broker", return_value=b):
        out = asyncio.run(o.execute_trading_cycle([], sig, config=cfg))
    return out, b


def test_orch_price_error_denies():
    out, b = _orch(price_exc=RuntimeError("ticker down"))
    assert out["action"] == "DENIED" and out["blocked_reason"] == "market_data_error"
    b.place_order.assert_not_called()


@pytest.mark.parametrize("bad", [0.0, -1.0, float("nan"), float("inf"), "abc"])
def test_orch_invalid_broker_price_is_market_data_error(bad):
    out, b = _orch(price=bad)
    assert out["action"] == "DENIED" and out["blocked_reason"] == "market_data_error"
    b.place_order.assert_not_called()


def _ord(status, filled):
    from trading.broker.base import Order
    return Order(order_id="1", symbol="BTCUSDT", side=OrderSide.BUY, order_type=OrderType.MARKET,
                 quantity=0.02, status=status, filled_qty=filled, avg_fill_price=50000.0)


def test_orch_partial_not_reported_as_executed():
    out, _ = _orch(order=_ord(OrderStatus.PARTIAL, 0.005))
    assert out["action"] != "EXECUTED"
    assert out["order_status"] == "PARTIAL" and math.isclose(out["filled_qty"], 0.005)


def test_orch_pending_not_reported_as_executed():
    out, _ = _orch(order=_ord(OrderStatus.PENDING, 0.0))
    assert out["action"] != "EXECUTED" and out["filled_qty"] == 0.0


def test_orch_cancelled_not_executed():
    out, _ = _orch(order=_ord(OrderStatus.CANCELLED, 0.0))
    assert out["action"] != "EXECUTED"


def test_orch_filled_executed_with_filled_qty():
    out, _ = _orch(order=_ord(OrderStatus.FILLED, 0.002))
    assert out["action"] == "EXECUTED" and out["filled_qty"] == 0.002
