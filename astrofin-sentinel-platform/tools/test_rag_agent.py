"""Smoke test for Phase 5.3: RAG Integration in BaseAgent."""

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.base_agent import BaseAgent, get_rag


class TestRAGAgent(BaseAgent):
    """Test agent with RAG enabled."""

    def __init__(self):
        super().__init__(
            name="TestRAGAgent",
            domain="trading",
            weight=0.05,
            use_rag=True,
        )

    async def run(self, state: dict):
        from core.base_agent import AgentResponse, SignalDirection
        return AgentResponse(
            agent_name=self.name,
            signal=SignalDirection.NEUTRAL,
            confidence=50,
            reasoning="RAG smoke test",
        )

    async def test_generate(self, prompt: str):
        return await self.generate_with_rag(prompt)


async def main():
    print("=" * 60)
    print("Phase 5.3: RAG Integration Smoke Test")
    print("=" * 60)

    # Test 1: Singleton
    print("\n[Test 1] RAG Singleton...")
    rag1 = get_rag()
    rag2 = get_rag()
    assert rag1 is rag2, "Singleton failed — different instances!"
    assert rag1 is not None, "RAGIndex not initialized!"
    print(f"  ✅ Singleton: {len(rag1.chunks)} chunks loaded, same instance: {rag1 is rag2}")

    # Test 2: Direct retrieval
    print("\n[Test 2] Direct RAG retrieval...")
    chunks = rag1.retrieve("фундаментальный анализ BTC", top_k=3)
    assert len(chunks) > 0, "No chunks retrieved!"
    for i, c in enumerate(chunks):
        print(f"  [{i+1}] rrf={c.metadata.get('rrf_score', 0):.4f} src={c.metadata.get('source', '?')[:60]}")
    assert len(chunks) >= 1, "Should get at least 1 chunk"

    # Test 3: Agent with use_rag=True
    print("\n[Test 3] Agent with use_rag=True...")
    agent = TestRAGAgent()
    assert agent.use_rag is True, "use_rag should be True"
    ctx = agent._get_rag_context("анализ волатильности Bitcoin")
    assert len(ctx) > 0, "RAG context should not be empty"
    print(f"  ✅ RAG context: {len(ctx)} chars")

    # Test 4: Second call (no model reload)
    print("\n[Test 4] Second call (cached model)...")
    ctx2 = agent._get_rag_context("Ethereum market outlook")
    print(f"  ✅ Context length: {len(ctx2)} chars")
    assert len(ctx2) > 0

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED — Phase 5.3 RAG Integration")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
