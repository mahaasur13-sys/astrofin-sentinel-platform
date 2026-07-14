"""Integration tests for BaseAgent ↔ RAG stack (async, hybrid).

Covers the contract introduced in P2-03d: BaseAgent owns a lazy
`_retriever` whose `retrieve()` is async; `_build_prompt` is async too.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch


from core.base_agent import (
    AgentResponse,
    BaseAgent,
    SignalDirection,
    _DegradedRetriever,
)


import pytest


class MockAgent(BaseAgent):
    """Concrete agent for testing."""

    async def run(self, state: dict) -> AgentResponse:
        return AgentResponse(
            agent_name="test",
            signal=SignalDirection.NEUTRAL,
            confidence=50,
            reasoning="test",
        )


@pytest.mark.unit
def test_build_prompt_includes_rag_results():
    agent = MockAgent(name="TestAgent", domain="astrology")
    fake_chunks = [
        {
            "content": "Muhurta trading rule: avoid Tuesdays",
            "source": "test.md",
            "title": "Test Rule",
            "domain": "astrology",
            "relevance_score": 0.9,
        }
    ]
    with patch.object(
        agent._retriever, "retrieve", new_callable=AsyncMock
    ) as mock_retrieve:
        mock_retrieve.return_value = fake_chunks
        import asyncio

        prompt = asyncio.get_event_loop().run_until_complete(
            agent._build_prompt("Should I trade now?", use_rag=True)
        )
        assert "Muhurta trading rule" in prompt
        assert "Test Rule" in prompt
        assert "RAG источники" in prompt


@pytest.mark.unit
def test_build_prompt_no_rag_when_disabled():
    agent = MockAgent(name="TestAgent", domain="astrology")
    with patch.object(
        agent._retriever, "retrieve", new_callable=AsyncMock
    ) as mock_retrieve:
        import asyncio

        asyncio.get_event_loop().run_until_complete(
            agent._build_prompt("Task", use_rag=False)
        )
        mock_retrieve.assert_not_called()


@pytest.mark.unit
def test_build_prompt_works_with_degraded_retriever():
    """При деградированном ретривере (pgvector недоступен) промпт строится без ошибок."""
    agent = MockAgent(name="TestAgent", domain="astrology")
    # Принудительно подменяем реальный ретривер на _DegradedRetriever.
    agent._retriever = _DegradedRetriever()
    import asyncio

    prompt = asyncio.get_event_loop().run_until_complete(
        agent._build_prompt("Task", use_rag=True)
    )
    assert "нет релевантных источников" in prompt
    assert "RAG" in prompt
