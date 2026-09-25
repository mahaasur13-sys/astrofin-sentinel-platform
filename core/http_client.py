"""Shared async HTTP client for agent data fetching."""

from __future__ import annotations

import logging
from urllib.parse import parse_qs, urlparse

import httpx
from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)

# Браузероподобные заголовки, чтобы Cloudflare/CDN (OKX и др.) не резали
# запросы python-клиентов (403 Forbidden из-за отсутствия User-Agent).
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AstroFinSentinel/1.0)",
    "Accept": "application/json",
}

_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    """Return a reusable httpx AsyncClient singleton."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=10.0)
        logger.info("Created shared httpx AsyncClient")
    return _client


async def close_http_client():
    """Close the shared client (e.g., on shutdown).

    Resilient to event-loop closure (CI/pytest scenario):
    when the loop is already closed, aclose() raises RuntimeError.
    """
    global _client
    if _client is not None:
        try:
            await _client.aclose()
        except RuntimeError:
            _client = None
            return
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


# ── OKX outbound request observability ──────────────────────────────────────
# Single choke-point for every OKX v5 call so metrics are recorded in one place
# regardless of which agent issues the request (shared or per-call client).

OKX_REQUESTS_TOTAL = Counter(
    "okx_requests_total",
    "OKX API requests by normalized endpoint, HTTP status, and OKX business code",
    ["endpoint", "status", "okx_code"],
)
OKX_REQUEST_DURATION = Histogram(
    "okx_request_duration_seconds",
    "OKX API request latency (seconds)",
    ["endpoint"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)
OKX_EMPTY_CANDLES = Counter(
    "okx_empty_candles_total",
    "OKX candles responses with empty data when code=0",
    ["inst_id", "bar"],
)
OKX_ERRORS = Counter(
    "okx_errors_total",
    "OKX request failures by reason",
    ["reason"],
)


def _okx_endpoint(url: str) -> str:
    """Normalize the OKX endpoint to a low-cardinality label."""
    for name in ("candles", "ticker", "instruments"):
        if f"/market/{name}" in url:
            return name
    return "other"


def normalize_okx_inst_id(symbol: str) -> str:
    """Normalize a trading symbol to an OKX spot ``instId`` (BASE-QUOTE).

    Canonical form is ``BTC-USDT``::

        BTC / btc / BTCUSDT / BTC-USDT  ->  BTC-USDT
        ETHUSDT                         ->  ETH-USDT

    Symbols already containing a dash are returned uppercased as-is (never
    double-processed). A symbol without a trailing ``USDT`` quote gets
    ``-USDT`` appended, matching the existing spot-quote convention.
    """
    sym = symbol.strip().upper()
    if "-" in sym:
        return sym
    if sym.endswith("USDT"):
        return sym[: -len("USDT")] + "-USDT"
    return sym + "-USDT"


async def okx_get_json(
    client: httpx.AsyncClient,
    url: str,
    *,
    timeout: float = 10.0,
    headers: dict[str, str] | None = None,
) -> dict:
    """GET an OKX v5 endpoint and record Prometheus metrics.

    Single entry point for all OKX outbound requests: records request count,
    latency, OKX business code, empty-candles and error metrics. Returns the
    parsed JSON dict (``{}`` on JSON decode failure). Raises on transport
    errors so callers keep their existing ``except``-path behaviour.
    """
    headers = headers if headers is not None else DEFAULT_HEADERS
    endpoint = _okx_endpoint(url)
    qs = parse_qs(urlparse(url).query)
    inst_id = (qs.get("instId") or [""])[0]
    bar = (qs.get("bar") or [""])[0]

    with OKX_REQUEST_DURATION.labels(endpoint=endpoint).time():
        try:
            resp = await client.get(url, timeout=timeout, headers=headers)
        except Exception as exc:  # noqa: BLE001 — record, then re-raise to caller
            OKX_ERRORS.labels(reason=type(exc).__name__.lower()).inc()
            OKX_REQUESTS_TOTAL.labels(endpoint=endpoint, status="error", okx_code="").inc()
            raise

    status = str(resp.status_code)
    try:
        payload = resp.json()
    except Exception:  # noqa: BLE001 — non-JSON body (Cloudflare page, proxy error)
        OKX_ERRORS.labels(reason="json_error").inc()
        OKX_REQUESTS_TOTAL.labels(endpoint=endpoint, status=status, okx_code="").inc()
        return {}

    okx_code = str(payload.get("code", "")) if isinstance(payload, dict) else ""
    OKX_REQUESTS_TOTAL.labels(endpoint=endpoint, status=status, okx_code=okx_code).inc()

    if endpoint == "candles" and okx_code == "0" and not payload.get("data"):
        OKX_EMPTY_CANDLES.labels(inst_id=inst_id, bar=bar).inc()

    return payload
