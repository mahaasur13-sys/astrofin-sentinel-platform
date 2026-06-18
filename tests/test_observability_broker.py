from __future__ import annotations

from unittest.mock import Mock, patch


import pytest
@pytest.mark.unit
def test_broker_error_increments_counter():
    """При ошибке брокера счётчик astrofin_broker_errors_total увеличивается."""
    from tools.metrics_server import BROKER_ERRORS
    from trading.broker.binance import BinanceBroker

    broker = BinanceBroker(paper=True)
    broker.connected = True
    mock_exchange = Mock()
    mock_exchange.fetch_ticker.side_effect = Exception("Connection error")
    broker.exchange = mock_exchange

    before = BROKER_ERRORS._value.get() if hasattr(BROKER_ERRORS, "_value") else 0

    with patch("trading.broker.binance.HAS_CCXT", True):
        price = broker.get_market_price("BTCUSDT")

    after = BROKER_ERRORS._value.get() if hasattr(BROKER_ERRORS, "_value") else 0

    assert price == 0.0, "Should return 0.0 on error"
    assert after > before, f"Counter should increment: {before} -> {after}"
