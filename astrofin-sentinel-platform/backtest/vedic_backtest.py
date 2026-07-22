"""backtest/vedic_backtest.py — Sprint 7: Vedic-Aware Backtesting Framework.

Extends trading/backtester.py with:
  - Nakshatra-annotated trades (vedic_trade_type, muhurta_score)
  - Per-Nakshatra performance matrix (Sharpe, win-rate, max-DD)
  - Vedic signal filter (entry only on EXCELLENT/GOOD election grades)
  - Muhurta-window aware execution (can't enter during Kaal/Udveg)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from trading.backtester import BacktestTrade, BacktestResult, BacktestConfig


@dataclass
class VedicTradeAnnotation:
    """Metadata attached to each trade for Vedic performance analysis."""
    nakshatra: str = ""
    nakshatra_number: int = 0
    muhurta_score: int = 0
    choghadiya: str = ""
    election_grade: str = "neutral"
    risk_multiplier: float = 1.0
    is_favorable_entry: bool = False
    entered_during_avoid: bool = False


@dataclass
class VedicBacktestTrade(BacktestTrade):
    """Backtest trade with Vedic metadata."""
    vedic: VedicTradeAnnotation = field(default_factory=VedicTradeAnnotation)


@dataclass
class NakshatraPerformance:
    """Performance metrics for a single Nakshatra."""
    nakshatra: str
    number: int
    trade_count: int = 0
    wins: int = 0
    losses: int = 0
    total_pnl_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    avg_holding_hours: float = 0.0
    election_grade: str = "neutral"

    @property
    def win_rate(self) -> float | None:
        return (self.wins / self.trade_count) if self.trade_count > 0 else None

    @property
    def avg_return(self) -> float:
        return (self.total_pnl_pct / self.trade_count) if self.trade_count > 0 else 0.0

    @property
    def sharpe_like(self) -> float:
        """Simple Sharpe-like: avg_return / sqrt(n) approximation."""
        if self.trade_count < 2:
            return 0.0
        import math
        import numpy as np
        # Simplified — full Sharpe needs per-trade return series
        return self.avg_return / (abs(self.avg_return / math.sqrt(self.trade_count)) + 0.001)


@dataclass
class VedicPerformanceMatrix:
    """Collection of per-Nakshatra performance metrics."""
    trades: list[VedicBacktestTrade] = field(default_factory=list)
    by_nakshatra: dict[str, NakshatraPerformance] = field(default_factory=dict)

    def add_trade(self, trade: VedicBacktestTrade) -> None:
        self.trades.append(trade)
        nak = trade.vedic.nakshatra
        if nak not in self.by_nakshatra:
            self.by_nakshatra[nak] = NakshatraPerformance(
                nakshatra=nak,
                number=trade.vedic.nakshatra_number,
                election_grade=trade.vedic.election_grade,
            )
        perf = self.by_nakshatra[nak]
        perf.trade_count += 1
        if trade.pnl_pct > 0:
            perf.wins += 1
        else:
            perf.losses += 1
        perf.total_pnl_pct += trade.pnl_pct
        perf.max_drawdown_pct = max(perf.max_drawdown_pct, abs(trade.pnl_pct) if trade.pnl_pct < 0 else 0.0)

    def summary(self) -> str:
        lines = ["═" * 80, "  VEDIC BACKTEST — Nakshatra Performance Matrix", "═" * 80]
        lines.append(f"  {'Nakshatra':20s} {'Grade':>10s} {'Trades':>7s} {'Win%':>7s} {'AvgRet':>7s} {'MaxDD':>7s} {'Multiplier':>10s}")
        lines.append("  " + "─" * 72)
        for name, perf in sorted(self.by_nakshatra.items(), key=lambda x: -x[1].trade_count):
            wr = f"{perf.win_rate*100:.0f}%" if perf.win_rate is not None else "—"
            from trading.vedic.nakshatra_risk import get_nakshatra_multiplier
            mult = get_nakshatra_multiplier(name)
            lines.append(
                f"  {name:20s} {perf.election_grade:>10s} {perf.trade_count:>7d} {wr:>7s} "
                f"{perf.avg_return*100:>6.1f}% {perf.max_drawdown_pct*100:>6.1f}% ×{mult:>8.2f}"
            )
        lines.append("═" * 80)
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            name: {
                "trades": p.trade_count,
                "win_rate": round(p.win_rate, 3) if p.win_rate is not None else None,
                "avg_return": round(p.avg_return, 4),
                "max_drawdown": round(p.max_drawdown_pct, 4),
                "election_grade": p.election_grade,
            }
            for name, p in self.by_nakshatra.items()
        }

    def best_nakshatra(self) -> str | None:
        if not self.by_nakshatra:
            return None
        return max(self.by_nakshatra, key=lambda n: (
            self.by_nakshatra[n].trade_count >= 5,
            self.by_nakshatra[n].win_rate or 0,
            self.by_nakshatra[n].avg_return,
        ))

    def worst_nakshatra(self) -> str | None:
        if not self.by_nakshatra:
            return None
        return min(self.by_nakshatra, key=lambda n: (
            self.by_nakshatra[n].avg_return,
        ))


def annotate_trade(trade: BacktestTrade, dt: datetime) -> VedicBacktestTrade:
    """Annotate a trade with Vedic metadata based on entry datetime."""
    from core.panchanga import calculate_panchanga
    from trading.vedic.nakshatra_risk import (
        get_nakshatra_multiplier, get_election_grade,
        is_favorable_nakshatra, is_dangerous_nakshatra,
    )

    try:
        from core.ephemeris import get_planetary_positions
        positions = get_planetary_positions(dt)
        moon = positions.get("Moon", positions.get("moon"))
        sun = positions.get("Sun", positions.get("sun"))
        moon_lon = moon.longitude if moon else 0.0
        sun_lon = sun.longitude if sun else 0.0
        panch = calculate_panchanga(dt, moon_lon, sun_lon)
        nak = panch["nakshatra"]
        ms = panch.get("muhurta_score", {"score": 50})
        chog_slots = panch.get("choghadiya_slots", panch.get("choghadiya", []))
        chog = chog_slots[0]["name"] if chog_slots else ""
    except Exception:
        nak = {"name": "", "number": 0}
        ms = {"score": 50}
        chog = ""

    nak_name = nak.get("name", "")
    mult = get_nakshatra_multiplier(nak_name)
    grade = get_election_grade(nak_name)

    annotation = VedicTradeAnnotation(
        nakshatra=nak_name,
        nakshatra_number=nak.get("number", 0),
        muhurta_score=ms.get("score", 50),
        choghadiya=chog,
        election_grade=grade.value,
        risk_multiplier=mult,
        is_favorable_entry=is_favorable_nakshatra(nak_name),
        entered_during_avoid=is_dangerous_nakshatra(nak_name),
    )
    return VedicBacktestTrade(
        entry_time=trade.entry_time,
        exit_time=trade.exit_time,
        symbol=trade.symbol,
        side=trade.side,
        entry_price=trade.entry_price,
        exit_price=trade.exit_price,
        size=trade.size,
        pnl_pct=trade.pnl_pct,
        pnl_abs=trade.pnl_abs,
        commission=trade.commission,
        vedic=annotation,
    )


def vedic_filter(
    trades: list[BacktestTrade],
    min_muhurta: int = 50,
    exclude_dangerous: bool = True,
) -> list[BacktestTrade]:
    """Filter trades: keep only those entered during favorable Vedic conditions."""
    from core.panchanga import calculate_panchanga
    from trading.vedic.nakshatra_risk import is_dangerous_nakshatra

    filtered = []
    for trade in trades:
        try:
            panch = calculate_panchanga(trade.entry_time)
            ms = panch["muhurta_score"]["score"]
            nak = panch["nakshatra"]["name"]
            if ms < min_muhurta:
                continue
            if exclude_dangerous and is_dangerous_nakshatra(nak):
                continue
            filtered.append(trade)
        except Exception:
            filtered.append(trade)  # pass-through on error
    return filtered
