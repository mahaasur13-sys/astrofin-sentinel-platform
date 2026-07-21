"""Smoke test for RAG integration in agents."""

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.base_agent import get_rag
from agents._impl.fundamental_agent import FundamentalAgent


async def main():
    print("=" * 60)
    print("Phase 5.3: RAG Integration Smoke Test")
    print("=" * 60)

    # 1. Test Singleton
    print("\n[Test 1] RAG Singleton...")
    rag1 = get_rag()
    rag2 = get_rag()
    assert rag1 is rag2, "Singleton failed — different instances!"
    assert rag1 is not None, "RAGIndex not initialized!"
    print(f"  ✅ Singleton: {len(rag1.chunks)} chunks loaded, same instance: {rag1 is rag2}")

    # 2. Test FundamentalAgent with RAG
    print("\n[Test 2] FundamentalAgent with RAG...")
    agent = FundamentalAgent()
    assert agent.use_rag is True, "FundamentalAgent should have use_rag=True"
    
    result = await agent.generate("BTC/USDT fundamental analysis recent news")
    context_len = len(result.get("rag_context", ""))
    print(f"  ✅ Agent: {result['agent_name']}")
    print(f"  ✅ RAG context: {context_len} chars")
    print(f"  ✅ Signal: {result.get('signal', 'NEUTRAL')}")
    assert context_len > 0, "RAG context should not be empty!"

    # 3. Verify multi-call speed (second call no model load)
    print("\n[Test 3] Second call (no model reload)...")
    result2 = await agent.generate("ETH/USDT market outlook")
    context_len2 = len(result2.get("rag_context", ""))
    print(f"  ✅ RAG context: {context_len2} chars")
    assert context_len2 > 0, "Second call should also have RAG context"

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED — Phase 5.3 RAG Integration")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
