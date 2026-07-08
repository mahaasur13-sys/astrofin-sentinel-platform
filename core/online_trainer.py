"""
core/online_trainer.py — ATOM-STEP-6: Online RL Trainer
======================================================
Trains Kepler + market models online using REINFORCE-style policy gradient.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PolicyParams:
    """Trainable policy parameters."""

    base_position_pct: float = 0.05
    astro_position_scale: float = 0.02
    risk_position_scale: float = 0.03
    uncertainty_cap: float = 0.70
    min_confidence_for_trade: float = 50.0


@dataclass
class Experience:
    timestamp: datetime
    state_hash: str
    action_position_pct: float
    reward: float
    signal_strength: float
    uncertainty: float
    astro_alignment: float
    actual_pnl: float


@dataclass
class TrainingState:
    episode: int = 0
    total_experiences: int = 0
    best_reward: float = float("-inf")
    reward_history: list[float] = field(default_factory=list)
    params_history: list[dict] = field(default_factory=list)


class OnlineTrainer:
    """
    REINFORCE-style online trainer for position sizing policy.
    Updates PolicyParams based on reward feedback from executed trades.
    """

    def __init__(
        self,
        params: PolicyParams | None = None,
        learning_rate: float = 0.01,
        gamma: float = 0.95,
        exploration_noise: float = 0.1,
    ):
        self.params = params or PolicyParams()
        self.lr = learning_rate
        self.gamma = gamma
        self.noise = exploration_noise
        self.experience_buffer: list[Experience] = []
        self.state = TrainingState()
        self._best_params = PolicyParams(
            **{
                k: getattr(self.params, k)
                for k in [
                    "base_position_pct",
                    "astro_position_scale",
                    "risk_position_scale",
                    "uncertainty_cap",
                    "min_confidence_for_trade",
                ]
            }
        )

    def decide_position(
        self,
        signal_strength: float,  # 0-100
        uncertainty: float,  # 0-1
        astro_alignment: float,  # -1 to +1
        regime: str = "NORMAL",  # LOW/NORMAL/HIGH/EXTREME
    ) -> dict:
        """
        Decide position size based on current policy + exploration noise.
        Returns: {position_pct, explore, params_snapshot}
        """
        base = self.params.base_position_pct
        astro_adj = self.params.astro_position_scale * max(astro_alignment, 0)
        self.params.risk_position_scale * (1.0 - uncertainty)

        # Skip if uncertainty too high
        if uncertainty > self.params.min_confidence_for_trade / 100:
            if uncertainty > self.params.uncertainty_cap:
                return {
                    "position_pct": 0.0,
                    "explore": False,
                    "reason": f"uncertainty_cap_exceeded_{uncertainty:.2f}",
                    "params_snapshot": self._snapshot(),
                }

        # Regime-based risk multiplier
        regime_mult = {"LOW": 1.0, "NORMAL": 0.75, "HIGH": 0.5, "EXTREME": 0.25}.get(regime, 0.5)

        position = max(0.0, base + astro_adj - self.params.risk_position_scale * uncertainty)
        position *= regime_mult

        # Exploration noise
        explore = random.gauss(0, self.noise) > 0
        if explore:
            position += random.gauss(0, self.noise * 0.05)

        position = max(0.0, min(position, 1.0))

        return {
            "position_pct": position,
            "explore": explore,
            "signal_strength": signal_strength,
            "uncertainty": uncertainty,
            "astro_alignment": astro_alignment,
            "params_snapshot": self._snapshot(),
        }

    def record_experience(
        self,
        timestamp: datetime,
        state_hash: str,
        action_position_pct: float,
        reward: float,
        signal_strength: float,
        uncertainty: float,
        astro_alignment: float,
        actual_pnl: float,
    ):
        """Add experience to replay buffer."""
        exp = Experience(
            timestamp=timestamp,
            state_hash=state_hash,
            action_position_pct=action_position_pct,
            reward=reward,
            signal_strength=signal_strength,
            uncertainty=uncertainty,
            astro_alignment=astro_alignment,
            actual_pnl=actual_pnl,
        )
        self.experience_buffer.append(exp)
        self.state.total_experiences += 1
        self.state.reward_history.append(reward)

    def update_policy(self, batch_size: int = 32) -> dict:
        """
        REINFORCE policy gradient update.
        Computes gradient estimate from recent experiences and updates params.
        """
        if len(self.experience_buffer) < batch_size:
            return {"updated": False, "reason": "insufficient_experiences"}

        # Sample recent experiences
        recent = self.experience_buffer[-batch_size:]
        mean_reward = sum(e.reward for e in recent) / len(recent)

        # Baseline = exponential moving average of past rewards
        if self.state.reward_history:
            baseline = sum(self.state.reward_history[-100:]) / min(len(self.state.reward_history), 100)
        else:
            baseline = 0.0

        # Advantage estimate
        advantage = mean_reward - baseline

        # Gradient estimates for each parameter
        lr = self.lr
        d_base = 0.0
        d_astro = 0.0
        d_risk = 0.0

        for exp in recent:
            # Gradient of position w.r.t. base_position_pct ≈ 1.0
            d_base += advantage * 1.0 * (1.0 if exp.reward > baseline else -1.0)
            # Gradient w.r.t. astro_position_scale
            d_astro += advantage * max(exp.astro_alignment, 0) * (1.0 if exp.reward > baseline else -1.0)
            # Gradient w.r.t. risk_position_scale (penalized by uncertainty)
            d_risk += advantage * (1.0 - exp.uncertainty) * (1.0 if exp.reward > baseline else -1.0)

        # Normalize gradients
        n = len(recent)
        d_base /= n
        d_astro /= n
        d_risk /= n

        # Apply gradient ascent (maximize reward)
        old_base = self.params.base_position_pct
        self.params.base_position_pct = max(0.01, min(0.2, self.params.base_position_pct + lr * d_base))
        self.params.astro_position_scale = max(0.0, min(0.1, self.params.astro_position_scale + lr * d_astro))
        self.params.risk_position_scale = max(0.0, min(0.1, self.params.risk_position_scale + lr * d_risk))

        # Track best
        if mean_reward > self.state.best_reward:
            self.state.best_reward = mean_reward
            self._best_params = PolicyParams(
                **{
                    k: getattr(self.params, k)
                    for k in [
                        "base_position_pct",
                        "astro_position_scale",
                        "risk_position_scale",
                        "uncertainty_cap",
                        "min_confidence_for_trade",
                    ]
                }
            )

        self.state.episode += 1
        self.state.params_history.append(self._snapshot())

        return {
            "updated": True,
            "episode": self.state.episode,
            "mean_reward": mean_reward,
            "baseline": baseline,
            "advantage": advantage,
            "param_deltas": {
                "base_position_pct": self.params.base_position_pct - old_base,
                "astro_position_scale": self.params.astro_position_scale,
                "risk_position_scale": self.params.risk_position_scale,
            },
            "best_reward": self.state.best_reward,
        }

    def reset_to_best(self):
        """Reset parameters to best observed configuration."""
        self.params = PolicyParams(
            **{
                k: getattr(self._best_params, k)
                for k in [
                    "base_position_pct",
                    "astro_position_scale",
                    "risk_position_scale",
                    "uncertainty_cap",
                    "min_confidence_for_trade",
                ]
            }
        )

    def _snapshot(self) -> dict:
        return {
            k: getattr(self.params, k)
            for k in [
                "base_position_pct",
                "astro_position_scale",
                "risk_position_scale",
                "uncertainty_cap",
                "min_confidence_for_trade",
            ]
        }

    def save(self, path: str):
        data = {
            "params": self._snapshot(),
            "best_params": {
                k: getattr(self._best_params, k)
                for k in [
                    "base_position_pct",
                    "astro_position_scale",
                    "risk_position_scale",
                    "uncertainty_cap",
                    "min_confidence_for_trade",
                ]
            },
            "state": {
                "episode": self.state.episode,
                "total_experiences": self.state.total_experiences,
                "best_reward": self.state.best_reward,
            },
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def load(self, path: str):
        with open(path) as f:
            data = json.load(f)
        self.params = PolicyParams(**data["params"])
        self._best_params = PolicyParams(**data["best_params"])
        self.state = TrainingState(
            episode=data["state"]["episode"],
            total_experiences=data["state"]["total_experiences"],
            best_reward=data["state"]["best_reward"],
        )

    def run_episode(self, n_trades: int = 10) -> dict:
        """
        Run a simulated episode of n_trades.
        Returns: episode summary.
        """
        rewards = []
        for i in range(n_trades):
            ss = random.uniform(40, 90)
            unc = random.uniform(0.1, 0.9)
            astro = random.uniform(-1, 1)
            regime = random.choice(["LOW", "NORMAL", "HIGH"])
            decision = self.decide_position(ss, unc, astro, regime)
            pos = decision["position_pct"]
            if pos == 0.0:
                continue
            # Simulate outcome
            pnl = random.gauss(0.5, 2.0) * pos * 100
            reward = pnl + 0.1 * astro * abs(pos)
            self.record_experience(
                timestamp=datetime.utcnow(),
                state_hash=f"state_{i}",
                action_position_pct=pos,
                reward=reward,
                signal_strength=ss,
                uncertainty=unc,
                astro_alignment=astro,
                actual_pnl=pnl,
            )
            rewards.append(reward)

        update = self.update_policy()
        return {
            "n_trades": n_trades,
            "executed_trades": len(rewards),
            "mean_reward": sum(rewards) / len(rewards) if rewards else 0.0,
            "update": update,
        }


if __name__ == "__main__":
    import numpy as np

    np.random.seed(42)
    random.seed(42)

    trainer = OnlineTrainer(learning_rate=0.005)

    print("=" * 60)
    print("ATOM-STEP-6: Online RL Trainer — Simulation")
    print("=" * 60)

    for ep in range(1, 21):
        result = trainer.run_episode(n_trades=20)
        update = result["update"]
        if update["updated"]:
            print(
                f"  Ep {ep:2d}: reward={result['mean_reward']:+.4f}  base={trainer.params.base_position_pct:.4f}  best={trainer.state.best_reward:.4f}"
            )

    print(f"\n  Best reward: {trainer.state.best_reward:.4f}")
    print(f"  Final params: {trainer._snapshot()}")
    print(f"  Experiences: {trainer.state.total_experiences}")
    print("  Saved → models/online_policy.json")
    trainer.save("models/online_policy.json")
