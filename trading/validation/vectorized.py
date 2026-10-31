"""Vectorised position-series backtest (daily bars, full allocation) with B&H benchmark.

Complements the event-driven ``trading.backtester.Backtester`` (sized positions, SL/TP), which
cannot express a fully-invested on/off rule such as SMA200. Costs and slippage are charged per
side on turnover: cost_t = |pos_t - pos_{t-1}| * (cost_per_side + slippage_per_side).
Positions must already be lagged by the caller (pos[t] decided at close[t-1]).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .errors import ValidationError
from .stats import performance_metrics


@dataclass(frozen=True)
class PositionBacktest:
    frame: pd.DataFrame  # columns: r, pos, turnover, strategy, benchmark
    periods_per_year: int

    def metrics(self, start=None, end=None) -> dict:
        d = self.frame.loc[start:end]
        if len(d) < 3:
            raise ValidationError("period too short")
        s = performance_metrics(d["strategy"].to_numpy(), self.periods_per_year)
        s["trades"] = int(d["turnover"].sum())
        s["in_mkt"] = float(d["pos"].mean())
        b = performance_metrics(d["benchmark"].to_numpy(), self.periods_per_year)
        return {"strategy": s, "buy_and_hold": b, "start": str(d.index[0].date()), "end": str(d.index[-1].date())}


def sma_signal(close: pd.Series, window: int) -> pd.Series:
    """1.0 if close > SMA(window), else 0.0; NaN during warm-up. Uses data up to t only."""
    sma = close.rolling(window).mean()
    return (close > sma).astype(float).where(sma.notna())


def run_position_backtest(
    close: pd.Series,
    signal: pd.Series,
    *,
    periods_per_year: int,
    cost_per_side: float = 0.0,
    slippage_per_side: float = 0.0,
) -> PositionBacktest:
    """signal[t] is known at close[t]; position for (t, t+1] is signal[t] (shift(1), no look-ahead)."""
    for name, v in (("cost_per_side", cost_per_side), ("slippage_per_side", slippage_per_side)):
        if not (np.isfinite(v) and v >= 0):
            raise ValidationError(f"{name} must be finite and >= 0")
    if not close.index.is_monotonic_increasing:
        raise ValidationError("close index must be chronological")
    pos = signal.shift(1)
    r = close.pct_change()
    df = pd.DataFrame({"r": r, "pos": pos}).dropna()
    if df.empty:
        raise ValidationError("no bars after warm-up")
    turnover = df["pos"].diff().abs().fillna(df["pos"].iloc[0])
    df["turnover"] = turnover
    df["strategy"] = df["pos"] * df["r"] - turnover * (cost_per_side + slippage_per_side)
    df["benchmark"] = df["r"]
    return PositionBacktest(df, periods_per_year)
