"""meta_rl/quant/regime.py -- ATOM-META-RL-024: Market regime detection"""

from __future__ import annotations

from enum import Enum

import numpy as np


class Regime(Enum):
    BULL = "BULL"
    BEAR = "BEAR"
    VOLATILE = "VOLATILE"
    CRISIS = "CRISIS"
    SIDEWAYS = "SIDEWAYS"


class RegimeDetector:
    def __init__(self, volatility_window: int = 20, trend_window: int = 50):
        self.vol_window = volatility_window
        self.trend_window = trend_window

    def detect(self, prices: list[float]) -> Regime:
        if len(prices) < self.trend_window:
            return Regime.SIDEWAYS
        arr = np.array(prices[-self.trend_window :])
        returns = np.diff(arr) / arr[:-1]
        vol = np.std(returns) * np.sqrt(252)
        trend = (arr[-1] - arr[0]) / arr[0]
        if vol > 0.40:
            return Regime.CRISIS
        elif vol > 0.25:
            return Regime.VOLATILE
        elif trend > 0.15:
            return Regime.BULL
        elif trend < -0.10:
            return Regime.BEAR
        return Regime.SIDEWAYS
