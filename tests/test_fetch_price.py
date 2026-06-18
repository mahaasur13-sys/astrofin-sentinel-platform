from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest

from orchestration.sentinel_v5 import _fetch_price


@pytest.mark.asyncio
async def test_fetch_price_uses_async_http():
    with patch("httpx.AsyncClient") as mock_client:
        # Настраиваем асинхронный get, который возвращает синхронный ответ
        mock_get = AsyncMock()
        mock_get.return_value = Mock(
            status_code=200, raise_for_status=Mock(), json=Mock(return_value={"price": "100.0"})
        )
        mock_client.return_value.__aenter__.return_value.get = mock_get

        price = await _fetch_price("BTCUSDT")
        mock_get.assert_called_once()
        assert price == 100.0
