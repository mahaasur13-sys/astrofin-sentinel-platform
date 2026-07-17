"""
tests/test_hmm_risk_karl.py — Unit tests for HMM-aware RiskEngineV2 and KARL hooks.
"""

import pytest
from core.base_agent import AgentResponse, SignalDirection
from trading.risk_v2 import RiskEngineV2, RiskConfigV2
from agents.karl_synthesis import resolve_conflict


# ─── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def risk_engine():
    engine = RiskEngineV2(RiskConfigV2())
    engine.update_equity(100_000)
    return engine


def hmm_response(is_anomaly=False, probs=None):
    return AgentResponse(
        agent_name="HMMRegimeAgent",
        signal=SignalDirection.AVOID if is_anomaly else SignalDirection.NEUTRAL,
        confidence=90 if is_anomaly else 50,
        reasoning="HMM test",
        metadata={"is_anomaly": is_anomaly, "regime_probabilities": probs or [0.33, 0.34, 0.33]},
    )


def quant_response(signal=SignalDirection.LONG, confidence=80):
    return AgentResponse(
        agent_name="QuantAgent",
        signal=signal,
        confidence=confidence,
        reasoning="Quant test",
    )


# ─── RiskEngineV2.adjust_position_size tests ───────────────────────────────────


def test_no_hmm_data(risk_engine):
    size, reason = risk_engine.adjust_position_size(1000, [])
    assert size == 1000
    assert reason == "No HMM data"


def test_anomaly_stop(risk_engine):
    r = hmm_response(is_anomaly=True, probs=[0.1, 0.1, 0.8])
    size, reason = risk_engine.adjust_position_size(1000, [r])
    assert size == 0.0
    assert "STOP" in reason


def test_sideways_temper(risk_engine):
    r = hmm_response(probs=[0.1, 0.8, 0.1])
    size, reason = risk_engine.adjust_position_size(1000, [r])
    assert size == 500
    assert "0.5x" in reason


def test_bear_temper(risk_engine):
    r = hmm_response(probs=[0.1, 0.1, 0.7])
    size, reason = risk_engine.adjust_position_size(1000, [r])
    assert size == 300
    assert "0.3x" in reason


def test_normal_unchanged(risk_engine):
    r = hmm_response(probs=[0.8, 0.1, 0.1])
    size, reason = risk_engine.adjust_position_size(1000, [r])
    assert size == 1000
    assert "Normal" in reason


# ─── KARL resolve_conflict tests ───────────────────────────────────────────────


def test_no_conflict_normal_case():
    quant = quant_response(SignalDirection.LONG, 80)
    hmm = hmm_response()
    result = resolve_conflict(quant, hmm)
    assert result.confidence == 80
    assert result.signal == SignalDirection.LONG


def test_anomaly_conflict_temper():
    quant = quant_response(SignalDirection.LONG, 80)
    hmm = hmm_response(is_anomaly=True)
    result = resolve_conflict(quant, hmm)
    assert result.confidence == 0
    assert result.signal == SignalDirection.NEUTRAL
    assert "KARL" in result.reasoning
    assert "tempered" in result.reasoning


def test_partial_anomaly_high_confidence():
    quant = quant_response(SignalDirection.LONG, 99)
    hmm = hmm_response(is_anomaly=True)
    result = resolve_conflict(quant, hmm)
    assert result.confidence == 0
    assert result.signal == SignalDirection.NEUTRAL
