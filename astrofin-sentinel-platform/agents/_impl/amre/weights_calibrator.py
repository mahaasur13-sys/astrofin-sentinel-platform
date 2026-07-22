"""agents/_impl/amre/weights_calibrator.py — Dynamic weight calibration.

P2-04 refactoring: extracted from agents/karl_synthesis.py.
Calibrates agent weights based on historical win rate, EMA-smoothed reward,
and lag windowing for temporal stability.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone

from agents._impl.amre.reward import (
    RewardState,
    compute_trajectory_reward,
    update_reward_ema,
)

logger = logging.getLogger(__name__)

ALPHA_EMA = 0.3   # EMA smoothing factor
WARMUP_THRESHOLD = 20  # Lag window maturity threshold


def compute_state_hash(
    state: dict, signal: str, confidence: int, regime: str
) -> str:
    """Compute reproducible state hash for audit trail.

    Uses sha256 — content hash, NOT security.
    """
    data = (
        f"{state.get('symbol', '')}:{state.get('current_price', 0)}:"
        f"{state.get('timeframe_requested', 'SWING')}:"
        f"{len(state.get('all_signals', []))}:{regime}:{signal}:{confidence}"
    )
    return hashlib.sha256(data.encode()).hexdigest()[
        :12
    ]  # nosec B324 — content hash for synthesis key, not security


def estimate_karl_reward(
    state: dict,
    signals: list,
    confidence: int,
    signal: str,
    reward_state: RewardState,
    market_state_cls,
) -> float:
    """EMA-smoothed reward with astro enrichment.

    70% market reward + 30% astro reward, EMA smoothing (α=0.3).
    """
    # Build MarketState
    ms = market_state_cls(
        symbol=state.get("symbol", "BTC"),
        price=state.get("current_price", 50000),
        timeframe=state.get("timeframe_requested", "SWING"),
        n_signals=len(signals),
        session_id=state.get("session_id", ""),
        timestamp=datetime.now(timezone.utc).isoformat(),
        regime=state.get("regime", "NORMAL"),
        confidence=confidence,
    )

    # Base market reward
    market_reward = compute_trajectory_reward(ms, signals)

    # Astro enrichment (ATOM-021)
    try:
        from agents._impl.amre.astro_reward import compute_astro_reward

        moon_long = state.get("moon_longitude", 0.0)
        aspects = state.get("planetary_aspects", [])
        nak_long = state.get("nakshatra_longitude", 0.0)
        astro_dict = compute_astro_reward(
            state=ms,
            moon_longitude=moon_long,
            aspects=aspects,
            nakshatra_longitude=nak_long,
            base_reward=market_reward,
        )
        astro_reward = astro_dict.get("final_reward", 0.0)
    except Exception:
        astro_reward = 0.0

    # Combined: 70% market + 30% astro
    raw_reward = 0.7 * market_reward + 0.3 * astro_reward

    # EMA smoothing
    previous_ema = reward_state.ema_reward
    smoothed = update_reward_ema(previous_ema, raw_reward)
    reward_state.ema_reward = smoothed
    reward_state.raw_reward = raw_reward
    reward_state.count += 1

    if reward_state.count % 10 == 0:
        logger.info(
            f"[REWARD EMA] count={reward_state.count} "
            f"market={market_reward:.3f} astro={astro_reward:.3f} "
            f"raw={raw_reward:.3f} ema={smoothed:.3f}"
        )

    return smoothed


def apply_lag_smoothing(
    lag_window,
    confidence: int,
    position_pct: float,
    lag_enabled: bool = True,
) -> tuple[int, float, dict]:
    """Apply LagWindow smoothing to confidence and compute position_lag metrics.

    Returns (adjusted_confidence, adjusted_position_pct, lag_metrics_dict).
    """
    if not lag_enabled:
        return confidence, position_pct, {}

    metrics = lag_window.add(
        confidence=confidence,
        position_pct=position_pct,
    )

    adjusted_conf = metrics["final_confidence"]
    window_mature = metrics["count"] >= WARMUP_THRESHOLD

    lag_meta = {
        "raw_confidence": metrics["raw_confidence"],
        "ema_confidence": metrics["ema"],
        "lag_adjustment": metrics["lag_adj"],
        "position_lag": metrics["position_lag"],
        "window_mature": window_mature,
        "window_size": metrics["window_size"],
        "blend": metrics["blend"],
    }

    if metrics["lag_adj"] != 0:
        logger.info(
            f"[LagWindow] conf {confidence} → {adjusted_conf} "
            f"(adj={metrics['lag_adj']:+.3f}, pos_lag={metrics['position_lag']:+.3f})"
        )

    return adjusted_conf, position_pct, lag_meta
