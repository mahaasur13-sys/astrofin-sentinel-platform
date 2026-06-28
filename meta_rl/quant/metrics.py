"""meta_rl/quant/metrics.py -- ATOM-META-RL-024: Extended risk metrics"""

from __future__ import annotations

import math
from collections.abc import Sequence


def sortino_ratio(returns: Sequence[float], target: float = 0.0) -> float:
    """Sortino: return / downside deviation. Higher is better."""
    vals = [r - target for r in returns if r < target]
    if not vals:
        return 0.0
    downside = math.sqrt(sum(v**2 for v in vals) / len(returns))
    return (sum(returns) / len(returns)) / downside if downside else 0.0


def calmar_ratio(returns: Sequence[float], max_dd: float) -> float:
    """Calmar: annualized return / max drawdown. Higher is better."""
    if max_dd == 0:
        return 0.0
    ann = (sum(returns) / len(returns)) * 252
    return ann / abs(max_dd)


def max_consecutive_losses(returns: Sequence[float]) -> int:
    """Max consecutive losing periods."""
    best = cur = 0
    for r in returns:
        cur = cur + 1 if r < 0 else 0
        if cur > best:
            best = cur
    return best


def tail_ratio(returns: Sequence[float]) -> float:
    """95th percentile / 5th percentile. >1 means right-skew."""
    if len(returns) < 20:
        return 1.0
    s = sorted(returns)
    upper = s[int(len(s) * 0.95)]
    lower = s[int(len(s) * 0.05)]
    return abs(upper / lower) if lower != 0 else 1.0


def omega_ratio(returns: Sequence[float], threshold: float = 0.0) -> float:
    """Omega: gain above threshold / loss below threshold."""
    gain = sum(threshold - r for r in returns if r >= threshold)
    loss = sum(r - threshold for r in returns if r < threshold)
    return gain / loss if loss != 0 else 0.0


def rolling_sharpe(returns: Sequence[float], window: int = 20) -> list[float]:
    """Rolling Sharpe ratio (annualized)."""
    result = []
    for i in range(window, len(returns) + 1):
        chunk = returns[i - window : i]
        mean = sum(chunk) / len(chunk)
        var = sum((r - mean) ** 2 for r in chunk) / len(chunk)
        std = math.sqrt(var)
        result.append((mean / std * math.sqrt(252)) if std else 0.0)
    return result


# ─── Extended EvaluationResult fields ────────────────────────────────────────
from meta_rl.types import EvaluationResult  # noqa: E402


def enrich_result(ev: EvaluationResult, returns: list[float]) -> EvaluationResult:
    """Fill extended fields from return series."""
    ev.sortino_ratio = sortino_ratio(returns)
    ev.tail_ratio = tail_ratio(returns)
    ev.omega_ratio = omega_ratio(returns)
    ev.max_consecutive_losses = max_consecutive_losses(returns)
    return ev
