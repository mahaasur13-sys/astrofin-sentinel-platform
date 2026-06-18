"""core/reward/ema.py — ATOM-REWARD-001: Reward EMA Engine

Exponential smoothing of reward signals per symbol or agent.
Alpha=0.3 means: 30% new signal + 70% historical EMA.

Critical: first value seeds EMA (NOT 0).
"""
from __future__ import annotations

from collections import defaultdict


class RewardEMA:
    """
    Per-key EMA for reward stabilization.

    Key design:
    - First call with a key seeds the EMA to the raw value (NOT 0)
    - All subsequent calls apply EMA formula
    - Initial value = raw reward (no baseline penalty)
    """

    def __init__(self, alpha: float = 0.3):
        self.alpha = alpha
        # key → EMA value (starts as None = uninitialized)
        self._state: dict[str, float | None] = defaultdict(lambda: None)

    def update(self, key: str, value: float) -> float:
        """
        Update EMA for key. First call seeds with `value` (NOT 0).

        Returns clamped EMA in [-1, 1].
        """
        prev = self._state[key]
        if prev is None:
            # First value: seed EMA directly (no lag from 0)
            ema = value
        else:
            ema = self.alpha * value + (1 - self.alpha) * prev

        self._state[key] = ema
        # Clamp to [-1, 1] for stability
        return max(-1.0, min(1.0, ema))

    def get(self, key: str) -> float:
        """Get current EMA. Returns 0.0 for unknown keys."""
        v = self._state.get(key)
        return v if v is not None else 0.0

    def reset(self, key: str | None = None):
        """Reset one key or all keys."""
        if key is None:
            self._state.clear()
        else:
            self._state.pop(key, None)


# ─── Module-level singleton ───────────────────────────────────────────────────

_REWARD_EMA: RewardEMA | None = None


def get_reward_ema() -> RewardEMA:
    global _REWARD_EMA
    if _REWARD_EMA is None:
        _REWARD_EMA = RewardEMA(alpha=0.3)
    return _REWARD_EMA
