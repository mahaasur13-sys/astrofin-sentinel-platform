"""Data Room Blueprint — единственная точка доступа к рыночным данным.

R3 (CodeRabbit): все агенты ОБЯЗАНЫ получать цены/метрики через этот модуль.
Прямой `import requests` в `agents/` запрещён.

Провайдеры:
- ``get_price(symbol, timeframe)`` — текущая/историческая цена.
- ``get_market_cap(symbol)`` — капитализация.
- ``get_klines(symbol, interval, limit)`` — OHLCV-свечи.

Поведение:
- При сбое внешних API возвращает ``None`` (degrade gracefully).
- Таймауты 10s, ретраев нет (выше — ответственность оркестратора).
"""

from __future__ import annotations

import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)


def get_price(symbol: str, timeframe: str = "1d") -> Optional[float]:
    """Вернуть текущую цену ``symbol`` (``BTCUSDT`` → Binance).

    :param symbol: торговый символ, например ``BTCUSDT``.
    :param timeframe: ``1H|4H|1D|1W|SWING`` (маппится в Binance interval).
    :return: цена закрытия или ``None`` при ошибке.
    """
    try:
        interval_map = {"1H": "1h", "4H": "4h", "1D": "1d", "1W": "1w", "SWING": "1d"}
        interval = interval_map.get(timeframe, "1d")
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=1"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data:
                return float(data[-1][4])  # close price
    except Exception as exc:  # noqa: BLE001 — boundary log only
        logger.warning("data_room.get_price failed for %s: %s", symbol, exc)
    return None


def get_klines(symbol: str, interval: str = "1d", limit: int = 100) -> list[float]:
    """Вернуть список close-цен (Binance)."""
    try:
        url = (
            f"https://api.binance.com/api/v3/klines"
            f"?symbol={symbol}&interval={interval}&limit={limit}"
        )
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return [float(x[4]) for x in data]
    except Exception as exc:  # noqa: BLE001
        logger.warning("data_room.get_klines failed for %s: %s", symbol, exc)
    return []


def get_market_cap(symbol: str) -> Optional[dict]:
    """Вернуть базовые метрики CoinGecko для ``symbol`` (без USDT)."""
    try:
        coin_id = symbol.replace("USDT", "").lower()
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "name": data.get("name", ""),
                "market_cap_rank": data.get("market_cap_rank", 999),
                "market_cap": data.get("market_data", {})
                .get("market_cap", {})
                .get("usd", 0),
                "volume_24h": data.get("market_data", {})
                .get("total_volume", {})
                .get("usd", 0),
                "ath": data.get("market_data", {}).get("ath", {}).get("usd", 0),
                "atl": data.get("market_data", {}).get("atl", {}).get("usd", 0),
            }
    except Exception as exc:  # noqa: BLE001
        logger.warning("data_room.get_market_cap failed for %s: %s", symbol, exc)
    return None


__all__ = ["get_price", "get_klines", "get_market_cap"]
