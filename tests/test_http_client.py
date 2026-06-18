from __future__ import annotations

import pytest
import httpx
from unittest.mock import AsyncMock, patch
from core.http_client import get_http_client, close_http_client


@pytest.fixture(autouse=True)
async def reset_client():
    await close_http_client()
    yield
    await close_http_client()


@pytest.mark.asyncio
async def test_get_http_client_returns_async_client():
    client = get_http_client()
    assert isinstance(client, httpx.AsyncClient)
    assert client.timeout == httpx.Timeout(10.0)


@pytest.mark.asyncio
async def test_get_http_client_is_singleton():
    c1 = get_http_client()
    c2 = get_http_client()
    assert c1 is c2


@pytest.mark.asyncio
async def test_get_request_succeeds():
    client = get_http_client()
    mock_response = httpx.Response(200, json={"data": "ok"}, request=httpx.Request("GET", "http://test"))
    with patch.object(client, "get", AsyncMock(return_value=mock_response)) as mock_get:
        response = await client.get("http://test")
        assert response.status_code == 200
        assert response.json() == {"data": "ok"}
        mock_get.assert_called_once()


@pytest.mark.asyncio
async def test_retry_on_5xx():
    client = get_http_client()
    # Первый запрос упал, второй ок
    mock_get = AsyncMock(
        side_effect=[
            httpx.HTTPStatusError("error", request=httpx.Request("GET", "http://test"), response=httpx.Response(502)),
            httpx.Response(200, json={"data": "ok"}, request=httpx.Request("GET", "http://test")),
        ]
    )
    with patch.object(client, "get", mock_get):
        # Передаём retry вручную (будет реализовано в методе)
        # Пока проверяем только сам retry-механизм — его нужно будет добавить в клиент
        pass  # этот тест написан для будущей реализации retry
