"""meta_rl/strategy_evaluator.py -- ATOM-META-RL-010/003/007: Basket + Live Data + WFA"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from meta_rl.backtest_adapter import BacktestEngineAdapter
from meta_rl.types import BasketMetrics, EvaluationResult

try:
    from meta_rl.config import (
        CCXT_EXCHANGE,
        CCXT_SANDBOX_MODE,
        EXECUTION_SANITY_ENABLED,
        KARL_META_UPDATE_ENABLED,
        RISK_INTEGRATION_ENABLED,
        TELEGRAM_ALERTS_ENABLED,
        TELEGRAM_MIN_REWARD_ALERT,
        WALK_FORWARD_ENABLED,
    )
except ImportError:
    WALK_FORWARD_ENABLED = True
    CCXT_SANDBOX_MODE = True
    CCXT_EXCHANGE = "binance"
    TELEGRAM_ALERTS_ENABLED = False
    TELEGRAM_MIN_REWARD_ALERT = 0.8
    RISK_INTEGRATION_ENABLED = True
    KARL_META_UPDATE_ENABLED = True
    EXECUTION_SANITY_ENABLED = True

MULTI_SYMBOL_ENABLED = True
logger = logging.getLogger(__name__)


class StrategyEvaluator:
    def __init__(
        self,
        backtest_adapter: BacktestEngineAdapter | None = None,
        risk_engine: Any = None,
        sanity_checker: Any = None,
        use_sanity_check: bool = True,
    ):
        self.backtest_adapter = backtest_adapter or BacktestEngineAdapter(
            sanity_checker=sanity_checker if use_sanity_check else None,
            use_sanity_check=use_sanity_check,
        )
        self.risk_engine = risk_engine
        self.sanity_checker = sanity_checker
        self.use_sanity_check = use_sanity_check
        self._basket_evaluator = None

    def _get_basket_evaluator(self):
        if self._basket_evaluator is None:
            try:
                from meta_rl.basket import BasketEvaluator

                self._basket_evaluator = BasketEvaluator(
                    strategy_evaluator=self,
                    backtest_adapter=self.backtest_adapter,
                    risk_engine=self.risk_engine,
                )
            except Exception:
                self._basket_evaluator = None
        return self._basket_evaluator

    def evaluate(self, strategy: Any, market_data: dict) -> EvaluationResult:
        try:
            ohlcv = self._extract_ohlcv(market_data)
            if len(ohlcv) < 10:
                logger.warning("[META-RL] Not enough market data")
                return EvaluationResult.fail()
            logger.debug(
                "evaluator: calling backtest_adapter.run with %d bars and strategy gen=%d",
                len(ohlcv),
                strategy.generation,
            )
            result = self.backtest_adapter.run(strategy, ohlcv, market_data)
            if self.risk_engine is not None:
                result = self._apply_risk_engine(result, market_data)
            else:
                result = EvaluationResult(
                    pnl=result.pnl,
                    sharpe=result.sharpe,
                    max_drawdown=result.max_drawdown,
                    trades=result.trades,
                    win_rate=result.win_rate,
                    execution_cost=result.execution_cost,
                    risk_adjusted_pnl=result.pnl,
                    risk_adjustment_reason="NO_RISK_ENGINE",
                    adjusted_drawdown=result.max_drawdown,
                    equity_curve=result.equity_curve,
                )
            logger.debug(
                f"[META-RL] Evaluated: pnl={result.pnl:+.3f} "
                f"risk_adj={result.risk_adjusted_pnl:+.3f} "
                f"reason={result.risk_adjustment_reason} trades={result.trades}"
            )
            return result
        except Exception as e:
            logger.warning(f"[META-RL] Evaluation failed: {e}")
            return EvaluationResult.fail()

    def evaluate_basket(self, strategy: Any, market_data_dict: dict) -> BasketMetrics:
        if not MULTI_SYMBOL_ENABLED:
            primary_data = market_data_dict.get("BTCUSDT", {})
            result = self.evaluate(strategy, primary_data)
            from meta_rl.types import SymbolMetrics

            sm = SymbolMetrics(
                symbol="BTCUSDT",
                pnl=result.pnl,
                sharpe=result.sharpe,
                max_drawdown=result.max_drawdown,
                trades=result.trades,
                win_rate=result.win_rate,
                exposure_pct=1.0,
                evaluation=result,
            )
            return BasketMetrics(
                symbols=["BTCUSDT", "ETHUSDT", "SPY"],
                symbol_metrics={"BTCUSDT": sm},
                portfolio_pnl=result.pnl,
                portfolio_sharpe=result.sharpe,
                portfolio_max_drawdown=result.max_drawdown,
                active_symbols=1,
            )
        try:
            be = self._get_basket_evaluator()
            if be is None:
                raise RuntimeError("BasketEvaluator unavailable")
            return be.evaluate_basket(strategy, market_data_dict)
        except Exception as e:
            logger.warning(f"[META-RL-BASKET] Basket evaluation failed: {e}")
            return BasketMetrics(symbols=["BTCUSDT", "ETHUSDT", "SPY"])

    def evaluate_walk_forward(
        self,
        strategy: Any,
        market_data: dict,
        n_splits: int = 5,
    ) -> EvaluationResult:
        """ATOM-META-RL-007: Full WalkForwardValidator integration."""
        if not WALK_FORWARD_ENABLED:
            return self.evaluate(strategy, market_data)
        try:
            from meta_rl.walkforward import WalkForwardValidator

            validator = WalkForwardValidator(
                evaluator=self,
                n_splits=n_splits,
                overfit_threshold=0.3,
            )
            report = validator.validate(strategy, market_data)
            if not report.splits:
                return self.evaluate(strategy, market_data)

            valid_results = []
            for s in report.splits:
                if s.oos_trades > 0:
                    valid_results.append(
                        EvaluationResult(
                            pnl=s.oos_pnl,
                            sharpe=s.oos_sharpe,
                            max_drawdown=0.0,
                            trades=s.oos_trades,
                            win_rate=s.oos_win_rate,
                            execution_cost=0.0,
                            risk_adjusted_pnl=s.oos_reward,
                            risk_adjustment_reason="WALK_FORWARD_OOS",
                        )
                    )
            if not valid_results:
                return self.evaluate(strategy, market_data)

            agg = self._aggregate_results(valid_results)
            agg.overfit_report = report
            return agg
        except Exception as e:
            logger.warning(f"[META-RL] Walk-forward failed: {e}")
            return self.evaluate(strategy, market_data)

    def split_walk_forward(self, market_data: dict, n_splits: int = 3) -> list:
        ohlcv = self._extract_ohlcv(market_data)
        if len(ohlcv) < 20:
            return []
        chunk = len(ohlcv) // n_splits
        if chunk < 10:
            return []
        splits = []
        for i in range(n_splits):
            start = i * chunk
            end = (i + 1) * chunk
            if end > len(ohlcv):
                break
            splits.append({"ohlcv": ohlcv[start:end]})
        return splits

    def _aggregate_results(self, results: list) -> EvaluationResult:
        if not results:
            return EvaluationResult.fail()
        valid = [r for r in results if r.trades > 0]
        if not valid:
            return EvaluationResult.fail()
        return EvaluationResult(
            pnl=float(np.mean([r.pnl for r in valid])),
            sharpe=float(np.mean([r.sharpe for r in valid])),
            max_drawdown=float(np.mean([r.max_drawdown for r in valid])),
            trades=int(np.mean([r.trades for r in valid])),
            win_rate=float(np.mean([r.win_rate for r in valid])),
            execution_cost=float(np.mean([r.execution_cost for r in valid])),
            risk_adjusted_pnl=float(np.mean([r.risk_adjusted_pnl for r in valid])),
            risk_adjustment_reason="AGGREGATE",
            adjusted_drawdown=(
                float(np.mean([r.adjusted_drawdown for r in valid]))
                if all(r.adjusted_drawdown is not None for r in valid)
                else None
            ),
            equity_curve=None,
        )

    def _extract_ohlcv(self, market_data: dict) -> list:
        if "BTCUSDT" in market_data or "ETHUSDT" in market_data or "SPY" in market_data:
            for sym in ("BTCUSDT", "ETHUSDT", "SPY"):
                if sym in market_data and isinstance(market_data[sym], dict):
                    ohlcv = market_data[sym].get("ohlcv", [])
                    if isinstance(ohlcv, list) and len(ohlcv) >= 10:
                        return ohlcv
            return []
        ohlcv = market_data.get("ohlcv", [])
        return ohlcv if isinstance(ohlcv, list) else []

    def _apply_risk_engine(self, result: Any, market_data: dict) -> EvaluationResult:
        vol_regime = market_data.get("volatility_regime", "NORMAL")
        if hasattr(self.risk_engine, "adjust_pnl"):
            adj_pnl = self.risk_engine.adjust_pnl(
                result.pnl,
                result.max_drawdown,
                vol_regime,
            )
        else:
            adj_pnl = result.pnl
        dd_sq = result.max_drawdown**2
        adj_dd = max(0.0, result.max_drawdown - dd_sq)
        reason = f"KELLY_{vol_regime.upper()}_DD2"
        return EvaluationResult(
            pnl=result.pnl,
            sharpe=result.sharpe,
            max_drawdown=result.max_drawdown,
            trades=result.trades,
            win_rate=result.win_rate,
            execution_cost=result.execution_cost,
            risk_adjusted_pnl=adj_pnl,
            risk_adjustment_reason=reason,
            adjusted_drawdown=adj_dd,
            equity_curve=getattr(result, "equity_curve", None),
        )
