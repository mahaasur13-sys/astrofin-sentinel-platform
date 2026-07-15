"""meta_rl/data_adapter.py — ATOM-META-RL-003: OHLCV ↔ Strategy format adapter"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from data.market_adapter import OHLCV


def ohlcv_to_strategy_format(ohlcv_data: list[OHLCV]) -> dict[str, Any]:
    """
    Convert List[OHLCV] → market_data dict for StrategyEvaluator.

    Compatible with:
        - BacktestEngineAdapter._build_signals()
        - StrategyEvaluator.evaluate()
    """
    if not ohlcv_data:
        return {"close": [], "ohlcv": []}

    return {
        "ohlcv": ohlcv_data,
        "close": [d.close for d in ohlcv_data],
        "high": [d.high for d in ohlcv_data],
        "low": [d.low for d in ohlcv_data],
        "volume": [d.volume for d in ohlcv_data],
        "timestamps": [d.timestamp for d in ohlcv_data],
    }


def market_data_to_ohlcv(market_data: dict[str, Any]) -> list[OHLCV]:
    """
    Reverse converter: market_data dict → List[OHLCV].

    Used when meta_rl output needs to be fed back into backtesting.
    """
    closes = market_data.get("close", [])
    opens = market_data.get("open", closes)
    highs = market_data.get("high", closes)
    lows = market_data.get("low", closes)
    volumes = market_data.get("volume", [0.0] * len(closes))
    timestamps = market_data.get("timestamps", [datetime.now(timezone.utc)] * len(closes))

    n = len(closes)
    return [
        OHLCV(
            timestamp=timestamps[i] if i < len(timestamps) else datetime.now(timezone.utc),
            open=float(opens[i] if i < len(opens) else closes[i]),
            high=float(highs[i] if i < len(highs) else closes[i]),
            low=float(lows[i] if i < len(lows) else closes[i]),
            close=float(closes[i]),
            volume=float(volumes[i] if i < len(volumes) else 0.0),
        )
        for i in range(n)
    ]


def normalize_symbol(symbol: str) -> str:
    """
    Normalize symbol between CCXT format (with slash) and internal format.

    Binance:    BTC/USDT  → BTCUSDT
    Kraken:     BTC/USD   → BTCUSD
    Generic:    XXX/YYY   → XXXYYY
    """
    return symbol.replace("/", "").replace("-", "")


def denormalize_symbol(symbol: str) -> str:
    """Convert internal BTCUSDT → CCXT BTC/USDT."""
    if len(symbol) <= 3:
        return symbol
    # Try to split: last 3-4 chars are quote
    for i in range(3, min(5, len(symbol))):
        base, quote = symbol[:-i], symbol[-i:]
        if quote in ("USDT", "USD", "BTC", "ETH", "EUR", "GBP"):
            return f"{base}/{quote}"
    return symbol


def validate_market_data(market_data: dict[str, Any]) -> bool:
    """
    Validate market_data has required fields for StrategyEvaluator.

    Required: close (list of floats)
    Optional: high, low, volume, regime, signal_strength, momentum, atr
    """
    if not market_data:
        return False
    closes = market_data.get("close", [])
    if not closes or not isinstance(closes, (list, tuple)):  # noqa: UP038
        return False
    if not all(isinstance(c, (int, float)) for c in closes):  # noqa: UP038
        return False
    return True
