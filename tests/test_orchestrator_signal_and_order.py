"""CouncilOrchestrator step 5: direction mapping, reduced_position_pct validation,
broker errors. Broker is a MagicMock stub, no network, PAPER mode."""
from __future__ import annotations

import asyncio
from unittest import mock

import pytest

import orchestration.council_orchestrator as co
from core.base_agent import AgentResponse, SignalDirection
from trading.broker.base import OrderSide
from trading.safety_gate import SafetyDecision, SafetyGate, SafetyStatus

MARKET = {"last_price": 50000.0, "bid_price": 49999.0, "ask_price": 50001.0, "spread_bps": 0.4,
          "adv_24h_quote": 5e9, "current_vol_regime": "NORMAL"}
CFG = {"symbol": "BTCUSDT", "current_price": 50000.0, "equity": 10000.0, "trading_mode": "PAPER", "market": MARKET}


def _sig(s, c=75):
    return AgentResponse(agent_name="AstroCouncil", signal=s, confidence=c, reasoning="t")


def _broker():
    b = mock.MagicMock()
    b.name = "stub"
    b.place_order.return_value = mock.MagicMock(order_id="x", avg_fill_price=50000.0, commission=0.0)
    return b


def _run(s, gate=None, broker=None):
    o = co.CouncilOrchestrator(mock.MagicMock(), safety_gate=gate or SafetyGate())
    o.adjust_through_risk = lambda b, r: (0.1, "ok")
    broker = broker or _broker()
    with mock.patch.object(co, "get_broker", return_value=broker):
        out = asyncio.run(o.execute_trading_cycle([], s, config=dict(CFG)))
    return out, broker


def _gate(**kw):
    g = mock.MagicMock()
    g.check.return_value = SafetyDecision(**kw)
    return g


@pytest.mark.parametrize("s", [SignalDirection.AVOID, SignalDirection.NEUTRAL, "NEUTRAL", "HOLD", "AVOID", None, "garbage"])
def test_non_directional_never_places_order(s):
    out, b = _run(_sig(s))
    assert out["action"] == "NEUTRAL", out
    b.place_order.assert_not_called()


@pytest.mark.parametrize("s", [SignalDirection.LONG, "LONG", "BUY", "STRONG_BUY"])
def test_long_aliases_buy_through_real_gate(s):
    out, b = _run(_sig(s))
    assert out["action"] == "EXECUTED", out
    args = b.place_order.call_args.args
    assert args[1] == OrderSide.BUY and args[3] == pytest.approx(0.02)


def test_short_reaches_gate_as_short_and_paper_denies_it():
    out, b = _run(_sig("SELL"))
    assert out["action"] == "DENIED" and "SHORT" in out["safety_reason"]
    b.place_order.assert_not_called()


def test_approved_default_and_reduced_pct():
    out, _ = _run(_sig(SignalDirection.LONG), gate=_gate(status=SafetyStatus.APPROVED, reason="ok"))
    assert out["qty"] == pytest.approx(0.02)  # default 1.0 -> min(0.1, 1.0)
    out, _ = _run(_sig(SignalDirection.LONG), gate=_gate(status=SafetyStatus.REDUCED, reason="r", reduced_position_pct=0.05))
    assert out["qty"] == pytest.approx(0.01)


@pytest.mark.parametrize("pct", [None, 0.0, -1.0, float("nan"), 5.0])
def test_invalid_reduced_pct_is_denied_not_crash(pct):
    out, b = _run(_sig(SignalDirection.LONG), gate=_gate(status=SafetyStatus.APPROVED, reason="r", reduced_position_pct=pct))
    assert out["action"] == "DENIED" and out["blocked_reason"] == "invalid_quantity", out
    b.place_order.assert_not_called()


def test_broker_exception_is_contained_and_not_retried():
    b = _broker()
    b.place_order.side_effect = RuntimeError("exchange 502")
    out, _ = _run(_sig(SignalDirection.LONG), broker=b)
    assert out["action"] == "ORDER_ERROR" and out["blocked"] is True
    assert b.place_order.call_count == 1
