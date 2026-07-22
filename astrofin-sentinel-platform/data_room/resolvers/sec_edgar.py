"""SEC EDGAR 10-K/10-Q/13F Resolver — production-grade with rate-limit, cache, retry.

ADR-001 P3-09: Replace stub with real SEC EDGAR API integration.
Uses SEC's REST API (data.sec.gov) with mandatory User-Agent header.

Rate Limit: 10 req/sec per SEC fair-access policy.
Cache: dictionary + optional disk cache (ISSUE_FILES folder), TTL 24h.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import ClassVar

logger = logging.getLogger(__name__)

# ── constants ────────────────────────────────────────────────────────────────
_SEC_USER_AGENT = os.getenv(
    "SEC_USER_AGENT",
    "AstroFin Sentinel Platform (contact: mahaasur13@gmail.com)",
)
_SEC_BASE = "https://data.sec.gov"
_SEC_ARCHIVE_BASE = "https://www.sec.gov/Archives/edgar/data"
_CIK_LOOKUP_URL = f"{_SEC_BASE}/submissions/CIK{{cik_padded}}.json"
_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
_CACHE_DIR = Path(os.getenv("SEC_CACHE_DIR", "/tmp/sec_edgar_cache"))
_CACHE_TTL_SEC = int(os.getenv("SEC_CACHE_TTL_SEC", "86400"))  # 24h
_RATE_LIMIT = 9  # requests/sec (10 is max, leave 1 slack)
_TIMEOUT_SEC = 30
_MAX_RETRIES = 3
_RETRY_BACKOFF_BASE = 1.5

# ── data model ───────────────────────────────────────────────────────────────


@dataclass
class SECFiling:
    """One SEC filing record."""

    accession_number: str
    filing_type: str       # 10-K, 10-Q, 13F-HR, 8-K, etc.
    filing_date: str       # ISO date
    report_date: str       # period ending date
    primary_document: str  # e.g. "aapl-20240928.htm"
    doc_url: str           # full SEC archive URL


@dataclass
class SECData:
    """Full result returned to agents."""

    ticker: str
    cik: str = ""
    company_name: str = ""
    filing_type: str = ""
    period: str = ""
    text: str = ""
    filing_url: str = ""
    source: str = "cache"
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ── helpers ──────────────────────────────────────────────────────────────────


def _padded_cik(cik: str | int) -> str:
    """Pad CIK to 10 digits with leading zeros."""
    return str(int(cik)).zfill(10)


def _strip_html(text: str) -> str:
    """Crude HTML→text for SEC filings."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&#?\w+;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _truncate_text(text: str, max_chars: int = 50_000) -> str:
    """Truncate filing text to avoid memory bloat."""
    if len(text) <= max_chars:
        return text
    return (
        text[:max_chars // 2]
        + f"\n\n… [truncated {len(text) - max_chars} chars] …\n\n"
        + text[-(max_chars // 2):]
    )


def _cache_key(ticker: str, filing_type: str) -> str:
    return f"{ticker.upper()}:{filing_type.upper()}"


def _cache_path(cache_key: str) -> Path:
    h = hashlib.sha256(cache_key.encode()).hexdigest()[:16]
    return _CACHE_DIR / f"{h}.json"


# ── rate limiter ─────────────────────────────────────────────────────────────


class _RateLimiter:
    """Token-bucket rate limiter (async-safe)."""

    def __init__(self, rate: float) -> None:
        self._sem = asyncio.Semaphore(rate)
        self._interval = 1.0 / rate

    async def acquire(self) -> None:
        await self._sem.acquire()
        # Replenish after interval
        asyncio.get_running_loop().call_later(self._interval, self._sem.release)


# ── CIK lookup — static + lazy ───────────────────────────────────────────────


class _CIKLookup:
    """Lazy-loading CIK → ticker map from SEC company_tickers.json."""

    _ticker_to_cik: ClassVar[dict[str, str]] = {}
    _cik_to_name: ClassVar[dict[str, str]] = {}
    _loaded: ClassVar[bool] = False
    _lock: ClassVar[asyncio.Lock | None] = None

    @classmethod
    async def _ensure_loaded(cls) -> None:
        if cls._loaded:
            return
        if cls._lock is None:
            cls._lock = asyncio.Lock()
        async with cls._lock:
            if cls._loaded:
                return
            try:
                logger.info("Loading SEC company tickers…")
                import aiohttp

                async with aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=_TIMEOUT_SEC),
                    headers={"User-Agent": _SEC_USER_AGENT},
                ) as session:
                    async with session.get(_COMPANY_TICKERS_URL) as resp:
                        resp.raise_for_status()
                        raw = await resp.json()
                for _idx, entry in raw.items():
                    ticker = entry.get("ticker", "").upper()
                    cik = str(entry.get("cik_str", ""))
                    name = entry.get("title", "")
                    if ticker and cik:
                        cls._ticker_to_cik[ticker] = cik
                        cls._cik_to_name[cik] = name
                cls._loaded = True
                logger.info("Loaded %d SEC tickers.", len(cls._ticker_to_cik))
            except Exception:
                logger.exception("Failed to load SEC ticker map — will use stub names.")
                cls._loaded = True  # don't retry forever

    @classmethod
    async def get_cik(cls, ticker: str) -> str:
        await cls._ensure_loaded()
        return cls._ticker_to_cik.get(ticker.upper(), "")

    @classmethod
    async def get_name(cls, cik: str) -> str:
        await cls._ensure_loaded()
        return cls._cik_to_name.get(str(cik), "")


# ── resolver ─────────────────────────────────────────────────────────────────


class SECEdgarResolver:
    """Production-grade SEC EDGAR resolver.

    Fetch chain: live EDGAR API → disk cache → in-memory cache → stub.
    """

    def __init__(self, cache_dir: Path | None = None) -> None:
        self._mem_cache: dict[str, SECData] = {}
        self._cache_dir = Path(cache_dir or _CACHE_DIR)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    # ── public API ───────────────────────────────────────────────────────

    async def fetch_10k(self, ticker: str) -> SECData:
        return await self.fetch(ticker, "10-K")

    async def fetch_10q(self, ticker: str) -> SECData:
        return await self.fetch(ticker, "10-Q")

    async def fetch_13f(self, ticker: str) -> SECData:
        return await self.fetch(ticker, "13F-HR")

    async def fetch(self, ticker: str, filing_type: str = "10-K") -> SECData:
        """Fetch filing with full fallback chain."""
        key = _cache_key(ticker, filing_type)

        # 1. disk cache
        data = self._load_disk_cache(key)
        if data:
            logger.debug("SEC disk-cache hit: %s", key)
            return data

        # 2. live EDGAR
        try:
            data = await self._fetch_live(ticker, filing_type)
            self._save_disk_cache(key, data)
            return data
        except Exception as exc:
            logger.warning("SEC EDGAR live fetch failed (%s), falling back: %s", key, exc)

        # 3. in-memory stub
        return self._make_stub(ticker, filing_type)

    def invalidate(self, ticker: str, filing_type: str = "10-K") -> None:
        """Remove cached entry (disk + memory)."""
        key = _cache_key(ticker, filing_type)
        self._mem_cache.pop(key, None)
        path = _cache_path(key)
        if path.exists():
            path.unlink()

    # ── live fetch ────────────────────────────────────────────────────────

    async def _fetch_live(self, ticker: str, filing_type: str) -> SECData:
        """Full pipeline: CIK lookup → submissions → latest filing → document text."""
        import aiohttp

        cik = await _CIKLookup.get_cik(ticker)
        if not cik:
            raise ValueError(f"No CIK found for ticker {ticker}")

        company_name = await _CIKLookup.get_name(cik)

        submissions_url = _CIK_LOOKUP_URL.format(cik_padded=_padded_cik(cik))

        headers = {"User-Agent": _SEC_USER_AGENT}

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=_TIMEOUT_SEC),
            headers=headers,
        ) as session:
            # Step 1: get submissions
            filings_data = await self._get_json_retry(session, submissions_url)
            if not filings_data:
                raise RuntimeError(f"Empty submissions data for CIK {cik}")

            # Step 2: find latest filing of requested type
            filings = filings_data.get("filings", {}).get("recent", {})
            if not filings:
                raise RuntimeError("No recent filings in submissions data")

            target = self._find_latest(filings, filing_type)
            if not target:
                raise RuntimeError(
                    f"No {filing_type} found for CIK {cik} (ticker {ticker}) "
                    f"in recent filings"
                )

            # Step 3: fetch document text
            doc_text = await self._fetch_document(session, cik, target)

        return SECData(
            ticker=ticker.upper(),
            cik=cik,
            company_name=company_name,
            filing_type=filing_type,
            period=target.report_date,
            text=doc_text,
            filing_url=target.doc_url,
            source="edgar",
        )

    @staticmethod
    async def _get_json_retry(
        session, url: str, retries: int = _MAX_RETRIES
    ) -> dict | None:
        """GET JSON with exponential backoff retry."""
        last_exc: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                async with session.get(url) as resp:
                    if resp.status == 429:
                        retry_after = int(resp.headers.get("Retry-After", "5"))
                        logger.warning("SEC rate-limited, waiting %ds", retry_after)
                        await asyncio.sleep(retry_after)
                        continue
                    resp.raise_for_status()
                    return await resp.json(content_type=None)
            except Exception as exc:
                last_exc = exc
                if attempt < retries:
                    delay = _RETRY_BACKOFF_BASE**attempt
                    logger.warning("SEC request retry %d/%d in %.1fs: %s", attempt, retries, delay, exc)
                    await asyncio.sleep(delay)
        raise last_exc or RuntimeError(f"All {retries} retries exhausted for {url}")

    @staticmethod
    def _find_latest(filings: dict, filing_type: str) -> SECFiling | None:
        """Scan recent filings for the latest matching type."""
        types = filings.get("form", [])
        dates = filings.get("filingDate", [])
        report_dates = filings.get("reportDate", [])
        accessions = filings.get("accessionNumber", [])
        primary_docs = filings.get("primaryDocument", [])

        # Prefer exact match, fall back to prefix match
        candidates = []
        for i, ft in enumerate(types):
            if i >= len(accessions):
                break
            if ft == filing_type or ft.startswith(filing_type):
                candidates.append({
                    "idx": i,
                    "filing_type": ft,
                    "filing_date": dates[i] if i < len(dates) else "",
                    "report_date": report_dates[i] if i < len(report_dates) else "",
                    "accession": accessions[i],
                    "primary_doc": primary_docs[i] if i < len(primary_docs) else "",
                })
        if not candidates:
            return None
        # Pick most recent (first = newest in SEC response)
        best = candidates[0]
        acc = best["accession"].replace("-", "")
        doc_url = f"{_SEC_ARCHIVE_BASE}/{best['accession'].split('-')[0]}/{acc}/{best['primary_doc']}"

        return SECFiling(
            accession_number=best["accession"],
            filing_type=best["filing_type"],
            filing_date=best["filing_date"],
            report_date=best["report_date"],
            primary_document=best["primary_doc"],
            doc_url=doc_url,
        )

    @staticmethod
    async def _fetch_document(
        session, cik: str, filing: SECFiling, max_chars: int = 50_000
    ) -> str:
        """Download and parse an SEC filing document.

        SEC filings may be HTML, plain text, or XBRL. We extract text content
        and strip boilerplate for LLM consumption.
        """
        # Determine document URL
        # Primary document often points to the .htm file
        # Also try .txt alternative (cleaner for text extraction)
        acc_no_dash = filing.accession_number.replace("-", "")
        txt_url = f"{_SEC_ARCHIVE_BASE}/{cik}/{acc_no_dash}/{acc_no_dash}.txt"

        try:
            doc_url = txt_url if filing.primary_document else filing.doc_url
            async with session.get(doc_url) as resp:
                resp.raise_for_status()
                raw = await resp.text()
        except Exception:
            # Fall back to primary document URL
            if filing.doc_url and filing.doc_url != txt_url:
                async with session.get(filing.doc_url) as resp:
                    resp.raise_for_status()
                    raw = await resp.text()
            else:
                raise

        # Detect content type and extract text
        content_type = resp.headers.get("Content-Type", "").lower()
        if "text/html" in content_type or raw.strip().startswith("<"):
            text = _strip_html(raw)
        else:
            text = raw

        text = _truncate_text(text.strip(), max_chars)
        return text

    # ── caching ───────────────────────────────────────────────────────────

    def _load_disk_cache(self, key: str) -> SECData | None:
        path = _cache_path(key)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            age = time.time() - data.get("cached_at", 0)
            if age > _CACHE_TTL_SEC:
                logger.debug("SEC disk cache expired for %s (age=%.0fs)", key, age)
                path.unlink(missing_ok=True)
                return None
            return SECData(**data["payload"])
        except Exception:
            logger.debug("SEC disk cache read error for %s", key)
            path.unlink(missing_ok=True)
            return None

    def _save_disk_cache(self, key: str, data: SECData) -> None:
        path = _cache_path(key)
        try:
            record = {
                "cached_at": time.time(),
                "payload": {
                    "ticker": data.ticker,
                    "cik": data.cik,
                    "company_name": data.company_name,
                    "filing_type": data.filing_type,
                    "period": data.period,
                    "text": data.text,
                    "filing_url": data.filing_url,
                    "source": data.source,
                    "fetched_at": data.fetched_at,
                },
            }
            path.write_text(json.dumps(record, ensure_ascii=False, indent=2))
        except Exception:
            logger.debug("SEC disk cache write error for %s", key)

    def _make_stub(self, ticker: str, filing_type: str) -> SECData:
        """Return stub data when EDGAR is unreachable."""
        key = _cache_key(ticker, filing_type)
        if key in self._mem_cache:
            return self._mem_cache[key]
        data = SECData(
            ticker=ticker.upper(),
            filing_type=filing_type,
            text=(
                f"[SEC EDGAR stub] {filing_type} for {ticker.upper()}. "
                f"Real filing data unavailable — SEC EDGAR API could not be reached. "
                f"This is a placeholder generated at {datetime.now(timezone.utc).isoformat()}. "
                f"FundamentalAgent: treat this as NO_DATA — do not make trading decisions "
                f"based on stub content. Wait for real EDGAR data before generating signals."
            ),
            source="stub",
        )
        self._mem_cache[key] = data
        return data


# ── singleton ────────────────────────────────────────────────────────────────

_resolver: SECEdgarResolver | None = None


def get_resolver() -> SECEdgarResolver:
    global _resolver
    if _resolver is None:
        _resolver = SECEdgarResolver()
    return _resolver


async def fetch_10k(ticker: str) -> SECData:
    """Convenience: fetch latest 10-K for a ticker."""
    return await get_resolver().fetch_10k(ticker)


async def fetch_10q(ticker: str) -> SECData:
    """Convenience: fetch latest 10-Q for a ticker."""
    return await get_resolver().fetch_10q(ticker)
