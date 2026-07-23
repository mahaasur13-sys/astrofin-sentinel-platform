"""meta_rl/reward.py — ATOM-META-RL-004: Risk-Adjusted Reward Function"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass

import numpy as np

from meta_rl.types import EvaluationResult

logger = logging.getLogger(__name__)


@dataclass
class RewardConfig:
    """
    Weights for multi-component risk-adjusted reward function.

    ATOM-META-RL-004: All pnl components MUST use risk_adjusted_pnl,
    not the raw pnl field. The reward function is the single source of
    truth for strategy selection.
    """

    # ── Component weights ────────────────────────────────────────────────
    sharpe_weight: float = 0.45
    pnl_weight: float = 0.30  # MUST be risk_adjusted_pnl (ATOM-META-RL-004)
    drawdown_penalty_scale: float = 2.5  # increased from 2.0 (ATOM-META-RL-004)
    execution_cost_weight: float = 0.10
    stability_bonus_scale: float = 0.20
    min_trades_for_stability: int = 5
    base_reward: float = 0.0

    # ── Hard constraints ────────────────────────────────────────────────
    min_trades: int = 5
    max_drawdown_soft: float = 0.50  # soft cap, heavy penalty above

    def __post_init__(self):
        # Weights must sum to ~1.0 (normalised)
        total = self.sharpe_weight + self.pnl_weight + self.execution_cost_weight
        if abs(total - 1.0) > 0.01:
            norm = total
            self.sharpe_weight /= norm
            self.pnl_weight /= norm
            self.execution_cost_weight /= norm


class RewardCalculator:
    """
    Computes scalar reward from EvaluationResult using ONLY risk-adjusted metrics.

    ATOM-META-RL-004 invariant:
        reward = f(risk_adjusted_pnl, sharpe, adjusted_drawdown, ...)
        NOT:  reward = f(raw_pnl, ...)

    Components:
        - sharpe: risk-adjusted returns (capped, shaped)
        - pnl: risk_adjusted_pnl from RiskEngineV2 (MANDATORY)
        - drawdown: adjusted_drawdown from RiskEngineV2 (MANDATORY)
        - execution_cost: transaction cost penalty
        - stability: consistency bonus
    """

    def __init__(self, config: RewardConfig | None = None):
        self.config = config or RewardConfig()

    def compute(self, result: EvaluationResult) -> float:
        """
        Compute scalar reward from evaluation result.

        ATOM-META-RL-004: Uses ONLY risk-adjusted fields.
        Raw pnl is NEVER used in the reward computation.
        """
        try:
            cfg = self.config

            # ── Hard constraints ──────────────────────────────────────────
            if result.trades < cfg.min_trades:
                logger.debug(f"[META-RL] Reward=0: only {result.trades} trades (min={cfg.min_trades})")
                return cfg.base_reward

            if math.isnan(result.risk_adjusted_pnl) or math.isinf(result.risk_adjusted_pnl):
                return cfg.base_reward

            # ── 1. Sharpe component ─────────────────────────────────────────
            sharpe_comp = self._sharpe_component(result.sharpe)

            # ── 2. PnL component — RISK-ADJUSTED (ATOM-META-RL-004) ───────
            pnl_comp = self._pnl_component(result.risk_adjusted_pnl)

            # ── 3. Drawdown penalty — ADJUSTED_DRAWDOWN (ATOM-META-RL-004) ──
            adj_dd = result.adjusted_drawdown if result.adjusted_drawdown is not None else result.max_drawdown
            dd_penalty = self._drawdown_penalty(adj_dd)

            # ── 4. Execution cost penalty ───────────────────────────────────
            cost_penalty = self._execution_cost_penalty(result.execution_cost)

            # ── 5. Stability bonus ──────────────────────────────────────────
            stability = self._stability_bonus(result)

            reward = (
                cfg.base_reward
                + cfg.sharpe_weight * sharpe_comp
                + cfg.pnl_weight * pnl_comp
                - dd_penalty
                - cfg.execution_cost_weight * cost_penalty
                + stability
            )

            # ── Hard drawdown ceiling ──────────────────────────────────────
            if adj_dd > cfg.max_drawdown_soft:
                reward -= (adj_dd - cfg.max_drawdown_soft) * 10

            # Clamp to prevent extreme values
            reward = float(np.clip(reward, -1000.0, 1000.0))

            if math.isnan(reward) or math.isinf(reward):
                return cfg.base_reward

            return reward

        except Exception as e:
            logger.warning(f"[META-RL] Reward computation failed: {e}")
            return self.config.base_reward

    def _sharpe_component(self, sharpe: float) -> float:
        """Map Sharpe ratio to reward. Cap at 5.0 (diminishing returns)."""
        if math.isnan(sharpe) or math.isinf(sharpe):
            return 0.0
        capped = float(np.clip(sharpe, -5.0, 5.0))
        return 1.0 / (1.0 + math.exp(-capped * 0.5))

    def _pnl_component(self, risk_adj_pnl: float) -> float:
        """
        Normalize risk-adjusted PnL. 100% return -> 1.0, -100% -> 0.0.

        ATOM-META-RL-004: This receives risk_adjusted_pnl, NOT raw pnl.
        """
        if math.isnan(risk_adj_pnl) or math.isinf(risk_adj_pnl):
            return 0.0
        normalized = float(np.clip((risk_adj_pnl + 1.0) / 2.0, 0.0, 1.0))
        return normalized

    def _drawdown_penalty(self, adjusted_dd: float) -> float:
        """
        Quadratic penalty for adjusted drawdown.
        ATOM-META-RL-004: Uses adjusted_drawdown (already penalised by RiskEngineV2).
        """
        if math.isnan(adjusted_dd) or math.isinf(adjusted_dd):
            return 0.5
        dd = float(np.clip(adjusted_dd, 0.0, 1.0))
        return self.config.drawdown_penalty_scale * (dd**2)

    def _execution_cost_penalty(self, cost: float) -> float:
        """Penalty proportional to round-trip cost as fraction of capital."""
        if math.isnan(cost) or math.isinf(cost):
            return 0.0
        return float(np.clip(cost, 0.0, 1.0))

    def _stability_bonus(self, result: EvaluationResult) -> float:
        """
        Bonus for consistent performance across many trades.
        Rewards high win_rate * moderate trade count.
        """
        cfg = self.config
        if result.trades < cfg.min_trades_for_stability:
            return 0.0

        wr = float(np.clip(result.win_rate, 0.0, 1.0))
        trade_factor = min(result.trades / 20.0, 1.0)

        bonus = cfg.stability_bonus_scale * wr * trade_factor
        return float(np.clip(bonus, 0.0, cfg.stability_bonus_scale))

    def summary(self, result: EvaluationResult) -> dict:
        """
        Return detailed breakdown of reward components.

        ATOM-META-RL-004: All pnl/dd values are risk-adjusted.
        """
        cfg = self.config
        adj_dd = result.adjusted_drawdown if result.adjusted_drawdown is not None else result.max_drawdown
        return {
            "sharpe_comp": cfg.sharpe_weight * self._sharpe_component(result.sharpe),
            "pnl_comp": cfg.pnl_weight * self._pnl_component(result.risk_adjusted_pnl),
            "dd_penalty": self._drawdown_penalty(adj_dd),
            "cost_penalty": cfg.execution_cost_weight * self._execution_cost_penalty(result.execution_cost),
            "stability_bonus": self._stability_bonus(result),
            "risk_adj_pnl_used": result.risk_adjusted_pnl,
            "raw_pnl_available_but_not_used": result.pnl,
            "total": self.compute(result),
        }
