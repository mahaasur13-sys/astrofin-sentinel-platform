#!/usr/bin/env python3
"""
Probabilistic Admission Controller — predicts overload before it happens.
Replaces static threshold (GPU>85%) with P(overload in next M minutes).

v4.1 → v5 bridge component.
"""
import math
import sys
from typing import Dict, Optional
from dataclasses import dataclass

from state_store import StateStore


# Rolling window estimator (online stats, no distribution assumption)
class RollingWindow:
    """Online rolling mean + variance (Welford's algorithm)."""
    def __init__(self, window_size: int = 60):
        self.n = 0
        self.mean = 0.0
        self.M2 = 0.0
        self.max_seen = -math.inf
        self.min_seen = math.inf
        self.window_size = window_size
        self.history = []

    def update(self, x: float) -> None:
        self.n += 1
        delta = x - self.mean
        self.mean += delta / self.n
        delta2 = x - self.mean
        self.M2 += delta * delta2
        self.history.append(x)
        if len(self.history) > self.window_size:
            self.history.pop(0)
        self.max_seen = max(self.max_seen, x)
        self.min_seen = min(self.min_seen, x)

    @property
    def variance(self) -> float:
        return self.M2 / self.n if self.n > 1 else 0.0

    @property
    def std(self) -> float:
        return math.sqrt(self.variance)


class ProbabilisticAdmissionController:
    """
    Computes P(overload | next M minutes) using online statistics.
    
    Overload is defined as: gpu_util > OVERLOAD_THRESHOLD (e.g., 85%)
    
    Strategy:
      - Fit a Gaussian on recent GPU utilization
      - Estimate P(GPU > threshold) via CDF
      - Reject if P > reject_threshold (e.g., 0.30)
    """
    
    OVERLOAD_THRESHOLD = 85.0   # GPU % threshold
    REJECT_THRESHOLD  = 0.30   # P(overload) rejection cutoff
    CONFIDENCE_ALPHA  = 0.05   # minimum data confidence (at least N samples)

    def __init__(self, windows: Dict[str, RollingWindow]):
        # windows["rtx-node"]: RollingWindow for GPU util
        # windows["rk3576"]: RollingWindow for CPU util
        self.windows = windows

    def p_overload(self, node_id: str) -> float:
        """
        Compute P(GPU_util > OVERLOAD_THRESHOLD | history).
        Uses Gaussian CDF approximation when n >= 30.
        Falls back to empirical frequency otherwise.
        """
        key = node_id
        if key not in self.windows:
            return 0.0
        w = self.windows[key]
        if w.n < max(30, self.CONFIDENCE_ALPHA * w.window_size):
            # Not enough data → use empirical frequency
            overload_count = sum(1 for x in w.history if x > self.OVERLOAD_THRESHOLD)
            return overload_count / w.n if w.n > 0 else 0.0

        # Gaussian approximation
        mu = w.mean
        sigma = w.std if w.std > 0 else 0.001
        z = (self.OVERLOAD_THRESHOLD - mu) / sigma
        # P(X > threshold) = 1 - Phi(z) = Phi(-z)
        return self._normal_cdf(-z)

    def _normal_cdf(self, z: float) -> float:
        """Approximation of standard normal CDF at z."""
        # Abramowitz and Stegun approximation
        t = 1.0 / (1.0 + 0.2316419 * abs(z))
        poly = t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))))
        return 1.0 - (1.0 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * z * z) * poly

    def should_reject(self, node_id: str, lookahead_minutes: int = 10) -> tuple[bool, float]:
        """
        Main decision: reject if P(overload in next M min) > threshold.
        Returns (should_reject, p_overload).
        """
        p = self.p_overload(node_id)
        reject = p > self.REJECT_THRESHOLD
        return reject, p

    def update(self, node_id: str, gpu_util: float) -> None:
        """Feed a new GPU utilization reading."""
        if node_id not in self.windows:
            self.windows[node_id] = RollingWindow()
        self.windows[node_id].update(gpu_util)


def create_from_state_store(db: StateStore) -> ProbabilisticAdmissionController:
    """
    Bootstrap rolling windows from historical GPU metrics in state_store.
    Real implementation: query timeseries from Prometheus or job_events table.
    """
    windows = {}  # node_id → RollingWindow
    # Placeholder: in production, load recent GPU readings from job_engine history
    return ProbabilisticAdmissionController(windows)


if __name__ == "__main__":
    # Demo: simulate rolling GPU util readings
    import random
    windows = {}
    controller = ProbabilisticAdmissionController(windows)
    
    # Simulate 100 readings (mix of normal and spike periods)
    for i in range(60):
        if 20 <= i < 30:
            val = random.gauss(88, 5)   # spike period
        else:
            val = random.gauss(55, 10)  # normal period
        controller.update("rtx-node", val)
    
    reject, p = controller.should_reject("rtx-node")
    print(f"rtx-node: P(overload) = {p:.3f} → {'REJECT' if reject else 'ADMIT'}")
