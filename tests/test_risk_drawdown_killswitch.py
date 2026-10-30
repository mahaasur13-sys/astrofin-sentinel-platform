"""Drawdown kill switch must work through SafetyGate (peak kept across calls and
across copy.copy of the gate), positions need their own price, and
get_current_params must not invent equity. No network, stub broker."""
from __future__ import annotations

import asyncio
import copy
from types import SimpleNamespace
from unittest import mock

import pytest

import orchestration.council_orchestrator as co
from core.base_agent import AgentResponse, SignalDirection
from trading.risk_v2 import RiskConfigV2, RiskEngineV2
from trading.safety_gate import SafetyGate

PRICE = 50_000.0
MARKET = {"last_price": PRICE, "bid_price": 49_999.0, "ask_price": 50_001.0, "spread_bps": 0.4,
          "adv_24h_quote": 5e9, "current_vol_regime": "NORMAL"}
STATE = {"trading_mode": "PAPER", "market": MARKET, "order_type": "market"}
PCT = 0.1


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("RISK_REDUCED_POSITION_FACTOR", raising=False)


def _sig():
    return AgentResponse(agent_name="AstroCouncil", signal=SignalDirection.LONG, confidence=90, reasoning="t")


def _check(gate, equity, positions=None):
    gate.portfolio = SimpleNamespace(total_value=equity, positions=positions or {})
    return gate.check(_sig(), dict(STATE), current_price=PRICE, symbol="BTCUSDT",
                      suggested_position_pct=PCT, order_qty=equity * PCT / PRICE if equity else 0.01)


def _is_kill(d):
    return not (d.is_approved or d.is_reduced) and "kill_switch" in (d.blocked_reason or "")


def test_gate_drawdown_kill_switch_fires():
    # Gate config max_drawdown=0.15: 100k -> 84k (16%) must be denied.
    g = SafetyGate()
    assert _check(g, 100_000.0).is_approved
    assert _is_kill(_check(g, 84_000.0))


def test_gate_88k_below_gate_threshold_not_killed():
    g = SafetyGate()
    _check(g, 100_000.0)
    assert not _is_kill(_check(g, 88_000.0))  # 12% < 15%


def test_peak_rises_and_survives_copy():
    g = SafetyGate()
    _check(copy.copy(g), 100_000.0)
    _check(copy.copy(g), 120_000.0)  # new peak
    assert g._equity_track["peak"] == 120_000.0
    assert _is_kill(_check(copy.copy(g), 100_000.0))  # 16.7% from 120k


@pytest.mark.parametrize("bad", [None, float("nan"), float("inf"), 0.0, -1.0])
def test_invalid_equity_does_not_touch_peak(bad):
    g = SafetyGate()
    _check(g, 100_000.0)
    d = _check(g, bad)
    assert d.blocked_reason == "no_equity"
    assert g._equity_track["peak"] == 100_000.0


def test_orchestrator_kill_switch_across_cycles():
    gate = SafetyGate()
    o = co.CouncilOrchestrator(mock.MagicMock(), safety_gate=gate)
    o.adjust_through_risk = lambda b, r: (PCT, "ok")
    outs = []
    for eq in (100_000.0, 84_000.0):
        broker = mock.MagicMock()
        broker.name = "stub"
        broker.connected = True
        broker.get_positions.return_value = []
        broker.place_order.return_value = mock.MagicMock(order_id="x", avg_fill_price=PRICE, commission=0.0)
        cfg = {"symbol": "BTCUSDT", "current_price": PRICE, "equity": eq, "trading_mode": "PAPER", "market": MARKET}
        with mock.patch.object(co, "get_broker", return_value=broker):
            outs.append((asyncio.run(o.execute_trading_cycle([], _sig(), config=cfg)), broker))
    assert outs[0][0]["blocked"] is False
    out, broker = outs[1]
    assert out["action"] == "DENIED" and "kill_switch" in out["blocked_reason"], out
    broker.place_order.assert_not_called()


@pytest.mark.parametrize("px", [None, 0, float("nan"), -1.0])
def test_position_without_own_price_fail_closed(px):
    pos = {"ETHUSDT": SimpleNamespace(notional_value=1_000.0, current_price=px, entry_price=3_000.0)}
    d = _check(SafetyGate(), 100_000.0, pos)
    assert not (d.is_approved or d.is_reduced)
    assert d.blocked_reason == "position_price_invalid"


def test_position_with_own_price_ok():
    pos = {"ETHUSDT": SimpleNamespace(notional_value=1_000.0, current_price=3_000.0)}
    assert _check(SafetyGate(), 100_000.0, pos).is_approved


def test_get_current_params_no_equity_size_zero():
    p = RiskEngineV2(RiskConfigV2()).get_current_params(observations={})
    assert p["position_size_pct"] == 0.0 and p["no_equity"] is True


def test_get_current_params_small_equity_not_floored():
    e = RiskEngineV2(RiskConfigV2())
    e.update_equity(500.0)
    p = e.get_current_params(observations={})
    assert p["equity"] == 500.0 and p["no_equity"] is False and p["position_size_pct"] > 0
