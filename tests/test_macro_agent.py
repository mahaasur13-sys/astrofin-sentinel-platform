"""Tests for MacroAgent — VIX, DXY, geopolitical risk."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock
from agents._impl.macro_agent import MacroAgent
from core.base_agent import SignalDirection


@pytest.fixture
def agent():
    return MacroAgent()


class TestMacroAgentVIX:
    def test_vix_fear_bearish(self, agent):
        sig, conf, reason = agent._analyze_vix(30.0)
        assert sig == SignalDirection.SHORT
        assert conf > 50
        assert "fear" in reason.lower()

    def test_vix_complacency_bullish(self, agent):
        sig, conf, reason = agent._analyze_vix(12.0)
        assert sig == SignalDirection.LONG
        assert conf > 50
        assert "complacency" in reason.lower()

    def test_vix_normal_neutral(self, agent):
        sig, conf, reason = agent._analyze_vix(20.0)
        assert sig == SignalDirection.NEUTRAL
        assert "normal" in reason.lower()


class TestMacroAgentDXY:
    def test_dxy_strong_bearish(self, agent):
        sig, conf, reason = agent._analyze_dxy(108.0)
        assert sig == SignalDirection.SHORT
        assert "strong" in reason.lower()

    def test_dxy_weak_bullish(self, agent):
        sig, conf, reason = agent._analyze_dxy(92.0)
        assert sig == SignalDirection.LONG
        assert "weak" in reason.lower()

    def test_dxy_normal_neutral(self, agent):
        sig, conf, reason = agent._analyze_dxy(100.0)
        assert sig == SignalDirection.NEUTRAL


class TestMacroAgentGeopolitical:
    @pytest.mark.asyncio
    async def test_rag_returns_bearish_on_conflict(self, agent):
        mock_rag = MagicMock()
        mock_rag.search = AsyncMock(
            return_value=[MagicMock(page_content="war and conflict in region causing instability")]
        )
        agent.rag = mock_rag
        sig, conf, reason = await agent._analyze_geopolitical({})
        assert sig == SignalDirection.SHORT

    @pytest.mark.asyncio
    async def test_rag_returns_bullish_on_peace(self, agent):
        mock_rag = MagicMock()
        mock_rag.search = AsyncMock(return_value=[MagicMock(page_content="peace agreement signed, trade deal reached")])
        agent.rag = mock_rag
        sig, conf, reason = await agent._analyze_geopolitical({})
        assert sig == SignalDirection.LONG

    @pytest.mark.asyncio
    async def test_rag_unavailable_returns_none(self, agent):
        agent.rag = None
        sig, conf, reason = await agent._analyze_geopolitical({})
        assert sig is None


class TestMacroAgentAggregate:
    def test_weighted_aggregate_bullish(self, agent):
        scores = [(SignalDirection.LONG, 80), (SignalDirection.LONG, 70), (SignalDirection.SHORT, 30)]
        sig, conf = agent._weighted_aggregate(scores)
        assert sig == SignalDirection.LONG

    def test_weighted_aggregate_neutral(self, agent):
        scores = [(SignalDirection.LONG, 50), (SignalDirection.SHORT, 50)]
        sig, conf = agent._weighted_aggregate(scores)
        assert sig == SignalDirection.NEUTRAL

    def test_analyze_no_data(self, agent):
        # Вызываем analyze синхронно, так как без моков RAG не вызовется
        import asyncio

        async def run():
            resp = await agent.analyze({})
            assert resp.signal == SignalDirection.NEUTRAL
            assert "missing" in resp.reasoning.lower()

        asyncio.run(run())


if __name__ == "__main__":
    pytest.main([__file__])
