"""Market-data freshness guards (fail-closed).

Two rules shared by agents and the live cycle:

* OKX candles whose newest bar is older than ``max_bars`` intervals are
  treated as *no data* (callers get ``[]`` and take the existing #479
  ``no_data`` path) instead of being used as if they were current.
* A missing current price is ``None`` -- never a made-up constant such as
  50000.  Agents that need the price return NEUTRAL/no_data.

Threshold: ``ASTROFIN_CANDLE_MAX_AGE_BARS`` (float, default 3.0).  The age is
measured from the *start* of the newest candle, so with the default a 1D
series is accepted while its newest bar started < 72h ago (the previous closed bar,
the forming one, plus one bar of slack for a late exchange update).
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)


def _now() -> float:
    """Wall clock (epoch s); patch point for tests."""
    return time.time()

DEFAULT_MAX_AGE_BARS = 3.0
ENV_MAX_AGE_BARS = "ASTROFIN_CANDLE_MAX_AGE_BARS"

_UNIT_SECONDS = {"m": 60, "h": 3600, "d": 86400, "w": 7 * 86400}


def bar_seconds(bar: str) -> int | None:
    """Interval of an OKX/Binance bar string in seconds (``"4H"`` -> 14400).

    ``"1M"`` (month, OKX) is approximated as 31 days.  Unknown -> ``None``.
    """
    if not bar:
        return None
    b = bar.strip()
    if b.endswith("utc"):  # OKX "1Dutc", "4Hutc"
        b = b[:-3]
    if b.endswith("M") and b[:-1].isdigit():
        return int(b[:-1]) * 31 * 86400
    unit = b[-1:].lower()
    num = b[:-1]
    if unit not in _UNIT_SECONDS or not num.isdigit():
        return None
    return int(num) * _UNIT_SECONDS[unit]


def max_age_bars() -> float:
    raw = os.environ.get(ENV_MAX_AGE_BARS, "")
    try:
        val = float(raw) if raw else DEFAULT_MAX_AGE_BARS
    except ValueError:
        logger.warning("[freshness] bad %s=%r, using %s", ENV_MAX_AGE_BARS, raw, DEFAULT_MAX_AGE_BARS)
        return DEFAULT_MAX_AGE_BARS
    return val if val > 0 else DEFAULT_MAX_AGE_BARS


def newest_candle_ts(rows: list) -> float | None:
    """Newest candle start time in epoch seconds (OKX row[0] is ms)."""
    best: float | None = None
    for row in rows or []:
        try:
            ts = float(row[0])
        except (TypeError, ValueError, IndexError):
            continue
        if ts > 1e11:  # milliseconds
            ts /= 1000.0
        if best is None or ts > best:
            best = ts
    return best


def candles_are_fresh(rows: list, bar: str, *, now: float | None = None, max_bars: float | None = None) -> bool:
    """True if the newest candle started at most ``max_bars`` intervals ago.

    No rows, no parseable timestamp or an unknown bar -> ``False`` (fail-closed).
    """
    interval = bar_seconds(bar)
    newest = newest_candle_ts(rows)
    if interval is None or newest is None:
        return False
    now = _now() if now is None else now
    limit = (max_bars if max_bars is not None else max_age_bars()) * interval
    return (now - newest) <= limit


def _row_ts(row: Any) -> float:
    try:
        return float(row[0])
    except (TypeError, ValueError, IndexError):
        return float("-inf")


def fresh_okx_rows(rows: Any, bar: str, *, now: float | None = None, source: str = "") -> list:
    """Return ``rows`` sorted oldest -> newest if fresh, otherwise ``[]``.

    OKX returns candles newest first; every caller indexes ``closes[-1]`` /
    ``[-N:]`` as "latest", so rows are sorted by ts ascending here.
    Stale/undated -> ``[]`` (=> caller's no_data path).
    """
    rows = list(rows or [])
    if not rows:
        return []
    if candles_are_fresh(rows, bar, now=now):
        return sorted(rows, key=_row_ts)
    newest = newest_candle_ts(rows)
    age = None if newest is None else round(((_now() if now is None else now) - newest) / 3600, 1)
    logger.warning("[freshness] stale/undated candles dropped: source=%s bar=%s age_h=%s", source or "?", bar, age)
    return []


def get_current_price(state: dict) -> float | None:
    """Current price from agent state; ``None`` if missing or non-positive."""
    for key in ("current_price", "price"):
        val = state.get(key)
        try:
            if val is not None and float(val) > 0:
                return float(val)
        except (TypeError, ValueError):
            continue
    return None


def price_no_data_response(agent_name: str):
    """NEUTRAL 20 ``no_data`` response, same shape as the #479 path."""
    from core.base_agent import AgentResponse, SignalDirection

    return AgentResponse(
        agent_name=agent_name,
        signal=SignalDirection.NEUTRAL,
        confidence=20,
        reasoning="No current price available",
        sources=[],
        metadata={"no_data": True, "reason": "no_price"},
    )
