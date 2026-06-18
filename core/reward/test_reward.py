"""test_reward.py — ATOM-REWARD-001: Reward Pipeline Tests

Tests:
1. EMA stabilization (11.1)
2. Reward direction correctness (11.2)
3. Astro reward range
4. Full pipeline clamp
5. Per-agent EMA keys
6. Regime modifier
"""
from __future__ import annotations

import sys

sys.path.insert(0, "/home/workspace/AstroFinSentinelV5")

import pytest

from core.reward.astro_reward import compute_astro_reward
from core.reward.ema import RewardEMA, get_reward_ema
from core.reward.reward_engine import (
    compute_agent_rewards,
    compute_raw_reward,
    compute_reward_pipeline,
)


class TestEMA:
    """11.1: EMA stabilization — first value seeds, NOT 0."""

    def test_first_value_seeds_ema(self):
        ema = RewardEMA(alpha=0.3)
        result = ema.update("BTC", 0.5)
        assert result == 0.5  # First call = seed, not 0

    def test_ema_stabilization_oscillation(self):
        """Oscillating values should NOT produce oscillating EMA."""
        ema = RewardEMA(alpha=0.3)
        values = [1.0, -1.0, 1.0, -1.0, 1.0]
        smoothed = [ema.update("BTC", v) for v in values]
        # Last value should be closer to 0 than raw input
        assert abs(smoothed[-1]) < 1.0, f"EMA oscillating! last={smoothed[-1]}"
        assert abs(smoothed[-1]) < abs(values[-1])

    def test_ema_convergence(self):
        """EMA should converge toward stable values."""
        ema = RewardEMA(alpha=0.1)
        for _ in range(100):
            ema.update("BTC", 0.8)
        assert 0.75 <= ema.get("BTC") <= 0.85

    def test_ema_different_keys_independent(self):
        """BTC and ETH should have separate EMA states."""
        ema = RewardEMA(alpha=0.3)
        ema.update("BTC", 0.5)
        ema.update("ETH", -0.5)
        assert ema.get("BTC") == 0.5
        assert ema.get("ETH") == -0.5

    def test_ema_clamped_to_one(self):
        """EMA should clamp output to [-1, 1]."""
        ema = RewardEMA(alpha=0.3)
        for _ in range(10):
            r = ema.update("BTC", 5.0)
        assert abs(r) <= 1.0

    def test_reset(self):
        """Reset should clear state."""
        ema = RewardEMA(alpha=0.3)
        ema.update("BTC", 0.5)
        ema.reset("BTC")
        assert ema.get("BTC") == 0.0

    def test_singleton_get_reward_ema(self):
        """get_reward_ema() should return same instance."""
        e1 = get_reward_ema()
        e2 = get_reward_ema()
        assert e1 is e2


class TestRawReward:
    """11.2: Reward direction correctness."""

    def test_buy_positive_price_wins(self):
        """BUY + positive price → positive reward."""
        r = compute_raw_reward("BUY", price_change=0.02, confidence=80)
        assert r > 0, f"BUY+2% should be positive, got {r}"

    def test_buy_negative_price_loses(self):
        """BUY + negative price → negative reward."""
        r = compute_raw_reward("BUY", price_change=-0.02, confidence=80)
        assert r < 0, f"BUY-2% should be negative, got {r}"

    def test_sell_positive_price_wins(self):
        """SELL + positive price → positive reward (price drops)."""
        r = compute_raw_reward("SELL", price_change=0.02, confidence=80)
        assert r < 0, f"SELL+2% should be negative, got {r}"

    def test_neutral_zero(self):
        """NEUTRAL → 0 regardless of price."""
        r = compute_raw_reward("NEUTRAL", price_change=0.05, confidence=80)
        assert r == 0.0

    def test_confidence_scaling(self):
        """High confidence → larger magnitude."""
        r_low = compute_raw_reward("BUY", price_change=0.02, confidence=30)
        r_high = compute_raw_reward("BUY", price_change=0.02, confidence=90)
        assert abs(r_high) > abs(r_low)


class TestAstroReward:
    """Astro reward component."""

    def test_abhijit_muhurta_boost(self):
        """Abhijit Muhurta should boost reward."""
        r_abhijit = compute_astro_reward(muhurta="abhijit")
        r_neutral = compute_astro_reward(muhurta="neutral")
        assert r_abhijit > r_neutral

    def test_rahu_kaal_penalty(self):
        """Rahu Kaal should penalize reward."""
        r_rahu = compute_astro_reward(rahu_kaal_active=True)
        r_normal = compute_astro_reward(rahu_kaal_active=False)
        assert r_rahu < r_normal

    def test_extreme_regime_penalty(self):
        """EXTREME regime should penalize reward."""
        r = compute_astro_reward(regime="EXTREME")
        assert r < 0

    def test_range_clamped(self):
        """Astro reward always in [-1, 1]."""
        for regime in ["LOW", "NORMAL", "HIGH", "EXTREME"]:
            for muhurta in ["abhijit", "rauda", "amrita"]:
                r = compute_astro_reward(muhurta=muhurta, regime=regime, aspects=["mars_square_saturn"] * 10)
                assert -1.0 <= r <= 1.0, f"Out of range: {r}"


class TestPipeline:
    """Full reward pipeline."""

    def test_pipeline_output_range(self):
        """Pipeline always returns clamped values."""
        result = compute_reward_pipeline(
            signal="BUY",
            price_change=0.05,
            confidence=80,
            symbol="BTCUSDT",
        )
        assert -1.0 <= result.raw <= 1.0
        assert -1.0 <= result.smoothed <= 1.0

    def test_pipeline_has_all_fields(self):
        """RewardResult has all required fields."""
        result = compute_reward_pipeline(
            signal="BUY",
            price_change=0.02,
            confidence=60,
            symbol="BTCUSDT",
        )
        assert hasattr(result, "raw")
        assert hasattr(result, "smoothed")
        assert hasattr(result, "market_part")
        assert hasattr(result, "astro_part")
        assert hasattr(result, "clamped")

    def test_pipeline_smoothed_more_stable(self):
        """Smoothed reward should vary less than raw."""
        results_raw = []
        results_smooth = []
        ema = get_reward_ema()
        ema.reset("TESTBTC")
        for sig, pc in [("BUY", 0.03), ("SELL", -0.02), ("BUY", 0.05)]:
            r = compute_reward_pipeline(sig, pc, 70, "TESTBTC")
            results_raw.append(r.raw)
            results_smooth.append(r.smoothed)

        raw_var = max(results_raw) - min(results_raw)
        smooth_var = max(results_smooth) - min(results_smooth)
        assert smooth_var <= raw_var, "Smoothed should be more stable"


class TestAgentRewards:
    """Per-agent reward breakdown."""

    def test_agent_rewards_independent(self):
        """Different agents should have independent keys."""
        signals = [
            {
                "agent_name": "FundamentalAgent",
                "signal": "BUY",
                "confidence": 80,
                "price_change": 0.02,
            },
            {
                "agent_name": "QuantAgent",
                "signal": "SELL",
                "confidence": 70,
                "price_change": 0.02,
            },
        ]
        results = compute_agent_rewards(
            agent_signals=signals,
            price_change=0.02,
            symbol="BTCUSDT",
        )
        assert "FundamentalAgent" in results
        assert "QuantAgent" in results
        # BUY agent should have positive reward
        assert results["FundamentalAgent"].raw > 0
        # SELL agent gets negative reward when price rises (short loses)
        assert results["QuantAgent"].raw < 0  # short loses when price rises


# ─── Run ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
