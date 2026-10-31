"""Without ccxt the Binance broker must not pretend to be connected, fill orders
or invent prices, and the orchestrator must DENY cleanly. No network."""
import asyncio
from unittest import mock

import pytest

import trading.broker.binance as bmod
from trading.broker.base import BalanceUnavailableError, OrderSide, OrderStatus, OrderType
from trading.broker.binance import BinanceBroker


@pytest.fixture
def no_ccxt(monkeypatch):
    monkeypatch.setattr(bmod, "HAS_CCXT", False)
    monkeypatch.delenv("BINANCE_API_KEY", raising=False)
    monkeypatch.delenv("BINANCE_SECRET", raising=False)


@pytest.mark.parametrize("paper", [True, False])
def test_connect_without_ccxt_is_not_connected(no_ccxt, paper):
    b = BinanceBroker(paper=paper)
    assert b.connect() is False
    assert b.connected is False


def _forced(paper):
    """Even if something marks the broker connected, no exchange => no simulation."""
    b = BinanceBroker(paper=paper)
    b.connected = True
    b.exchange = None
    return b


@pytest.mark.parametrize("paper", [True, False])
def test_place_order_without_ccxt_rejected(no_ccxt, paper):
    for b in (BinanceBroker(paper=paper), _forced(paper)):
        b.connect() if not b.connected else None
        o = b.place_order("BTCUSDT", OrderSide.BUY, OrderType.MARKET, 0.01, client_order_id=None)
        assert o.status is OrderStatus.REJECTED
        assert o.filled_qty == 0 and not o.avg_fill_price


@pytest.mark.parametrize("paper", [True, False])
def test_limit_order_without_ccxt_not_filled(no_ccxt, paper):
    o = _forced(paper).place_order("BTCUSDT", OrderSide.SELL, OrderType.LIMIT, 1.0, price=123.0)
    assert o.status is OrderStatus.REJECTED and o.filled_qty == 0


@pytest.mark.parametrize("paper", [True, False])
def test_no_invented_price_without_ccxt(no_ccxt, paper):
    for b in (BinanceBroker(paper=paper), _forced(paper)):
        b.connect() if not b.connected else None
        try:
            p = b.get_market_price("BTCUSDT")
        except Exception:
            continue
        assert p != 100.0 and not p, f"invented price {p!r}"


def test_other_methods_fail_closed(no_ccxt):
    b = _forced(False)
    assert b.cancel_order("1") is False
    assert b.get_order_status("1") is None
    with pytest.raises(BalanceUnavailableError):
        b.get_positions()  # unknown holdings are not "no positions"
    with pytest.raises(Exception):
        b.get_account_balance()


def test_factory_live_without_ccxt_not_connected(no_ccxt, monkeypatch):
    from trading import factory
    from trading.mode import TradingMode
    monkeypatch.setenv(factory.LIVE_TRADING_FLAG_ENV, factory.LIVE_TRADING_FLAG_VALUE)
    with pytest.raises(factory.BrokerConnectionError):
        factory.get_broker(TradingMode.LIVE_LIMITED)


# ── orchestrator ─────────────────────────────────────────────────────────

def _run(broker, cfg_extra=None):
    import orchestration.council_orchestrator as co
    from core.base_agent import AgentResponse, SignalDirection
    from trading.safety_gate import SafetyGate
    market = {"last_price": 50000.0, "bid_price": 49999.0, "ask_price": 50001.0, "spread_bps": 0.4,
              "adv_24h_quote": 5e9, "current_vol_regime": "NORMAL"}
    cfg = {"symbol": "BTCUSDT", "trading_mode": "PAPER", "market": market, "equity": 10000.0}
    cfg.update(cfg_extra or {})
    o = co.CouncilOrchestrator(mock.MagicMock(), safety_gate=SafetyGate())
    o.adjust_through_risk = lambda b_, r: (0.1, "ok")
    sig = AgentResponse(agent_name="AstroCouncil", signal=SignalDirection.LONG, confidence=75, reasoning="t")
    with mock.patch.object(co, "get_broker", return_value=broker):
        return asyncio.run(o.execute_trading_cycle([], sig, config=cfg))


@pytest.mark.parametrize("cfg_extra", [None, {"current_price": 50000.0}])
def test_orch_no_ccxt_live_broker_denied(no_ccxt, cfg_extra):
    b = BinanceBroker(paper=False)
    b.connect()
    out = _run(b, cfg_extra)
    assert out["action"] == "DENIED", out
    assert out["blocked_reason"] == "broker_not_connected"


def test_orch_rejected_order_not_reported_executed(no_ccxt):
    b = _forced(False)
    # Without ccxt get_positions now raises (-> positions_unavailable, earlier deny).
    # Stub it to keep exercising the place_order REJECTED path.
    b.get_positions = lambda: []
    out = _run(b, {"current_price": 50000.0})
    assert out["action"] != "EXECUTED", out
    assert out["blocked_reason"] == "order_rejected"


def test_orch_no_ccxt_forced_connected_denied_before_order(no_ccxt):
    b = _forced(False)
    out = _run(b, {"current_price": 50000.0})
    assert out["action"] == "DENIED" and out["blocked_reason"] == "positions_unavailable", out
