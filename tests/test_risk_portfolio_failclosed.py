"""RiskEngineV2 must not invent equity (was 100_000) and the orchestrator must feed
the default SafetyGate() a real portfolio snapshot so RiskEngineV2 checks run.
No network, stub broker."""
from __future__ import annotations

import asyncio
from unittest import mock

import pytest

import orchestration.council_orchestrator as co
from core.base_agent import AgentResponse, SignalDirection
from trading.broker.base import BalanceUnavailableError, Position
from trading.broker.binance import MarketPriceUnavailableError
from trading.risk_v2 import RiskConfigV2, RiskEngineV2
from trading.safety_gate import SafetyGate

PRICE = 50_000.0
EQUITY = 10_000.0
MARKET = {"last_price": PRICE, "bid_price": 49_999.0, "ask_price": 50_001.0, "spread_bps": 0.4,
          "adv_24h_quote": 5e9, "current_vol_regime": "NORMAL"}
BAD = [None, "x", float("nan"), float("inf"), 0, -5.0]


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("RISK_REDUCED_POSITION_FACTOR", raising=False)


def test_engine_without_equity_has_no_invented_equity():
    e = RiskEngineV2(RiskConfigV2())
    assert e.get_state().total_equity == 0.0
    ok, _, msg = e.check_kill_switch()
    assert not ok and "no_equity" in msg
    assert e.check_exposure("BTC", 1_000)[0] is False
    assert e.pre_trade_check("BTC", 1_000)[0] == "REJECTED"


@pytest.mark.parametrize("bad", BAD, ids=repr)
def test_engine_invalid_equity_fail_closed(bad):
    e = RiskEngineV2(RiskConfigV2())
    e.update_equity(bad)
    assert e.get_state().total_equity == 0.0
    assert e.pre_trade_check("BTC", 1_000)[0] == "REJECTED"


def test_engine_invalid_after_valid_does_not_reuse_stale():
    e = RiskEngineV2(RiskConfigV2())
    e.update_equity(100_000)
    e.update_equity(float("nan"))
    assert e.check_kill_switch()[0] is False
    e.update_equity(99_000)
    assert e.check_kill_switch()[0] is True


def _run(positions=None, positions_exc=None, pct=0.1):
    broker = mock.MagicMock()
    broker.name = "stub"
    broker.connected = True
    if positions_exc:
        broker.get_positions.side_effect = positions_exc
    else:
        broker.get_positions.return_value = positions or []
    broker.place_order.return_value = mock.MagicMock(order_id="x", avg_fill_price=PRICE, commission=0.0)
    gate = SafetyGate()
    o = co.CouncilOrchestrator(mock.MagicMock(), safety_gate=gate)
    o.adjust_through_risk = lambda b, r: (pct, "ok")
    cfg = {"symbol": "BTCUSDT", "current_price": PRICE, "equity": EQUITY, "trading_mode": "PAPER", "market": MARKET}
    sig = AgentResponse(agent_name="AstroCouncil", signal=SignalDirection.LONG, confidence=90, reasoning="t")
    with mock.patch.object(co, "get_broker", return_value=broker):
        out = asyncio.run(o.execute_trading_cycle([], sig, config=cfg))
    assert gate.portfolio is None  # shared gate is not mutated
    return out, broker


def test_orchestrator_default_gate_runs_exposure_check():
    # Already 0.3*EQUITY in BTCUSDT -> exposure cap (30%) must stop a new 10% buy.
    held = Position("BTCUSDT", quantity=0.3 * EQUITY / PRICE, avg_entry_price=None, current_price=PRICE)
    out, broker = _run(positions=[held])
    assert out["action"] == "DENIED", out
    assert "RiskEngineV2" in out["safety_reason"]
    broker.place_order.assert_not_called()


@pytest.mark.parametrize("exc", [BalanceUnavailableError("x"), MarketPriceUnavailableError("x")])
def test_orchestrator_positions_unavailable_blocks(exc):
    out, broker = _run(positions_exc=exc)
    assert out["action"] == "DENIED" and out["blocked_reason"] == "positions_unavailable"
    broker.place_order.assert_not_called()


def test_orchestrator_invalid_position_price_blocks():
    bad = Position("ETHUSDT", quantity=1.0, avg_entry_price=None, current_price=float("nan"))
    out, broker = _run(positions=[bad])
    assert out["blocked_reason"] == "positions_unavailable"
    broker.place_order.assert_not_called()


def test_orchestrator_clean_portfolio_still_executes():
    out, broker = _run(positions=[])
    assert out["blocked"] is False, out
    broker.place_order.assert_called_once()
