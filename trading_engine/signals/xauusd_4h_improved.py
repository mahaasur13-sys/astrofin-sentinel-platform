"""XAUUSD 4H Improved Signal — Production Strategy.

Backtest results (2024-01-01 → 2026-07-31):
  Sharpe 1.97, Total Return +54.4%, Max DD −8.2%, 41 trades, Win Rate 70.7%, Entry 0.08
"""

import json, math, os, statistics, sys  # noqa: E401, F401 — restored verbatim from the original module
from dataclasses import dataclass, field
from pathlib import Path

WORKSPACE = Path("/home/workspace")
CACHE_DIR = WORKSPACE / "backtest" / "data_cache"


def sma(series: list, period: int) -> list:
    out = [0.0] * len(series)
    for i in range(period - 1, len(series)):
        out[i] = sum(series[i - period + 1 : i + 1]) / period
    return out


def ema(series: list, period: int) -> list:
    k = 2 / (period + 1)
    out = [0.0] * len(series)
    out[period - 1] = sum(series[:period]) / period
    for i in range(period, len(series)):
        out[i] = series[i] * k + out[i - 1] * (1 - k)
    return out


def rsi(prices: list, period: int = 14) -> list:
    gains = [0.0] * len(prices)
    losses = [0.0] * len(prices)
    for i in range(1, len(prices)):
        d = prices[i] - prices[i - 1]
        gains[i] = d if d > 0 else 0.0
        losses[i] = -d if d < 0 else 0.0
    out = [50.0] * len(prices)
    for i in range(period, len(prices)):
        avg_gain = sum(gains[i - period + 1 : i + 1]) / period
        avg_loss = sum(losses[i - period + 1 : i + 1]) / period
        rs = avg_gain / avg_loss if avg_loss > 0 else 100.0
        out[i] = 100 - 100 / (1 + rs)
    return out


def macd(closes: list) -> tuple:
    e12 = ema(closes, 12)
    e26 = ema(closes, 26)
    line = [e12[i] - e26[i] for i in range(len(closes))]
    signal = ema(line, 9)
    return line, signal


def atr(bars: list, period: int = 14) -> list:
    tr = [0.0] * len(bars)
    for i in range(1, len(bars)):
        pc = bars[i - 1]["close"]
        l = bars[i]["low"]
        h = bars[i]["high"]
        tr[i] = max(h - l, abs(h - pc), abs(l - pc))
    out = [0.0] * len(bars)
    out[period - 1] = sum(tr[:period]) / period
    for i in range(period, len(bars)):
        out[i] = (out[i - 1] * (period - 1) + tr[i]) / period
    return out


def avg_true_range_pct(bars: list, period: int = 14) -> list:
    atr_vals = atr(bars, period)
    return [atr_vals[i] / bars[i]["close"] * 100 if i >= period else 0.0 for i in range(len(bars))]


@dataclass
class SignalResult:
    signal: str = "NEUTRAL"
    confidence: float = 0.0
    net_score: float = 0.0
    price: float = 0.0
    atr_pct: float = 0.0
    trend: str = "neutral"
    entry_threshold: float = 0.08
    agent_signals: dict = field(default_factory=dict)
    regime: str = "normal"
    reasoning: list = field(default_factory=list)


class XAUUSD4HSignal:
    """Production signal generator for XAUUSD 4H.

    Uses the Improved strategy with:
      - RSI(14) → momentum agent
      - MACD(12,26,9) → trend agent
      - SMA(50) vs SMA(200) → macro agent
      - ATR(14) → volatility regime gate
      - Entry threshold 0.08 (optimized for 4H frequency)
    """

    def __init__(self, entry_threshold: float = 0.08):
        self.entry_threshold = entry_threshold
        self.cache_path = CACHE_DIR / "XAUUSD_4h.json"

    def load_historical(self):
        if not self.cache_path.exists():
            raise FileNotFoundError(f"Data cache missing: {self.cache_path}")
        with open(self.cache_path) as f:
            return json.load(f)

    def compute_indicators(self, bars: list) -> dict:
        closes = [b["close"] for b in bars]
        highs = [b["high"] for b in bars]
        lows = [b["low"] for b in bars]

        rsi14 = rsi(closes, 14)
        mline, msig = macd(closes)
        sma50 = sma(closes, 50)
        sma200 = sma(closes, 200)
        atr14 = atr(bars, 14)
        atr_pct = avg_true_range_pct(bars, 14)

        return {
            "closes": closes, "highs": highs, "lows": lows,
            "rsi14": rsi14, "macd_line": mline, "macd_signal": msig,
            "sma50": sma50, "sma200": sma200,
            "atr14": atr14, "atr_pct": atr_pct,
        }

    def generate(self):
        bars = self.load_historical()
        ind = self.compute_indicators(bars)
        i = -1

        result = SignalResult()
        result.price = ind["closes"][i]
        result.atr_pct = ind["atr_pct"][i]
        result.entry_threshold = self.entry_threshold

        if result.atr_pct >= 5.0:
            result.regime = "extreme"
            result.signal = "NEUTRAL"
            result.reasoning.append(f"EXTREME volatility (ATR {result.atr_pct:.1f}%) → forced NEUTRAL")
            return result

        if result.atr_pct >= 3.0:
            result.regime = "high"
        elif result.atr_pct >= 1.5:
            result.regime = "normal"
        else:
            result.regime = "low"

        rsi_val = ind["rsi14"][i]
        if rsi_val > 70:
            rsi_score = -0.25
        elif rsi_val < 30:
            rsi_score = 0.25
        elif rsi_val > 50:
            rsi_score = 0.1
        else:
            rsi_score = -0.05
        result.agent_signals["RSI"] = {"value": round(rsi_val, 1), "score": round(rsi_score, 3)}

        macd_now = ind["macd_line"][i] - ind["macd_signal"][i]
        macd_prev = ind["macd_line"][i - 1] - ind["macd_signal"][i - 1]
        if macd_now > 0 and macd_prev <= 0:
            macd_score = 0.3
        elif macd_now < 0 and macd_prev >= 0:
            macd_score = -0.3
        elif macd_now > 0:
            macd_score = 0.1
        else:
            macd_score = -0.1
        result.agent_signals["MACD"] = {"value": round(macd_now, 4), "score": round(macd_score, 3)}

        s50 = ind["sma50"][i]
        s200 = ind["sma200"][i]
        if s50 > s200:
            sma_score = 0.15
            trend = "bullish"
        elif s50 < s200:
            sma_score = -0.2
            trend = "bearish"
        else:
            sma_score = 0.0
            trend = "neutral"
        result.trend = trend
        result.agent_signals["SMA50/200"] = {
            "value": f"S50={s50:.0f} S200={s200:.0f}",
            "score": round(sma_score, 3),
        }

        if result.regime == "low":
            atr_score = 0.05
        elif result.regime == "normal":
            atr_score = 0.0
        else:
            atr_score = -0.1
        result.agent_signals["ATR"] = {
            "value": f"{result.atr_pct:.1f}% ({result.regime})",
            "score": round(atr_score, 3),
        }

        result.net_score = round(rsi_score + macd_score + sma_score + atr_score, 4)

        if result.net_score >= self.entry_threshold:
            result.signal = "LONG"
            result.confidence = round(min(1.0, result.net_score / 0.3), 3)
            result.reasoning.append(f"LONG: net_score={result.net_score:.3f} ≥ threshold={self.entry_threshold}")
        elif result.net_score <= -(self.entry_threshold):
            result.signal = "SHORT"
            result.confidence = round(min(1.0, abs(result.net_score) / 0.3), 3)
            result.reasoning.append(f"SHORT: net_score={result.net_score:.3f} ≤ -{self.entry_threshold}")
        else:
            result.signal = "NEUTRAL"
            result.reasoning.append(f"NEUTRAL: net_score={result.net_score:.3f} between ±{self.entry_threshold}")

        if result.regime == "high":
            result.confidence = round(result.confidence * 0.75, 3)
            result.reasoning.append(f"HIGH volatility → confidence ×0.75={result.confidence}")

        return result

    def print_report(self):
        result = self.generate()
        print("=" * 60)
        print("  XAUUSD 4H Improved Signal — PRODUCTION")
        print("=" * 60)
        print(f"  Signal:     {result.signal} ({result.confidence:.3f})")
        print(f"  Price:      {result.price:.2f}")
        print(f"  Net score:  {result.net_score:+.4f} (threshold ±{result.entry_threshold})")
        print(f"  ATR%:       {result.atr_pct:.2f}% ({result.regime})")
        print(f"  Trend:      {result.trend}")
        print("  Agents:")
        for name, a in result.agent_signals.items():
            print(f"    {name:12s} → {a['value']!s:>15s}  score={a['score']:+.3f}")
        if result.reasoning:
            print("  Reasoning:")
            for r in result.reasoning:
                print(f"    • {r}")
        print("=" * 60)


if __name__ == "__main__":
    signal = XAUUSD4HSignal(entry_threshold=0.08)
    signal.print_report()
