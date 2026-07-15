import pytest
from unittest.mock import AsyncMock, Mock, patch
from agents._impl.sentiment_agent import SentimentAgent


@pytest.mark.asyncio
async def test_fetch_fear_greed_uses_async_http():
    agent = SentimentAgent()

    with patch("httpx.AsyncClient") as mock_client:
        mock_get = AsyncMock()
        mock_get.return_value = Mock(
            status_code=200,
            raise_for_status=Mock(),
            json=Mock(return_value={"data": [{"value": "25", "value_classification": "Fear"}]}),
        )
        mock_client.return_value.__aenter__.return_value.get = mock_get

        result = await agent._fetch_fear_greed()

        mock_get.assert_called_once()
        assert result["raw_value"] == 25
        assert "Fear" in result["summary"]
        assert result["score"] == 0.25
