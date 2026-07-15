"""meta_rl/reward.py — ATOM-META-RL-004: Risk-Adjusted Reward Function

This module implements the canonical risk-adjusted scalar reward used by
the meta-RL layer to rank and select strategies.

Design contract
---------------
* The reward is computed **exclusively** from risk-adjusted metrics
  (``risk_adjusted_pnl``, ``adjusted_drawdown``) — never from raw ``pnl``
  or ``max_drawdown`` (ATOM-META-RL-004).
* All numeric "magic constants" (caps, normalisers, penalties) live in
  :class:`RewardConfig` and can be tuned per-deployment without changing
  the formula. The constants are documented inline with their rationale.
* :func:`RewardCalculator.compute` is a thin orchestration layer: all
  heavy lifting is delegated to private component methods so the
  orchestration complexity stays low (target cyclomatic complexity ≤ 4).

Formula
-------
    reward = base
           + w_sharpe   * sharpe_component(sharpe)
           + w_pnl      * pnl_component(risk_adjusted_pnl)
           - drawdown_penalty(adjusted_drawdown)
           - w_cost     * execution_cost_penalty(execution_cost)
           + stability_bonus(trades, win_rate)
           - hard_dd_ceiling_penalty(adjusted_drawdown)

with a final hard clamp to ``[reward_clip_min, reward_clip_max]``.
"""

from __future__ import annotations

import logging
import math
import warnings
from dataclasses import dataclass

import numpy as np

from meta_rl.types import EvaluationResult

logger = logging.getLogger(__name__)


@dataclass
class RewardConfig:
    """
    Tunable parameters for the multi-component risk-adjusted reward.

    Component weights
    ~~~~~~~~~~~~~~~~~
    The three "primary" weights (``sharpe_weight``, ``pnl_weight``,
    ``execution_cost_weight``) are expected to sum to ~1.0. When they
    don't, :meth:`__post_init__` issues a :mod:`warnings` warning and
    silently re-normalises them so existing callers keep working.

    Notes
    -----
    ATOM-META-RL-004: All pnl components MUST use ``risk_adjusted_pnl``,
    not the raw ``pnl`` field. The reward function is the single source
    of truth for strategy selection.
    """

    # ── Component weights (expected to sum to 1.0) ──────────────────────
    # Default values are tuned so that the three "primary" weights
    # sum to exactly 1.0 and no renormalisation warning fires.
    sharpe_weight: float = 0.55
    pnl_weight: float = 0.30  # applies to risk_adjusted_pnl (ATOM-META-RL-004)
    execution_cost_weight: float = 0.15

    # ── Penalty / bonus scales ──────────────────────────────────────────
    drawdown_penalty_scale: float = 2.5  # quadratic on adjusted_drawdown
    stability_bonus_scale: float = 0.10  # max bonus magnitude
    min_trades_for_stability: int = 5
    base_reward: float = 0.0

    # ── Hard constraints ────────────────────────────────────────────────
    min_trades: int = 5
    max_drawdown_soft: float = 0.50  # soft cap; extra penalty above this

    # ── Component shaping constants (formerly inline magic numbers) ─────
    # Sharpe: clipped to ±sharpe_clip, then passed through a logistic
    # with steepness ``sigmoid_steepness``.
    sharpe_clip: float = 5.0
    sigmoid_steepness: float = 0.5

    # PnL: linear map from ``[pnl_normalize_min, pnl_normalize_max]`` to
    # ``[0, 1]`` then clipped. Defaults encode "100 % loss -> 0",
    # "100 % gain -> 1", "break-even -> 0.5".
    pnl_normalize_min: float = -1.0
    pnl_normalize_max: float = 1.0

    # Drawdown: penalty for NaN/Inf input (defensive fallback).
    drawdown_penalty_fallback: float = 0.5

    # Execution cost: clipped to ``[0, 1]`` (a cost as a fraction of
    # capital cannot exceed 100 % of the position size).
    execution_cost_clip: float = 1.0

    # Stability bonus: trade-count term saturates at this many trades.
    stability_trade_norm: float = 20.0

    # Hard drawdown ceiling: extra per-unit penalty once
    # ``adjusted_drawdown > max_drawdown_soft``.
    hard_dd_extra_penalty: float = 10.0

    # Final reward clamp — defends the RL optimiser from extreme outliers.
    reward_clip_min: float = -1000.0
    reward_clip_max: float = 1000.0

    def __post_init__(self) -> None:
        # Weights must sum to ~1.0. If not, warn and silently renormalise
        # so behaviour stays backward-compatible with callers that pass
        # weights summing to e.g. 0.9 or 1.1.
        total = self.sharpe_weight + self.pnl_weight + self.execution_cost_weight
        if abs(total - 1.0) > 0.01:
            warnings.warn(
                f"RewardConfig weights sum to {total:.4f}, expected 1.0 "
                f"(±0.01). Renormalising sharpe/pnl/execution_cost weights "
                f"to maintain relative proportions.",
                stacklevel=2,
            )
            norm = total
            self.sharpe_weight /= norm
            self.pnl_weight /= norm
            self.execution_cost_weight /= norm


class RewardCalculator:
    """
    Computes a scalar reward from an :class:`EvaluationResult` using
    **only** risk-adjusted metrics.

    ATOM-META-RL-004 invariant
    --------------------------
        reward = f(risk_adjusted_pnl, sharpe, adjusted_drawdown, ...)
        NOT:  reward = f(raw_pnl, ...)

    Components
    ~~~~~~~~~~
    * **sharpe** — risk-adjusted returns, clipped and squashed by a
      logistic so extreme values contribute diminishing returns.
    * **pnl** — linear normalisation of ``risk_adjusted_pnl`` from
      ``[pnl_normalize_min, pnl_normalize_max]`` to ``[0, 1]``.
    * **drawdown** — quadratic penalty on ``adjusted_drawdown``
      (already penalised upstream by ``RiskEngineV2``).
    * **execution_cost** — direct cost penalty, clipped to ``[0, 1]``.
    * **stability** — bonus for high win-rate × many trades,
      saturating at ``stability_trade_norm`` trades.
    * **hard ceiling** — extra per-unit penalty once
      ``adjusted_drawdown > max_drawdown_soft``.

    The orchestration in :meth:`compute` is intentionally thin (target
    cyclomatic complexity ≤ 4) so that future changes — e.g. swapping
    the logistic for a tanh, or adding a turnover term — are local.
    """

    def __init__(self, config: RewardConfig | None = None) -> None:
        self.config = config or RewardConfig()

    # ── Public API ───────────────────────────────────────────────────────

    def compute(self, result: EvaluationResult) -> float:
        """
        Compute the scalar reward for ``result``.

        Returns ``config.base_reward`` (default ``0.0``) for invalid
        inputs, for the safety short-circuits, and for any unexpected
        exception in component evaluation. Never raises.
        """
        try:
            short_circuit = self._validate(result)
            if short_circuit is not None:
                return short_circuit

            cfg = self.config
            adj_dd = (
                result.adjusted_drawdown
                if result.adjusted_drawdown is not None
                else result.max_drawdown
            )

            reward = (
                cfg.base_reward
                + cfg.sharpe_weight * self._sharpe_component(result.sharpe)
                + cfg.pnl_weight * self._pnl_component(result.risk_adjusted_pnl)
                - self._drawdown_penalty(adj_dd)
                - cfg.execution_cost_weight
                * self._execution_cost_penalty(result.execution_cost)
                + self._stability_bonus(result)
                - self._hard_dd_ceiling_penalty(adj_dd)
            )

            return self._combine(reward)

        except Exception as exc:  # noqa: BLE001 — reward is best-effort
            logger.warning("[META-RL] Reward computation failed: %s", exc)
            return self.config.base_reward

    def summary(self, result: EvaluationResult) -> dict:
        """
        Return a detailed breakdown of reward components.

        All pnl/dd values are risk-adjusted (ATOM-META-RL-004).
        """
        cfg = self.config
        adj_dd = (
            result.adjusted_drawdown
            if result.adjusted_drawdown is not None
            else result.max_drawdown
        )
        return {
            "sharpe_comp": cfg.sharpe_weight * self._sharpe_component(result.sharpe),
            "pnl_comp": cfg.pnl_weight * self._pnl_component(result.risk_adjusted_pnl),
            "dd_penalty": self._drawdown_penalty(adj_dd),
            "cost_penalty": cfg.execution_cost_weight
            * self._execution_cost_penalty(result.execution_cost),
            "stability_bonus": self._stability_bonus(result),
            "hard_dd_ceiling_penalty": self._hard_dd_ceiling_penalty(adj_dd),
            "risk_adj_pnl_used": result.risk_adjusted_pnl,
            "raw_pnl_available_but_not_used": result.pnl,
            "total": self.compute(result),
        }

    # ── Validation & finalisation ───────────────────────────────────────

    def _validate(self, result: EvaluationResult) -> float | None:
        """
        Pre-flight check on ``result``.

        Returns ``base_reward`` for inputs that should bypass the
        component pipeline (too few trades, non-finite pnl). Returns
        ``None`` to signal "OK, proceed with full computation".
        """
        cfg = self.config

        if result.trades < cfg.min_trades:
            logger.debug(
                "[META-RL] Reward=0: only %d trades (min=%d)",
                result.trades,
                cfg.min_trades,
            )
            return cfg.base_reward

        if math.isnan(result.risk_adjusted_pnl) or math.isinf(result.risk_adjusted_pnl):
            return cfg.base_reward

        return None

    def _combine(self, reward: float) -> float:
        """Clamp to ``[reward_clip_min, reward_clip_max]`` and guard NaN/Inf."""
        clipped = float(
            np.clip(reward, self.config.reward_clip_min, self.config.reward_clip_max)
        )
        if math.isnan(clipped) or math.isinf(clipped):
            return self.config.base_reward
        return clipped

    # ── Components ──────────────────────────────────────────────────────

    def _sharpe_component(self, sharpe: float) -> float:
        """
        Map Sharpe ratio to ``[0, 1]`` via a logistic.

            f(s) = 1 / (1 + exp(-steepness * clip(s, ±sharpe_clip)))

        The logistic is preferred over a linear map because it gives
        diminishing returns for very high Sharpe values, which is
        desirable when comparing many strategies (avoids the optimiser
        chasing outliers).
        """
        cfg = self.config
        if math.isnan(sharpe) or math.isinf(sharpe):
            return 0.0
        capped = float(np.clip(sharpe, -cfg.sharpe_clip, cfg.sharpe_clip))
        return 1.0 / (1.0 + math.exp(-capped * cfg.sigmoid_steepness))

    def _pnl_component(self, risk_adj_pnl: float) -> float:
        """
        Linear normalisation of risk-adjusted PnL to ``[0, 1]``.

            f(p) = clip((p - pnl_normalize_min)
                        / (pnl_normalize_max - pnl_normalize_min), 0, 1)

        ATOM-META-RL-004: ``risk_adj_pnl`` is mandatory, raw ``pnl`` is
        never used here.
        """
        cfg = self.config
        if math.isnan(risk_adj_pnl) or math.isinf(risk_adj_pnl):
            return 0.0
        span = cfg.pnl_normalize_max - cfg.pnl_normalize_min
        if span <= 0:
            return 0.0
        normalized = (risk_adj_pnl - cfg.pnl_normalize_min) / span
        return float(np.clip(normalized, 0.0, 1.0))

    def _drawdown_penalty(self, adjusted_dd: float) -> float:
        """
        Quadratic penalty on adjusted drawdown.

            f(d) = drawdown_penalty_scale * clip(d, 0, 1) ** 2

        ATOM-META-RL-004: ``adjusted_dd`` is the drawdown already
        penalised upstream by ``RiskEngineV2`` (e.g. for tail risk); we
        do **not** apply the penalty twice on the same value — instead
        the upstream adjustment is folded into the metric.
        """
        cfg = self.config
        if math.isnan(adjusted_dd) or math.isinf(adjusted_dd):
            return cfg.drawdown_penalty_fallback
        dd = float(np.clip(adjusted_dd, 0.0, 1.0))
        return cfg.drawdown_penalty_scale * (dd**2)

    def _execution_cost_penalty(self, cost: float) -> float:
        """
        Penalty proportional to round-trip cost as fraction of capital,
        clipped to ``[0, execution_cost_clip]``.
        """
        cfg = self.config
        if math.isnan(cost) or math.isinf(cost):
            return 0.0
        return float(np.clip(cost, 0.0, cfg.execution_cost_clip))

    def _stability_bonus(self, result: EvaluationResult) -> float:
        """
        Bonus for consistent performance across many trades.

            bonus = stability_bonus_scale
                  * clip(win_rate, 0, 1)
                  * min(trades / stability_trade_norm, 1)

        The trade-count term saturates at ``stability_trade_norm``
        trades so the bonus does not grow unbounded for very active
        strategies.
        """
        cfg = self.config
        if result.trades < cfg.min_trades_for_stability:
            return 0.0

        wr = float(np.clip(result.win_rate, 0.0, 1.0))
        trade_factor = min(result.trades / cfg.stability_trade_norm, 1.0)
        bonus = cfg.stability_bonus_scale * wr * trade_factor
        return float(np.clip(bonus, 0.0, cfg.stability_bonus_scale))

    def _hard_dd_ceiling_penalty(self, adjusted_dd: float) -> float:
        """
        Extra linear penalty once ``adjusted_dd`` exceeds the soft cap.

            f(d) = max(0, d - max_drawdown_soft) * hard_dd_extra_penalty

        This is the "circuit breaker" for strategies whose drawdown has
        blown past the soft cap — every additional point of drawdown
        costs ``hard_dd_extra_penalty`` reward units.
        """
        cfg = self.config
        if math.isnan(adjusted_dd) or math.isinf(adjusted_dd):
            return 0.0
        over = adjusted_dd - cfg.max_drawdown_soft
        if over <= 0:
            return 0.0
        return over * cfg.hard_dd_extra_penalty
