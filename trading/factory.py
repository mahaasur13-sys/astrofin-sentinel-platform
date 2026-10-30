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


LIVE_TRADING_FLAG_ENV = "ASTROFIN_ALLOW_LIVE_TRADING"
LIVE_TRADING_FLAG_VALUE = "I_UNDERSTAND"


class LiveTradingNotAllowedError(RuntimeError):
    """Raised when a LIVE mode is requested without the explicit opt-in flag."""


class BrokerConnectionError(RuntimeError):
    """Raised when a live broker could not connect (fail-closed: no broker returned)."""


def live_trading_allowed() -> bool:
    """True only if ASTROFIN_ALLOW_LIVE_TRADING is exactly 'I_UNDERSTAND'."""
    return os.environ.get(LIVE_TRADING_FLAG_ENV) == LIVE_TRADING_FLAG_VALUE


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
        # Live gate: real exchange execution requires a separate explicit opt-in.
        # Checked BEFORE importing/instantiating BinanceBroker (no keys loaded, no network).
        if not live_trading_allowed():
            raise LiveTradingNotAllowedError(
                f"Live trading mode {mode.value} is disabled: set "
                f"{LIVE_TRADING_FLAG_ENV}={LIVE_TRADING_FLAG_VALUE} to allow real order execution. "
                "Default mode is PAPER."
            )
        from .broker.binance import BinanceBroker
        broker = BinanceBroker(paper=False)
        try:
            ok = broker.connect()
        except Exception as e:  # noqa: BLE001 — any connect failure is fail-closed
            raise BrokerConnectionError(
                f"{mode.value}: BinanceBroker.connect() raised {type(e).__name__}"
            ) from e
        if not ok:
            raise BrokerConnectionError(
                f"{mode.value}: BinanceBroker.connect() failed — broker not connected"
            )
        return broker

    # Fallback: always safe
    from .paper_broker import get_paper_broker
    log.warning(f"[Factory] Unhandled mode {mode}, falling back to PaperBroker")
    return get_paper_broker()
