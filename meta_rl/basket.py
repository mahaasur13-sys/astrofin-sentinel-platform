"""meta_rl/basket.py -- ATOM-META-RL-010: Multi-symbol Basket Evaluation"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

# F821 fix: keep StrategyEvaluator import out of cycle
from meta_rl.strategy_evaluator import StrategyEvaluator  # F821 fix

# lazy import inside methods to avoid circular
from meta_rl.backtest_adapter import BacktestEngineAdapter
from meta_rl.types import BasketMetrics, SymbolMetrics
from trading.risk_v2 import RiskEngineV2


logger = logging.getLogger(__name__)

MULTI_SYMBOL_ENABLED = True
DEFAULT_BASKET = ["BTCUSDT", "ETHUSDT", "SPY"]


def correlation_penalty_matrix(returns_dict: dict[str, list[float]]) -> float:
    """
    Compute pairwise correlation penalty for a basket.

    Penalizes high correlation between assets.
    penalty = mean(|corr(i,j)|) for all pairs i<j

    Returns 0.0 for single-asset basket.
    """
    symbols = list(returns_dict.keys())
    if len(symbols) < 2:
        return 0.0

    # Build returns matrix
    min_len = min(len(returns_dict[s]) for s in symbols)
    if min_len < 2:
        return 0.0

    matrix = np.array([returns_dict[s][:min_len] for s in symbols], dtype=float)

    try:
        corr_matrix = np.corrcoef(matrix)
        n = len(symbols)
        total_corr = 0.0
        count = 0
        for i in range(n):
            for j in range(i + 1, n):
                c = float(corr_matrix[i][j])
                if not np.isnan(c):
                    total_corr += abs(c)
                    count += 1
        if count == 0:
            return 0.0
        return total_corr / count
    except Exception:  # noqa: BLE001
        return 0.0


def diversification_bonus(n_active: int, n_total: int) -> float:
    """
    Bonus for holding multiple uncorrelated assets.

    bonus = min(0.10, (n_active / n_total) * 0.10)
    Full basket (3/3) → 0.10
    Single asset (1/3) → 0.033
    """
    if n_total == 0:
        return 0.0
    return float(min(0.10, (n_active / n_total) * 0.10))


class BasketEvaluator:
    """
    ATOM-META-RL-010: Evaluates strategies across a basket of assets.

    Pipeline:
        For each symbol in basket:
            1. Extract symbol-specific market_data
            2. Run StrategyEvaluator.evaluate() → SymbolMetrics
        Aggregate:
            3. Portfolio equity curve (sum across symbols)
            4. Portfolio Sharpe = mean(sharpe) - correlation_penalty
            5. Portfolio max_dd = max per-symbol max_dd
            6. Correlation penalty + diversification bonus
            7. BasketMetrics

    Single-symbol fallback (MULTI_SYMBOL_ENABLED=False):
        evaluate_basket() → evaluate() on first symbol
    """

    def __init__(
        self,
        strategy_evaluator: StrategyEvaluator | None = None,
        backtest_adapter: BacktestEngineAdapter | None = None,
        risk_engine: RiskEngineV2 | None = None,
        basket: list[str] | None = None,
    ):
        self.strategy_evaluator = strategy_evaluator or StrategyEvaluator()
        self.backtest_adapter = backtest_adapter
        self.risk_engine = risk_engine
        self.basket = basket or DEFAULT_BASKET
        self.multi_enabled = MULTI_SYMBOL_ENABLED

    def evaluate_basket(
        self,
        strategy: Any,
        market_data_dict: dict[str, dict],
    ) -> BasketMetrics:
        """
        Evaluate a strategy across a basket of assets.

        Args:
            strategy: GeneratedStrategy instance
            market_data_dict: dict keyed by symbol, each containing:
                - 'ohlcv': list of OHLCV bars
                - 'regime': Regime value
                - 'signal_strength': float
                - etc.

        Returns:
            BasketMetrics (never raises — always returns safe result)
        """
        if not self.multi_enabled:
            return self._single_symbol_fallback(strategy, market_data_dict)

        symbols = self.basket
        symbol_metrics: dict[str, SymbolMetrics] = {}
        portfolio_returns: dict[str, list[float]] = {}
        equity_curves: dict[str, np.ndarray] = {}

        for symbol in symbols:
            sym_data = market_data_dict.get(symbol)
            if sym_data is None:
                logger.debug(f"[META-RL-BASKET] No market data for {symbol}, skipping")
                continue

            try:
                eval_result = self.strategy_evaluator.evaluate(strategy, sym_data)
            except Exception as e:  # noqa: BLE001
                logger.warning(f"[META-RL-BASKET] Evaluation failed for {symbol}: {e}")
                continue

            if eval_result.trades == 0:
                logger.debug(f"[META-RL-BASKET] No trades for {symbol}, skipping")
                continue

            equity_curve = eval_result.equity_curve
            if equity_curve is not None and len(equity_curve) > 1:
                returns = np.diff(equity_curve) / equity_curve[:-1]
                portfolio_returns[symbol] = returns.tolist()
                equity_curves[symbol] = equity_curve

            exposure_pct = 1.0 / len(symbols)  # Equal weight per symbol
            sm = SymbolMetrics(
                symbol=symbol,
                pnl=eval_result.pnl,
                sharpe=eval_result.sharpe,
                max_drawdown=eval_result.max_drawdown,
                trades=eval_result.trades,
                win_rate=eval_result.win_rate,
                exposure_pct=exposure_pct,
                evaluation=eval_result,
            )
            symbol_metrics[symbol] = sm
            logger.debug(
                f"[META-RL-BASKET] {symbol}: "
                f"pnl={eval_result.pnl:+.4f} sharpe={eval_result.sharpe:.3f} "
                f"trades={eval_result.trades} dd={eval_result.max_drawdown:.4f}"
            )

        if not symbol_metrics:
            logger.warning("[META-RL-BASKET] No valid metrics across basket, returning fail-safe")
            return BasketMetrics(symbols=symbols)

        # Aggregate portfolio equity curve
        portfolio_equity = self._aggregate_equity_curves(equity_curves)

        # Portfolio metrics
        total_symbols = len(symbols)
        active_symbols = len(symbol_metrics)

        # Mean portfolio Sharpe (weighted)
        mean_sharpe = float(np.mean([sm.sharpe for sm in symbol_metrics.values()]))

        # Correlation penalty
        corr_penalty = correlation_penalty_matrix(portfolio_returns)

        # Diversification bonus
        div_bonus = diversification_bonus(active_symbols, total_symbols)

        # Portfolio Sharpe = mean - correlation_penalty + diversification_bonus
        portfolio_sharpe = max(-5.0, mean_sharpe - corr_penalty + div_bonus)

        # Portfolio max drawdown = worst individual
        portfolio_max_dd = max(sm.max_drawdown for sm in symbol_metrics.values())

        # Portfolio PnL = sum of individual PnLs
        portfolio_pnl = sum(sm.pnl for sm in symbol_metrics.values()) / active_symbols

        basket_metrics = BasketMetrics(
            symbols=symbols,
            symbol_metrics=symbol_metrics,
            portfolio_pnl=portfolio_pnl,
            portfolio_sharpe=portfolio_sharpe,
            portfolio_max_drawdown=portfolio_max_dd,
            correlation_penalty=corr_penalty,
            diversification_bonus=div_bonus,
            active_symbols=active_symbols,
            portfolio_equity_curve=portfolio_equity,
        )

        logger.info(
            f"[META-RL-BASKET] Basket result: "
            f"active={active_symbols}/{total_symbols} "
            f"portfolio_pnl={portfolio_pnl:+.4f} "
            f"portfolio_sharpe={portfolio_sharpe:.4f} "
            f"corr_penalty={corr_penalty:.4f} "
            f"div_bonus={div_bonus:.4f} "
            f"worst_dd={portfolio_max_dd:.4f}"
        )

        return basket_metrics

    def _aggregate_equity_curves(
        self,
        curves: dict[str, np.ndarray],
    ) -> np.ndarray | None:
        """Aggregate multiple equity curves (equal weight, normalized)."""
        if not curves:
            return None

        min_len = min(len(c) for c in curves.values())
        if min_len < 2:
            return None

        normalized = []
        for arr in curves.values():
            normalized_arr = arr[:min_len] / arr[0] if arr[0] != 0 else arr[:min_len]
            normalized.append(normalized_arr)

        avg_normalized = np.mean(normalized, axis=0)
        return avg_normalized

    def _single_symbol_fallback(
        self,
        strategy: Any,
        market_data_dict: dict[str, dict],
    ) -> BasketMetrics:
        """Fallback when multi-symbol is disabled: evaluate first available symbol."""
        logger.warning("[META-RL-BASKET] Multi-symbol disabled, using single-symbol fallback")

        primary = self.basket[0] if self.basket else "BTCUSDT"
        sym_data = market_data_dict.get(primary, market_data_dict.get("BTCUSDT"))

        if sym_data is None:
            logger.warning(f"[META-RL-BASKET] No market data for {primary}, returning empty basket")
            return BasketMetrics(symbols=self.basket)

        eval_result = self.strategy_evaluator.evaluate(strategy, sym_data)

        sm = SymbolMetrics(
            symbol=primary,
            pnl=eval_result.pnl,
            sharpe=eval_result.sharpe,
            max_drawdown=eval_result.max_drawdown,
            trades=eval_result.trades,
            win_rate=eval_result.win_rate,
            exposure_pct=1.0,
            evaluation=eval_result,
        )

        return BasketMetrics(
            symbols=self.basket,
            symbol_metrics={primary: sm},
            portfolio_pnl=eval_result.pnl,
            portfolio_sharpe=eval_result.sharpe,
            portfolio_max_drawdown=eval_result.max_drawdown,
            active_symbols=1,
        )
