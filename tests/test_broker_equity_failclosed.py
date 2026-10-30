"""Fail-closed equity: the broker must never invent a balance and the
orchestrator must not size an order from missing/invalid equity. No network."""
import asyncio
import math
from unittest import mock

import pytest

import trading.broker.binance as bmod
from trading.broker.binance import BinanceBroker


def _broker(exchange):
    b = BinanceBroker.__new__(BinanceBroker)
    b.paper = True
    b.connected = True
    b.exchange = exchange
    b.api_key = b.secret = None
    return b


def _no_fake_equity(b):
    """Either raise, or return a balance that is NOT the invented 10000."""
    try:
        bal = b.get_account_balance()
    except Exception:
        return
    assert bal.total_equity != 10000, "fabricated equity 10000"
    assert bal.available_cash != 10000, "fabricated cash 10000"


def test_no_ccxt_does_not_invent_equity():
    with mock.patch.object(bmod, "HAS_CCXT", False):
        _no_fake_equity(_broker(None))


def test_no_exchange_does_not_invent_equity():
    with mock.patch.object(bmod, "HAS_CCXT", True):
        _no_fake_equity(_broker(None))


def test_fetch_balance_error_does_not_invent_equity():
    ex = mock.MagicMock()
    ex.fetch_balance.side_effect = RuntimeError("boom")
    with mock.patch.object(bmod, "HAS_CCXT", True):
        _no_fake_equity(_broker(ex))


def test_fetch_balance_error_raises_balance_unavailable():
    from trading.broker.base import BalanceUnavailableError
    ex = mock.MagicMock()
    ex.fetch_balance.side_effect = RuntimeError("boom")
    with mock.patch.object(bmod, "HAS_CCXT", True), pytest.raises(BalanceUnavailableError):
        _broker(ex).get_account_balance()


def test_real_balance_passes_through():
    ex = mock.MagicMock()
    ex.fetch_balance.return_value = {"total": {"USDT": 1234.5}, "free": {"USDT": 1000.0}}
    with mock.patch.object(bmod, "HAS_CCXT", True):
        bal = _broker(ex).get_account_balance()
    assert bal.total_equity == 1234.5 and bal.available_cash == 1000.0


# ── orchestrator ─────────────────────────────────────────────────────────

def _run(cfg_equity=None, balance=None, balance_exc=None):
    import orchestration.council_orchestrator as co
    from core.base_agent import AgentResponse, SignalDirection
    from trading.safety_gate import SafetyGate
    market = {"last_price": 50000.0, "bid_price": 49999.0, "ask_price": 50001.0, "spread_bps": 0.4,
              "adv_24h_quote": 5e9, "current_vol_regime": "NORMAL"}
    cfg = {"symbol": "BTCUSDT", "current_price": 50000.0, "trading_mode": "PAPER", "market": market}
    if cfg_equity is not None:
        cfg["equity"] = cfg_equity
    b = mock.MagicMock()
    b.name = "stub"
    if balance_exc is not None:
        b.get_account_balance.side_effect = balance_exc
    else:
        b.get_account_balance.return_value = mock.MagicMock(total_equity=balance)
    b.place_order.return_value = mock.MagicMock(order_id="x", avg_fill_price=50000.0, commission=0.0,
                                                status=co.OrderStatus.FILLED, notes="n")
    o = co.CouncilOrchestrator(mock.MagicMock(), safety_gate=SafetyGate())
    o.adjust_through_risk = lambda b_, r: (0.1, "ok")
    sig = AgentResponse(agent_name="AstroCouncil", signal=SignalDirection.LONG, confidence=75, reasoning="t")
    with mock.patch.object(co, "get_broker", return_value=b):
        out = asyncio.run(o.execute_trading_cycle([], sig, config=cfg))
    return out, b


def test_orch_balance_error_blocks_no_equity():
    from trading.broker.base import BalanceUnavailableError
    out, b = _run(balance_exc=BalanceUnavailableError("x"))
    assert out["action"] == "DENIED" and out["blocked_reason"] == "no_equity"
    b.place_order.assert_not_called()


@pytest.mark.parametrize("bad", [0, -1.0, float("nan"), float("inf"), "10000", None, True])
def test_orch_invalid_broker_equity_blocks(bad):
    out, b = _run(balance=bad)
    assert out["action"] == "DENIED" and out["blocked_reason"] == "no_equity"
    b.place_order.assert_not_called()


@pytest.mark.parametrize("bad", [0, -5, float("nan"), "abc"])
def test_orch_invalid_cfg_equity_blocks(bad):
    out, b = _run(cfg_equity=bad, balance=5000.0)
    assert out["action"] == "DENIED" and out["blocked_reason"] == "no_equity"
    b.place_order.assert_not_called()


def test_orch_valid_cfg_equity_used_without_broker_balance():
    out, b = _run(cfg_equity=10000.0, balance_exc=RuntimeError("must not be called"))
    assert out["action"] == "EXECUTED"
    b.get_account_balance.assert_not_called()
    assert math.isclose(b.place_order.call_args.args[3] if len(b.place_order.call_args.args) > 3
                        else b.place_order.call_args.kwargs.get("quantity", 0.02), 0.02)


def test_orch_valid_broker_equity_executes():
    out, b = _run(balance=10000.0)
    assert out["action"] == "EXECUTED"
