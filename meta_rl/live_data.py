"""meta_rl/live_data.py — ATOM-META-RL-006: Production CCXT Integration

Supports both sandbox (mock) and real exchange modes.
Credentials loaded from environment variables — NEVER hardcoded.

Production mode requires:
    CCXT_API_KEY=<key>
    CCXT_API_SECRET=<secret>
    CCXT_EXCHANGE=binance  (or binanceus, bybit, etc.)
    CCXT_SANDBOX_MODE=false

Feature flags:
    CCXT_SANDBOX_MODE (default: true)
    CCXT_RATE_LIMIT (default: 50ms)
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone

import numpy as np

from meta_rl.config import (
    CCXT_API_KEY,
    CCXT_API_SECRET,
    CCXT_ENABLE_RATE_LIMIT,
    CCXT_EXCHANGE,
    CCXT_RATE_LIMIT,
    CCXT_SANDBOX_MODE,
)

logger = logging.getLogger(__name__)

# ── Exchange registry ───────────────────────────────────────────────────────────
_EXCHANGES = {}  # cached ccxt instances

CCXT_LIVE_MODE = os.getenv("CCXT_LIVE_MODE", "false").lower() == "true"
LIVE_DATA_ENABLED = os.getenv("LIVE_DATA_ENABLED", "true").lower() == "true"


def _get_exchange():
    """Get or create a cached ccxt exchange instance."""
    global _EXCHANGES
    mode = "sandbox" if CCXT_SANDBOX_MODE else "production"
    key = f"{CCXT_EXCHANGE}:{mode}"

    if key in _EXCHANGES:
        return _EXCHANGES[key]

    try:
        import ccxt
    except ImportError:
        logger.warning("[LIVE-DATA] ccxt not installed — falling back to sandbox")
        return None

    if CCXT_SANDBOX_MODE:
        exchange_class = getattr(ccxt, CCXT_EXCHANGE, None)
        if exchange_class is None:
            raise ValueError(f"Unknown exchange: {CCXT_EXCHANGE}")
        ex = exchange_class({"enableRateLimit": False, "sandbox": True})
        logger.info(f"[LIVE-DATA] {CCXT_EXCHANGE} sandbox mode")
    else:
        if not CCXT_API_KEY or not CCXT_API_SECRET:
            raise ValueError("CCXT_SANDBOX_MODE=false but CCXT_API_KEY / CCXT_API_SECRET not set. Set them via environment variables.")
        exchange_class = getattr(ccxt, CCXT_EXCHANGE, None)
        if exchange_class is None:
            raise ValueError(f"Unknown exchange: {CCXT_EXCHANGE}")
        ex = exchange_class(
            {
                "apiKey": CCXT_API_KEY,
                "secret": CCXT_API_SECRET,
                "enableRateLimit": CCXT_ENABLE_RATE_LIMIT,
                "options": {"defaultType": "spot"},
            }
        )
        logger.info(f"[LIVE-DATA] {CCXT_EXCHANGE} production mode — authenticated")

    _EXCHANGES[key] = ex
    return ex


class LiveDataProvider:
    """
    Unified data provider for Meta-RL.

    Sandbox mode: returns synthetic OHLCV data (useful for backtesting).
    Production mode: fetches real OHLCV from exchange via ccxt.

    Supports: BTC/USDT, ETH/USDT, SOL/USDT, and any pair the exchange supports.
    """

    # Supported symbols (ccxt normalized)
    SYMBOLS = {
        "BTC/USDT": "BTC/USDT",
        "ETH/USDT": "ETH/USDT",
        "SOL/USDT": "SOL/USDT",
        "BNB/USDT": "BNB/USDT",
        "BTCUSDT": "BTC/USDT",  # legacy alias
        "ETHUSDT": "ETH/USDT",  # legacy alias
    }

    # Timeframe → ccxt interval string
    TIMEFRAMES = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "1h": "1h",
        "4h": "4h",
        "1d": "1d",
        "1w": "1w",
    }

    def __init__(
        self,
        sandbox: bool | None = None,
        symbol: str = "BTC/USDT",
        exchange: str | None = None,
        rate_limit_ms: int = CCXT_RATE_LIMIT,
    ):
        self.sandbox = sandbox if sandbox is not None else CCXT_SANDBOX_MODE
        self.symbol = self.SYMBOLS.get(symbol, symbol)
        self.exchange_name = exchange or CCXT_EXCHANGE
        self.rate_limit_ms = rate_limit_ms
        self._last_request_time = 0.0
        self._total_requests = 0

    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_ms / 1000.0:
            time.sleep(self.rate_limit_ms / 1000.0 - elapsed)
        self._last_request_time = time.time()
        self._total_requests += 1

    def fetch_ohlcv(
        self,
        symbol: str | None = None,
        interval: str = "1h",
        limit: int = 500,
    ) -> list[dict]:
        """
        Fetch OHLCV bars from exchange or generate sandbox data.

        Args:
            symbol: Trading pair (default: self.symbol). Accepts both
                    normalized ("BTC/USDT") and legacy ("BTCUSDT") formats.
            interval: Timeframe — 1m, 5m, 15m, 1h, 4h, 1d, 1w
            limit: Number of bars to fetch (max 1000 for ccxt)

        Returns:
            List of OHLCV dicts with keys: timestamp, open, high, low, close, volume
            All numeric values are floats.
        """
        sym = self.SYMBOLS.get(symbol or self.symbol, symbol or self.symbol)

        if self.sandbox:
            return self._sandbox_ohlcv(sym, interval, limit)

        try:
            ex = _get_exchange()
            if ex is None:
                return self._sandbox_ohlcv(sym, interval, limit)

            self._rate_limit()

            tf = self.TIMEFRAMES.get(interval, interval)
            # ccxt.fetch_ohlcv returns [[timestamp, open, high, low, close, volume], ...]
            raw = ex.fetch_ohlcv(sym, tf, limit=min(limit, 1000))

            result = []
            for bar in raw:
                ts, o, h, l, c, v = bar
                result.append(
                    {
                        "timestamp": ts,
                        "open": float(o),
                        "high": float(h),
                        "low": float(l),
                        "close": float(c),
                        "volume": float(v),
                    }
                )

            logger.info(f"[LIVE-DATA] Fetched {len(result)} bars {sym} {interval} from {self.exchange_name} (total requests: {self._total_requests})")
            return result

        except Exception as e:
            logger.warning(f"[LIVE-DATA] Fetch failed for {sym}: {e} — using sandbox fallback")
            return self._sandbox_ohlcv(sym, interval, limit)

    def fetch_ticker(self, symbol: str | None = None) -> dict:
        """Fetch current ticker (last price, 24h change, etc.)."""
        sym = self.SYMBOLS.get(symbol or self.symbol, symbol or self.symbol)

        if self.sandbox:
            bars = self._sandbox_ohlcv(sym, "1h", 2)
            if bars:
                last = bars[-1]
                return {
                    "symbol": sym,
                    "last": last["close"],
                    "change_pct": 0.0,
                    "volume_24h": last["volume"],
                    "timestamp": last["timestamp"],
                }
            return {}

        try:
            ex = _get_exchange()
            if ex is None:
                return {}
            self._rate_limit()
            ticker = ex.fetch_ticker(sym)
            return {
                "symbol": sym,
                "last": float(ticker.get("last", 0)),
                "change_pct": float(ticker.get("change", 0)),
                "volume_24h": float(ticker.get("baseVolume", 0)),
                "timestamp": ticker.get("timestamp", 0),
            }
        except Exception as e:
            logger.warning(f"[LIVE-DATA] Ticker fetch failed for {sym}: {e}")
            return {}

    def get_latest_price(self, symbol: str | None = None) -> float:
        """Get latest close price (convenience method)."""
        bars = self.fetch_ohlcv(symbol, "1h", 1)
        return bars[-1]["close"] if bars else 0.0

    def to_market_data(self, ohlcv: list[dict]) -> dict:
        """
        Convert raw OHLCV list to strategy-ready market_data dict.

        Computes: regime, signal_strength, momentum, mean_reversion_signal, atr
        using only the OHLCV data (no external dependencies).
        """
        if not ohlcv or len(ohlcv) < 10:
            return {"symbol": self.symbol, "ohlcv": ohlcv or []}

        closes = np.array([b["close"] for b in ohlcv], dtype=np.float64)
        highs = np.array([b["high"] for b in ohlcv], dtype=np.float64)
        lows = np.array([b["low"] for b in ohlcv], dtype=np.float64)
        volumes = np.array([b["volume"] for b in ohlcv], dtype=np.float64)

        # Returns
        returns = np.diff(closes) / closes[:-1]
        returns = np.concatenate([[0.0], returns])

        # Momentum: 20-bar cumulative return
        mom = float(np.sum(returns[-20:]))

        # Mean reversion: z-score of current close vs 20-bar SMA
        sma20 = float(np.mean(closes[-20:]))
        std20 = float(np.std(closes[-20:]))
        mr_signal = float((closes[-1] - sma20) / (std20 + 1e-8))

        # ATR (Average True Range) — 14-bar
        trs = []
        for i in range(1, len(ohlcv)):
            h, l, pc = highs[i], lows[i], closes[i - 1]
            tr = max(h - l, abs(h - pc), abs(l - pc))
            trs.append(tr)
        atr = float(np.mean(trs[-14:])) if len(trs) >= 14 else float(np.mean(trs))

        # Signal strength (0-100, neutral = 50)
        if mom > 0.01:
            signal_strength = min(100.0, 50.0 + mr_signal * 50 + mom * 500)
        elif mom < -0.01:
            signal_strength = max(0.0, 50.0 + mr_signal * 50 + mom * 500)
        else:
            signal_strength = 50.0 + mr_signal * 25

        # Regime detection (simple)
        recent_ret = float(np.mean(returns[-20:]))
        recent_vol = float(np.std(returns[-20:]))
        vol_median = float(np.median(np.abs(returns[max(0, -100) :])))
        if recent_vol > vol_median * 2:
            regime = "VOLATILE"
        elif recent_ret > 0.0005:
            regime = "BULL"
        elif recent_ret < -0.0005:
            regime = "BEAR"
        else:
            regime = "NEUTRAL"

        # ATR-based stop distance
        atr_distance = atr

        return {
            "symbol": self.symbol,
            "ohlcv": ohlcv,
            "regime": regime,
            "signal_strength": float(np.clip(signal_strength, 0.0, 100.0)),
            "momentum": mom,
            "mean_reversion_signal": mr_signal,
            "atr": atr_distance,
            "last_price": float(closes[-1]),
            "volume_mean": float(np.mean(volumes)),
            "metadata": {
                "source": "sandbox" if self.sandbox else self.exchange_name,
                "timeframe": "1h",
                "bars": len(ohlcv),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

    def _sandbox_ohlcv(self, symbol: str, interval: str, limit: int) -> list[dict]:
        """
        Generate realistic synthetic OHLCV for sandbox/backtest mode.

        Uses regime-aware random walk with:
        - Mean reversion
        - Volatility clustering
        - Realistic OHLC relationships (H >= max(O,C), L <= min(O,C))
        """
        now = datetime.now(timezone.utc)
        interval_seconds = {
            "1m": 60,
            "5m": 300,
            "15m": 900,
            "1h": 3600,
            "4h": 14400,
            "1d": 86400,
            "1w": 604800,
        }
        dt_seconds = interval_seconds.get(interval, 3600)

        # Base price depends on symbol
        base_prices = {"BTC/USDT": 67500, "ETH/USDT": 3450, "SOL/USDT": 145}
        price = base_prices.get(symbol, 1000.0)

        # Volatility per interval
        vol_map = {
            "1m": 0.001,
            "5m": 0.003,
            "15m": 0.005,
            "1h": 0.008,
            "4h": 0.015,
            "1d": 0.025,
            "1w": 0.05,
        }
        vol = vol_map.get(interval, 0.008)

        ohlcv = []
        drift = 0.0  # starts neutral
        np.random.random()

        for i in range(limit):
            ts = int(now.timestamp()) - (limit - i) * dt_seconds

            # Occasionally shift regime
            if np.random.random() < 0.05:
                r = np.random.random()
                drift = 0.0001 if r > 0.6 else -0.0001 if r > 0.3 else 0.0

            ret = np.random.normal(drift, vol)
            o = price
            c = price * (1 + ret)
            h = max(o, c) * (1 + abs(ret) * np.random.uniform(0.1, 0.5))
            l = min(o, c) * (1 - abs(ret) * np.random.uniform(0.1, 0.5))
            v = np.random.uniform(500, 5000) * (1 + abs(ret) / vol)

            ohlcv.append(
                {
                    "timestamp": ts,
                    "open": round(o, 4),
                    "high": round(h, 4),
                    "low": round(l, 4),
                    "close": round(c, 4),
                    "volume": round(v, 2),
                }
            )
            price = c

        logger.debug(f"[LIVE-DATA] Sandbox: generated {limit} bars {symbol} {interval} (base_price={base_prices.get(symbol, 1000)})")
        return ohlcv

    def get_latest_bars(
        self,
        symbol: str = "BTC/USDT",
        timeframe: str = "1h",
        limit: int = 500,
    ) -> dict:
        """
        ATOM-META-RL-007: Full market data bundle for strategy evaluation.

        Entry point used by cli.py --live and --paper modes.
        Returns a dict ready for StrategyEvaluator.evaluate().

        Args:
            symbol: Trading pair (BTC/USDT, ETH/USDT, etc.)
            timeframe: 1m, 5m, 15m, 1h, 4h, 1d
            limit: Number of OHLCV bars

        Returns:
            dict with keys: symbol, ohlcv, regime, signal_strength,
                           momentum, mean_reversion_signal, atr, last_price
        """
        sym = self.SYMBOLS.get(symbol, symbol)
        ohlcv = self.fetch_ohlcv(sym, timeframe, limit)
        if not ohlcv:
            logger.warning(f"[LIVE-DATA] No bars returned for {sym}")
            return {"symbol": sym, "ohlcv": [], "regime": "NEUTRAL"}

        market_data = self.to_market_data(ohlcv)
        market_data["symbol"] = sym
        logger.info(f"[LIVE-DATA] Market bundle: {sym} {timeframe} {len(ohlcv)} bars | regime={market_data.get('regime', 'unknown')} price={market_data.get('last_price', 0):,.2f}")
        return market_data

    def health_check(self) -> dict:
        """
        ATOM-META-RL-007: Production health check for live data pipeline.

        Returns:
            dict with {status, mode, exchange, last_price, ohlcv_bars, latency_ms, error}
        """
        import time

        start = time.time()
        status = "OK"
        error = None
        last_price = None
        bars = 0

        try:
            ohlcv = self.fetch_ohlcv(self.symbol, "1h", 1)
            if ohlcv:
                last_price = ohlcv[-1]["close"]
                bars = len(ohlcv)
            else:
                status = "DEGRADED"
                error = "No bars returned"
        except Exception as e:
            status = "ERROR"
            error = str(e)

        latency_ms = round((time.time() - start) * 1000, 1)

        return {
            "status": status,
            "mode": "sandbox" if self.sandbox else "production",
            "exchange": self.exchange_name,
            "symbol": self.symbol,
            "last_price": last_price,
            "ohlcv_bars": bars,
            "latency_ms": latency_ms,
            "error": error,
        }


# Convenience factory
def create_live_provider(symbol: str = "BTC/USDT", sandbox: bool = None) -> LiveDataProvider:
    """Factory for LiveDataProvider with sensible defaults."""
    return LiveDataProvider(
        sandbox=sandbox if sandbox is not None else CCXT_SANDBOX_MODE,
        symbol=symbol,
    )
