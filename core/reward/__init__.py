"""core/reward — ATOM-REWARD-001: Reward Pipeline

Modules:
    ema.py           — RewardEMA class + singleton
    astro_reward.py   — Astro-based reward component
    reward_engine.py — Combined pipeline (raw → EMA → smoothed)

Pipeline:
    compute_raw_reward()   → market (70%) + astro (30%)
    compute_smoothed_reward() → EMA per symbol
    compute_reward_pipeline() → combined with full breakdown
"""
from __future__ import annotations

from core.reward.astro_reward import compute_astro_reward
from core.reward.ema import RewardEMA, get_reward_ema
from core.reward.reward_engine import (
    RewardResult,
    compute_agent_rewards,
    compute_raw_reward,
    compute_reward_pipeline,
    compute_smoothed_reward,
)

__all__ = [
    # EMA
    "RewardEMA",
    "get_reward_ema",
    # Astro
    "compute_astro_reward",
    # Engine
    "RewardResult",
    "compute_raw_reward",
    "compute_smoothed_reward",
    "compute_reward_pipeline",
    "compute_agent_rewards",
]
