"""SafetyGate must not invent equity (was 100_000), SafetyDecision must default
to a fail-closed size, and the orchestrator must report the actual size sent.
No network, stub broker."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest import mock

import pytest

import orchestration.council_orchestrator as co
from core.base_agent import AgentResponse, SignalDirection
from trading.safety_gate import SafetyDecision, SafetyGate, SafetyStatus

PRICE = 50_000.0
EQUITY = 10_000.0
MARKET = {"last_price": PRICE, "bid_price": 49_999.0, "ask_price": 50_001.0, "spread_bps": 0.4,
          "adv_24h_quote": 5e9, "current_vol_regime": "NORMAL"}
PCT = 0.1
STATE = {"trading_mode": "PAPER", "market": MARKET, "order_type": "market"}
BAD = [None, "10000", float("nan"), float("inf"), float("-inf"), 0, 0.0, -5.0, True]


def _sig(conf=90):
    return AgentResponse(agent_name="AstroCouncil", signal=SignalDirection.LONG, confidence=conf, reasoning="t")


def _gate_check(portfolio, conf=90):
    return SafetyGate(portfolio=portfolio).check(
        _sig(conf), dict(STATE), current_price=PRICE, symbol="BTCUSDT",
        suggested_position_pct=PCT, order_qty=EQUITY * PCT / PRICE)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("RISK_REDUCED_POSITION_FACTOR", raising=False)


@pytest.mark.parametrize("tv", BAD, ids=repr)
def test_invalid_total_value_blocks_no_equity(tv):
    p = SimpleNamespace(positions={}) if tv is None else SimpleNamespace(positions={}, total_value=tv)
    d = _gate_check(p)
    assert d.is_blocked, (d.status, d.reason)
    assert d.blocked_reason == "no_equity"


def test_exposure_uses_real_equity_not_100k():
    # 0.1 * 10_000 = 1_000 notional; existing 2_400 position -> 34% > 25% per-asset limit.
    # With the old invented 100_000 the same exposure would have passed.
    pos = SimpleNamespace(notional_value=2_400.0, current_price=PRICE, entry_price=PRICE)
    d = _gate_check(SimpleNamespace(positions={"BTCUSDT": pos}, total_value=EQUITY))
    assert not d.is_approved and not d.is_reduced, (d.status, d.reason)


def test_valid_total_value_approved_as_before():
    d = _gate_check(SimpleNamespace(positions={}, total_value=EQUITY))
    assert d.is_approved, d.reason
    assert d.reduced_position_pct == pytest.approx(PCT)


def test_total_equity_field_is_used_when_total_value_absent():
    d = _gate_check(SimpleNamespace(positions={}, total_equity=EQUITY))
    assert d.is_approved, d.reason


def test_decision_default_size_is_fail_closed():
    assert SafetyDecision(status=SafetyStatus.APPROVED, reason="x").reduced_position_pct == 0.0


def test_stack_disabled_still_passes_explicit_size(monkeypatch):
    import trading.safety_gate as sg
    monkeypatch.setattr(sg, "SAFETY_STACK_ENABLED", False)
    d = SafetyGate().check(_sig(), dict(STATE), current_price=PRICE, suggested_position_pct=PCT)
    assert d.is_approved and d.reduced_position_pct == pytest.approx(PCT)


def _run(conf, portfolio):
    broker = mock.MagicMock()
    broker.name = "stub"
    broker.place_order.return_value = mock.MagicMock(order_id="x", avg_fill_price=PRICE, commission=0.0)
    o = co.CouncilOrchestrator(mock.MagicMock(), safety_gate=SafetyGate(portfolio=portfolio))
    o.adjust_through_risk = lambda b, r: (PCT, "ok")
    cfg = {"symbol": "BTCUSDT", "current_price": PRICE, "equity": EQUITY, "trading_mode": "PAPER", "market": MARKET}
    with mock.patch.object(co, "get_broker", return_value=broker):
        out = asyncio.run(o.execute_trading_cycle([], _sig(conf), config=cfg))
    return out, broker


def test_orchestrator_no_equity_blocks_and_no_order():
    out, broker = _run(90, SimpleNamespace(positions={}))
    assert out["action"] == "DENIED" and out["status"] == "BLOCKED"
    assert out["blocked_reason"] == "no_equity"
    broker.place_order.assert_not_called()


def test_orchestrator_size_is_actual_on_reduced():
    out, broker = _run(50, SimpleNamespace(positions={}, total_value=EQUITY))
    assert out["status"] == "REDUCED"
    assert out["size"] == pytest.approx(PCT * 0.5)
    assert broker.place_order.call_args.args[3] == pytest.approx(EQUITY * out["size"] / PRICE)


def test_orchestrator_size_is_actual_on_approved():
    out, broker = _run(90, SimpleNamespace(positions={}, total_value=EQUITY))
    assert out["status"] == "APPROVED"
    assert out["size"] == pytest.approx(PCT)
    assert broker.place_order.call_args.args[3] == pytest.approx(EQUITY * PCT / PRICE)
