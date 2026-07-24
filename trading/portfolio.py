"""
trading/portfolio.py — ATOM-STEP-8: Portfolio & Position Tracking
===============================================================
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class PositionSide(Enum):
    LONG = 1
    SHORT = -1
    FLAT = 0


@dataclass
class Position:
    entry_price: float
    size: float
    side: PositionSide
    entry_time: datetime
    stop_loss: float | None = None
    take_profit: float | None = None
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0

    def current_value(self, current_price: float) -> float:
        if self.side == PositionSide.FLAT:
            return self.size
        price_diff = (current_price - self.entry_price) * self.side.value
        return self.size * (1 + price_diff / self.entry_price)

    def update_pnl(self, current_price: float):
        if self.side == PositionSide.FLAT:
            self.unrealized_pnl = 0.0
            return
        price_diff = (current_price - self.entry_price) * self.side.value
        pct = price_diff / self.entry_price
        self.unrealized_pnl = pct * 100  # percent


@dataclass
class Portfolio:
    initial_capital: float
    cash: float
    positions: dict[str, Position] = field(default_factory=dict)
    equity_curve: list[float] = field(default_factory=list)
    trades: list[dict] = field(default_factory=list)
    peak_capital: float = 0.0
    max_drawdown: float = 0.0
    win_count: int = 0
    loss_count: int = 0
    total_return: float = 0.0

    def equity(self, current_prices: dict[str, float]) -> float:
        pos_value = 0.0
        for symbol, pos in self.positions.items():
            if pos.side != PositionSide.FLAT:
                cp = current_prices.get(symbol, pos.entry_price)
                pos.update_pnl(cp)
                pos_value += pos.current_value(cp)
        return self.cash + pos_value

    def open_position(
        self,
        symbol: str,
        side: PositionSide,
        price: float,
        size: float,
        stop_loss: float | None = None,
        take_profit: float | None = None,
    ):
        self.positions[symbol] = Position(
            entry_price=price,
            size=size,
            side=side,
            entry_time=datetime.now(),
            stop_loss=stop_loss,
            take_profit=take_profit,
        )

    def close_position(self, symbol: str, exit_price: float):
        pos = self.positions.get(symbol)
        if not pos or pos.side == PositionSide.FLAT:
            return
        pnl_pct = (exit_price - pos.entry_price) * pos.side.value / pos.entry_price
        realized = pnl_pct * 100
        pos.realized_pnl = realized
        self.cash *= 1 + pnl_pct
        self.trades.append(
            {
                "symbol": symbol,
                "side": pos.side.name,
                "entry_price": pos.entry_price,
                "exit_price": exit_price,
                "pnl_pct": realized,
                "timestamp": datetime.now().isoformat(),
            }
        )
        if realized > 0:
            self.win_count += 1
        else:
            self.loss_count += 1
        pos.side = PositionSide.FLAT
        pos.unrealized_pnl = 0.0

    def record_equity(self, current_prices: dict[str, float]):
        eq = self.equity(current_prices)
        self.equity_curve.append(eq)
        if eq > self.peak_capital:
            self.peak_capital = eq
        dd = (self.peak_capital - eq) / self.peak_capital * 100
        if dd > self.max_drawdown:
            self.max_drawdown = dd
        self.total_return = (eq - self.initial_capital) / self.initial_capital * 100

    def summary(self) -> dict:
        total_trades = self.win_count + self.loss_count
        return {
            "initial_capital": self.initial_capital,
            "final_equity": (
                self.equity_curve[-1] if self.equity_curve else self.initial_capital
            ),
            "total_return_pct": round(self.total_return, 2),
            "max_drawdown_pct": round(self.max_drawdown, 2),
            "total_trades": total_trades,
            "win_rate_pct": (
                round(self.win_count / total_trades * 100, 1) if total_trades > 0 else 0
            ),
            "win_count": self.win_count,
            "loss_count": self.loss_count,
            "sharpe_ratio": round(self._sharpe(), 2),
        }

    def _sharpe(self) -> float:
        if len(self.equity_curve) < 2:
            return 0.0
        returns = [
            (self.equity_curve[i] - self.equity_curve[i - 1]) / self.equity_curve[i - 1]
            for i in range(1, len(self.equity_curve))
        ]
        if not returns:
            return 0.0
        import statistics

        mean_ret = statistics.mean(returns)
        std_ret = statistics.stdev(returns) if len(returns) > 1 else 1e-9
        return mean_ret / std_ret * (252**0.5) if std_ret > 0 else 0.0
