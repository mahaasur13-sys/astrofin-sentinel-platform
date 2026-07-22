"""HistoricalDataLoader — Binance API client with local caching (R03-compliant)."""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta

import aiohttp

logger = logging.getLogger(__name__)

# ─── Constants ─────────────────────────────────────────────────────────────────

BINANCE_KLINE_URL = "https://api.binance.com/api/v3/klines"
DEFAULT_CACHE_DIR = "backtest/data_cache"
DEFAULT_DAYS = 1825  # 5 years


class HistoricalDataLoader:
    """Fetches historical OHLCV from Binance, caches locally.

    Architecture (R03): all external HTTP goes through this adapter.
    No agent or orchestrator calls Binance directly.
    """

    def __init__(self, cache_dir: str = DEFAULT_CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _cache_path(self, symbol: str, interval: str, days: int) -> str:
        return os.path.join(self.cache_dir, f"{symbol}_{interval}_{days}d.csv")

    async def fetch_binance_klines(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1d",
        days: int = DEFAULT_DAYS,
    ) -> list[dict]:
        """Fetch historical daily candles from Binance public API.

        Args:
            symbol: Trading pair, e.g. 'BTCUSDT', 'ETHUSDT'
            interval: Kline interval — '1d' for daily, '4h', '1h'
            days: Number of days to fetch (default: 1825 = ~5 years)

        Returns:
            List of OHLCV dicts: [{'open', 'high', 'low', 'close', 'volume'}, ...]
            Sorted chronologically.
        """
        cache_file = self._cache_path(symbol, interval, days)

        if os.path.exists(cache_file):
            logger.info("Loading cached %s data (%d days)...", symbol, days)
            rows = self._read_csv_to_ohlcv(cache_file)
            if rows:
                return rows

        logger.info("Fetching %d days of %s from Binance...", days, symbol)
        raw = await self._download_klines(symbol, interval, days)
        if not raw:
            logger.error("Binance returned empty data for %s", symbol)
            return []

        ohlcv = self._parse_klines(raw)
        self._save_csv(cache_file, ohlcv)
        logger.info("Data saved to cache (%d rows).", len(ohlcv))
        return ohlcv

    # ── Binance API ──────────────────────────────────────────────────────────

    async def _download_klines(
        self,
        symbol: str,
        interval: str,
        days: int,
    ) -> list:
        """Paginate Binance klines API, return raw JSON rows."""
        end_ms = int(datetime.utcnow().timestamp() * 1000)
        start_ms = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)

        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": 1000,
        }
        all_rows: list = []

        async with aiohttp.ClientSession() as session:
            while True:
                chunk_params = {**params, "startTime": start_ms, "endTime": end_ms}
                try:
                    async with session.get(
                        BINANCE_KLINE_URL, params=chunk_params, timeout=aiohttp.ClientTimeout(total=30)
                    ) as resp:
                        if resp.status == 429:
                            logger.warning("Binance rate limit — backing off 10s")
                            await asyncio.sleep(10)
                            continue
                        if resp.status != 200:
                            logger.error("Binance API error: HTTP %s", resp.status)
                            break

                        data = await resp.json()
                        if not data or not isinstance(data, list):
                            break
                        all_rows.extend(data)
                        if len(data) < 1000:
                            break
                        start_ms = data[-1][0] + 1
                except asyncio.TimeoutError:
                    logger.warning("Binance timeout — retrying after 5s")
                    await asyncio.sleep(5)
                    continue
                except Exception:
                    logger.exception("Binance download failed")
                    break

                await asyncio.sleep(0.5)  # Rate limit headroom

        return all_rows

    # ── Parsing ──────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_klines(raw: list) -> list[dict]:
        """Convert Binance klines JSON to OHLCV dicts.

        Binance format:
            [open_time, open, high, low, close, volume,
             close_time, quote_volume, trades, taker_buy_base,
             taker_buy_quote, ignore]
        """
        return [
            {
                "open": float(r[1]),
                "high": float(r[2]),
                "low": float(r[3]),
                "close": float(r[4]),
                "volume": float(r[5]),
            }
            for r in raw
            if len(r) >= 6
        ]

    # ── CSV cache ────────────────────────────────────────────────────────────

    @staticmethod
    def _read_csv_to_ohlcv(path: str) -> list[dict]:
        """Read cached CSV back to ohlcv list."""
        import csv
        rows = []
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append({
                    "open": float(row.get("open", 0)),
                    "high": float(row.get("high", 0)),
                    "low": float(row.get("low", 0)),
                    "close": float(row.get("close", 0)),
                    "volume": float(row.get("volume", 0)),
                })
        return rows

    @staticmethod
    def _save_csv(path: str, ohlcv: list[dict]) -> None:
        import csv
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["open", "high", "low", "close", "volume"])
            writer.writeheader()
            writer.writerows(ohlcv)
