#!/usr/bin/env python3
"""
Objective Reweight Engine — self-adjusting utility function.
v6: U = fixed weights
v7: U = f(α(t), β(t), γ(t), δ(t))
Weight updates via gradient from regret signal.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import numpy as np


@dataclass
class ObjectiveWeights:
    alpha: float = 0.4   # throughput
    beta: float = 0.3    # reliability
    gamma: float = 0.15  # latency
    delta: float = 0.15  # energy
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def utility(self, throughput: float, reliability: float, latency: float, energy: float) -> float:
        return self.alpha * throughput + self.beta * reliability + self.gamma * latency + self.delta * energy


class ObjectiveReweighter:
    """
    Self-adjusting objective function weights.
    weights = weights + lr * gradient(regret_signal)
    """

    def __init__(self, lr: float = 0.01, momentum: float = 0.9, normalize: bool = True):
        self.lr = lr
        self.momentum = momentum
        self.normalize = normalize
        self._weights = ObjectiveWeights()
        self._gradient_accum: dict[str, float] = {"alpha": 0.0, "beta": 0.0, "gamma": 0.0, "delta": 0.0}

    def update(self, regret_signal: float, performance: dict) -> ObjectiveWeights:
        """
        Update weights using gradient ascent on negative regret.
        performance: {throughput, reliability, latency, energy}
        """
        perf = np.array([
            performance.get("throughput", 0.0),
            performance.get("reliability", 1.0),
            performance.get("latency", 0.0),
            performance.get("energy", 0.0),
        ])

        # Gradient = regret * performance (higher regret → adjust more)
        gradient = regret_signal * perf
        gradient = gradient / (np.linalg.norm(gradient) + 1e-9)

        # Momentum
        for i, key in enumerate(["alpha", "beta", "gamma", "delta"]):
            self._gradient_accum[key] = self.momentum * self._gradient_accum[key] + gradient[i]

        # Gradient ascent
        new_weights = ObjectiveWeights(
            alpha=max(0.05, self._weights.alpha + self.lr * self._gradient_accum["alpha"]),
            beta=max(0.05, self._weights.beta + self.lr * self._gradient_accum["beta"]),
            gamma=max(0.0, self._weights.gamma + self.lr * self._gradient_accum["gamma"]),
            delta=max(0.0, self._weights.delta + self.lr * self._gradient_accum["delta"]),
            timestamp=datetime.utcnow(),
        )

        # Normalize to sum=1
        if self.normalize:
            total = new_weights.alpha + new_weights.beta + new_weights.gamma + new_weights.delta
            new_weights.alpha /= total
            new_weights.beta /= total
            new_weights.gamma /= total
            new_weights.delta /= total

        self._weights = new_weights
        return self._weights

    def get(self) -> ObjectiveWeights:
        return self._weights
REWEIGH_EOF
