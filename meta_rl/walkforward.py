"""meta_rl/walkforward.py — ATOM-META-RL-006: Walk-Forward Out-of-Sample Validation

Implements standard quant walk-forward analysis (WFA) to detect overfitting:
  1. Train window: in-sample (IS) — strategy is optimized on this data
  2. Test window: out-of-sample (OOS) — strategy is evaluated on unseen data
  3. Rolling shift: window slides forward by test_window each iteration

Metrics computed per split:
  - IS Sharpe, OOS Sharpe
  - Sharpe degradation: (OOS - IS) / IS (negative = overfitting)
  - OOS win rate vs IS win rate
  - Consistency: fraction of splits where OOS reward > 0

Overfitting flags:
  - sharpe_degradation > OOS_OVERFIT_THRESHOLD (default 0.3)
  - OOS win rate < IS win rate by > 20%
  - Fewer than 50% splits with positive OOS reward

Feature flag: WALK_FORWARD_ENABLED (default True)
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np

from meta_rl.config import (
    OOS_OVERFIT_THRESHOLD,
    OOS_SHARPE_DEGRADATION_LIMIT,
    WALK_FORWARD_ENABLED,
)
from meta_rl.types import EvaluationResult

logger = logging.getLogger(__name__)


@dataclass
class SplitMetrics:
    """Metrics for a single train/test split."""

    split_index: int
    train_start: int
    train_end: int
    test_start: int
    test_end: int

    # In-sample (train) metrics
    is_sharpe: float = 0.0
    is_pnl: float = 0.0
    is_win_rate: float = 0.0
    is_trades: int = 0
    is_reward: float = 0.0

    # Out-of-sample (test) metrics
    oos_sharpe: float = 0.0
    oos_pnl: float = 0.0
    oos_win_rate: float = 0.0
    oos_trades: int = 0
    oos_reward: float = 0.0

    # Degradation
    sharpe_degradation: float = 0.0  # fraction: (oos - is) / abs(is)
    pnl_degradation: float = 0.0

    # Overfitting flags
    is_overfit: bool = False
    overfit_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "split": self.split_index,
            "train": f"{self.train_start}:{self.train_end}",
            "test": f"{self.test_start}:{self.test_end}",
            "is_sharpe": round(self.is_sharpe, 3),
            "oos_sharpe": round(self.oos_sharpe, 3),
            "sharpe_degradation": round(self.sharpe_degradation, 3),
            "is_reward": round(self.is_reward, 4),
            "oos_reward": round(self.oos_reward, 4),
            "is_trades": self.is_trades,
            "oos_trades": self.oos_trades,
            "is_overfit": self.is_overfit,
            "reasons": self.overfit_reasons,
        }


@dataclass
class WalkForwardReport:
    """Full walk-forward analysis report."""

    n_splits: int
    splits: list[SplitMetrics]

    # Aggregate metrics
    mean_is_sharpe: float = 0.0
    mean_oos_sharpe: float = 0.0
    mean_degradation: float = 0.0

    # Consistency
    positive_oos_fraction: float = 0.0  # fraction of splits with oos_reward > 0
    consistent_splits: int = 0

    # Overfitting
    overfit_splits: int = 0
    overall_overfit_flag: bool = False
    overfit_reasons: list[str] = field(default_factory=list)

    # Recommendations
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "n_splits": self.n_splits,
            "mean_is_sharpe": round(self.mean_is_sharpe, 3),
            "mean_oos_sharpe": round(self.mean_oos_sharpe, 3),
            "mean_degradation": round(self.mean_degradation, 3),
            "positive_oos_fraction": round(self.positive_oos_fraction, 3),
            "overfit_splits": self.overfit_splits,
            "overall_overfit_flag": self.overall_overfit_flag,
            "reasons": self.overfit_reasons,
            "recommendations": self.recommendations,
            "splits": [s.to_dict() for s in self.splits],
        }

    def summary(self) -> str:
        flag = "⚠️ OVERFITTING DETECTED" if self.overall_overfit_flag else "✅ PASSED"
        return (
            f"[WFA] {flag} | "
            f"IS-Sharpe={self.mean_is_sharpe:.2f} OOS-Sharpe={self.mean_oos_sharpe:.2f} "
            f"deg={self.mean_degradation:+.2f} | "
            f"positive_OOS={self.positive_oos_fraction:.0%} | "
            f"overfit_splits={self.overfit_splits}/{self.n_splits}"
        )


class WalkForwardValidator:
    """
    Walk-forward analysis to detect overfitting in evolved strategies.

    Usage:
        validator = WalkForwardValidator(
            evaluator=evaluator,
            n_splits=5,
            train_window=100,
            test_window=20,
        )
        report = validator.validate(strategy, market_data)
        if report.overall_overfit_flag:
            print("⚠️ Strategy may be overfitting!")
    """

    def __init__(
        self,
        evaluator: Callable | None = None,
        n_splits: int = 5,
        train_window: int = 100,
        test_window: int = 20,
        overfit_threshold: float = OOS_OVERFIT_THRESHOLD,
        sharpe_degradation_limit: float = OOS_SHARPE_DEGRADATION_LIMIT,
    ):
        self.evaluator = evaluator
        self.n_splits = n_splits
        self.train_window = train_window
        self.test_window = test_window
        self.overfit_threshold = overfit_threshold
        self.sharpe_degradation_limit = sharpe_degradation_limit

    def validate(
        self,
        strategy: any,
        market_data: dict,
        ohlcv_key: str = "ohlcv",
    ) -> WalkForwardReport:
        """
        Run full walk-forward analysis on a strategy.

        Args:
            strategy: Any object with evaluate(bar_dict) → StrategyResult
            market_data: Dict with OHLCV data under ohlcv_key
            ohlcv_key: Key for OHLCV list (default "ohlcv")

        Returns:
            WalkForwardReport with per-split metrics and aggregate assessment
        """
        if not WALK_FORWARD_ENABLED:
            logger.info("[WFA] Walk-forward disabled (WALK_FORWARD_ENABLED=false)")
            return WalkForwardReport(n_splits=0, splits=[])

        ohlcv = market_data.get(ohlcv_key, [])
        total_len = len(ohlcv)
        min_required = self.train_window + self.test_window + 10

        if total_len < min_required:
            logger.warning(f"[WFA] Insufficient data: {total_len} bars (need {min_required}). Reducing splits.")
            effective_window = total_len // 3
            self.train_window = effective_window
            self.test_window = effective_window
            if total_len < 50:
                logger.warning("[WFA] Too few bars for walk-forward — returning empty report")
                return WalkForwardReport(n_splits=0, splits=[])

        splits = []
        total_len - self.train_window
        step = max(1, (total_len - self.train_window) // self.n_splits)

        for i in range(self.n_splits):
            test_start = self.train_window + i * step
            test_end = min(test_start + self.test_window, total_len)

            if test_end - test_start < 5:
                continue

            train_end = test_start
            train_start = max(0, train_end - self.train_window)

            train_data = market_data.copy()
            train_data[ohlcv_key] = ohlcv[train_start:train_end]
            test_data = market_data.copy()
            test_data[ohlcv_key] = ohlcv[test_start:test_end]

            split_metrics = self._evaluate_split(
                strategy=strategy,
                train_data=train_data,
                test_data=test_data,
                split_index=i,
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
            )
            splits.append(split_metrics)

        return self._aggregate_report(splits)

    def _evaluate_split(
        self,
        strategy: any,
        train_data: dict,
        test_data: dict,
        split_index: int,
        train_start: int,
        train_end: int,
        test_start: int,
        test_end: int,
    ) -> SplitMetrics:
        """Evaluate strategy on train and test windows."""
        ev = self.evaluator

        try:
            train_result = ev.evaluate(strategy, train_data) if ev else None
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[WFA] Train eval failed (split {split_index}): {e}")
            train_result = None

        try:
            test_result = ev.evaluate(strategy, test_data) if ev else None
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[WFA] Test eval failed (split {split_index}): {e}")
            test_result = None

        sm = SplitMetrics(
            split_index=split_index,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        )

        if isinstance(train_result, EvaluationResult):
            sm.is_sharpe = train_result.sharpe
            sm.is_pnl = train_result.risk_adjusted_pnl
            sm.is_win_rate = train_result.win_rate
            sm.is_trades = train_result.trades
            sm.is_reward = train_result.risk_adjusted_pnl

        if isinstance(test_result, EvaluationResult):
            sm.oos_sharpe = test_result.sharpe
            sm.oos_pnl = test_result.risk_adjusted_pnl
            sm.oos_win_rate = test_result.win_rate
            sm.oos_trades = test_result.trades
            sm.oos_reward = test_result.risk_adjusted_pnl

        # Degradation metrics
        if abs(sm.is_sharpe) > 1e-6:
            sm.sharpe_degradation = (sm.oos_sharpe - sm.is_sharpe) / abs(sm.is_sharpe)

        if abs(sm.is_pnl) > 1e-6:
            sm.pnl_degradation = (sm.oos_pnl - sm.is_pnl) / abs(sm.is_pnl)

        # Overfitting flags
        reasons = []
        if sm.sharpe_degradation < -self.overfit_threshold:
            reasons.append(f"Sharpe degradation {sm.sharpe_degradation:.2f} exceeds -{self.overfit_threshold:.2f}")
        if sm.oos_sharpe < self.sharpe_degradation_limit and sm.is_sharpe > sm.oos_sharpe * 2:
            reasons.append(f"OOS Sharpe {sm.oos_sharpe:.2f} << IS Sharpe {sm.is_sharpe:.2f}")
        if sm.oos_win_rate < sm.is_win_rate - 0.2:
            reasons.append(f"OOS win rate {sm.oos_win_rate:.0%} << IS {sm.is_win_rate:.0%}")
        if sm.oos_trades < 3:
            reasons.append(f"Too few OOS trades ({sm.oos_trades})")

        sm.overfit_reasons = reasons
        sm.is_overfit = bool(reasons)

        return sm

    def _aggregate_report(self, splits: list[SplitMetrics]) -> WalkForwardReport:
        """Aggregate per-split metrics into a full report."""
        if not splits:
            return WalkForwardReport(n_splits=0, splits=[])

        n = len(splits)
        mean_is = float(np.mean([s.is_sharpe for s in splits]))
        mean_oos = float(np.mean([s.oos_sharpe for s in splits]))
        mean_deg = float(np.mean([s.sharpe_degradation for s in splits]))

        positive_oos = sum(1 for s in splits if s.oos_reward > 0)
        overfit_count = sum(1 for s in splits if s.is_overfit)

        overall_flag = overfit_count > n // 2 or mean_deg < -self.overfit_threshold

        all_reasons: dict[str, int] = {}
        for s in splits:
            for r in s.overfit_reasons:
                all_reasons[r] = all_reasons.get(r, 0) + 1

        recommendations = []
        if mean_deg < -0.3:
            recommendations.append("HIGH_PRIORITY: Reduce crossover_rate — strategy is overfitting to train data")
        if positive_oos < n * 0.5:
            recommendations.append("Strategy fails on OOS — increase regularization or reduce population complexity")
        if overfit_count > n * 0.5:
            recommendations.append("Majority of splits overfit — consider simpler strategy chromosome (fewer genes)")

        report = WalkForwardReport(
            n_splits=n,
            splits=splits,
            mean_is_sharpe=mean_is,
            mean_oos_sharpe=mean_oos,
            mean_degradation=mean_deg,
            positive_oos_fraction=positive_oos / n,
            consistent_splits=positive_oos,
            overfit_splits=overfit_count,
            overall_overfit_flag=overall_flag,
            overfit_reasons=list(all_reasons.keys()),
            recommendations=recommendations,
        )

        logger.info(f"[WFA] {report.summary()}")
        return report


def run_walkforward_on_elites(
    elites: list,
    evaluator: any,
    market_data: dict,
    n_splits: int = 5,
) -> dict[str, WalkForwardReport]:
    """
    Run walk-forward analysis on all elite strategies.

    Returns a dict mapping strategy_id → WalkForwardReport.
    Strategies flagged as overfitting are annotated.
    """
    results = {}
    for scored in elites:
        strategy_id = scored.id if hasattr(scored, "id") else str(id(scored))
        try:
            report = WalkForwardValidator(
                evaluator=evaluator,
                n_splits=n_splits,
            ).validate(scored.strategy, market_data)

            # Annotate the scored strategy
            if hasattr(scored, "evaluation") and scored.evaluation:
                scored.evaluation.overfit_report = report

            results[strategy_id] = report
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[WFA] Elite {strategy_id} failed: {e}")

    return results
