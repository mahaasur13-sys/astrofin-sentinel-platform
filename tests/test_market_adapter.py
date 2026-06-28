"""tests/test_market_adapter.py — Regression test for data.market_adapter.

Фиксирует баг, закрытый коммитом 43b005e:
  MarketAdapter.fetch_ohlcv() использовал self._cache, но __init__ создаёт self._redis
  → AttributeError на каждом вызове, невозможно прогнать бэктест.

Также проверяет:
  - Synthetic fallback возвращает ровно `limit` OHLCV-свечей
  - Каждая свеча валидна: high >= max(open, close), low <= min(open, close)
  - Источники 'binance'/'coingecko' строят source_chain через fallback на synthetic
  - Новые источники 'polygon'/'unusual_whales' тоже валидны
"""

from __future__ import annotations

import os
from datetime import timedelta
from unittest.mock import patch

import pytest
from data.market_adapter import MarketAdapter, OHLCV


@pytest.fixture
def adapter_synthetic():
    """MarketAdapter в режиме synthetic (без Redis, без сети)."""
    os.environ["MARKET_DATA_SOURCE"] = "synthetic"
    from data.market_adapter import MarketAdapter

    return MarketAdapter(source="synthetic")


def test_fetch_ohlcv_synthetic_does_not_raise_attribute_error(adapter_synthetic):
    """Регресс 43b005e: раньше падало с AttributeError: 'MarketAdapter' object has no attribute '_cache'."""
    data = adapter_synthetic.fetch_ohlcv("BTCUSDT", interval="1h", limit=10)
    assert isinstance(data, list)
    assert len(data) == 10


def test_fetch_ohlcv_synthetic_shape_and_invariants(adapter_synthetic):
    """Все свечи валидны: high >= low, high >= open, high >= close."""
    data = adapter_synthetic.fetch_ohlcv("ETHUSDT", interval="1h", limit=50)
    assert len(data) == 50
    for c in data:
        assert c.high >= c.low
        assert c.high >= c.open
        assert c.high >= c.close
        assert c.low <= c.open
        assert c.low <= c.close
        assert c.volume > 0


def test_timestamps_are_monotonic(adapter_synthetic):
    """Свечи идут по времени вперёд."""
    data = adapter_synthetic.fetch_ohlcv("BTCUSDT", interval="1h", limit=20)
    ts = [c.timestamp for c in data]
    assert ts == sorted(ts), "timestamps must be non-decreasing"
    # разница между соседними ≈ 1 час
    delta = ts[1] - ts[0]
    assert timedelta(minutes=55) <= delta <= timedelta(minutes=65)


def test_source_chain_binance_falls_back_to_synthetic_on_network_error():
    """binance → coingecko → synthetic: при ошибке сети всё равно возвращаются данные."""
    os.environ["MARKET_DATA_SOURCE"] = "binance"
    from data.market_adapter import MarketAdapter

    a = MarketAdapter(source="binance")
    chain = a._build_source_chain()
    assert chain == ["binance", "coingecko", "synthetic"]
    assert "synthetic" in chain  # fallback всегда есть

    # Принудительно гасим оба источника — synthetic должен сработать
    with (
        patch.object(a, "_fetch_binance", side_effect=ConnectionError("net down")),
        patch.object(a, "_fetch_coingecko", side_effect=ConnectionError("net down")),
    ):
        data = a.fetch_ohlcv("BTCUSDT", interval="1h", limit=5)
    assert len(data) == 5


def test_get_latest_price_returns_close(adapter_synthetic):
    """get_latest_price возвращает close первой свечи своей собственной выборки.

    Не сравниваем с отдельным fetch_ohlcv(), т.к. synthetic при каждом вызове
    генерирует новые данные (random.gauss). Тест проверяет, что возвращённая цена
    совпадает с close свечи, на которой она основана.
    """
    # Подменяем fetch_ohlcv, чтобы зафиксировать возврат и проверить контракт
    from datetime import datetime

    fixed = [
        OHLCV(timestamp=datetime(2026, 1, 1), open=100.0, high=101.0, low=99.0, close=100.5, volume=1000.0),
        OHLCV(timestamp=datetime(2026, 1, 2), open=100.5, high=102.0, low=100.0, close=101.5, volume=1100.0),
    ]
    with patch.object(adapter_synthetic, "fetch_ohlcv", return_value=fixed):
        price = adapter_synthetic.get_latest_price("BTCUSDT")
    assert price == 100.5


def test_polygon_and_uw_sources_have_fallback():
    """Polygon и UnusualWhales должны иметь synthetic в source_chain как safety net."""
    from data.market_adapter import MarketAdapter

    for src in ("polygon", "unusual_whales", "uw"):
        a = MarketAdapter(source=src)
        chain = a._build_source_chain()
        assert chain[-1] == "synthetic", f"{src} must end with synthetic fallback"
        assert chain[0] == src, f"{src} must be primary source"


def test_polygon_deterministic_for_same_input():
    """Polygon mock должен быть детерминирован — критично для реплеев бэктеста."""
    a1 = MarketAdapter(source="polygon")
    a2 = MarketAdapter(source="polygon")
    c1 = a1.fetch_ohlcv("BTCUSDT", "1h", 5)
    c2 = a2.fetch_ohlcv("BTCUSDT", "1h", 5)
    for x, y in zip(c1, c2):
        assert x.open == y.open and x.close == y.close


def test_unusual_whales_higher_volume_than_synthetic():
    """UW mock имеет x10 volume по сравнению с synthetic baseline."""
    a_synth = MarketAdapter(source="synthetic")
    a_uw = MarketAdapter(source="unusual_whales")
    # Same symbol + interval
    s = a_synth.fetch_ohlcv("ETHUSDT", "4h", 5)
    u = a_uw.fetch_ohlcv("ETHUSDT", "4h", 5)
    avg_s = sum(c.volume for c in s) / len(s)
    avg_u = sum(c.volume for c in u) / len(u)
    assert avg_u > avg_s * 5, f"UW avg vol {avg_u} should be >> synthetic {avg_s}"


def test_source_chain_dispatch_table():
    """Проверка source_chain для всех 5 источников."""
    from data.market_adapter import MarketAdapter

    for src in ("binance", "coingecko", "polygon", "unusual_whales", "uw"):
        a = MarketAdapter(source=src)
        chain = a._build_source_chain()
        assert chain[0] == src, f"{src} must be primary source"
        assert "synthetic" in chain, f"{src} must have synthetic fallback"
