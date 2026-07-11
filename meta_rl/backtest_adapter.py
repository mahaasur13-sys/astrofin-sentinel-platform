"""meta_rl/backtest_adapter.py — ATOM-META-RL-003: BacktestEngine Adapter"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from meta_rl.types import EvaluationResult
from trading.backtester import Backtester

logger = logging.getLogger(__name__)


class BacktestEngineAdapter:
    """
    Production backtest adapter.

    Converts GeneratedStrategy + market data into EvaluationResult
    using the real Backtester (trading/backtester.py).

    Safety chain:
        1. Build signals from strategy evaluation
        2. Backtester.run() — handles portfolio, SL/TP, commission
        3. ExecutionSanityChecker (if enabled)
        4. Return EvaluationResult

    Seed-controlled: Backtester is deterministic per strategy evaluation.
    """

    def __init__(
        self,
        backtester: Backtester | None = None,
        sanity_checker: Any | None = None,
        use_sanity_check: bool = True,
    ):
        self.backtester = backtester or Backtester()
        self.sanity_checker = sanity_checker
        self.use_sanity_check = use_sanity_check

    def run(
        self,
        strategy: Any,
        ohlcv: list,
        market_data: dict | None = None,
    ) -> EvaluationResult:
        """Run production backtest via Backtester."""
        try:
            # 1. Build signals from strategy evaluation
            signals = self._build_signals(strategy, ohlcv, market_data)
            if not signals:
                logger.warning("[META-RL-INTEGRATION] No signals generated")
                return EvaluationResult.fail()

            # 2. Build price series dict
            prices = self._build_prices(ohlcv)

            # 3. Run Backtester (real engine)
            result = self.backtester.run(signals, prices)

            # 4. Sanity check on trades
            if self.use_sanity_check and self.sanity_checker:
                result = self._apply_sanity_check(result, market_data)

            # 5. Convert to EvaluationResult
            return self._to_evaluation_result(result)

        except Exception as e:  # noqa: BLE001
            logger.warning(f"[META-RL-INTEGRATION] Backtester failed: {e}")
            return EvaluationResult.fail()

    def _build_signals(self, strategy: Any, ohlcv: list, market_data: dict | None) -> list:
        """Build signals by calling strategy.evaluate() on each bar."""
        from strategies.base import Regime

        symbol = "BTCUSDT"
        regime = Regime.NEUTRAL_R
        sym_data: dict = {}

        if market_data:
            if "BTCUSDT" in market_data or "ETHUSDT" in market_data or "SPY" in market_data:
                for sym in ("BTCUSDT", "ETHUSDT", "SPY"):
                    if sym in market_data and isinstance(market_data[sym], dict):
                        symbol = sym
                        sym_data = market_data[sym]
                        break
            else:
                sym_data = market_data
                symbol = market_data.get("symbol", "BTCUSDT")

            regime_str = sym_data.get("regime", "NEUTRAL_R")
            if regime_str == "NEUTRAL_R":
                regime = Regime.NEUTRAL_R
            elif regime_str in (r.value for r in Regime):
                regime = Regime(regime_str)
            elif hasattr(regime_str, "value"):
                regime = regime_str
            else:
                regime = Regime.NEUTRAL_R

        # Унификация символа – используется "BTCUSDT" для согласованности с _build_prices
        symbol = "BTCUSDT" if symbol == "BTC/USDT" else symbol

        signals = []
        for idx, bar in enumerate(ohlcv):
            close = self._get_close(bar)

            bar_dict = {
                "close": close,
                "open": self._get_open(bar),
                "high": self._get_high(bar),
                "low": self._get_low(bar),
                "volume": self._get_volume(bar),
                "regime": regime,
                "signal_strength": sym_data.get("signal_strength", 50.0),
                "momentum": sym_data.get("momentum", 0.0),
                "mean_reversion_signal": sym_data.get("mean_reversion_signal", 0.0),
                "atr": sym_data.get("atr", close * 0.02),
            }

            result = strategy.evaluate(bar_dict)
            ts = self._get_timestamp(bar)
            if ts is None:
                ts_int = idx
            elif hasattr(ts, "timestamp"):
                ts_int = int(ts.timestamp())
            elif isinstance(ts, (int, float)) and ts > 1e9:
                ts_int = int(ts)
            else:
                ts_int = idx

            signals.append(
                {
                    "timestamp": ts_int,
                    "symbol": symbol,
                    "signal": result.signal.value,
                    "confidence": result.confidence,
                    "reasoning": result.reasoning,
                }
            )

        return signals

    def _build_prices(self, ohlcv: list) -> dict:
        """Build price series dict for Backtester."""
        symbol = "BTCUSDT"
        series = []
        for idx, bar in enumerate(ohlcv):
            ts = self._get_timestamp(bar)
            close = self._get_close(bar)
            if hasattr(ts, "timestamp"):
                ts_int = int(ts.timestamp())
            elif isinstance(ts, (int, float)) and ts > 1e9:
                ts_int = int(ts)
            else:
                ts_int = idx
            series.append((ts_int, close))
        return {symbol: series}

    def _apply_sanity_check(self, result: Any, market_data: dict | None) -> Any:
        """Apply ExecutionSanityChecker to backtest result."""
        try:
            if not hasattr(self.sanity_checker, "validate"):
                return result

            for trade in getattr(result, "trades", []):
                market_state = self._build_market_state(market_data)
                order_req = self._build_order_request(trade, market_data)
                sanity = self.sanity_checker.validate(order_req, market_state)
                if sanity.status.value == "REJECTED":
                    logger.warning(f"[META-RL-INTEGRATION] Trade rejected by sanity: {sanity.reason}")
            return result
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[META-RL-INTEGRATION] Sanity check failed: {e}")
            return result

    def _to_evaluation_result(self, result: Any) -> EvaluationResult:
        """Convert BacktestResult => EvaluationResult."""
        try:
            summary = result.portfolio_summary
            trades = result.trades
            equity_curve = result.equity_curve

            winning = sum(1 for t in trades if t.pnl_abs > 0)
            total = len(trades)
            win_rate = winning / max(1, total)

            equity_arr = np.array([eq for _, eq in equity_curve]) if equity_curve else None
            returns = (
                np.diff(equity_arr) / equity_arr[:-1]
                if equity_arr is not None and len(equity_arr) > 1
                else np.array([0.0])
            )
            mean_ret = float(np.mean(returns)) if len(returns) > 0 else 0.0
            std_ret = float(np.std(returns)) if len(returns) > 0 else 0.01
            sharpe = float((mean_ret / std_ret) * np.sqrt(252)) if std_ret > 1e-8 else 0.0

            total_return_pct = summary.get("total_return_pct", 0.0)
            max_dd_pct = summary.get("max_drawdown_pct", 0.0)

            total_commission = sum(t.commission for t in trades)
            execution_cost = total_commission / summary.get("initial_capital", 10000.0)

            return EvaluationResult(
                pnl=total_return_pct / 100.0,
                sharpe=sharpe,
                max_drawdown=max_dd_pct / 100.0,
                trades=total,
                win_rate=win_rate,
                execution_cost=execution_cost,
                equity_curve=equity_arr,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[META-RL-INTEGRATION] Conversion failed: {e}")
            return EvaluationResult.fail()

    # Field accessors (handle both dict and dataclass)
    def _get_close(self, bar: Any) -> float:
        if hasattr(bar, "close"):
            return float(bar.close)
        if isinstance(bar, dict):
            return float(bar.get("close", 0))
        return 0.0

    def _get_open(self, bar: Any) -> float:
        if hasattr(bar, "open"):
            return float(bar.open)
        if isinstance(bar, dict):
            return float(bar.get("open", 0))
        return 0.0

    def _get_high(self, bar: Any) -> float:
        if hasattr(bar, "high"):
            return float(bar.high)
        if isinstance(bar, dict):
            return float(bar.get("high", 0))
        return 0.0

    def _get_low(self, bar: Any) -> float:
        if hasattr(bar, "low"):
            return float(bar.low)
        if isinstance(bar, dict):
            return float(bar.get("low", 0))
        return 0.0

    def _get_volume(self, bar: Any) -> float:
        if hasattr(bar, "volume"):
            return float(bar.volume)
        if isinstance(bar, dict):
            return float(bar.get("volume", 0))
        return 0.0

    def _get_timestamp(self, bar: Any):
        if hasattr(bar, "dt"):
            return bar.dt
        if hasattr(bar, "timestamp"):
            return bar.timestamp
        if isinstance(bar, dict):
            if "timestamp" in bar:
                return bar["timestamp"]
            if "dt" in bar:
                return bar["dt"]
        return None

    def _build_market_state(self, market_data: dict | None):
        from trading.execution.sanity import MarketState

        if market_data is None:
            return MarketState(
                symbol="BTCUSDT",
                last_price=50000.0,
                bid_price=49999.0,
                ask_price=50001.0,
                spread_bps=4.0,
                adv_24h=1e9,
                realized_vol_20d=0.02,
                current_vol_regime="NORMAL",
            )
        return MarketState(
            symbol=market_data.get("symbol", "BTCUSDT"),
            last_price=market_data.get("last_price", 50000.0),
            bid_price=market_data.get("bid_price", 49999.0),
            ask_price=market_data.get("ask_price", 50001.0),
            spread_bps=market_data.get("spread_bps", 4.0),
            adv_24h=market_data.get("adv_24h", 1e9),
            realized_vol_20d=market_data.get("realized_vol_20d", 0.02),
            current_vol_regime=market_data.get("current_vol_regime", "NORMAL"),
        )

    def _build_order_request(self, trade: Any, market_data: dict | None):
        from trading.execution.sanity import OrderRequest

        return OrderRequest(
            symbol=getattr(trade, "symbol", "BTCUSDT"),
            side=getattr(trade, "side", "BUY"),
            qty=getattr(trade, "size", 0.0),
            price=getattr(trade, "entry_price", 0.0),
            order_type="MARKET",
            slippage_bp_estimate=market_data.get("slippage_bp", 5.0) if market_data else 5.0,
        )
