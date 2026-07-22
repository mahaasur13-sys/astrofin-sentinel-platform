"""
trading/factory.py — Broker Factory (Sprint 8.1).

Instantiate the correct broker based on MODE env var / TradingMode.
Strategy pattern — PaperBroker and BinanceBroker share identical interface.
"""

from __future__ import annotations

import os

from .broker.base import BaseBroker
from .mode import TradingMode

import logging
log = logging.getLogger(__name__)


def _resolve_mode() -> TradingMode:
    """Resolve trading mode from env, defaulting to PAPER for safety."""
    mode_str = os.getenv("TRADING_MODE", "PAPER").upper()
    try:
        return TradingMode[mode_str]
    except KeyError:
        log.warning(
            f"[Factory] Unknown TRADING_MODE={mode_str}, falling back to PAPER"
        )
        return TradingMode.PAPER


def get_broker(mode: TradingMode | None = None) -> BaseBroker:
    """Return the appropriate broker for the given mode.

    PAPER → PaperBroker (simulated, no API keys)
    LIVE_LIMITED / LIVE_FULL → BinanceBroker (real execution)
    BACKTEST → PaperBroker (simulated)

    Usage:
        from trading.factory import get_broker
        broker = get_broker()
        order = broker.place_order("BTCUSDT", OrderSide.BUY, OrderType.MARKET, 0.01)
    """
    mode = mode or _resolve_mode()

    if mode == TradingMode.BACKTEST:
        from .paper_broker import get_paper_broker
        return get_paper_broker()

    if mode == TradingMode.PAPER:
        from .paper_broker import get_paper_broker
        return get_paper_broker()

    if mode in (TradingMode.LIVE_LIMITED, TradingMode.LIVE_FULL):
        from .broker.binance import BinanceBroker
        broker = BinanceBroker(paper=False)
        broker.connect()
        return broker

    # Fallback: always safe
    from .paper_broker import get_paper_broker
    log.warning(f"[Factory] Unhandled mode {mode}, falling back to PaperBroker")
    return get_paper_broker()
