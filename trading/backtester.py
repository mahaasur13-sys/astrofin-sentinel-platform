"""trading/backtester.py — ATOM-STEP-8: Backtesting Engine"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime

from .portfolio import Portfolio, PositionSide


@dataclass
class BacktestConfig:
    initial_capital: float = 10000.0
    max_positions: int = 3
    risk_per_trade_pct: float = 2.0
    stop_loss_pct: float = 5.0
    take_profit_pct: float = 10.0
    commission_pct: float = 0.05


@dataclass
class BacktestTrade:
    entry_time: datetime
    exit_time: datetime
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    size: float
    pnl_pct: float
    pnl_abs: float
    commission: float


@dataclass
class BacktestResult:
    config: BacktestConfig
    portfolio_summary: dict
    trades: list[BacktestTrade] = field(default_factory=list)
    equity_curve: list = field(default_factory=list)
    signals_log: list = field(default_factory=list)

    def print_summary(self):
        s = self.portfolio_summary
        trades = self.trades
        print()
        print("=" * 60)
        print("  BACKTEST RESULTS")
        print("=" * 60)
        print(f"  Initial Capital:  ${s['initial_capital']:,.2f}")
        print(f"  Final Equity:    ${s['final_equity']:,.2f}")
        print(f"  Total Return:    {s['total_return_pct']:+.2f}%")
        print(f"  Max Drawdown:    {s['max_drawdown_pct']:.2f}%")
        print(f"  Sharpe Ratio:    {s['sharpe_ratio']:.2f}")
        print(f"  Win Rate:        {s['win_rate_pct']:.1f}% ({s['win_count']}/{s['total_trades']})")
        print(f"  Total Trades:    {s['total_trades']}")
        total_comm = sum(t.commission for t in trades)
        print(f"  Commission Paid: ${total_comm:.2f}")
        print("=" * 60)


class Backtester:
    def __init__(self, config: BacktestConfig | None = None):
        self.config = config or BacktestConfig()
        self.portfolio = Portfolio(
            initial_capital=self.config.initial_capital,
            cash=self.config.initial_capital,
        )
        self.trades = []
        self.equity_curve = []
        self.signals_log = []

    def run(self, signals: list, prices: dict):
        if not signals:
            return self._build_result()
        for sig in sorted(signals, key=lambda x: x["timestamp"]):
            ts = sig["timestamp"]
            symbol = sig["symbol"]
            signal = sig["signal"]
            confidence = sig.get("confidence", 50)
            price_series = prices.get(symbol, [])
            if not price_series:
                continue
            current_price = self._price_at(price_series, ts)
            if current_price is None:
                continue
            self.signals_log.append(sig)
            pos = self.portfolio.positions.get(symbol)
            in_position = pos and pos.side != PositionSide.FLAT
            if signal == "LONG" and not in_position and len(self.portfolio.positions) < self.config.max_positions:
                size = self._position_size(confidence)
                sl = current_price * (1 - self.config.stop_loss_pct / 100)
                tp = current_price * (1 + self.config.take_profit_pct / 100)
                self.portfolio.open_position(symbol, PositionSide.LONG, current_price, size, sl, tp)
            elif signal == "SHORT" and not in_position and len(self.portfolio.positions) < self.config.max_positions:
                size = self._position_size(confidence)
                sl = current_price * (1 + self.config.stop_loss_pct / 100)
                tp = current_price * (1 - self.config.take_profit_pct / 100)
                self.portfolio.open_position(symbol, PositionSide.SHORT, current_price, size, sl, tp)
            elif signal == "NEUTRAL" and in_position:
                self._close_trade(symbol, current_price, ts)
            if in_position:
                self._check_stops(pos, current_price, ts)
            self.portfolio.record_equity({symbol: current_price})
            self.equity_curve.append((ts, self.portfolio.equity({symbol: current_price})))
        for symbol, pos in list(self.portfolio.positions.items()):
            if pos.side != PositionSide.FLAT:
                ps = prices.get(symbol, [])
                if ps:
                    self._close_trade(symbol, ps[-1][1], ps[-1][0])
        return self._build_result()

    def _price_at(self, series, ts):
        for dt, p in series:
            if dt >= ts:
                return p
        return None

    def _position_size(self, confidence: float) -> float:
        base_risk = self.config.initial_capital * self.config.risk_per_trade_pct / 100
        conf_mult = confidence / 50.0
        size = base_risk * conf_mult
        # Cap at max_position_pct of portfolio equity to prevent compounding blow-up
        equity = self.portfolio.equity({})
        max_pos = equity * (getattr(self.config, "max_position_pct", 20.0) / 100.0)
        return min(size, max_pos)

    def _check_stops(self, pos, current_price, ts):
        hit = False
        if pos.side == PositionSide.LONG:
            if pos.stop_loss and current_price <= pos.stop_loss:
                hit = True
            elif pos.take_profit and current_price >= pos.take_profit:
                hit = True
        elif pos.side == PositionSide.SHORT:
            if pos.stop_loss and current_price >= pos.stop_loss:
                hit = True
            elif pos.take_profit and current_price <= pos.take_profit:
                hit = True
        if hit:
            for sym, p in list(self.portfolio.positions.items()):
                if p is pos:
                    self._close_trade(sym, current_price, ts)
                    break

    def _close_trade(self, symbol, exit_price, exit_time):
        pos = self.portfolio.positions.get(symbol)
        if not pos or pos.side == PositionSide.FLAT:
            return
        entry_price = pos.entry_price
        size = pos.size
        pnl_pct = (exit_price - entry_price) * pos.side.value / entry_price * 100
        commission = size * self.config.commission_pct / 100
        pnl_abs = size * pnl_pct / 100 - commission
        self.trades.append(
            BacktestTrade(
                entry_time=pos.entry_time,
                exit_time=exit_time,
                symbol=symbol,
                side=pos.side.name,
                entry_price=entry_price,
                exit_price=exit_price,
                size=size,
                pnl_pct=pnl_pct,
                pnl_abs=pnl_abs,
                commission=commission,
            )
        )
        self.portfolio.close_position(symbol, exit_price)

    def _build_result(self):
        self.portfolio.record_equity({})
        return BacktestResult(
            config=self.config,
            portfolio_summary=self.portfolio.summary(),
            trades=self.trades,
            equity_curve=self.equity_curve,
            signals_log=self.signals_log,
        )
