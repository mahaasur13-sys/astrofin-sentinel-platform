"""Integration tests for AstroCouncilAgent aggregation logic."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock
from agents._impl.astro_council.agent import AstroCouncilAgent
from core.base_agent import AgentResponse, SignalDirection


@pytest.fixture
def council():
    return AstroCouncilAgent()


def mock_response(
    signal: SignalDirection, confidence: float, reasoning: str = "test"
) -> AgentResponse:
    return AgentResponse(
        agent_name="TestAgent",
        signal=signal,
        confidence=confidence,
        reasoning=reasoning,
    )


class TestAstroCouncilBasic:
    @pytest.mark.asyncio
    async def test_all_agents_long(self, council):
        for agent in council.agents.values():
            agent.run = AsyncMock(return_value=mock_response(SignalDirection.LONG, 80))
        resp = await council.aggregate({})
        assert resp.signal == SignalDirection.LONG
        assert resp.confidence > 50

    @pytest.mark.asyncio
    async def test_all_agents_short(self, council):
        for agent in council.agents.values():
            agent.run = AsyncMock(return_value=mock_response(SignalDirection.SHORT, 80))
        resp = await council.aggregate({})
        assert resp.signal == SignalDirection.SHORT
        assert resp.confidence > 50

    @pytest.mark.asyncio
    async def test_all_neutral(self, council):
        for agent in council.agents.values():
            agent.run = AsyncMock(
                return_value=mock_response(SignalDirection.NEUTRAL, 50)
            )
        resp = await council.aggregate({})
        assert resp.signal == SignalDirection.NEUTRAL

    @pytest.mark.asyncio
    async def test_mixed_signals_no_majority(self, council):
        agents = list(council.agents.values())
        agents[0].run = AsyncMock(return_value=mock_response(SignalDirection.LONG, 70))
        agents[1].run = AsyncMock(return_value=mock_response(SignalDirection.SHORT, 70))
        for a in agents[2:]:
            a.run = AsyncMock(return_value=mock_response(SignalDirection.NEUTRAL, 50))
        resp = await council.aggregate({})
        assert resp.signal == SignalDirection.NEUTRAL

    @pytest.mark.asyncio
    async def test_one_agent_fails_others_long(self, council):
        agents = list(council.agents.values())
        agents[0].run = AsyncMock(side_effect=Exception("Ephemeris error"))
        for a in agents[1:]:
            a.run = AsyncMock(return_value=mock_response(SignalDirection.LONG, 80))
        resp = await council.aggregate({})
        assert resp.signal == SignalDirection.LONG

    @pytest.mark.asyncio
    async def test_all_agents_fail_returns_neutral(self, council):
        for agent in council.agents.values():
            agent.run = AsyncMock(side_effect=Exception("Ephemeris error"))
        resp = await council.aggregate({})
        assert resp.signal == SignalDirection.NEUTRAL
        assert resp.confidence <= 20

    @pytest.mark.asyncio
    async def test_high_confidence_overrides(self, council):
        agents = list(council.agents.values())
        agents[0].run = AsyncMock(return_value=mock_response(SignalDirection.LONG, 95))
        for a in agents[1:]:
            a.run = AsyncMock(return_value=mock_response(SignalDirection.SHORT, 10))
        resp = await council.aggregate({})
        assert resp.signal == SignalDirection.LONG

    @pytest.mark.asyncio
    async def test_ephemeris_unavailable_neutral(self, council):
        agents = list(council.agents.values())
        agents[0].run = AsyncMock(
            return_value=mock_response(
                SignalDirection.NEUTRAL, 10, "Ephemeris unavailable"
            )
        )
        for a in agents[1:]:
            a.run = AsyncMock(return_value=mock_response(SignalDirection.LONG, 70))
        resp = await council.aggregate({})
        assert resp.signal == SignalDirection.LONG

    @pytest.mark.asyncio
    async def test_conflicting_strong_signals_neutral(self, council):
        agents = list(council.agents.values())
        agents[0].run = AsyncMock(return_value=mock_response(SignalDirection.LONG, 90))
        agents[1].run = AsyncMock(return_value=mock_response(SignalDirection.SHORT, 90))
        for a in agents[2:]:
            a.run = AsyncMock(return_value=mock_response(SignalDirection.NEUTRAL, 10))
        resp = await council.aggregate({})
        assert resp.signal == SignalDirection.NEUTRAL

    @pytest.mark.asyncio
    async def test_run_returns_dict(self, council):
        for agent in council.agents.values():
            agent.run = AsyncMock(return_value=mock_response(SignalDirection.LONG, 70))
        result = await council.run({})
        assert isinstance(result, dict)
        assert "astro_council_signal" in result
        assert result["astro_council_signal"]["signal"] == "LONG"


if __name__ == "__main__":
    pytest.main([__file__])
