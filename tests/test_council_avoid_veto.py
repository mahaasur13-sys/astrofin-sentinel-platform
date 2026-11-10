"""CouncilOrchestrator: AVOID veto (DEC-1 / DEC-7), flag ASTROFIN_AVOID_VETO.

Default is off: the cycle keeps today's behaviour (AVOID consensus -> NEUTRAL, no order).
candidate records the evidence only. enforce exits before the risk step and before the
broker when the veto is confirmed: synthesis AVOID, or >= 2 independent agents AVOID.
One AVOID (e.g. a lone ElectoralAgent) is a candidate, never a block.

Broker is a MagicMock stub, no network, PAPER mode, no money.
"""
from __future__ import annotations

import asyncio
from unittest import mock

import pytest

import orchestration.council_orchestrator as co
from core.base_agent import AgentResponse, SignalDirection
from trading.safety_gate import SafetyGate

MARKET = {"last_price": 50000.0, "bid_price": 49999.0, "ask_price": 50001.0, "spread_bps": 0.4,
          "adv_24h_quote": 5e9, "current_vol_regime": "NORMAL"}
CFG = {"symbol": "BTCUSDT", "current_price": 50000.0, "equity": 10000.0,
       "trading_mode": "PAPER", "market": MARKET}
FLAG = "ASTROFIN_AVOID_VETO"


def _sig(signal, name="AstroCouncil"):
    return AgentResponse(agent_name=name, signal=signal, confidence=75, reasoning="t")


def _run(final_signal, responses=()):
    o = co.CouncilOrchestrator(mock.MagicMock(), safety_gate=SafetyGate())
    o.adjust_through_risk = lambda b, r: (0.1, "ok")
    broker = mock.MagicMock()
    broker.name = "stub"
    broker.place_order.return_value = mock.MagicMock(order_id="x", avg_fill_price=50000.0, commission=0.0)
    with mock.patch.object(co, "get_broker", return_value=broker) as get_broker:
        out = asyncio.run(o.execute_trading_cycle(list(responses), final_signal, config=dict(CFG)))
    return out, broker, get_broker


def test_single_electoral_avoid_is_candidate_not_veto(monkeypatch):
    monkeypatch.setenv(FLAG, "enforce")
    responses = [
        _sig(SignalDirection.AVOID, "ElectoralAgent"),
        _sig(SignalDirection.LONG, "FundamentalAgent"),
        _sig(SignalDirection.LONG, "QuantAgent"),
    ]
    out, broker, _ = _run(_sig(SignalDirection.LONG), responses)

    assert out["action"] == "EXECUTED", out
    assert out["blocked"] is False
    broker.place_order.assert_called_once()  # veto does not block the LONG trade
    candidates = out["avoid_veto"]["candidates"]
    assert [c["source_agent"] for c in candidates] == ["ElectoralAgent"]
    assert out["avoid_veto"]["confirmed"] is False
    assert candidates[0]["decision_id"] == out["avoid_veto"]["decision_id"]
    assert candidates[0]["ts"] and candidates[0]["reason"]


def test_two_independent_avoids_veto_the_long_consensus(monkeypatch):
    monkeypatch.setenv(FLAG, "enforce")
    responses = [
        _sig(SignalDirection.AVOID, "ElectoralAgent"),
        _sig(SignalDirection.AVOID, "SentimentAgent"),
        _sig(SignalDirection.LONG, "FundamentalAgent"),
    ]
    out, broker, get_broker = _run(_sig(SignalDirection.LONG), responses)

    assert out["action"] == "VETO", out
    assert out["size"] == 0.0
    assert out["blocked"] is True
    assert out["signal"] == "AVOID"
    assert "ElectoralAgent" in out["blocked_reason"] and "SentimentAgent" in out["blocked_reason"]
    broker.place_order.assert_not_called()
    get_broker.assert_not_called()
    assert len(out["avoid_veto"]["candidates"]) == 2
    assert out["avoid_veto"]["enforced"] is True
    vetoes = out["vetoes"]
    assert {v["source_agent"] for v in vetoes} == {"ElectoralAgent", "SentimentAgent"}
    assert all(v["reason"] and v["ts"] and v["decision_id"] == out["decision_id"] for v in vetoes)


def test_all_neutral_stays_neutral(monkeypatch):
    monkeypatch.setenv(FLAG, "enforce")
    out, _, _ = _run(_sig(SignalDirection.NEUTRAL),
                     [_sig(SignalDirection.NEUTRAL, "FundamentalAgent")])

    assert out["action"] == "NEUTRAL", out
    assert out["blocked"] is False
    assert out["avoid_veto"]["confirmed"] is False


def test_consensus_avoid_is_veto_without_second_agent(monkeypatch):
    monkeypatch.setenv(FLAG, "enforce")
    out, broker, get_broker = _run(_sig(SignalDirection.AVOID))

    assert out["action"] == "VETO", out
    assert out["blocked"] is True and out["size"] == 0.0
    assert out["avoid_veto"]["sources"] == ["final_signal=AVOID (AstroCouncil)"]
    broker.place_order.assert_not_called()
    get_broker.assert_not_called()
    assert [v["source_agent"] for v in out["vetoes"]] == ["AstroCouncil"]
    assert out["vetoes"][0]["decision_id"] == out["decision_id"]


def test_final_signal_in_responses_is_not_a_second_agent(monkeypatch):
    """The consensus agent repeating AVOID in agent_responses must not count as agent #2."""
    monkeypatch.setenv(FLAG, "enforce")
    out, broker, _ = _run(_sig(SignalDirection.AVOID),
                          [_sig(SignalDirection.AVOID, "AstroCouncil"),
                           _sig(SignalDirection.LONG, "QuantAgent")])

    assert out["action"] == "VETO", out
    assert out["avoid_veto"]["candidates"] == []  # own agent_name excluded
    assert out["avoid_veto"]["sources"] == ["final_signal=AVOID (AstroCouncil)"]
    broker.place_order.assert_not_called()


def test_single_agent_avoid_with_avoid_consensus_is_not_double_counted(monkeypatch):
    """One AVOID agent + non-AVOID consensus: candidate only, no veto."""
    monkeypatch.setenv(FLAG, "enforce")
    out, broker, _ = _run(_sig(SignalDirection.LONG),
                          [_sig(SignalDirection.AVOID, "ElectoralAgent")])

    assert out["action"] == "EXECUTED", out
    assert out["avoid_veto"]["confirmed"] is False
    broker.place_order.assert_called_once()


def test_consensus_hold_is_not_a_veto(monkeypatch):
    monkeypatch.setenv(FLAG, "enforce")
    out, _, _ = _run(_sig("HOLD"))

    assert out["action"] == "NEUTRAL", out
    assert out["blocked"] is False
    assert out["avoid_veto"]["confirmed"] is False


def test_flag_off_keeps_todays_behaviour(monkeypatch):
    monkeypatch.delenv(FLAG, raising=False)
    out, broker, _ = _run(_sig(SignalDirection.AVOID))

    assert out["action"] == "NEUTRAL", out
    assert out["blocked"] is False
    assert "avoid_veto" not in out
    broker.place_order.assert_not_called()


def test_candidate_mode_records_evidence_without_blocking(monkeypatch):
    monkeypatch.setenv(FLAG, "candidate")
    responses = [
        _sig(SignalDirection.AVOID, "ElectoralAgent"),
        _sig(SignalDirection.AVOID, "SentimentAgent"),
    ]
    out, broker, _ = _run(_sig(SignalDirection.LONG), responses)

    assert out["action"] == "EXECUTED", out
    assert out["blocked"] is False
    broker.place_order.assert_called_once()
    veto = out["avoid_veto"]
    assert veto["mode"] == "candidate"
    assert veto["confirmed"] is True and veto["enforced"] is False
    assert len(veto["candidates"]) == 2


@pytest.mark.parametrize("raw", ["", "  ", "on", "true", "ENFORCE!", "candidate "])
def test_unknown_or_blank_flag_is_read_conservatively(monkeypatch, raw):
    """Unknown values fall back to off; the trailing-space candidate is normalised to candidate."""
    monkeypatch.setenv(FLAG, raw)
    mode = co._avoid_veto_mode()
    assert mode in ("off", "candidate")
    if raw.strip().lower() != "candidate":
        assert mode == "off"


def test_decision_id_is_reused_from_config(monkeypatch):
    monkeypatch.setenv(FLAG, "enforce")
    o = co.CouncilOrchestrator(mock.MagicMock(), safety_gate=SafetyGate())
    o.adjust_through_risk = lambda b, r: (0.1, "ok")
    cfg = dict(CFG, decision_id="dec-42")
    with mock.patch.object(co, "get_broker", return_value=mock.MagicMock()):
        out = asyncio.run(o.execute_trading_cycle([], _sig(SignalDirection.AVOID), config=cfg))

    assert out["decision_id"] == "dec-42"
    assert out["avoid_veto"]["decision_id"] == "dec-42"
