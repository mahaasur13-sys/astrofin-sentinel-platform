"""SEC EDGAR 10-K/10-Q Resolver — graceful degradation."""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class SECData:
    ticker: str
    filing_type: str = ""          # 10-K, 10-Q, 13F, etc.
    period: str = ""              # fiscal period
    text: str = ""
    source: str = "cache"         # edgar | cache | stub
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SECEdgarResolver:
    """
    SEC EDGAR resolver with graceful fallback.

    Production path: fetch real 10-K/10-Q from sec.gov via EDGAR API.
    CI/stub path: return cached or placeholder text.
    """

    _cache: dict[str, SECData] = {}

    async def fetch(self, ticker: str, filing_type: str = "10-K") -> SECData:
        """Fetch filing with fallback chain: EDGAR → cache → stub."""
        try:
            return await self._fetch_from_edgar(ticker, filing_type)
        except (NotImplementedError, OSError, ConnectionError) as exc:
            logger.warning("SEC EDGAR unavailable for %s (%s), falling back to cache", ticker, exc)
            return await self._fetch_from_cache(ticker, filing_type)

    async def _fetch_from_edgar(self, ticker: str, filing_type: str) -> SECData:
        """Real EDGAR API call — blocked by NotImplementedError until Sprint 4."""
        raise NotImplementedError(
            f"SEC EDGAR live fetch not yet integrated. Ticker: {ticker}, Filing: {filing_type}. "
            f"Scheduled for Sprint 4 (ADR-001 P3-09)."
        )

    async def _fetch_from_cache(self, ticker: str, filing_type: str) -> SECData:
        """Return cached data or generate a stub for CI/test environments."""
        cache_key = f"{ticker}:{filing_type}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        data = SECData(
            ticker=ticker,
            filing_type=filing_type,
            period="FY2025",
            text=f"[SEC EDGAR stub] Placeholder 10-K text for {ticker}. "
                 f"Real filing will be fetched when EDGAR integration is complete (Sprint 4).",
            source="stub",
        )
        self._cache[cache_key] = data
        return data

    def invalidate_cache(self, ticker: str, filing_type: str = "10-K") -> None:
        """Remove a cached entry, forcing a fresh fetch on next call."""
        cache_key = f"{ticker}:{filing_type}"
        self._cache.pop(cache_key, None)


# Singleton for convenience
_resolver: SECEdgarResolver | None = None


def get_resolver() -> SECEdgarResolver:
    global _resolver
    if _resolver is None:
        _resolver = SECEdgarResolver()
    return _resolver
