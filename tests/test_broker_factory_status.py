"""Factory fail-closed on failed connect, no duplicate paper simulation in
BinanceBroker, correct ccxt order-status mapping. ccxt is faked; no network."""
import asyncio
import sys
from types import SimpleNamespace
from unittest import mock

import pytest

import trading.broker.binance as bmod
from trading.broker.base import OrderSide, OrderStatus, OrderType
from trading.broker.binance import BinanceBroker


@pytest.fixture
def live_flag(monkeypatch):
    from trading import factory
    monkeypatch.setenv(factory.LIVE_TRADING_FLAG_ENV, factory.LIVE_TRADING_FLAG_VALUE)
    return factory


def _fake_binance_mod(monkeypatch, connect):
    inst = mock.MagicMock(name="broker")
    if isinstance(connect, Exception):
        inst.connect.side_effect = connect
    else:
        inst.connect.return_value = connect
    inst.connected = connect is True
    cls = mock.MagicMock(name="BinanceBroker", return_value=inst)
    monkeypatch.setitem(sys.modules, "trading.broker.binance", SimpleNamespace(BinanceBroker=cls))
    return inst


# ── a) factory ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("connect", [False, None, RuntimeError("boom")])
def test_factory_raises_when_connect_fails(live_flag, monkeypatch, connect):
    from trading.mode import TradingMode
    _fake_binance_mod(monkeypatch, connect)
    with pytest.raises(live_flag.BrokerConnectionError):
        live_flag.get_broker(TradingMode.LIVE_LIMITED)


def test_factory_returns_connected_broker(live_flag, monkeypatch):
    from trading.mode import TradingMode
    inst = _fake_binance_mod(monkeypatch, True)
    assert live_flag.get_broker(TradingMode.LIVE_FULL) is inst


def test_factory_paper_unaffected(monkeypatch):
    from trading import factory
    from trading.mode import TradingMode
    paper = mock.MagicMock(name="PaperBroker")
    monkeypatch.setitem(sys.modules, "trading.paper_broker",
                        SimpleNamespace(get_paper_broker=lambda: paper))
    monkeypatch.delenv(factory.LIVE_TRADING_FLAG_ENV, raising=False)
    assert factory.get_broker(TradingMode.PAPER) is paper


@pytest.mark.parametrize("exc_name", ["BrokerConnectionError", "LiveTradingNotAllowedError"])
def test_orchestrator_denies_when_factory_raises(exc_name):
    import orchestration.council_orchestrator as co
    from trading import factory
    from core.base_agent import AgentResponse, SignalDirection
    from trading.safety_gate import SafetyGate
    exc_cls = getattr(factory, exc_name)
    o = co.CouncilOrchestrator(mock.MagicMock(), safety_gate=SafetyGate())
    o.adjust_through_risk = lambda b_, r: (0.1, "ok")
    sig = AgentResponse(agent_name="AstroCouncil", signal=SignalDirection.LONG, confidence=75, reasoning="t")
    with mock.patch.object(co, "get_broker", side_effect=exc_cls("x")):
        res = asyncio.run(o.execute_trading_cycle([], sig, config={"symbol": "BTCUSDT", "equity": 1e4}))
    assert res["action"] == "DENIED"
    assert res["blocked_reason"] == "broker_not_connected"


# ── b) paper=True must not simulate fills ────────────────────────────────

def _connected(paper, exchange=None):
    b = BinanceBroker(paper=paper)
    b.connected = True
    b.exchange = exchange or mock.MagicMock()
    return b


def test_paper_binance_does_not_simulate_fill(monkeypatch):
    monkeypatch.setattr(bmod, "HAS_CCXT", True)
    ex = mock.MagicMock()
    ex.fetch_ticker.return_value = {"last": 50000.0}
    b = _connected(True, ex)
    o = b.place_order("BTC/USDT", OrderSide.BUY, OrderType.MARKET, 0.01)
    assert o.status == OrderStatus.REJECTED
    assert o.filled_qty == 0
    assert "PaperBroker" in (o.notes or "")
    ex.create_order.assert_not_called()


# ── c) get_order_status mapping ──────────────────────────────────────────

@pytest.mark.parametrize("st,filled,expected", [
    ("open", 0.0, OrderStatus.PENDING),
    ("open", 0.4, OrderStatus.PARTIAL),
    ("closed", 1.0, OrderStatus.FILLED),
    ("closed", 0.4, OrderStatus.PARTIAL),
    ("canceled", 0.0, OrderStatus.CANCELLED),
    ("cancelled", 0.0, OrderStatus.CANCELLED),
    ("canceled", 0.4, OrderStatus.PARTIAL),
    ("expired", 0.0, OrderStatus.CANCELLED),
    ("rejected", 0.0, OrderStatus.REJECTED),
    ("weird", 0.0, OrderStatus.UNKNOWN),
    (None, 0.0, OrderStatus.UNKNOWN),
])
def test_get_order_status_mapping(monkeypatch, st, filled, expected):
    monkeypatch.setattr(bmod, "HAS_CCXT", True)
    ex = mock.MagicMock()
    ex.fetch_order.return_value = {"id": "1", "symbol": "BTC/USDT", "side": "buy", "amount": 1.0,
                                   "price": 100.0, "status": st, "filled": filled}
    o = _connected(False, ex).get_order_status("1")
    assert o.status == expected
    assert o.filled_qty == filled
