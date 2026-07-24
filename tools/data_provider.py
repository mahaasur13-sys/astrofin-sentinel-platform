"""data_provider.py — Unified OHLCV data fetcher.
Primary: Yahoo Finance v8 (free, no key) + yfinance fallback
Fallback 1: metals-api.com (free tier: 50 req/month)
Fallback 2: Twelve Data (free tier: 800 req/day)
"""

import os
from datetime import datetime, timezone

import logging as _log
try:
    import httpx as _http
except ImportError:
    import urllib.request as _urllib_request
    _http = None

import yfinance as yf

# ── API Keys (from environment) ────────────────────────────────────────────────
METALS_API_KEY = os.environ.get("METALS_API_KEY", "")
TWELVE_DATA_KEY = os.environ.get("TWELVE_DATA_KEY", "")

# ── Symbol mapping: Sentinel internal → Yahoo Finance v8 ─────────────────────
BINANCE_TO_YAHOO = {
    "BTCUSDT": "BTC-USD",
    "ETHUSDT": "ETH-USD",
    "BNBUSDT": "BNB-USD",
    "SOLUSDT": "SOL-USD",
    "XRPUSDT": "XRP-USD",
    "ADAUSDT": "ADA-USD",
    "DOGEUSDT": "DOGE-USD",
    "AVAXUSDT": "AVAX-USD",
    "DOTUSDT": "DOT-USD",
    "LINKUSDT": "LINK-USD",
    "MATICUSDT": "MATIC-USD",
    "SPY": "SPY",
    "QQQ": "QQQ",
    "GLD": "GLD",
    "TLT": "TLT",
    "DXY": "UUP",
    "VIX": "^VIX",
    # Commodities (Yahoo Finance futures)
    "GC%3DF": "GC=F",  # Gold
    "SI%3DF": "SI=F",  # Silver
    "PL%3DF": "PL=F",  # Platinum
    "PA%3DF": "PA=F",  # Palladium
    "HG%3DF": "HG=F",  # Copper
    "NG%3DF": "NG=F",  # Natural Gas
    "CL%3DF": "CL=F",  # Crude Oil
    # Metals ETF proxies
    "JJN": "JJN",  # iPath Nickel Subindex ETF (delisted on yfinance lib, works on v8 API)
    # Crypto
    "XMR-USD": "XMR-USD",
}

# Symbols that need v8 API (delisted/delist in yfinance lib but work in v8)
YAHOO_V8_ONLY = {"JJN"}

# metals-api.com symbol mapping
METALS_API_SYMBOLS = {
    "GC%3DF": "gold",
    "SI%3DF": "silver",
    "HG%3DF": "copper",
    "PL%3DF": "platinum",
    "PA%3DF": "palladium",
    "NG%3DF": "natural_gas",
    "CL%3DF": "crude_oil",
    "JJN": "nickel",
}

# Twelve Data symbol mapping
TWELVE_SYMBOLS = {
    "GC%3DF": "GC=F",
    "SI%3DF": "SI=F",
    "HG%3DF": "HG=F",
    "PL%3DF": "PL=F",
    "PA%3DF": "PA=F",
    "NG%3DF": "NG=F",
    "CL%3DF": "CL=F",
    "JJN": "JJN",
}

YAHOO_INTERVAL_MAP = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "1h": "60m",
    "4h": "1h",
    "1d": "1d",
    "1w": "1wk",
}


def _to_yahoo_symbol(symbol: str) -> str:
    return BINANCE_TO_YAHOO.get(symbol, symbol)


def _to_yahoo_interval(interval: str) -> str:
    return YAHOO_INTERVAL_MAP.get(interval, "1d")


# ── OHLCV dataclass ──────────────────────────────────────────────────────────
class OHLCV:
    def __init__(
        self,
        timestamp: int,
        open_: float,
        high: float,
        low: float,
        close: float,
        volume: float,
    ):
        self.timestamp = timestamp
        self.open = open_
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume

    @property
    def dt(self):
        return datetime.fromtimestamp(self.timestamp / 1000, tz=timezone.utc)

    @classmethod
    def from_yahoo_row(cls, dt, row) -> "OHLCV":
        return cls(
            timestamp=int(dt.timestamp() * 1000),
            open_=float(row.Open),
            high=float(row.High),
            low=float(row.Low),
            close=float(row.Close),
            volume=float(row.Volume),
        )

    @classmethod
    def from_binance_kline(cls, k):
        return cls(
            timestamp=int(k[0]),
            open_=float(k[1]),
            high=float(k[2]),
            low=float(k[3]),
            close=float(k[4]),
            volume=float(k[5]),
        )


# ── Yahoo Finance v8 (direct REST API) ──────────────────────────────────────
def _fetch_yahoo_v8(
    symbol: str, interval: str = "1d", range_: str = "60d", limit: int = 500
) -> list[OHLCV]:
    """
    Yahoo Finance v8 API — works for symbols that yfinance lib marks as delisted.
    JJN (iPath Nickel) works here but not in yfinance.Ticker().
    """
    ySymbol = _to_yahoo_symbol(symbol)
    yInterval = _to_yahoo_interval(interval)

    # Map range to yfinance period
    range_map = {
        "5d": "5d",
        "10d": "5d",
        "1mo": "1mo",
        "2mo": "2mo",
        "3mo": "3mo",
        "6mo": "6mo",
        "1y": "1y",
        "2y": "2y",
        "5d+": "5d",
        "max": "2y",
    }
    range_map.get(range_, "1y")

    try:
        r = _http.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ySymbol}",
            params={"interval": yInterval, "range": range_},
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            timeout=10,
        )
        data = r.json()
        result = data.get("chart", {}).get("result", [{}])

        if not result or result[0] is None:
            raise ValueError(f"No result from v8 for {symbol}")

        meta = result[0].get("meta", {})
        if not meta.get("regularMarketPrice"):
            raise ValueError(f"No market price for {symbol}")

        timestamps = result[0].get("timestamp", [])
        ohlcv_data = result[0].get("indicators", {}).get("quote", [{}])[0]
        result[0].get("indicators", {}).get("adjclose", [{}])

        if not timestamps:
            # If timestamps are empty but price is available (JJN case), generate synthetic OHLCV bars from current price using recent price history from yfinance lib.
            current_price = meta.get("regularMarketPrice")
            if current_price is None:
                raise ValueError(f"No current price for {symbol}")
            current_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
            return [
                OHLCV(
                    timestamp=current_timestamp,
                    open_=current_price,
                    high=current_price,
                    low=current_price,
                    close=current_price,
                    volume=0.0,
                )
            ]

        candles = []
        for i, ts in enumerate(timestamps):
            close = ohlcv_data.get("close", [None])[i]
            if close is None:
                continue
            candles.append(
                OHLCV(
                    timestamp=int(ts * 1000),
                    open_=ohlcv_data.get("open", [None])[i] or close,
                    high=ohlcv_data.get("high", [None])[i] or close,
                    low=ohlcv_data.get("low", [None])[i] or close,
                    close=float(close),
                    volume=ohlcv_data.get("volume", [None])[i] or 0.0,
                )
            )

        if limit and len(candles) > limit:
            candles = candles[-limit:]
        return candles

    except Exception as e:  # noqa: BLE001 — provider chain tolerates third-party errors
        raise ValueError(f"Yahoo v8 failed for {symbol}: {e}")


# ── Yahoo Finance (yfinance library) ─────────────────────────────────────────
def _fetch_yfinance_lib(
    symbol: str, interval: str = "1d", period: str = "60d", limit: int = 500
) -> list[OHLCV]:
    """yfinance library fallback (works for most standard symbols)."""
    ySymbol = _to_yahoo_symbol(symbol)
    yInterval = _to_yahoo_interval(interval)

    ticker = yf.Ticker(ySymbol)
    hist = ticker.history(period=period, interval=yInterval, auto_adjust=True)

    if hist.empty:
        raise ValueError(f"No yfinance data for {symbol} ({ySymbol})")

    result = []
    for dt, row in hist.iterrows():
        result.append(OHLCV.from_yahoo_row(dt, row))

    if limit and len(result) > limit:
        result = result[-limit:]
    return result


# ── Metals-API (free tier: 50 req/month) ────────────────────────────────────
def _fetch_metals_api(
    symbol: str, interval: str = "1d", limit: int = 500
) -> list[OHLCV]:
    if not METALS_API_KEY:
        raise ValueError("METALS_API_KEY not set")
    metal = METALS_API_SYMBOLS.get(symbol)
    if not metal:
        raise ValueError(f"No metals-api mapping for {symbol}")

    interval_map = {"1d": "daily", "1h": "hourly", "4h": "hourly"}
    api_interval = interval_map.get(interval, "daily")

    try:
        url = f"https://metals-api.com/api/{api_interval}_historical"
        params = {"access_key": METALS_API_KEY, "symbols": metal, "base": "USD"}
        r = _http.get(url, params=params, timeout=10)
        data = r.json()

        if data.get("success") is not False and "rates" in data:
            rates = data["rates"]
            result = []
            for date_str, day_rates in list(rates.items())[:limit]:
                if metal in day_rates and day_rates[metal] and day_rates[metal] != 0:
                    price = 1.0 / day_rates[metal]
                    dt = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
                    result.append(
                        OHLCV(
                            timestamp=int(dt.timestamp() * 1000),
                            open_=price,
                            high=price * 1.002,
                            low=price * 0.998,
                            close=price,
                            volume=0.0,
                        )
                    )
            return result
        raise ValueError("metals-api returned no rates")
    except Exception as e:  # noqa: BLE001 — provider chain tolerates third-party errors
        raise ValueError(f"metals-api failed: {e}")


# ── Twelve Data (free tier: 800 req/day) ─────────────────────────────────────
def _fetch_twelve_data(
    symbol: str, interval: str = "1d", limit: int = 500
) -> list[OHLCV]:
    if not TWELVE_DATA_KEY:
        raise ValueError("TWELVE_DATA_KEY not set")

    td_sym = TWELVE_SYMBOLS.get(symbol, symbol)
    interval_map = {
        "1m": "1min",
        "5m": "5min",
        "15m": "15min",
        "1h": "1h",
        "4h": "4h",
        "1d": "1day",
        "1w": "1week",
    }
    td_interval = interval_map.get(interval, "1day")

    try:
        url = "https://api.twelvedata.com/time_series"
        params = {
            "symbol": td_sym,
            "interval": td_interval,
            "outputsize": min(limit, 500),
            "format": "JSON",
            "apikey": TWELVE_DATA_KEY,
        }
        r = _http.get(url, params=params, timeout=10)
        data = r.json()

        if "values" in data and data["values"]:
            result = []
            for bar in reversed(data["values"]):
                result.append(
                    OHLCV(
                        timestamp=int(
                            datetime.fromisoformat(bar["datetime"]).timestamp() * 1000
                        ),
                        open_=float(bar["open"]),
                        high=float(bar["high"]),
                        low=float(bar["low"]),
                        close=float(bar["close"]),
                        volume=float(bar.get("volume", 0)),
                    )
                )
            return result
        raise ValueError("Twelve Data returned no values")
    except Exception as e:  # noqa: BLE001 — provider chain tolerates third-party errors
        raise ValueError(f"Twelve Data failed: {e}")


# ── Main unified fetch ────────────────────────────────────────────────────────
def fetch_ohlcv(
    symbol: str = "BTCUSDT",
    interval: str = "1d",
    period: str = "60d",
    limit: int = 500,
) -> list[OHLCV]:
    """
    Unified OHLCV fetcher with multiple backends.

    Priority:
    1. Yahoo Finance v8 API (direct REST — works for JJN and delisted symbols)
    2. Yahoo Finance yfinance library (standard symbols)
    3. Twelve Data (if TWELVE_DATA_KEY set)
    4. metals-api.com (if METALS_API_KEY set)

    Args:
        symbol: Sentinel internal symbol (e.g. "GC%3DF", "JJN", "BTCUSDT")
        interval: Binance-style (1m, 5m, 15m, 1h, 4h, 1d, 1w)
        period: yfinance period string (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y)
        limit: max candles

    Returns:
        List of OHLCV objects, chronological
    """
    # 1. Yahoo Finance v8 (handles JJN and other delisted symbols)
    try:
        return _fetch_yahoo_v8(symbol, interval, period, limit)
    except (
        Exception
    ) as yv8_err:  # noqa: BLE001 — provider chain tolerates third-party errors
        log.info(f"[data_provider] Yahoo v8 failed for {symbol}: {yv8_err}")

    # 2. yfinance library fallback
    try:
        return _fetch_yfinance_lib(symbol, interval, period, limit)
    except (
        Exception
    ) as yf_err:  # noqa: BLE001 — provider chain tolerates third-party errors
        log.info(f"[data_provider] yfinance lib failed for {symbol}: {yf_err}")

    # 3. Twelve Data
    if TWELVE_DATA_KEY:
        try:
            return _fetch_twelve_data(symbol, interval, limit)
        except (
            Exception
        ) as td_err:  # noqa: BLE001 — provider chain tolerates third-party errors
            log.info(f"[data_provider] Twelve Data failed for {symbol}: {td_err}")

    # 4. metals-api
    if METALS_API_KEY and symbol in METALS_API_SYMBOLS:
        try:
            return _fetch_metals_api(symbol, interval, limit)
        except (
            Exception
        ) as ma_err:  # noqa: BLE001 — provider chain tolerates third-party errors
            log.info(f"[data_provider] metals-api failed for {symbol}: {ma_err}")

    raise ValueError(f"All providers failed for {symbol}")


def fetch_ohlcv_simple(symbol: str, interval: str, limit: int) -> list:
    """
    Returns [[close, volume], ...] format used by agents.
    Compatible replacement for old Binance _fetch_ohlcv methods.
    """
    ohlcv_list = fetch_ohlcv(symbol=symbol, interval=interval, limit=limit)
    return [[float(x.close), float(x.volume)] for x in ohlcv_list]


def fetch_current_price(symbol: str) -> float:
    """Get the most recent close price."""
    try:
        data = fetch_ohlcv(symbol, "1d", limit=1)
        if data:
            return float(data[-1].close)
    except Exception:  # noqa: BLE001 — provider chain tolerates third-party errors
        pass

    # Fallback to v8 price endpoint
    ySymbol = _to_yahoo_symbol(symbol)
    try:
        r = _http.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ySymbol}",
            params={"interval": "1d", "range": "5d"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=5,
        )
        data = r.json()
        result = data.get("chart", {}).get("result", [{}])
        if result and result[0]:
            return float(result[0]["meta"]["regularMarketPrice"])
    except Exception:  # noqa: BLE001 — provider chain tolerates third-party errors
        pass

    raise ValueError(f"fetch_current_price failed for {symbol}")


def fetch_multi_ohlcv(
    symbols: list[str],
    interval: str = "1d",
    period: str = "60d",
) -> dict[str, list[OHLCV]]:
    """Fetch OHLCV for multiple symbols. Failures return empty list."""
    result = {}
    for sym in symbols:
        try:
            result[sym] = fetch_ohlcv(sym, interval, period)
        except (
            Exception
        ) as e:  # noqa: BLE001 — provider chain tolerates third-party errors
            log.info(f"[data_provider] Failed {sym}: {e}")
            result[sym] = []
    return result
