"""RiskEngineV2 REDUCED (low_confidence) must shrink the position and keep the
REDUCED status through SafetyGate and CouncilOrchestrator. No network, stub broker."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest import mock

import pytest

import orchestration.council_orchestrator as co
import trading.safety_gate as sg
from core.base_agent import AgentResponse, SignalDirection
from trading.safety_gate import SafetyGate

PRICE = 50_000.0
EQUITY = 10_000.0
MARKET = {"last_price": PRICE, "bid_price": 49_999.0, "ask_price": 50_001.0, "spread_bps": 0.4,
          "adv_24h_quote": 5e9, "current_vol_regime": "NORMAL"}
PCT = 0.1  # min_confidence = 40 + 0.9 * 20 = 58


def _portfolio():
    return SimpleNamespace(positions={}, total_value=EQUITY)


def _sig(conf, s=SignalDirection.LONG):
    return AgentResponse(agent_name="AstroCouncil", signal=s, confidence=conf, reasoning="t")


def _check(conf, pct=PCT, state=None):
    gate = SafetyGate(portfolio=_portfolio())
    st = state or {"trading_mode": "PAPER", "market": dict(MARKET), "order_type": "market"}
    return gate.check(_sig(conf), st, current_price=PRICE, symbol="BTCUSDT",
                      suggested_position_pct=pct, order_qty=EQUITY * pct / PRICE)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("RISK_REDUCED_POSITION_FACTOR", raising=False)


def test_low_confidence_is_reduced_not_approved():
    d = _check(50)
    assert d.is_reduced, (d.status, d.reason)
    assert "low_confidence" in (d.blocked_reason or "")
    assert d.reduced_position_pct == pytest.approx(PCT * sg.DEFAULT_REDUCED_POSITION_FACTOR)
    assert d.reduced_position_pct < PCT


def test_default_factor_is_half():
    assert sg.DEFAULT_REDUCED_POSITION_FACTOR == 0.5
    assert sg.reduced_position_factor() == 0.5


def test_env_factor_applied(monkeypatch):
    monkeypatch.setenv("RISK_REDUCED_POSITION_FACTOR", "0.25")
    d = _check(50)
    assert d.is_reduced and d.reduced_position_pct == pytest.approx(PCT * 0.25)


@pytest.mark.parametrize("raw", ["abc", "nan", "inf", "-1", "0", "1", "1.5", "2"])
def test_bad_env_factor_never_keeps_or_increases_size(monkeypatch, raw):
    monkeypatch.setenv("RISK_REDUCED_POSITION_FACTOR", raw)
    d = _check(50)
    assert d.is_reduced
    assert d.reduced_position_pct == pytest.approx(PCT * sg.DEFAULT_REDUCED_POSITION_FACTOR)


def test_high_confidence_still_approved_full_size():
    d = _check(90)
    assert d.is_approved, d.reason
    assert d.reduced_position_pct == pytest.approx(PCT)


def test_blocked_stays_blocked_on_low_confidence():
    d = _check(50, state={"trading_mode": "PAPER", "market": {**MARKET, "spread_bps": None,
                                                                "bid_price": None, "ask_price": None}})
    assert d.is_blocked


def test_sanity_scaled_plus_low_confidence_keeps_both():
    d = _check(50, state={"trading_mode": "PAPER", "order_type": "market",
                          "market": {**MARKET, "adv_24h_quote": 1_000.0}})
    assert d.is_reduced
    assert d.adjusted_qty is not None
    assert d.reduced_position_pct == pytest.approx(PCT * 0.5)
    assert "low_confidence" in d.blocked_reason and "sanity_scaled" in d.blocked_reason


def _run_orchestrator(conf):
    broker = mock.MagicMock()
    broker.name = "stub"
    broker.place_order.return_value = mock.MagicMock(order_id="x", avg_fill_price=PRICE, commission=0.0)
    o = co.CouncilOrchestrator(mock.MagicMock(), safety_gate=SafetyGate(portfolio=_portfolio()))
    o.adjust_through_risk = lambda b, r: (PCT, "ok")
    cfg = {"symbol": "BTCUSDT", "current_price": PRICE, "equity": EQUITY, "trading_mode": "PAPER", "market": MARKET}
    with mock.patch.object(co, "get_broker", return_value=broker):
        out = asyncio.run(o.execute_trading_cycle([], _sig(conf), config=cfg))
    return out, broker


def test_orchestrator_reduced_status_and_half_qty_reach_order():
    out, broker = _run_orchestrator(50)
    assert out["action"] == "EXECUTED", out
    assert out["status"] == "REDUCED"
    qty = broker.place_order.call_args.args[3]
    assert qty == pytest.approx(EQUITY * PCT * 0.5 / PRICE)
    assert out["qty"] == pytest.approx(qty)


def test_orchestrator_approved_full_qty_unchanged():
    out, broker = _run_orchestrator(90)
    assert out["status"] == "APPROVED"
    assert broker.place_order.call_args.args[3] == pytest.approx(EQUITY * PCT / PRICE)
