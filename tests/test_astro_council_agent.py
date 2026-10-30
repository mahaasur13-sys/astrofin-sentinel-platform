"""Unit tests for AstroCouncil weighted vote, weights and metadata serialization.

Locks the behaviour shipped in PRs #302 (weighted vote + signal normalization),
#303 (ElliotAgent weight), #304 (NEUTRAL confidence fallback) and
#305 (final_signal metadata as dict). No network / OKX / ephemeris — sub-agents
are mocked and ``_weighted_vote`` is exercised directly.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from agents._impl.synthesis.weights import AGENT_WEIGHTS
from agents._impl.synthesis.weights import get_agent_weight
from agents.astro_council_agent import AstroCouncilAgent
from core.base_agent import AgentResponse, SignalDirection

# Equal weights so the "3 LONG + 2 NEUTRAL" example maps to a 60/40 split.
EQ_WEIGHTS = {
    "GannAgent": 0.2,
    "BradleyAgent": 0.2,
    "ElliotAgent": 0.2,
    "CycleAgent": 0.2,
    "TimeWindowAgent": 0.2,
}


def _resp(name: str, signal, confidence: int = 100) -> AgentResponse:
    return AgentResponse(
        agent_name=name,
        signal=signal,
        confidence=confidence,
        reasoning="test",
        sources=[],
    )


@pytest.fixture
def council() -> AstroCouncilAgent:
    agent = AstroCouncilAgent()
    agent._weights = dict(EQ_WEIGHTS)
    return agent


def test_majority_long(council):
    responses = [
        _resp("GannAgent", SignalDirection.LONG),
        _resp("BradleyAgent", SignalDirection.LONG),
        _resp("CycleAgent", SignalDirection.LONG),
        _resp("ElliotAgent", SignalDirection.NEUTRAL),
        _resp("TimeWindowAgent", SignalDirection.NEUTRAL),
    ]
    result = council._weighted_vote(responses)
    assert result.signal == SignalDirection.LONG
    assert result.confidence == 60


# "BUY" is now a known alias of LONG (see tests/test_council_weights.py)
@pytest.mark.parametrize(
    "bad",
    [SignalDirection.AVOID, "NEUTRAL", "HOLD", "garbage", None, 12345],
)
def test_unknown_direction_does_not_crash(council, bad):
    responses = [
        _resp("GannAgent", SignalDirection.LONG),
        _resp("BradleyAgent", bad),
        _resp("CycleAgent", SignalDirection.LONG),
        _resp("ElliotAgent", SignalDirection.NEUTRAL),
        _resp("TimeWindowAgent", SignalDirection.NEUTRAL),
    ]
    result = council._weighted_vote(responses)  # no KeyError / AttributeError
    # unknown direction folds into NEUTRAL: LONG 0.4 vs NEUTRAL 0.6 -> NEUTRAL
    assert result.signal == SignalDirection.NEUTRAL


def test_neutral_fallback_confidence_from_neutral_bucket(council):
    # LONG raw 0.45 vs NEUTRAL raw 0.40 -> margin 5% <= 10% -> NEUTRAL,
    # confidence must come from the NEUTRAL bucket (40), not the rejected LONG (45).
    responses = [
        _resp("GannAgent", SignalDirection.LONG, 100),
        _resp("BradleyAgent", SignalDirection.LONG, 100),
        _resp("CycleAgent", SignalDirection.LONG, 25),
        _resp("ElliotAgent", SignalDirection.NEUTRAL, 100),
        _resp("TimeWindowAgent", SignalDirection.NEUTRAL, 100),
    ]
    result = council._weighted_vote(responses)
    assert result.signal == SignalDirection.NEUTRAL
    assert result.confidence == 40


def test_total_weight_zero_falls_back(council):
    result = council._weighted_vote([])
    assert result.signal == SignalDirection.NEUTRAL
    assert result.confidence == 20


async def test_run_metadata_final_signal_is_dict(council):
    responses = [
        _resp("GannAgent", SignalDirection.LONG),
        _resp("BradleyAgent", SignalDirection.LONG),
        _resp("CycleAgent", SignalDirection.LONG),
        _resp("ElliotAgent", SignalDirection.NEUTRAL),
        _resp("TimeWindowAgent", SignalDirection.NEUTRAL),
    ]
    council._call_ephemeris = MagicMock(return_value={"yoga": "test", "score": 50})
    council._run_sub_agents = AsyncMock(return_value=responses)

    result = await council.run({"symbol": "BTC", "datetime": None})

    final_signal = result.metadata["final_signal"]
    assert isinstance(final_signal, dict)
    assert not isinstance(final_signal, AgentResponse)
    json.dumps(final_signal)  # must not raise without default=str


def test_elliot_in_agent_weights():
    assert "ElliotAgent" in AGENT_WEIGHTS


def test_astro_weights_normalized_and_bounded():
    # weights come from the single source synthesis/weights.py
    for name in EQ_WEIGHTS:
        assert 0 < get_agent_weight(name) < 0.40
