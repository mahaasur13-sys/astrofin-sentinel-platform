import pytest
from unittest.mock import AsyncMock, Mock, patch
from agents._impl.market_analyst import MarketAnalystAgent


@pytest.mark.asyncio
async def test_market_analyst_uses_async_http():
    agent = MarketAnalystAgent()
    symbol = "BTCUSDT"

    with patch("httpx.AsyncClient") as mock_client:
        mock_get = AsyncMock()
        # ВАЖНО: явно задаём обычный Mock, чтобы raise_for_status/json были синхронными
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

        data = await agent._fetch_ohlcv(symbol, "1d", 50)

        mock_get.assert_called_once()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0][0] == 45500.0  # close
        assert data[0][1] == 100.5  # volume
