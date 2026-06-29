"""
test_core_volatility.py — Tests for core/volatility.py (Volatility engine)

Phase 1 (R9): Add coverage for the dynamic risk engine (R-07).
Tests cover:
  • VolatilityRegime enum + boundaries
  • VolatilityRisk dataclass helpers (stop_loss_*, target_*)
  • VolatilityEngine: ATR-to-regime classification
  • VolatilityEngine.analyze(): regime resolution + Kelly + stop distance
  • V-06 guard: confidence penalty in HIGH/EXTREME
  • Singleton cache: get_volatility_risk + clear_volatility_cache
  • calculate_atr: standalone True Range averaging
"""

from __future__ import annotations

import pytest

from core.volatility import (
    REGIME_CONFIDENCE_DROP,
    REGIME_POSITION_KELLY_MULT,
    REGIME_RISK_PCT,
    REGIME_STOP_MULTIPLIER,
    VolatilityEngine,
    VolatilityRegime,
    VolatilityRisk,
    calculate_atr,
    clear_volatility_cache,
    get_volatility_risk,
)


@pytest.fixture(autouse=True)
def _reset_cache():
    """Clear module-level volatility cache between tests."""
    clear_volatility_cache()
    yield
    clear_volatility_cache()


# ── Regime boundaries ─────────────────────────────────────────────────────────


class TestRegimeClassification:
    def test_low_regime_under_1_5pct(self):
        assert VolatilityEngine.atr_to_regime(0.010) == VolatilityRegime.LOW

    def test_low_regime_at_zero(self):
        assert VolatilityEngine.atr_to_regime(0.0) == VolatilityRegime.LOW

    def test_normal_regime_at_1_5pct(self):
        assert VolatilityEngine.atr_to_regime(0.015) == VolatilityRegime.NORMAL

    def test_normal_regime_just_below_3pct(self):
        assert VolatilityEngine.atr_to_regime(0.029) == VolatilityRegime.NORMAL

    def test_high_regime_at_3pct(self):
        assert VolatilityEngine.atr_to_regime(0.030) == VolatilityRegime.HIGH

    def test_high_regime_just_below_5pct(self):
        assert VolatilityEngine.atr_to_regime(0.049) == VolatilityRegime.HIGH

    def test_extreme_regime_at_5pct(self):
        assert VolatilityEngine.atr_to_regime(0.050) == VolatilityRegime.EXTREME

    def test_extreme_regime_above_5pct(self):
        assert VolatilityEngine.atr_to_regime(0.15) == VolatilityRegime.EXTREME


# ── VolatilityRisk helpers ────────────────────────────────────────────────────


class TestVolatilityRiskHelpers:
    def test_stop_loss_long_lowers_price(self):
        risk = VolatilityRisk(
            regime=VolatilityRegime.NORMAL,
            risk_pct=0.02,
            position_size=0.05,
            atr_pct=0.02,
            stop_distance_pct=0.02,
            confidence_drop=0,
            kelly_raw=0.10,
            kelly_adjusted=0.075,
            reasoning="test",
        )
        assert risk.stop_loss_long(100.0) == pytest.approx(98.0)

    def test_stop_loss_short_raises_price(self):
        risk = VolatilityRisk(
            regime=VolatilityRegime.NORMAL,
            risk_pct=0.02,
            position_size=0.05,
            atr_pct=0.02,
            stop_distance_pct=0.02,
            confidence_drop=0,
            kelly_raw=0.10,
            kelly_adjusted=0.075,
            reasoning="test",
        )
        assert risk.stop_loss_short(100.0) == pytest.approx(102.0)

    def test_target_long_rr_2(self):
        risk = VolatilityRisk(
            regime=VolatilityRegime.HIGH,
            risk_pct=0.01,
            position_size=0.025,
            atr_pct=0.04,
            stop_distance_pct=0.03,
            confidence_drop=10,
            kelly_raw=0.10,
            kelly_adjusted=0.05,
            reasoning="test",
        )
        # target = entry * (1 + stop_dist * 2.0)
        assert risk.target_long(100.0, rr=2.0) == pytest.approx(106.0)

    def test_target_short_rr_3(self):
        risk = VolatilityRisk(
            regime=VolatilityRegime.LOW,
            risk_pct=0.03,
            position_size=0.10,
            atr_pct=0.01,
            stop_distance_pct=0.025,
            confidence_drop=0,
            kelly_raw=0.10,
            kelly_adjusted=0.10,
            reasoning="test",
        )
        # target_short = entry * (1 - stop_dist * 3.0) = 100 * 0.925
        assert risk.target_short(100.0, rr=3.0) == pytest.approx(92.5)


# ── VolatilityEngine.analyze ──────────────────────────────────────────────────


class TestVolatilityEngineAnalyze:
    def test_explicit_regime_low(self):
        engine = VolatilityEngine()
        risk = engine.analyze(regime=VolatilityRegime.LOW, price=50000)
        assert risk.regime == VolatilityRegime.LOW
        assert risk.risk_pct == REGIME_RISK_PCT[VolatilityRegime.LOW]
        assert risk.position_size == pytest.approx(risk.kelly_adjusted)

    def test_explicit_regime_extreme_has_v06_drop(self):
        engine = VolatilityEngine()
        risk = engine.analyze(regime=VolatilityRegime.EXTREME, price=50000)
        assert risk.confidence_drop == 25
        assert risk.stop_distance_pct == 0.050

    def test_atr_input_infers_normal_regime(self):
        engine = VolatilityEngine()
        risk = engine.analyze(price=50000, atr=1000)  # 2% ATR
        assert risk.regime == VolatilityRegime.NORMAL
        assert risk.atr_pct == pytest.approx(0.02)

    def test_atr_pct_input_infers_high_regime(self):
        engine = VolatilityEngine()
        risk = engine.analyze(atr_pct=0.04)
        assert risk.regime == VolatilityRegime.HIGH

    def test_from_price_atr_constructor(self):
        engine = VolatilityEngine.from_price_atr(price=50000, atr=1500)
        risk = engine.analyze()
        assert risk.regime == VolatilityRegime.HIGH

    def test_from_regime_constructor_bypasses_atr(self):
        engine = VolatilityEngine.from_regime(VolatilityRegime.EXTREME)
        risk = engine.analyze()
        assert risk.regime == VolatilityRegime.EXTREME

    def test_no_atr_data_falls_back_to_normal(self):
        engine = VolatilityEngine()
        risk = engine.analyze(symbol="TEST")
        assert risk.regime == VolatilityRegime.NORMAL
        assert risk.atr_pct == 0.020

    def test_zero_price_safe_fallback(self):
        engine = VolatilityEngine()
        risk = engine.analyze(price=0, atr=100)
        # atr_pct = 100/0 → handled safely (price > 0 check)
        assert risk.atr_pct == 0.020  # falls into the fallback branch

    def test_reasoning_contains_regime_and_atr(self):
        engine = VolatilityEngine()
        risk = engine.analyze(price=50000, atr=1500)  # atr_pct = 3% → HIGH regime
        assert "HIGH" in risk.reasoning
        assert "3.00%" in risk.reasoning
        assert "V-06_drop=10" in risk.reasoning


# ── V-06: Confidence guard ────────────────────────────────────────────────────


class TestV06ConfidenceGuard:
    def test_low_regime_no_drop(self):
        engine = VolatilityEngine()
        adjusted, label = engine.apply_volatility_guard(raw_confidence=80, regime=VolatilityRegime.LOW)
        assert adjusted == 80
        assert label == ""

    def test_normal_regime_no_drop(self):
        engine = VolatilityEngine()
        adjusted, _ = engine.apply_volatility_guard(raw_confidence=70, regime=VolatilityRegime.NORMAL)
        assert adjusted == 70

    def test_high_regime_drops_10(self):
        engine = VolatilityEngine()
        adjusted, label = engine.apply_volatility_guard(raw_confidence=80, regime=VolatilityRegime.HIGH)
        assert adjusted == 70
        assert label == "V-06(dr=10)"

    def test_extreme_regime_drops_25(self):
        engine = VolatilityEngine()
        adjusted, label = engine.apply_volatility_guard(raw_confidence=80, regime=VolatilityRegime.EXTREME)
        assert adjusted == 55
        assert label == "V-06(dr=25)"

    def test_extreme_floor_at_30(self):
        engine = VolatilityEngine()
        adjusted, _ = engine.apply_volatility_guard(raw_confidence=20, regime=VolatilityRegime.EXTREME)
        # 20 - 25 = -5 → floor at 30
        assert adjusted == 30


# ── Kelly criterion ───────────────────────────────────────────────────────────


class TestKellyCriterion:
    def test_kelly_positive_with_edge(self):
        engine = VolatilityEngine(win_rate=0.55, avg_win_pct=0.03, avg_loss_pct=0.015)
        risk = engine.analyze(regime=VolatilityRegime.NORMAL)
        # wl_ratio = 2.0, kelly_raw = (0.55*2 - 0.45) / 2 = 0.325
        # raw is capped at MAX_KELLY=0.20, then dampened by NORMAL mult 0.75 → 0.15
        assert risk.kelly_raw == pytest.approx(0.20)
        assert risk.kelly_adjusted == pytest.approx(0.15)

    def test_kelly_capped_at_max(self):
        engine = VolatilityEngine(win_rate=0.80, avg_win_pct=0.10, avg_loss_pct=0.01)
        risk = engine.analyze(regime=VolatilityRegime.LOW)
        # wl_ratio = 10.0, kelly = (0.80*10 - 0.20) / 10 = 0.78
        # adjusted = 0.78 * 1.0 = 0.78 → cap at 0.20
        assert risk.kelly_adjusted == pytest.approx(0.20)

    def test_kelly_floor_on_no_edge(self):
        engine = VolatilityEngine(win_rate=0.50, avg_win_pct=0.01, avg_loss_pct=0.01)
        risk = engine.analyze(regime=VolatilityRegime.LOW)
        # wl_ratio = 1.0, kelly = (0.50 - 0.50) / 1.0 = 0.0 → floor at MIN_KELLY
        assert risk.kelly_adjusted == pytest.approx(0.01)

    def test_kelly_extreme_regime_dampens(self):
        engine = VolatilityEngine(win_rate=0.60, avg_win_pct=0.04, avg_loss_pct=0.02)
        risk = engine.analyze(regime=VolatilityRegime.EXTREME)
        # wl_ratio = 2.0, kelly_raw = (0.60*2 - 0.40) / 2 = 0.40
        # raw is capped at 0.20, then EXTREME mult = 0.20 → 0.04
        assert risk.kelly_adjusted == pytest.approx(0.04)


# ── Singleton cache ───────────────────────────────────────────────────────────


class TestSingletonCache:
    def test_get_volatility_risk_caches_result(self):
        r1 = get_volatility_risk("BTCUSDT", price=50000, atr=1000)
        r2 = get_volatility_risk("BTCUSDT", price=50000, atr=1000)
        assert r1 is r2  # cached reference

    def test_clear_cache_invalidates(self):
        r1 = get_volatility_risk("ETHUSDT", price=3000, atr=60)
        clear_volatility_cache()
        r2 = get_volatility_risk("ETHUSDT", price=3000, atr=60)
        assert r1 is not r2

    def test_different_regimes_cached_separately(self):
        r_low = get_volatility_risk("BTCUSDT", price=50000, regime=VolatilityRegime.LOW)
        r_extreme = get_volatility_risk("BTCUSDT", price=50000, regime=VolatilityRegime.EXTREME)
        assert r_low.regime == VolatilityRegime.LOW
        assert r_extreme.regime == VolatilityRegime.EXTREME
        assert r_low is not r_extreme


# ── calculate_atr ─────────────────────────────────────────────────────────────


class TestCalculateATR:
    def test_calculate_atr_short_data_uses_fallback(self):
        # Less than period+1 candles — fallback to 2% of last close
        data = [[100.0, 95.0, 98.0], [102.0, 97.0, 100.0]]
        atr = calculate_atr(data, period=14)
        assert atr == pytest.approx(100.0 * 0.02)

    def test_calculate_atr_empty_returns_default(self):
        atr = calculate_atr([], period=14)
        assert atr == 100.0

    def test_calculate_atr_basic_range(self):
        # Construct 15 candles with a single opening gap; ATR averages the last 14 true ranges.
        candles = [[100.0, 90.0, 95.0]] + [[110.0, 100.0, 105.0]] * 14
        atr = calculate_atr(candles, period=14)
        assert atr == pytest.approx(10.357142857142858)

    def test_calculate_atr_gap_tr(self):
        # TR captures gaps, but subsequent closes decay the series so the 14-period average is lower.
        candles = [[100.0, 95.0, 100.0]] + [[120.0, 110.0, 115.0]] * 14
        atr = calculate_atr(candles, period=14)
        assert atr == pytest.approx(10.714285714285714)


# ── Matrix completeness ───────────────────────────────────────────────────────


class TestRegimeMatrix:
    """Verify all 4 regimes have populated matrices (no missing keys)."""

    def test_all_regimes_have_risk_pct(self):
        for r in VolatilityRegime:
            assert r in REGIME_RISK_PCT

    def test_all_regimes_have_kelly_mult(self):
        for r in VolatilityRegime:
            assert r in REGIME_POSITION_KELLY_MULT

    def test_all_regimes_have_stop_mult(self):
        for r in VolatilityRegime:
            assert r in REGIME_STOP_MULTIPLIER

    def test_all_regimes_have_confidence_drop(self):
        for r in VolatilityRegime:
            assert r in REGIME_CONFIDENCE_DROP

    def test_extreme_has_highest_confidence_drop(self):
        assert (
            REGIME_CONFIDENCE_DROP[VolatilityRegime.EXTREME]
            >= REGIME_CONFIDENCE_DROP[VolatilityRegime.HIGH]
        )

    def test_low_has_highest_risk_pct(self):
        assert (
            REGIME_RISK_PCT[VolatilityRegime.LOW]
            >= REGIME_RISK_PCT[VolatilityRegime.NORMAL]
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])