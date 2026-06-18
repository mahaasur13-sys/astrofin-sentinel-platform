"""meta_rl/test_reward.py — Golden tests for RewardCalculator.

Golden tests that pin exact (or near-exact) numeric values for the
reward pipeline so any silent regression in the formula is caught
immediately. Values are derived from the closed-form definitions in
``meta_rl/reward.py`` — see that module's docstrings for the formulas.

Conventions
-----------
* Tolerances are explicit. ``float`` arithmetic uses ``math.isclose``
  with ``abs_tol=1e-9``.
* Component-level tests construct the calculator directly.
* Pipeline-level tests construct ``EvaluationResult`` with the full
  set of ATOM-META-RL-004 fields.
"""

from __future__ import annotations

import math
import warnings

import pytest

from meta_rl.reward import RewardCalculator, RewardConfig
from meta_rl.types import EvaluationResult


def _make_result(
    *,
    trades: int = 10,
    sharpe: float = 0.0,
    risk_adjusted_pnl: float = 0.0,
    adjusted_drawdown: float | None = 0.0,
    max_drawdown: float = 0.0,
    execution_cost: float = 0.0,
    win_rate: float = 0.5,
) -> EvaluationResult:
    """Build an EvaluationResult with ATOM-META-RL-004 fields populated."""
    return EvaluationResult(
        trades=trades,
        sharpe=sharpe,
        risk_adjusted_pnl=risk_adjusted_pnl,
        adjusted_drawdown=adjusted_drawdown,
        max_drawdown=max_drawdown,
        execution_cost=execution_cost,
        win_rate=win_rate,
    )


# ─── RewardConfig ─────────────────────────────────────────────────────────────


class TestRewardConfig:
    """RewardConfig invariants and warning behaviour."""

    def test_default_weights_sum_to_one(self):
        """Vanilla RewardConfig() must have weights summing to 1.0 exactly.

        Without this, ``__post_init__`` would warn every time the default
        config is used, which would pollute test output and signal
        "broken default" to downstream callers.
        """
        cfg = RewardConfig()
        total = cfg.sharpe_weight + cfg.pnl_weight + cfg.execution_cost_weight
        assert math.isclose(total, 1.0, abs_tol=1e-12)

    def test_default_construction_emits_no_warning(self):
        """Constructing RewardConfig() must not warn."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            RewardConfig()
        reward_warnings = [
            w for w in caught if "RewardConfig" in str(w.message)
        ]
        assert reward_warnings == [], (
            f"Default RewardConfig unexpectedly warned: "
            f"{[str(w.message) for w in reward_warnings]}"
        )

    def test_misweighted_construction_warns_and_renormalises(self):
        """Off-sum weights must warn (UserWarning) and renormalise."""
        with pytest.warns(UserWarning, match="RewardConfig"):
            cfg = RewardConfig(
                sharpe_weight=0.40,
                pnl_weight=0.30,
                execution_cost_weight=0.20,  # total = 0.90
            )
        total = (
            cfg.sharpe_weight
            + cfg.pnl_weight
            + cfg.execution_cost_weight
        )
        assert math.isclose(total, 1.0, abs_tol=1e-12)
        # Relative proportions preserved.
        assert math.isclose(
            cfg.sharpe_weight / cfg.pnl_weight, 0.40 / 0.30,
            abs_tol=1e-12,
        )
        assert math.isclose(
            cfg.pnl_weight / cfg.execution_cost_weight, 0.30 / 0.20,
            abs_tol=1e-12,
        )

    def test_within_tolerance_no_warning(self):
        """Weights within ±0.01 of 1.0 must NOT warn."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            RewardConfig(
                sharpe_weight=0.55,
                pnl_weight=0.30,
                execution_cost_weight=0.155,  # total = 1.005
            )
        reward_warnings = [
            w for w in caught if "RewardConfig" in str(w.message)
        ]
        assert reward_warnings == [], (
            f"Sum 1.005 (within tolerance) should not warn, got: "
            f"{[str(w.message) for w in reward_warnings]}"
        )


# ─── Component-level golden tests ────────────────────────────────────────────


class TestSharpeComponent:
    """_sharpe_component: logistic over clipped Sharpe."""

    def test_zero_sharpe_returns_half(self):
        calc = RewardCalculator()
        assert math.isclose(calc._sharpe_component(0.0), 0.5, abs_tol=1e-12)

    def test_positive_sharpe_above_half(self):
        calc = RewardCalculator()
        assert calc._sharpe_component(1.0) > 0.5

    def test_negative_sharpe_below_half(self):
        calc = RewardCalculator()
        assert calc._sharpe_component(-1.0) < 0.5

    def test_cap_at_sharpe_clip(self):
        calc = RewardCalculator()
        at_clip = calc._sharpe_component(calc.config.sharpe_clip)
        above_clip = calc._sharpe_component(calc.config.sharpe_clip + 100.0)
        assert math.isclose(at_clip, above_clip, abs_tol=1e-12)

    def test_nan_returns_zero(self):
        calc = RewardCalculator()
        assert calc._sharpe_component(float("nan")) == 0.0

    def test_inf_returns_zero(self):
        calc = RewardCalculator()
        assert calc._sharpe_component(float("inf")) == 0.0

    def test_logistic_formula(self):
        """Closed-form: 1 / (1 + exp(-steepness * clip(s, ±clip)))."""
        cfg = RewardConfig()
        calc = RewardCalculator(cfg)
        s = 2.0
        expected = 1.0 / (1.0 + math.exp(-cfg.sigmoid_steepness * s))
        assert math.isclose(calc._sharpe_component(s), expected, abs_tol=1e-12)


class TestPnlComponent:
    """_pnl_component: linear map of risk_adjusted_pnl to [0, 1]."""

    def test_break_even_returns_half(self):
        calc = RewardCalculator()
        assert math.isclose(calc._pnl_component(0.0), 0.5, abs_tol=1e-12)

    def test_full_loss_returns_zero(self):
        calc = RewardCalculator()
        assert math.isclose(calc._pnl_component(-1.0), 0.0, abs_tol=1e-12)

    def test_full_gain_returns_one(self):
        calc = RewardCalculator()
        assert math.isclose(calc._pnl_component(1.0), 1.0, abs_tol=1e-12)

    def test_clip_below_floor(self):
        calc = RewardCalculator()
        assert calc._pnl_component(-5.0) == 0.0

    def test_clip_above_ceiling(self):
        calc = RewardCalculator()
        assert calc._pnl_component(5.0) == 1.0

    def test_nan_returns_zero(self):
        calc = RewardCalculator()
        assert calc._pnl_component(float("nan")) == 0.0


class TestDrawdownPenalty:
    """_drawdown_penalty: scale * dd^2 with NaN/Inf fallback."""

    def test_zero_dd_returns_zero(self):
        calc = RewardCalculator()
        assert calc._drawdown_penalty(0.0) == 0.0

    def test_full_dd_returns_scale(self):
        calc = RewardCalculator()
        assert math.isclose(
            calc._drawdown_penalty(1.0),
            calc.config.drawdown_penalty_scale,
            abs_tol=1e-12,
        )

    def test_half_dd_returns_quarter_scale(self):
        """Quadratic: dd = 0.5 → scale * 0.25."""
        calc = RewardCalculator()
        assert math.isclose(
            calc._drawdown_penalty(0.5),
            calc.config.drawdown_penalty_scale * 0.25,
            abs_tol=1e-12,
        )

    def test_nan_returns_fallback(self):
        calc = RewardCalculator()
        assert math.isclose(
            calc._drawdown_penalty(float("nan")),
            calc.config.drawdown_penalty_fallback,
            abs_tol=1e-12,
        )

    def test_inf_returns_fallback(self):
        calc = RewardCalculator()
        assert math.isclose(
            calc._drawdown_penalty(float("inf")),
            calc.config.drawdown_penalty_fallback,
            abs_tol=1e-12,
        )


class TestExecutionCostPenalty:
    """_execution_cost_penalty: clipped cost."""

    def test_zero_cost_returns_zero(self):
        calc = RewardCalculator()
        assert calc._execution_cost_penalty(0.0) == 0.0

    def test_full_cost_returns_one(self):
        calc = RewardCalculator()
        assert math.isclose(calc._execution_cost_penalty(1.0), 1.0, abs_tol=1e-12)

    def test_clip_above_one(self):
        calc = RewardCalculator()
        assert calc._execution_cost_penalty(2.5) == 1.0

    def test_negative_cost_clipped_to_zero(self):
        calc = RewardCalculator()
        assert calc._execution_cost_penalty(-0.5) == 0.0

    def test_nan_returns_zero(self):
        calc = RewardCalculator()
        assert calc._execution_cost_penalty(float("nan")) == 0.0


class TestStabilityBonus:
    """_stability_bonus: trade-count * win-rate saturation."""

    def test_below_threshold_returns_zero(self):
        calc = RewardCalculator()
        result = _make_result(trades=calc.config.min_trades_for_stability - 1)
        assert calc._stability_bonus(result) == 0.0

    def test_at_threshold_zero_win_rate(self):
        """trades == threshold, win_rate = 0 → 0 bonus."""
        calc = RewardCalculator()
        result = _make_result(
            trades=calc.config.min_trades_for_stability,
            win_rate=0.0,
        )
        assert calc._stability_bonus(result) == 0.0

    def test_at_saturation(self):
        """trades >= stability_trade_norm and win_rate = 1 → full bonus."""
        calc = RewardCalculator()
        result = _make_result(
            trades=int(calc.config.stability_trade_norm),
            win_rate=1.0,
        )
        assert math.isclose(
            calc._stability_bonus(result),
            calc.config.stability_bonus_scale,
            abs_tol=1e-12,
        )

    def test_linear_trade_factor(self):
        """Half saturation in trades → half the bonus (with full win_rate)."""
        calc = RewardCalculator()
        result = _make_result(
            trades=int(calc.config.stability_trade_norm / 2),
            win_rate=1.0,
        )
        expected = calc.config.stability_bonus_scale * 0.5
        assert math.isclose(
            calc._stability_bonus(result), expected, abs_tol=1e-12
        )


# ─── Pipeline-level golden tests ─────────────────────────────────────────────


class TestComputeGolden:
    """End-to-end ``compute()`` golden values."""

    def test_neutral_inputs(self):
        """All-zero inputs → sharpe=0.5, pnl=0.5, dd_pen=0, cost=0,
        stability=scale*0.5*min(10/20,1) = 0.05.

        Default weights sum to 1.0 (no normalisation).

        reward = 0 + 0.55*0.5 + 0.30*0.5 - 0 - 0.15*0 + 0.05
               = 0.275 + 0.150 + 0.05 = 0.475
        """
        calc = RewardCalculator()
        result = _make_result(trades=10)
        expected = (
            0.55 * 0.5
            + 0.30 * 0.5
            - 0.0
            - 0.15 * 0.0
            + 0.10 * 0.5 * (10 / 20)
        )
        assert math.isclose(calc.compute(result), expected, abs_tol=1e-9)

    def test_clip_ceiling(self):
        """reward > reward_clip_max is clipped down to the ceiling.

        The default per-component bounds cap the natural maximum at
        ~0.91, so we double the weights (still summing to 1.0 after
        renormalisation) to push the raw reward above the clamp.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cfg = RewardConfig(
                reward_clip_min=-1.0,
                reward_clip_max=1.0,
                sharpe_weight=1.10,
                pnl_weight=0.60,
                execution_cost_weight=0.30,  # raw sum = 2.0, renormalised
                stability_bonus_scale=0.50,
            )
            calc = RewardCalculator(cfg)
            result = EvaluationResult(
                trades=1000,
                sharpe=cfg.sharpe_clip,
                risk_adjusted_pnl=cfg.pnl_normalize_max,
                max_drawdown=0.0,
                adjusted_drawdown=0.0,
                execution_cost=0.0,
                win_rate=1.0,
            )
        assert calc.compute(result) == pytest.approx(1.0, abs=1e-9)

    def test_clip_floor(self):
        """reward < reward_clip_min is clipped up to the floor.

        Symmetric counterpart of test_clip_ceiling: boost weights so
        the raw reward drops below -1.0, then assert the clamp fires.
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cfg = RewardConfig(
                reward_clip_min=-1.0,
                reward_clip_max=1.0,
                sharpe_weight=1.10,
                pnl_weight=0.60,
                execution_cost_weight=0.30,
                stability_bonus_scale=0.50,
                drawdown_penalty_scale=2.5,
            )
            calc = RewardCalculator(cfg)
            result = EvaluationResult(
                trades=1000,
                sharpe=-cfg.sharpe_clip,
                risk_adjusted_pnl=cfg.pnl_normalize_min,
                max_drawdown=1.0,
                adjusted_drawdown=1.0,
                execution_cost=1.0,
                win_rate=0.0,
            )
        assert calc.compute(result) == pytest.approx(-1.0, abs=1e-9)

    def test_few_trades_returns_base(self):
        """trades < min_trades → base_reward (0.0)."""
        calc = RewardCalculator()
        result = _make_result(trades=calc.config.min_trades - 1)
        assert calc.compute(result) == calc.config.base_reward

    def test_nan_risk_adjusted_pnl_returns_base(self):
        calc = RewardCalculator()
        result = _make_result(risk_adjusted_pnl=float("nan"))
        assert calc.compute(result) == calc.config.base_reward

    def test_uses_adjusted_not_raw_drawdown(self):
        """When adjusted_drawdown is None, fall back to max_drawdown.

        With adjusted_drawdown = 0.3 → dd_pen = 2.5 * 0.09 = 0.225
        """
        calc = RewardCalculator()
        result_with_adj = _make_result(adjusted_drawdown=0.3, max_drawdown=0.9)
        result_without_adj = _make_result(adjusted_drawdown=None, max_drawdown=0.3)
        assert math.isclose(
            calc.compute(result_with_adj),
            calc.compute(result_without_adj),
            abs_tol=1e-9,
        )

    def test_hard_dd_ceiling_applied(self):
        """dd > max_drawdown_soft adds extra penalty * (dd - soft).

        Build two configs that differ ONLY in max_drawdown_soft so the
        delta isolates the ceiling term.
        """
        base_cfg = RewardConfig()
        soft_cfg = RewardConfig(max_drawdown_soft=0.0)  # any dd triggers ceiling
        base_calc = RewardCalculator(base_cfg)
        soft_calc = RewardCalculator(soft_cfg)

        result = _make_result(
            trades=10,
            sharpe=0.0,
            risk_adjusted_pnl=0.0,
            adjusted_drawdown=0.2,
            win_rate=0.0,  # stability = 0
        )
        # soft_cfg: ceiling applies (0.2 > 0.0) → extra 10 * 0.2 = 2.0
        delta = base_calc.compute(result) - soft_calc.compute(result)
        expected_extra = base_cfg.hard_dd_extra_penalty * 0.2
        assert math.isclose(delta, expected_extra, abs_tol=1e-9)


class TestSummary:
    """summary() returns full component breakdown."""

    def test_summary_has_all_components(self):
        calc = RewardCalculator()
        result = _make_result(trades=10)
        s = calc.summary(result)
        for key in (
            "sharpe_comp",
            "pnl_comp",
            "dd_penalty",
            "cost_penalty",
            "stability_bonus",
            "risk_adj_pnl_used",
            "raw_pnl_available_but_not_used",
            "total",
        ):
            assert key in s, f"summary missing key: {key}"

    def test_summary_total_matches_compute(self):
        calc = RewardCalculator()
        result = _make_result(trades=10, sharpe=1.0, risk_adjusted_pnl=0.5)
        s = calc.summary(result)
        assert math.isclose(s["total"], calc.compute(result), abs_tol=1e-9)
