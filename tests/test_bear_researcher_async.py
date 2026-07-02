import pytest
from unittest.mock import AsyncMock, Mock, patch
from agents._impl.bear_researcher import BearResearcherAgent


@pytest.mark.asyncio
async def test_bear_researcher_uses_async_http():
    agent = BearResearcherAgent()
    symbol = "BTCUSDT"

    with patch("httpx.AsyncClient") as mock_client:
        mock_get = AsyncMock()
        mock_get.return_value = Mock(
            status_code=200,
            raise_for_status=Mock(),
            json=Mock(
                return_value={
                    "data": [
                        ["1672531200000", "45000", "46000", "44000", "45500", "100.5"],
                        ["1672617600000", "45500", "46500", "45000", "46000", "200.3"],
                    ]
                }
            ),
        )
        mock_client.return_value.__aenter__.return_value.get = mock_get

        data = await agent._fetch_ohlcv(symbol, "1d", 60)

        mock_get.assert_called_once()
        assert isinstance(data, list)
        assert len(data) == 2
        assert len(data[0]) == 5
        assert data[0][3] == 45500.0
        assert data[0][4] == 100.5
