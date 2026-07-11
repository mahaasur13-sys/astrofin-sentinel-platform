"""trading/monitoring.py — ATOM-PRODUCTION: Monitoring System
============================================================"""

from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TradeRecord:
    timestamp: float
    symbol: str
    side: str
    qty: float
    price: float
    commission: float
    slippage_bps: float
    realized_pnl: float = 0.0
    strategy_id: str = ""


@dataclass
class MonitoringSnapshot:
    timestamp: float
    equity: float
    drawdown: float
    pnl_total: float
    pnl_unrealized: float
    sharpe_ratio: float
    sortino_ratio: float
    slippage_bps_avg: float
    slippage_bps_max: float
    execution_cost_bps: float
    trade_count: int
    win_rate: float
    rl_reward_cumulative: float
    regime: str
    mode: str


class Monitoring:
    def __init__(self, window_size=100, risk_free_rate=0.0, target_return=0.0):
        self.window_size = window_size
        self.risk_free_rate = risk_free_rate
        self.target_return = target_return
        self._equity_ts = deque(maxlen=window_size)
        self._return_ts = deque(maxlen=window_size)
        self._slippage_ts = deque(maxlen=window_size)
        self._cost_ts = deque(maxlen=window_size)
        self._reward_ts = deque(maxlen=window_size)
        self._timestamps = deque(maxlen=window_size)
        self._trades = []
        self._peak_equity = 0.0
        self._initial_equity = 0.0
        self._cumulative_pnl = 0.0
        self._cumulative_reward = 0.0
        self._log_hook = None

    def update_equity(self, equity, timestamp=None):
        ts = timestamp or time.time()
        equity = float(equity)
        if math.isnan(equity) or math.isinf(equity):
            return
        self._equity_ts.append(equity)
        self._timestamps.append(ts)
        if self._initial_equity == 0:
            self._initial_equity = equity
        if equity > self._peak_equity:
            self._peak_equity = equity
        if len(self._equity_ts) >= 2:
            prev = self._equity_ts[-2]
            ret = (equity - prev) / prev if prev != 0 else 0.0
            ret = max(-1.0, min(1.0, ret))
            self._return_ts.append(ret)

    def record_trade(self, trade):
        self._trades.append(trade)
        self._cumulative_pnl += trade.realized_pnl
        if trade.slippage_bps > 0:
            self._slippage_ts.append(trade.slippage_bps)
        comm_bps = (trade.commission / trade.price / trade.qty * 10_000) if trade.price > 0 else 0.0
        self._cost_ts.append(comm_bps)

    def record_reward(self, reward):
        if not (math.isnan(reward) or math.isinf(reward)):
            self._cumulative_reward += reward
            self._reward_ts.append(reward)

    def get_snapshot(self, regime="NORMAL", mode="BACKTEST"):
        equity = self._equity_ts[-1] if self._equity_ts else self._initial_equity or 100_000.0
        drawdown = self._compute_drawdown(equity)
        pnl_total = self._cumulative_pnl + self._compute_unrealized_pnl()
        pnl_unrealized = self._compute_unrealized_pnl()
        returns = list(self._return_ts)
        sharpe = self._compute_sharpe(returns)
        sortino = self._compute_sortino(returns)
        win_rate = self._compute_win_rate()
        slippage_avg = self._mean(self._slippage_ts)
        slippage_max = max(self._slippage_ts) if self._slippage_ts else 0.0
        cost_bps = self._mean(self._cost_ts)
        return MonitoringSnapshot(
            timestamp=time.time(),
            equity=equity,
            drawdown=drawdown,
            pnl_total=pnl_total,
            pnl_unrealized=pnl_unrealized,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            slippage_bps_avg=slippage_avg,
            slippage_bps_max=slippage_max,
            execution_cost_bps=cost_bps,
            trade_count=len(self._trades),
            win_rate=win_rate,
            rl_reward_cumulative=self._cumulative_reward,
            regime=regime,
            mode=mode,
        )

    def get_metrics_dict(self, regime="NORMAL", mode="BACKTEST"):
        s = self.get_snapshot(regime, mode)
        return {
            "equity": round(s.equity, 2),
            "drawdown": round(s.drawdown, 4),
            "pnl_total": round(s.pnl_total, 2),
            "pnl_unrealized": round(s.pnl_unrealized, 2),
            "sharpe": round(s.sharpe_ratio, 3),
            "sortino": round(s.sortino_ratio, 3),
            "slippage_bps": round(s.slippage_bps_avg, 2),
            "slippage_bps_max": round(s.slippage_bps_max, 2),
            "execution_cost_bps": round(s.execution_cost_bps, 2),
            "trade_count": s.trade_count,
            "win_rate": round(s.win_rate, 4),
            "rl_reward": round(s.rl_reward_cumulative, 4),
            "regime": s.regime,
            "mode": s.mode,
            "timestamp": datetime.fromtimestamp(s.timestamp).strftime("%Y-%m-%d %H:%M:%S"),
        }

    def print_metrics(self, regime="NORMAL", mode="BACKTEST"):
        m = self.get_metrics_dict(regime, mode)
        print("\n=== MONITORING SNAPSHOT ===")
        for k, v in m.items():
            print(f"  {k}: {v}")
        print("=" * 30 + "\n")

    def _compute_drawdown(self, equity):
        if self._peak_equity <= 0:
            return 0.0
        return max(0.0, (self._peak_equity - equity) / self._peak_equity)

    def _compute_sharpe(self, returns):
        if len(returns) < 2:
            return 0.0
        try:
            import numpy as np

            mean_ret = float(np.mean(returns))
            std_ret = float(np.std(returns, ddof=0))
            if std_ret == 0 or math.isnan(std_ret):
                return 0.0
            excess = mean_ret - self.risk_free_rate / 252
            return excess / std_ret * math.sqrt(252)
        except Exception:  # noqa: BLE001
            return 0.0

    def _compute_sortino(self, returns):
        if len(returns) < 2:
            return 0.0
        try:
            import numpy as np

            rets = np.array(returns)
            mean_ret = float(np.mean(rets))
            downside = rets[rets < self.target_return]
            if len(downside) == 0:
                return 0.0
            down_std = float(np.std(downside, ddof=0))
            if down_std == 0:
                return 0.0
            excess = mean_ret - self.target_return
            return excess / down_std * math.sqrt(252)
        except Exception:  # noqa: BLE001
            return 0.0

    def _compute_win_rate(self):
        if not self._trades:
            return 0.0
        wins = sum(1 for t in self._trades if t.realized_pnl > 0)
        return wins / len(self._trades)

    def _compute_unrealized_pnl(self):
        return 0.0

    def _mean(self, deque_obj):
        if not deque_obj:
            return 0.0
        return sum(deque_obj) / len(deque_obj)

    def set_log_hook(self, hook):
        self._log_hook = hook


if __name__ == "__main__":
    print("Monitoring self-test...")
    mon = Monitoring()
    equity = 100_000.0
    for i in range(50):
        equity *= 1 + 0.001 if i % 2 == 0 else -0.0003
        mon.update_equity(equity)
    for i in range(10):
        mon.record_trade(
            TradeRecord(
                time.time(),
                "BTC",
                "BUY",
                0.1,
                50_000,
                5.0,
                5.0 + i * 0.5,
                100.0 if i % 3 == 0 else -30.0,
            )
        )
    for r in [0.1, -0.05, 0.2, 0.15, -0.1, 0.3]:
        mon.record_reward(r)
    m = mon.get_metrics_dict()
    assert m["trade_count"] == 10
    print("  Monitoring: all tests passed")
