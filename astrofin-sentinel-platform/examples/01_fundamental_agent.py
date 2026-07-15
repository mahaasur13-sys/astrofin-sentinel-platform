"""
Example 01 - FundamentalAgent smoke test.

Runs FundamentalAgent with mocked CoinGecko/market-data layer and prints
AgentResponse. Works offline - no external API calls.

Usage:
    cd /home/workspace/push
    python3 examples/01_fundamental_agent.py

Expected output:
    agent_name=FundamentalAgent
    signal=NEUTRAL  # or LONG/SHORT depending on stub data
    confidence=NN  # 0..100
    reasoning="..."
"""
import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock

# Allow running this script from anywhere
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agents._impl.fundamental_agent import FundamentalAgent


async def main() -> int:
    # FundamentalAgent has no constructor arguments in this codebase.
    # It will try external fetches; we monkeypatch the private network helpers
    # so the example remains offline and deterministic.
    agent = FundamentalAgent()

    agent._fetch_crypto_metadata = AsyncMock(return_value={
        "symbol": "BTCUSDT",
        "market_cap": 1.2e12,
        "circulating_supply": 19_500_000,
        "total_supply": 21_000_000,
    })
    agent._fetch_onchain_data = AsyncMock(return_value={
        "active_addresses": 1_000_000,
        "tx_count_24h": 350_000,
        "hash_rate": 650,
    })

    state = {
        "symbol": "BTCUSDT",
        "timeframe": "SWING",
        "price": 105.0,
    }

    response = await agent.run(state)

    # AgentResponse fields: agent_name, signal, confidence, reasoning,
    # sources, metadata, timestamp, session_id
    print("agent_name =", response.agent_name)
    print("signal     =", response.signal)
    print("confidence =", response.confidence)
    print("reasoning  =", response.reasoning[:120])
    print("sources    =", response.sources)
    print("timestamp  =", response.timestamp)

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
