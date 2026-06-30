"""
core/volatility.py — Dynamic Risk Engine (R-07)

Volatility-adaptive position sizing + dynamic risk_pct:
  • ATR-based volatility measurement
  • Regime classification (LOW / NORMAL / HIGH / EXTREME)
  • Kelly Criterion with volatility dampening
  • Dynamic stop-loss distances
  • V-06 guard: confidence penalty in high-vol regimes
  • V-07 guard: auto-AVOID in EXTREME volatility

Usage:
  from core.volatility import VolatilityEngine, get_volatility_risk

  engine = VolatilityEngine()
  risk = engine.analyze(symbol="BTCUSDT", price=50000, atr=1500, regime="HIGH")
  # risk.risk_pct        = 0.01   (halved from 0.02 in HIGH regime)
  # risk.position_size  = 0.05   (5% — Kelly adjusted down)
  # risk.stop_distance   = 0.03   (3%  — tight stop in HIGH)
  # risk.confidence_drop = 10     (V-06 penalty)

  # V-06: apply confidence drop in synthesis
  adjusted_conf = engine.apply_volatility_guard(raw_confidence, regime)

  # V-07: AVOID signal in EXTREME
  if regime == "EXTREME":
      signal = SignalDirection.AVOID
"""

import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class VolatilityRegime(Enum):
    LOW = "LOW"  # σ < 1.5%  — calm market
    NORMAL = "NORMAL"  # 1.5% ≤ σ < 3%
    HIGH = "HIGH"  # 3% ≤ σ < 5%
    EXTREME = "EXTREME"  # σ ≥ 5%   — crisis / black swan


# ─── Risk matrix ────────────────────────────────────────────────────────────────

REGIME_RISK_PCT = {
    VolatilityRegime.LOW: 0.03,  # 3% risk — can size up
    VolatilityRegime.NORMAL: 0.02,  # 2% risk — baseline
    VolatilityRegime.HIGH: 0.01,  # 1% risk — halve exposure
    VolatilityRegime.EXTREME: 0.005,  # 0.5% risk — near-zero
}

REGIME_POSITION_KELLY_MULT = {
    VolatilityRegime.LOW: 1.0,
    VolatilityRegime.NORMAL: 0.75,
    VolatilityRegime.HIGH: 0.50,
    VolatilityRegime.EXTREME: 0.20,
}

REGIME_CONFIDENCE_DROP = {
    VolatilityRegime.LOW: 0,
    VolatilityRegime.NORMAL: 0,
    VolatilityRegime.HIGH: 10,
    VolatilityRegime.EXTREME: 25,
}

REGIME_STOP_MULTIPLIER = {
    # stop = price * (1 ± regime_stop_mult[regime])
    VolatilityRegime.LOW: 0.025,  # 2.5% stop distance
    VolatilityRegime.NORMAL: 0.020,  # 2% stop distance
    VolatilityRegime.HIGH: 0.030,  # 3% stop distance (wider — false spikes)
    VolatilityRegime.EXTREME: 0.050,  # 5% stop distance
}


# ─── Core dataclass ─────────────────────────────────────────────────────────────


@dataclass
class VolatilityRisk:
    regime: VolatilityRegime
    risk_pct: float  # position risk fraction
    position_size: float  # kelly-based position size
    atr_pct: float  # ATR as % of price (volatility measure)
    stop_distance_pct: float
    confidence_drop: int  # V-06 penalty
    kelly_raw: float  # pre-dampening Kelly fraction
    kelly_adjusted: float  # post-dampening
    reasoning: str

    def stop_loss_long(self, entry: float) -> float:
        return entry * (1 - self.stop_distance_pct)

    def stop_loss_short(self, entry: float) -> float:
        return entry * (1 + self.stop_distance_pct)

    def target_long(self, entry: float, rr: float = 2.0) -> float:
        return entry * (1 + self.stop_distance_pct * rr)

    def target_short(self, entry: float, rr: float = 2.0) -> float:
        return entry * (1 - self.stop_distance_pct * rr)


# ─── Engine ────────────────────────────────────────────────────────────────────


class VolatilityEngine:
    """
    Dynamic risk calculator.

    Input (pick one):
      - price + atr  → compute atr_pct directly
      - price + atr_pct (precomputed)
      - regime (VolatilityRegime) directly

    If regime is given, it takes precedence.
    """

    # Kelly scale cap (never risk more than 20% of capital)
    MAX_KELLY = 0.20
    MIN_KELLY = 0.01

    def __init__(
        self,
        win_rate: float = 0.55,
        avg_win_pct: float = 0.03,
        avg_loss_pct: float = 0.015,
    ):
        self.win_rate = win_rate
        self.avg_win_pct = avg_win_pct
        self.avg_loss_pct = avg_loss_pct

    # ── ATR helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def atr_to_regime(atr_pct: float) -> VolatilityRegime:
        """Classify volatility regime from ATR%."""
        if atr_pct < 0.015:
            return VolatilityRegime.LOW
        if atr_pct < 0.030:
            return VolatilityRegime.NORMAL
        if atr_pct < 0.050:
            return VolatilityRegime.HIGH
        return VolatilityRegime.EXTREME

    @classmethod
    def from_price_atr(cls, price: float, atr: float) -> "VolatilityEngine":
        """Create engine pre-computing atr_pct."""
        inst = cls()
        inst._atr_pct = atr / price if price > 0 else 0.0
        return inst

    @classmethod
    def from_regime(cls, regime: VolatilityRegime) -> "VolatilityEngine":
        """Create engine with explicit regime (bypasses ATR calc)."""
        inst = cls()
        inst._regime_override = regime
        inst._atr_pct = 0.0
        return inst

    def analyze(
        self,
        symbol: str = "BTCUSDT",
        price: float = 50000,
        atr: float = None,
        atr_pct: float = None,
        regime: VolatilityRegime = None,
    ) -> VolatilityRisk:
        """
        Full risk analysis.

        Resolves regime in order:
          1. explicit regime arg
          2. regime override (from from_regime())
          3. atr / atr_pct → regime
          4. fallback: NORMAL
        """
        # Resolve ATR%
        if atr_pct is not None:
            resolved_atr_pct = atr_pct
        elif atr is not None and price > 0:
            resolved_atr_pct = atr / price
        elif hasattr(self, "_atr_pct"):
            resolved_atr_pct = self._atr_pct
        else:
            logger.warning(f"[VolatilityEngine] No ATR data for {symbol}, using NORMAL regime")
            resolved_atr_pct = 0.020

        # Resolve regime
        if regime is not None:
            resolved_regime = regime
        elif hasattr(self, "_regime_override"):
            resolved_regime = self._regime_override
        else:
            resolved_regime = self.atr_to_regime(resolved_atr_pct)

        # Kelly
        kelly_raw = self._kelly(self.win_rate, self.avg_win_pct, self.avg_loss_pct)
        kelly_mult = REGIME_POSITION_KELLY_MULT[resolved_regime]
        kelly_adjusted = max(self.MIN_KELLY, min(kelly_raw * kelly_mult, self.MAX_KELLY))

        # Risk pct
        risk_pct = REGIME_RISK_PCT[resolved_regime]

        # Stop distance
        stop_distance_pct = REGIME_STOP_MULTIPLIER[resolved_regime]

        # Confidence drop (V-06)
        confidence_drop = REGIME_CONFIDENCE_DROP[resolved_regime]

        reasoning = (
            f"VolatilityEngine: {resolved_regime.value} regime "
            f"(ATR={resolved_atr_pct * 100:.2f}%), "
            f"Kelly={kelly_raw:.3f}→{kelly_adjusted:.3f}, "
            f"risk_pct={risk_pct * 100:.1f}%, "
            f"stop_dist={stop_distance_pct * 100:.1f}%, "
            f"V-06_drop={confidence_drop}"
        )

        return VolatilityRisk(
            regime=resolved_regime,
            risk_pct=risk_pct,
            position_size=kelly_adjusted,
            atr_pct=resolved_atr_pct,
            stop_distance_pct=stop_distance_pct,
            confidence_drop=confidence_drop,
            kelly_raw=kelly_raw,
            kelly_adjusted=kelly_adjusted,
            reasoning=reasoning,
        )

    def apply_volatility_guard(
        self,
        raw_confidence: int,
        regime: VolatilityRegime,
    ) -> tuple[int, str]:
        """
        V-06: Reduce confidence in high-volatility regimes.

        Returns (adjusted_confidence, guard_label).
        """
        drop = REGIME_CONFIDENCE_DROP[regime]
        adjusted = max(30, raw_confidence - drop)
        label = f"V-06(dr={drop})" if drop > 0 else ""
        return adjusted, label

    # ── Kelly Criterion ─────────────────────────────────────────────────────────

    def _kelly(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        if avg_loss <= 0 or win_rate <= 0:
            return self.MIN_KELLY
        wl_ratio = avg_win / avg_loss
        kelly = (win_rate * wl_ratio - (1 - win_rate)) / wl_ratio
        return max(self.MIN_KELLY, min(kelly, self.MAX_KELLY))


# ── Singleton helper ──────────────────────────────────────────────────────────

_volatility_cache: dict[str, tuple[float, VolatilityRisk]] = {}


def get_volatility_risk(
    symbol: str,
    price: float,
    atr: float = None,
    atr_pct: float = None,
    regime: VolatilityRegime = None,
) -> VolatilityRisk:
    """
    Fetch-or-compute volatility risk for symbol.

    Results are cached by symbol to avoid redundant API calls within a session.
    Pass regime=VolatilityRegime.EXTREME to force AVOID.
    """
    cache_key = f"{symbol}:{regime}" if regime else symbol

    if cache_key in _volatility_cache:
        return _volatility_cache[cache_key]

    engine = VolatilityEngine.from_price_atr(price, atr) if atr else VolatilityEngine()
    if regime:
        engine = VolatilityEngine.from_regime(regime)

    risk = engine.analyze(symbol=symbol, price=price, atr=atr, atr_pct=atr_pct, regime=regime)
    _volatility_cache[cache_key] = (price, risk)
    return risk


def clear_volatility_cache():
    _volatility_cache.clear()


# ── ATR utilities (for standalone use) ────────────────────────────────────────


def calculate_atr(highs_lows_closes: list[list[float]], period: int = 14) -> float:
    """
    Calculate ATR from [[high, low, close], ...] data.

    Used by RiskAgent and QuantAgent.
    """
    if len(highs_lows_closes) < period + 1:
        return (highs_lows_closes[-1][2] * 0.02) if highs_lows_closes else 100.0

    true_ranges = []
    for i in range(1, len(highs_lows_closes)):
        high = highs_lows_closes[i][0]
        low = highs_lows_closes[i][1]
        prev_close = highs_lows_closes[i - 1][2]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        true_ranges.append(tr)

    return sum(true_ranges[-period:]) / period


def atr_from_binance(symbol: str, interval: str = "1d", limit: int = 30) -> float:
    """Fetch Binance klines and compute ATR via data_room blueprint (R3)."""
    try:
        from data_room import blueprint as dr_blueprint
        closes = dr_blueprint.get_klines(symbol, interval=interval, limit=limit)
        # derive klines with high/low proxies from close (best-effort for ATR fallback)
        klines = [[c, c, c] for c in closes]
        return calculate_atr(klines)
    except Exception as e:
        logger.warning(f"[VolatilityEngine] Failed to fetch ATR for {symbol}: {e}")
        return 0.0
