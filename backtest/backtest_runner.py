"""BacktestRunner — historical simulation of CouncilOrchestrator pipeline."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from core.base_agent import AgentResponse, SignalDirection
from orchestration.council_orchestrator import CouncilOrchestrator

logger = logging.getLogger(__name__)


@dataclass
class BacktestStats:
    trades: int = 0
    wins: int = 0
    losses: int = 0
    stops_triggered: int = 0
    neutrals_skipped: int = 0
    max_drawdown: float = 0.0
    peak_equity: float = 10000.0
    final_equity: float = 10000.0
    equity_curve: list[float] = field(default_factory=list)

    @property
    def win_rate(self) -> float | None:
        return (self.wins / self.trades) if self.trades > 0 else None

    @property
    def total_return_pct(self) -> float:
        return ((self.final_equity / 10000.0) - 1.0) * 100

    def to_dict(self) -> dict[str, Any]:
        return {
            "trades": self.trades,
            "wins": self.wins,
            "losses": self.losses,
            "stops_triggered": self.stops_triggered,
            "neutrals_skipped": self.neutrals_skipped,
            "win_rate": round(self.win_rate, 3) if self.win_rate is not None else None,
            "max_drawdown_pct": round(self.max_drawdown * 100, 2),
            "total_return_pct": round(self.total_return_pct, 2),
            "final_equity": round(self.final_equity, 2),
        }


class BacktestRunner:
    """Прогоняет исторические OHLCV данные через CouncilOrchestrator в режиме симуляции."""

    def __init__(
        self,
        orchestrator: CouncilOrchestrator,
        initial_capital: float = 10000.0,
        position_size_pct: float = 1.0,
    ):
        self.orch = orchestrator
        self.initial_capital = initial_capital
        self.position_size_pct = position_size_pct

        self.capital = initial_capital
        self.position = 0.0
        self.entry_price = 0.0
        self.stats = BacktestStats(peak_equity=initial_capital, final_equity=initial_capital)

    def _build_responses(self, hmm_regime: int = 1, is_anomaly: bool = False, probs=None) -> list[AgentResponse]:
        """Build synthetic agent responses for backtest simulation."""
        responses: list[AgentResponse] = []

        # QuantAgent — always bullish in simulation for testing purposes
        responses.append(
            AgentResponse(
                agent_name="QuantAgent",
                signal=SignalDirection.LONG,
                confidence=80,
                reasoning="Backtest simulated Quant response",
            )
        )

        # HMMRegimeAgent — driven by the lookback data
        if probs is None:
            probs = [0.33, 0.34, 0.33]
        responses.append(
            AgentResponse(
                agent_name="HMMRegimeAgent",
                signal=SignalDirection.AVOID if is_anomaly else SignalDirection.NEUTRAL,
                confidence=90 if is_anomaly else 50,
                reasoning=f"HMM regime={hmm_regime}",
                metadata={
                    "regime": hmm_regime,
                    "regime_probabilities": probs,
                    "is_anomaly": is_anomaly,
                    "log_likelihood": -20.0 if is_anomaly else -3.0,
                },
            )
        )

        return responses

    def _simulate_trade(self, action: dict, current_price: float) -> None:
        """Simulate trade execution against current close price."""
        if action["action"] == "STOP":
            self.stats.stops_triggered += 1
            return

        if action["action"] == "NEUTRAL":
            self.stats.neutrals_skipped += 1
            return

        signal_name = action.get("signal", "LONG")
        size = action.get("size", 0.0)

        # Close existing position if we have one
        if self.position != 0.0:
            pnl = self.position * (current_price - self.entry_price)
            self.capital += pnl
            self.stats.trades += 1
            if pnl > 0:
                self.stats.wins += 1
            else:
                self.stats.losses += 1
            self.position = 0.0

        # Open new position
        if size > 0:
            notional = self.capital * self.position_size_pct * size
            self.position = notional / current_price if signal_name == "LONG" else -notional / current_price
            self.entry_price = current_price

    async def run(self, ohlcv: list, symbol: str = "BTCUSDT") -> BacktestStats:
        """Run backtest over historical OHLCV data.

        Args:
            ohlcv: list of dicts with 'close', 'volume' keys
            symbol: trading pair symbol

        Returns:
            BacktestStats with equity curve and summary metrics.
        """
        lookback = 60
        self.stats.equity_curve = [self.initial_capital]

        for i in range(lookback, len(ohlcv)):
            window = ohlcv[max(0, i - lookback) : i + 1]
            current_price = ohlcv[i]["close"]

            # Detect regime from recent returns
            recent_closes = [c["close"] for c in window[-20:]]
            returns = np.diff(np.log(recent_closes))
            mean_ret = np.mean(returns) if len(returns) > 0 else 0
            agg_std = np.std(returns) if len(returns) > 0 else 0.02

            # Heuristic regime detection (same as HMM would do):
            #   bull: positive mean, low vol
            #   sideways: small mean, any vol
            #   bear: negative mean, high vol
            if mean_ret > 0.001 and agg_std < 0.03:
                regime = 0  # bull
                probs = [0.7, 0.2, 0.1]
            elif mean_ret < -0.001 and agg_std > 0.025:
                regime = 2  # bear
                probs = [0.1, 0.2, 0.7]
            else:
                regime = 1  # sideways
                probs = [0.1, 0.8, 0.1]

            # Anomaly: extreme daily move (>3 std)
            today_return = returns[-1] if len(returns) > 0 else 0
            is_anomaly = abs(today_return) > (agg_std * 3) if agg_std > 0 else False

            responses = self._build_responses(
                hmm_regime=regime,
                is_anomaly=is_anomaly,
                probs=probs,
            )

            final_signal = AgentResponse(
                agent_name="AstroCouncil",
                signal=SignalDirection.LONG,
                confidence=75,
                reasoning="Backtest consensus",
            )

            action = await self.orch.execute_trading_cycle(
                agent_responses=responses,
                final_signal=final_signal,
                config={"symbol": symbol, "base_position_size": 1.0},
                is_backtest=True,
            )

            self._simulate_trade(action, current_price)

            # Update equity
            current_equity = self.capital + (self.position * current_price)
            self.stats.equity_curve.append(current_equity)

            if current_equity > self.stats.peak_equity:
                self.stats.peak_equity = current_equity

            dd = (self.stats.peak_equity - current_equity) / self.stats.peak_equity if self.stats.peak_equity > 0 else 0
            if dd > self.stats.max_drawdown:
                self.stats.max_drawdown = dd

        # Close any open position at last price
        if self.position != 0.0 and len(ohlcv) > 0:
            last_price = ohlcv[-1]["close"]
            pnl = self.position * (last_price - self.entry_price)
            self.capital += pnl
            self.stats.trades += 1
            if pnl > 0:
                self.stats.wins += 1
            else:
                self.stats.losses += 1
            self.position = 0.0

        self.stats.final_equity = self.capital
        return self.stats


def generate_random_ohlcv(n_bars: int = 200, seed: int = 42) -> list[dict]:
    """Generate random OHLCV data for backtest testing."""
    np.random.seed(seed)
    prices = 100.0 * np.cumprod(1.0 + np.random.randn(n_bars) * 0.01)
    volumes = np.random.randint(100, 1000, n_bars)

    return [{"close": float(prices[i]), "volume": int(volumes[i])} for i in range(n_bars)]
