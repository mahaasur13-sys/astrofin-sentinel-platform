"""Order idempotency: clientOrderId is sent to Binance, a timeout is reconciled by
origClientOrderId (never blind-resubmitted), paper broker is idempotent per id.
No network: exchange is a MagicMock, ccxt is a fake module."""
from __future__ import annotations

import asyncio
import re
import types
from unittest import mock

import pytest

import trading.broker.binance as bn

# trading.paper_broker -> agents.data_provider imports yfinance at module level.
# yfinance is not in requirements and these tests never fetch prices, so when it is
# missing a stub is put in sys.modules only for this import and removed right after
# (other tests use pytest.importorskip("yfinance") and must still skip).
try:
    import yfinance  # noqa: F401

    import trading.paper_broker as pb
except ModuleNotFoundError:
    import sys

    sys.modules["yfinance"] = types.ModuleType("yfinance")
    try:
        import trading.paper_broker as pb
    finally:
        del sys.modules["yfinance"]

from trading.broker.base import OrderSide, OrderStatus, OrderType

CID_RE = re.compile(r"^[\.A-Z\:/a-z0-9_-]{1,36}$")


class _BaseError(Exception):
    pass


class _NetworkError(_BaseError):
    pass


class _RequestTimeout(_NetworkError):
    pass


class _ExchangeError(_BaseError):
    pass


class _InsufficientFunds(_ExchangeError):
    pass


class _OrderNotFound(_ExchangeError):
    pass


FAKE_CCXT = types.SimpleNamespace(
    NetworkError=_NetworkError, RequestTimeout=_RequestTimeout,
    ExchangeError=_ExchangeError, InsufficientFunds=_InsufficientFunds, OrderNotFound=_OrderNotFound,
)


@pytest.fixture
def live(monkeypatch):
    monkeypatch.setattr(bn, "HAS_CCXT", True)
    monkeypatch.setattr(bn, "ccxt", FAKE_CCXT, raising=False)
    b = bn.BinanceBroker(paper=False)
    b.connected = True
    b.exchange = mock.MagicMock()
    b.exchange.create_order.return_value = {"id": "123", "filled": 0.01, "average": 50000.0,
                                            "fee": {"cost": 0.0}, "timestamp": 1_700_000_000_000}
    return b


def _sent_cid(ex):
    call = ex.create_order.call_args
    params = call.kwargs.get("params")
    if params is None and len(call.args) >= 6:
        params = call.args[5]
    return (params or {}).get("newClientOrderId")


@pytest.mark.parametrize("ot,price", [(OrderType.MARKET, None), (OrderType.LIMIT, 50000.0), (OrderType.STOP, 49000.0)])
def test_binance_sends_new_client_order_id(live, ot, price):
    o = live.place_order("BTC/USDT", OrderSide.BUY, ot, 0.01, price)
    cid = _sent_cid(live.exchange)
    assert cid and CID_RE.match(cid), live.exchange.create_order.call_args
    assert o.client_order_id == cid


def test_binance_uses_caller_client_order_id(live):
    live.place_order("BTC/USDT", OrderSide.BUY, OrderType.MARKET, 0.01, client_order_id="af-fixed_1")
    assert _sent_cid(live.exchange) == "af-fixed_1"


def test_binance_rejects_invalid_client_order_id(live):
    with pytest.raises(ValueError):
        live.place_order("BTC/USDT", OrderSide.BUY, OrderType.MARKET, 0.01, client_order_id="bad id!" * 10)
    live.exchange.create_order.assert_not_called()


def test_generated_ids_unique(live):
    ids = set()
    for _ in range(50):
        live.place_order("BTC/USDT", OrderSide.BUY, OrderType.MARKET, 0.01)
        ids.add(_sent_cid(live.exchange))
    assert len(ids) == 50


def test_timeout_reconciles_by_client_id_found(live):
    live.exchange.create_order.side_effect = _RequestTimeout("read timeout")
    live.exchange.fetch_order.return_value = {"id": "777", "status": "closed", "filled": 0.01, "average": 50010.0}
    o = live.place_order("BTC/USDT", OrderSide.BUY, OrderType.MARKET, 0.01, client_order_id="af-t1")
    assert live.exchange.create_order.call_count == 1  # never resubmitted
    fo = live.exchange.fetch_order.call_args
    assert {"origClientOrderId": "af-t1"} in list(fo.args) + list(fo.kwargs.values())
    assert o.status == OrderStatus.FILLED and o.order_id == "777" and o.client_order_id == "af-t1"


def test_timeout_lookup_fails_is_unknown_not_rejected(live):
    live.exchange.create_order.side_effect = _RequestTimeout("read timeout")
    live.exchange.fetch_order.side_effect = _NetworkError("still down")
    o = live.place_order("BTC/USDT", OrderSide.BUY, OrderType.MARKET, 0.01)
    assert live.exchange.create_order.call_count == 1
    assert o.status.name == "UNKNOWN"  # not REJECTED: the order may be live on the exchange


def test_definite_exchange_reject_stays_rejected(live):
    live.exchange.create_order.side_effect = _InsufficientFunds("no money")
    o = live.place_order("BTC/USDT", OrderSide.BUY, OrderType.MARKET, 0.01)
    assert o.status == OrderStatus.REJECTED
    live.exchange.fetch_order.assert_not_called()


# ── paper broker ─────────────────────────────────────────────────────────

@pytest.fixture
def paper(monkeypatch):
    monkeypatch.setattr(pb, "fetch_current_price", lambda s: 50000.0)
    return pb.PaperBroker(initial_balance=10000.0)


def test_paper_same_client_id_is_idempotent(paper):
    o1 = paper.place_order("BTCUSDT", OrderSide.BUY, OrderType.MARKET, 0.01, client_order_id="af-p1")
    bal = paper.get_account_balance().available_cash
    o2 = paper.place_order("BTCUSDT", OrderSide.BUY, OrderType.MARKET, 0.01, client_order_id="af-p1")
    assert o2.order_id == o1.order_id
    assert paper.get_account_balance().available_cash == bal
    assert paper._positions["BTCUSDT"] == pytest.approx(0.01)


def test_paper_distinct_ids_create_distinct_orders(paper):
    o1 = paper.place_order("BTCUSDT", OrderSide.BUY, OrderType.MARKET, 0.01)
    o2 = paper.place_order("BTCUSDT", OrderSide.BUY, OrderType.MARKET, 0.01)
    assert o1.order_id != o2.order_id and o1.client_order_id != o2.client_order_id
    assert paper._positions["BTCUSDT"] == pytest.approx(0.02)


# ── orchestrator ─────────────────────────────────────────────────────────

def _run_orch(order_status=OrderStatus.FILLED):
    import orchestration.council_orchestrator as co
    from core.base_agent import AgentResponse, SignalDirection
    from trading.safety_gate import SafetyGate
    market = {"last_price": 50000.0, "bid_price": 49999.0, "ask_price": 50001.0, "spread_bps": 0.4,
              "adv_24h_quote": 5e9, "current_vol_regime": "NORMAL"}
    cfg = {"symbol": "BTCUSDT", "current_price": 50000.0, "equity": 10000.0,
           "trading_mode": "PAPER", "market": market}
    b = mock.MagicMock()
    b.name = "stub"
    b.place_order.return_value = mock.MagicMock(order_id="x", avg_fill_price=50000.0, commission=0.0,
                                                status=order_status, notes="n")
    o = co.CouncilOrchestrator(mock.MagicMock(), safety_gate=SafetyGate())
    o.adjust_through_risk = lambda b_, r: (0.1, "ok")
    sig = AgentResponse(agent_name="AstroCouncil", signal=SignalDirection.LONG, confidence=75, reasoning="t")
    with mock.patch.object(co, "get_broker", return_value=b):
        out = asyncio.run(o.execute_trading_cycle([], sig, config=cfg))
    return out, b


def test_orchestrator_passes_client_order_id():
    out, b = _run_orch()
    cid = b.place_order.call_args.kwargs.get("client_order_id")
    assert cid and CID_RE.match(cid)
    assert out["client_order_id"] == cid and out["action"] == "EXECUTED"


def test_orchestrator_unknown_status_is_not_executed():
    out, b = _run_orch(order_status=getattr(OrderStatus, "UNKNOWN", None))
    assert out["action"] == "ORDER_UNKNOWN" and b.place_order.call_count == 1
