"""Shared async HTTP client for agent data fetching."""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    """Return a reusable httpx AsyncClient singleton."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=10.0)
        logger.info("Created shared httpx AsyncClient")
    return _client


async def close_http_client():
    """Close the shared client (e.g., on shutdown)."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
        logger.info("Closed shared httpx AsyncClient")


class HTTPClient:
    """Thin wrapper around httpx.AsyncClient so tests can patch .get/.post."""

    def __init__(self, timeout: float = 10.0) -> None:
        self._inner = httpx.AsyncClient(timeout=timeout)

    async def get(self, url: str, **kw) -> httpx.Response:
        return await self._inner.get(url, **kw)

    async def post(self, url: str, **kw) -> httpx.Response:
        return await self._inner.post(url, **kw)

    async def aclose(self) -> None:
        await self._inner.aclose()