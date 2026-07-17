"""core/reward/reward_engine.py — ATOM-REWARD-001: Combined Reward Pipeline

Pipeline:
  compute_raw_reward()   → market + astro components
  compute_smoothed_reward() → EMA-smoothed per symbol
  compute_agent_rewards()   → per-agent breakdown

Clamp: all outputs in [-1, 1]
"""

from dataclasses import dataclass

from core.reward.astro_reward import compute_astro_reward
from core.reward.ema import get_reward_ema

# ─── Dataclasses ──────────────────────────────────────────────────────────────


@dataclass
class RewardResult:
    """Full reward breakdown."""

    raw: float  # Market + astro, pre-EMA
    smoothed: float  # EMA-smoothed
    market_part: float  # Just PnL component
    astro_part: float  # Just astro component
    clamped: bool  # Was clamped during EMA


# ─── Raw Reward ───────────────────────────────────────────────────────────────


def compute_raw_reward(
    signal: str,
    price_change: float,
    confidence: float,
    muhurta: str = "neutral",
    yoga: str = "neutral",
    nakshatra: str = "neutral",
    rahu_kaal_active: bool = False,
    regime: str = "NORMAL",
    aspects: list[str] = None,
    moon_sign: str = "",
    tithi: int = 0,
) -> float:
    """
    Compute raw reward BEFORE EMA smoothing.

    Returns value in [-1, 1].

    Parameters
    ----------
    signal : str
        Trading signal: BUY, SELL, NEUTRAL, etc.
    price_change : float
        Actual price change after signal (e.g. 0.02 = +2%)
    confidence : float
        Signal confidence 0-100
    astro params : ...
        Passed to compute_astro_reward()

    Formula
    --------
    reward = 0.7 * market_reward + 0.3 * astro_reward
    market_reward = direction * price_change * (confidence / 100)
    direction = +1 (BUY), -1 (SELL), 0 (NEUTRAL)
    """
    # Direction correctness
    direction_map = {
        "buy": 1,
        "long": 1,
        "strong_buy": 1,
        "sell": -1,
        "short": -1,
        "strong_sell": -1,
        "neutral": 0,
        "hold": 0,
        "avoid": 0,
    }
    direction = direction_map.get(signal.lower(), 0)

    # Market component
    conf_factor = max(0.0, min(1.0, confidence / 100.0))
    market_part = direction * price_change * conf_factor

    # Astro component
    astro_part = compute_astro_reward(
        muhurta=muhurta,
        yoga=yoga,
        nakshatra=nakshatra,
        rahu_kaal_active=rahu_kaal_active,
        regime=regime,
        aspects=aspects,
        moon_sign=moon_sign,
        tithi=tithi,
    )

    # Combined: 70% market + 30% astro
    raw = 0.7 * market_part + 0.3 * astro_part

    # Clamp
    return max(-1.0, min(1.0, raw))


# ─── EMA Smoothing ────────────────────────────────────────────────────────────


def compute_smoothed_reward(
    key: str,
    raw_reward: float,
    alpha: float = 0.3,
) -> float:
    """
    Apply EMA smoothing to raw reward.

    key : str
        Symbol (e.g. "BTCUSDT") or agent name
    raw_reward : float
        Output of compute_raw_reward()
    alpha : float
        EMA smoothing factor (default 0.3)

    Returns EMA value in [-1, 1].
    """
    ema = get_reward_ema()
    return ema.update(key, raw_reward)


# ─── Combined Pipeline ────────────────────────────────────────────────────────


def compute_reward_pipeline(
    signal: str,
    price_change: float,
    confidence: float,
    symbol: str,
    muhurta: str = "neutral",
    yoga: str = "neutral",
    nakshatra: str = "neutral",
    rahu_kaal_active: bool = False,
    regime: str = "NORMAL",
    aspects: list[str] = None,
    moon_sign: str = "",
    tithi: int = 0,
    alpha: float = 0.3,
) -> RewardResult:
    """
    Full reward pipeline: raw → EMA → clamped.

    Returns RewardResult with full breakdown.
    """
    # Raw
    raw = compute_raw_reward(
        signal=signal,
        price_change=price_change,
        confidence=confidence,
        muhurta=muhurta,
        yoga=yoga,
        nakshatra=nakshatra,
        rahu_kaal_active=rahu_kaal_active,
        regime=regime,
        aspects=aspects,
        moon_sign=moon_sign,
        tithi=tithi,
    )

    # EMA
    smoothed = compute_smoothed_reward(symbol, raw, alpha=alpha)

    # Detect clamping
    clamped = smoothed == 1.0 or smoothed == -1.0

    # Compute parts
    conf_factor = max(0.0, min(1.0, confidence / 100.0))
    direction_map = {
        "buy": 1,
        "long": 1,
        "strong_buy": 1,
        "sell": -1,
        "short": -1,
        "strong_sell": -1,
        "neutral": 0,
        "hold": 0,
        "avoid": 0,
    }
    direction = direction_map.get(signal.lower(), 0)
    market_part = direction * price_change * conf_factor
    astro_part = compute_astro_reward(
        muhurta=muhurta,
        yoga=yoga,
        nakshatra=nakshatra,
        rahu_kaal_active=rahu_kaal_active,
        regime=regime,
        aspects=aspects,
        moon_sign=moon_sign,
        tithi=tithi,
    )

    return RewardResult(
        raw=raw,
        smoothed=smoothed,
        market_part=market_part,
        astro_part=astro_part,
        clamped=clamped,
    )


# ─── Agent-level EMA (Phase 3.1) ───────────────────────────────────────────────


def compute_agent_rewards(
    agent_signals: list[dict],
    price_change: float,
    symbol: str,
    regime: str = "NORMAL",
    alpha: float = 0.3,
) -> dict[str, RewardResult]:
    """
    Compute per-agent smoothed rewards.

    agent_signals : list of dicts with keys:
        - agent_name: str
        - signal: str
        - confidence: float
        - muhurta / yoga / nakshatra / etc.

    Returns dict: agent_name → RewardResult
    """
    results = {}
    for sig_dict in agent_signals:
        agent_name = sig_dict.get("agent_name", "unknown")
        result = compute_reward_pipeline(
            signal=sig_dict.get("signal", "NEUTRAL"),
            price_change=price_change,
            confidence=sig_dict.get("confidence", 50),
            symbol=f"{symbol}:{agent_name}",  # Per-agent key
            regime=regime,
            muhurta=sig_dict.get("muhurta", "neutral"),
            yoga=sig_dict.get("yoga", "neutral"),
            nakshatra=sig_dict.get("nakshatra", "neutral"),
            rahu_kaal_active=sig_dict.get("rahu_kaal_active", False),
            aspects=sig_dict.get("aspects", []),
            moon_sign=sig_dict.get("moon_sign", ""),
            tithi=sig_dict.get("tithi", 0),
            alpha=alpha,
        )
        results[agent_name] = result
    return results
