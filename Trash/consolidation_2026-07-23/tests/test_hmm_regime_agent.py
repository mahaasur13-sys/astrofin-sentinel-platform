"""Tests for HMMRegimeAgent."""

import pytest
import numpy as np
from agents._impl.hmm_regime_agent import HMMRegimeAgent, run_hmm_regime_agent
from core.base_agent import AgentResponse, SignalDirection


@pytest.fixture
def agent():
    return HMMRegimeAgent()


@pytest.fixture
def valid_state():
    np.random.seed(42)
    prices = np.cumprod(1 + np.random.randn(60) * 0.01) * 100
    volumes = np.random.randint(100, 1000, 60)
    ohlcv = [{"close": float(p), "volume": int(v)} for p, v in zip(prices, volumes)]
    return {"symbol": "BTCUSDT", "ohlcv": ohlcv}


@pytest.mark.asyncio
async def test_hmm_agent_returns_response(agent, valid_state):
    response = await agent.run(valid_state)
    assert isinstance(response, AgentResponse)
    assert response.agent_name == "HMMRegimeAgent"


@pytest.mark.asyncio
async def test_hmm_agent_signal_in_bounds(agent, valid_state):
    response = await agent.run(valid_state)
    assert 0 <= response.confidence <= 100
    assert response.signal in [
        SignalDirection.LONG,
        SignalDirection.SHORT,
        SignalDirection.NEUTRAL,
        SignalDirection.AVOID,
    ]


@pytest.mark.asyncio
async def test_hmm_agent_degraded_on_empty_data(agent):
    state = {"symbol": "BTCUSDT", "ohlcv": []}
    response = await agent.run(state)
    assert response.signal == SignalDirection.NEUTRAL
    assert response.metadata.get("data_quality") == 0.0


@pytest.mark.asyncio
async def test_hmm_agent_convenience_runner(valid_state):
    response = await run_hmm_regime_agent(valid_state)
    assert isinstance(response, AgentResponse)
    assert response.agent_name == "HMMRegimeAgent"
