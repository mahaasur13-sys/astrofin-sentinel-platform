"""Shared HTTP client for agent data fetching.

This module is the single allowed HTTP entry-point for `core/` and `agents/`.
The architecture linter (R3) bans `import requests` outside `data_room/`;
everything in this repo must go through `core.http_client` instead.

The underlying driver is `httpx`, which gives us a clean sync + async API
with retry and timeout support.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Module-level sync client; httpx is thread-safe for a single client.
_sync_client: httpx.Client | None = None
_client: httpx.AsyncClient | None = None

DEFAULT_TIMEOUT = 10.0


def _get_sync_client() -> httpx.Client:
    global _sync_client
    if _sync_client is None:
        _sync_client = httpx.Client(timeout=DEFAULT_TIMEOUT)
        logger.info("Created shared httpx sync Client")
    return _sync_client


def get_http_client() -> httpx.AsyncClient:
    """Return a reusable httpx AsyncClient singleton."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=DEFAULT_TIMEOUT)
        logger.info("Created shared httpx AsyncClient")
    return _client


def get_json(url: str, timeout: float = DEFAULT_TIMEOUT) -> Any:
    """Synchronous GET that returns the parsed JSON body.

    Mirrors the `requests.get(url, timeout=10).json()` pattern that was
    used before, so call-sites can drop in with minimal diff:

        data = get_json(url)

    Raises whatever httpx raises on transport errors; callers are
    expected to handle failures locally (this helper deliberately does
    not swallow exceptions — the previous `requests.get` calls also let
    exceptions bubble up to the surrounding `except Exception:` blocks).
    """
    client = _get_sync_client()
    resp = client.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


async def fetch_json(url: str, timeout: float = DEFAULT_TIMEOUT) -> Any:
    """Async GET that returns the parsed JSON body."""
    client = get_http_client()
    resp = await client.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


async def close_http_client() -> None:
    """Close both sync and async shared clients (e.g. on shutdown)."""
    global _client, _sync_client
    if _client is not None:
        await _client.aclose()
        _client = None
        logger.info("Closed shared httpx AsyncClient")
    if _sync_client is not None:
        _sync_client.close()
        _sync_client = None
        logger.info("Closed shared httpx sync Client")
