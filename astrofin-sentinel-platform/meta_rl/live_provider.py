"""meta_rl/live_provider.py — ATOM-META-RL-012: Production CCXT Live Provider

Security guarantees:
- API keys NEVER logged (masked in all output)
- sandbox by default (CCXT_LIVE_MODE=false)
- graceful fallback to mock on any error
- rate limiting + automatic reconnection
"""

from __future__ import annotations

import logging
import os
import random
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

logger = logging.getLogger(__name__)

# ── Feature flags from config ──────────────────────────────────────────────
_CCXT_LIVE_MODE = os.getenv("CCXT_LIVE_MODE", "false").lower() == "true"
_CCXT_SANDBOX_MODE = os.getenv("CCXT_SANDBOX_MODE", "true").lower() == "true"
_CCXT_EXCHANGE = os.getenv("CCXT_EXCHANGE", "binance")
_CCXT_RATE_LIMIT_MS = int(os.getenv("CCXT_RATE_LIMIT_MS", "50"))
_CCXT_RECONNECT_ATTEMPTS = int(os.getenv("CCXT_RECONNECT_ATTEMPTS", "3"))
_CCXT_RECONNECT_DELAY_S = float(os.getenv("CCXT_RECONNECT_DELAY_S", "2.0"))


@dataclass
class MarketSnapshot:
    """Current market state snapshot."""

    price: float
    regime: Literal["BULL", "BEAR", "NEUTRAL", "VOLATILE"]
    atr: float
    volume_24h: float
    timestamp: str
    mode: Literal["LIVE", "SANDBOX"]
    exchange: str
    latency_ms: float | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "price": self.price,
            "regime": self.regime,
            "atr": self.atr,
            "volume_24h": self.volume_24h,
            "timestamp": self.timestamp,
            "mode": self.mode,
            "exchange": self.exchange,
            "latency_ms": self.latency_ms,
            "error": self.error,
        }


class CCXTLiveProvider:
    """
    Production-ready CCXT live data provider.

    Modes:
    - SANDBOX (default): synthetic OHLCV, no API calls
    - LIVE: real exchange data via CCXT

    Security: API keys are read from env vars and NEVER exposed in logs.
    """

    def __init__(self, exchange: str | None = None):
        self.exchange_name = exchange or _CCXT_EXCHANGE
        self._live_mode = _CCXT_LIVE_MODE and not _CCXT_SANDBOX_MODE
        self._exchange = None
        self._rate_limit_ms = _CCXT_RATE_LIMIT_MS
        self._last_request_time = 0.0
        self._session_start = time.time()
        self._total_requests = 0
        self._failed_requests = 0
        self._reconnect_count = 0

        if self._live_mode:
            self._connect_live()
        else:
            logger.info("[CCXT] SANDBOX mode (CCXT_LIVE_MODE=false or sandbox=true)")

    def _connect_live(self) -> None:
        """Establish authenticated exchange connection. Never logs keys."""
        import ccxt

        api_key = os.getenv("CCXT_API_KEY", "")
        api_secret = os.getenv("CCXT_API_SECRET", "")

        if not api_key or not api_secret:
            logger.warning(
                "[CCXT] LIVE requested but CCXT_API_KEY / CCXT_API_SECRET not set → fallback to SANDBOX"
            )
            self._live_mode = False
            return

        try:
            ex_class = getattr(ccxt, self.exchange_name)
            if ex_class is None:
                logger.warning(
                    f"[CCXT] Unknown exchange '{self.exchange_name}' → fallback to SANDBOX"
                )
                self._live_mode = False
                return

            self._exchange = ex_class(
                {
                    "apiKey": api_key,
                    "secret": api_secret,
                    "enableRateLimit": True,
                    "options": {"defaultType": "spot"},
                }
            )

            # Verify connection with a simple call
            self._exchange.fetch_ticker("BTC/USDT")
            self._reconnect_count = 0

            key_diagnostic = "LIVE" if not _CCXT_SANDBOX_MODE else "SANDBOX+LIVE"
            logger.info(f"[CCXT] Connected to {self.exchange_name} ({key_diagnostic})")

        except Exception as e:
            logger.warning(
                f"[CCXT] Exchange connection failed: {e} → fallback to SANDBOX"
            )
            self._live_mode = False
            self._exchange = None

    def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._rate_limit_ms / 1000.0:
            time.sleep(self._rate_limit_ms / 1000.0 - elapsed)
        self._last_request_time = time.time()

    def _fetch_with_retry(self, method: str, *args, **kwargs):
        """Fetch with retry + exponential backoff."""
        for attempt in range(_CCXT_RECONNECT_ATTEMPTS):
            try:
                self._rate_limit()
                self._total_requests += 1
                return getattr(self._exchange, method)(*args, **kwargs)
            except Exception as e:
                self._failed_requests += 1
                logger.warning(f"[CCXT] {method} attempt {attempt + 1} failed: {e}")
                if attempt < _CCXT_RECONNECT_ATTEMPTS - 1:
                    time.sleep(_CCXT_RECONNECT_DELAY_S * (attempt + 1))
        # All retries exhausted → fallback to mock
        logger.warning(
            "[CCXT] All retries exhausted → falling back to SANDBOX for this call"
        )
        return None

    def get_snapshot(self, symbol: str = "BTC/USDT") -> MarketSnapshot:
        """
        Get current market snapshot (live or sandbox).

        This is the primary API for the health endpoint and LiveTab.
        """
        t0 = time.time()
        mode: Literal["LIVE", "SANDBOX"] = "SANDBOX"
        exchange_name = self.exchange_name

        try:
            if self._live_mode and self._exchange:
                mode = "LIVE"
                ticker = self._fetch_with_retry("fetch_ticker", symbol)
                if ticker is None:
                    return self._sandbox_snapshot(speed=time.time() - t0)

                price = float(ticker.get("last", 0))
                volume_24h = float(ticker.get("baseVolume", 0))
                atr = price * 0.025  # ~2.5% daily ATR approximation

                regime = self._detect_regime_fast(price, symbol)
                mode = "LIVE"
            else:
                snap = self._sandbox_snapshot(speed=time.time() - t0)
                return snap

            return MarketSnapshot(
                price=round(price, 2),
                regime=regime,
                atr=round(atr, 2),
                volume_24h=round(volume_24h, 2),
                timestamp=datetime.now(timezone.utc).isoformat(),
                mode=mode,
                exchange=exchange_name,
                latency_ms=round((time.time() - t0) * 1000, 1),
            )

        except Exception as e:
            logger.warning(f"[CCXT] Snapshot error: {e} → SANDBOX fallback")
            return self._sandbox_snapshot(speed=time.time() - t0, error=str(e))

    def _detect_regime_fast(
        self, price: float, symbol: str
    ) -> Literal["BULL", "BEAR", "NEUTRAL", "VOLATILE"]:
        """Fast regime detection using 24h change from ticker."""
        try:
            if not self._exchange:
                return "NEUTRAL"
            ticker = self._fetch_with_retry("fetch_ticker", symbol)
            if ticker and ticker.get("change") is not None:
                change_pct = (
                    float(ticker["change"]) / max(float(ticker.get("last", 1)), 1) * 100
                )
                if change_pct > 1.0:
                    return "BULL"
                elif change_pct < -1.0:
                    return "BEAR"
                elif abs(change_pct) > 3.0:
                    return "VOLATILE"
        except Exception:
            log.warning("Live provider data fetch failed", exc_info=True)
        return "NEUTRAL"

    def _sandbox_snapshot(
        self, speed: float = 0, error: str | None = None
    ) -> MarketSnapshot:
        """Generate realistic sandbox snapshot."""
        base_prices = {"BTC/USDT": 67450.0, "ETH/USDT": 3520.0, "SOL/USDT": 145.0}
        price = base_prices.get("BTC/USDT", 50000.0)

        # Small random drift for realism
        drift = random.gauss(0, 0.003)
        price = price * (1 + drift)

        return MarketSnapshot(
            price=round(price, 2),
            regime=random.choice(["BULL", "BEAR", "NEUTRAL"]),
            atr=round(price * 0.025, 2),
            volume_24h=round(random.uniform(800_000_000, 2_500_000_000), 2),
            timestamp=datetime.now(timezone.utc).isoformat(),
            mode="SANDBOX",
            exchange=self.exchange_name,
            latency_ms=round(speed * 1000, 1),
            error=error,
        )

    @property
    def mode(self) -> Literal["LIVE", "SANDBOX"]:
        return "LIVE" if self._live_mode else "SANDBOX"

    @property
    def stats(self) -> dict:
        total = max(self._total_requests, 1)
        return {
            "mode": self.mode,
            "exchange": self.exchange_name,
            "total_requests": self._total_requests,
            "failed_requests": self._failed_requests,
            "fail_rate": round(self._failed_requests / total, 4),
            "uptime_s": round(time.time() - self._session_start, 1),
        }


# ── Singleton ──────────────────────────────────────────────────────────────────
_live_provider: CCXTLiveProvider | None = None


def get_live_provider() -> CCXTLiveProvider:
    global _live_provider
    if _live_provider is None:
        _live_provider = CCXTLiveProvider()
    return _live_provider
