"""Return-series statistics for the validation protocol: metrics, buy-and-hold benchmark, Deflated Sharpe.

Pure functions over per-period simple returns; stdlib + numpy only, offline.

Deflated Sharpe Ratio (Bailey & López de Prado, 2014), as fixed in the research plan
(/workspace/research/sma200/hypothesis.yaml ``dsr``):
  SR0 = sqrt(V[SR]) * ((1-γ)·Φ⁻¹(1-1/N) + γ·Φ⁻¹(1-1/(N·e)))
  DSR = Φ( (SR - SR0)·sqrt(T-1) / sqrt(1 - γ3·SR + (γ4-1)/4·SR²) )
with per-period (non-annualised) SR, N = number of trials, V[SR] = sample variance (ddof=1) of
the trials' per-period SRs, γ3 = skewness, γ4 = (non-excess) kurtosis of the tested returns.
N may never be smaller than the protocol's ``variants_tried``: under-counting trials is refused.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist
from typing import Sequence

import numpy as np

from .errors import ValidationError

EULER_GAMMA = 0.5772156649
_N = NormalDist()


def _arr(returns: Sequence[float]) -> np.ndarray:
    x = np.asarray(returns, dtype=float)
    if x.ndim != 1 or len(x) < 2:
        raise ValidationError("need at least 2 returns")
    if not np.all(np.isfinite(x)):
        raise ValidationError("returns contain NaN/inf")
    return x


def sharpe_per_period(returns: Sequence[float]) -> float:
    x = _arr(returns)
    sd = x.std(ddof=1)
    if sd == 0:
        raise ValidationError("zero-variance returns: Sharpe undefined")
    return float(x.mean() / sd)


def performance_metrics(returns: Sequence[float], periods_per_year: int) -> dict:
    """CAGR, annualised vol, annualised Sharpe (rf=0), max drawdown (fractions, not %)."""
    x = _arr(returns)
    eq = np.cumprod(1.0 + x)
    years = len(x) / periods_per_year
    dd = eq / np.maximum.accumulate(eq) - 1.0
    return {
        "CAGR": float(eq[-1] ** (1.0 / years) - 1.0),
        "vol": float(x.std(ddof=1) * math.sqrt(periods_per_year)),
        "Sharpe": sharpe_per_period(x) * math.sqrt(periods_per_year),
        "MaxDD": float(dd.min()),
        "n": int(len(x)),
    }


def buy_and_hold_returns(closes: Sequence[float]) -> np.ndarray:
    """Benchmark: fully invested, no costs, close-to-close returns."""
    c = np.asarray(closes, dtype=float)
    if len(c) < 3 or not np.all(np.isfinite(c)) or np.any(c <= 0):
        raise ValidationError("buy-and-hold needs >=3 positive finite closes")
    return c[1:] / c[:-1] - 1.0


def expected_max_sharpe(n_trials: int, sr_variance: float) -> float:
    """SR0: expected maximum per-period SR among ``n_trials`` unskilled trials."""
    if n_trials < 2:
        raise ValidationError("DSR needs n_trials >= 2")
    if not (math.isfinite(sr_variance) and sr_variance >= 0):
        raise ValidationError("invalid SR variance")
    return math.sqrt(sr_variance) * (
        (1 - EULER_GAMMA) * _N.inv_cdf(1 - 1 / n_trials) + EULER_GAMMA * _N.inv_cdf(1 - 1 / (n_trials * math.e))
    )


@dataclass(frozen=True)
class DeflatedSharpe:
    dsr: float  # probability that the true SR exceeds SR0
    sr: float  # per-period SR of the tested returns
    sr0: float  # per-period deflation threshold
    n_trials: int


def deflated_sharpe_ratio(
    returns: Sequence[float], trial_sharpes: Sequence[float], *, variants_tried: int | None = None
) -> DeflatedSharpe:
    """DSR of ``returns`` given the per-period SRs of ALL trials (including this one).

    ``variants_tried`` (from FrozenProtocol / ValidationReport) is a floor on N: if fewer trial SRs
    are supplied than variants were tried, the call is refused (ValidationError) instead of
    silently deflating less.
    """
    x = _arr(returns)
    trials = [float(s) for s in trial_sharpes]
    if not all(math.isfinite(s) for s in trials):
        raise ValidationError("trial Sharpe ratios must be finite")
    n = len(trials)
    if variants_tried is not None and n < variants_tried:
        raise ValidationError(
            f"{n} trial Sharpes supplied but variants_tried={variants_tried}; refusing to under-deflate"
        )
    sr0 = expected_max_sharpe(n, float(np.var(trials, ddof=1)))
    sr = sharpe_per_period(x)
    m, sd = x.mean(), x.std()  # population moments for skew/kurtosis (as scipy bias=True)
    g3 = float(np.mean((x - m) ** 3) / sd**3)
    g4 = float(np.mean((x - m) ** 4) / sd**4)
    denom = 1 - g3 * sr + (g4 - 1) / 4 * sr**2
    if denom <= 0:
        raise ValidationError("DSR denominator non-positive")
    z = (sr - sr0) * math.sqrt(len(x) - 1) / math.sqrt(denom)
    return DeflatedSharpe(dsr=_N.cdf(z), sr=sr, sr0=sr0, n_trials=n)
