from __future__ import annotations

from unittest.mock import patch


from core.base_agent import AgentResponse, BaseAgent, SignalDirection


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
    with patch.object(agent._rag, "retrieve", return_value=fake_chunks):
        prompt = agent._build_prompt("Should I trade now?", use_rag=True)
        assert "Muhurta trading rule" in prompt
        assert "Test Rule" in prompt
        assert "RAG источники" in prompt


@pytest.mark.unit
def test_build_prompt_no_rag_when_disabled():
    agent = MockAgent(name="TestAgent", domain="astrology")
    with patch.object(agent._rag, "retrieve") as mock_retrieve:
        agent._build_prompt("Task", use_rag=False)
        mock_retrieve.assert_not_called()


@pytest.mark.unit
def test_build_prompt_handles_ollama_unavailable():
    agent = MockAgent(name="TestAgent", domain="astrology")
    with patch.object(agent._rag, "retrieve", side_effect=Exception("Ollama down")):
        prompt = agent._build_prompt("Task", use_rag=True)
        assert "rag" in prompt.lower() and "unavailable" in prompt.lower()
