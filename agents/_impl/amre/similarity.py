"""amre/similarity.py — Trajectory similarity + Q* estimation"""

from __future__ import annotations

import math

from .trajectory import MarketState, Trajectory, trajectory_from_state


def trajectory_distance(t1: Trajectory, t2: Trajectory) -> float:
    if not t1.steps or not t2.steps:
        return 1.0
    s1, s2 = t1.steps[0], t2.steps[0]
    price_diff = abs(s1.price - s2.price) / max(s1.price, s2.price, 1)
    regime_match = 0.0 if s1.regime == s2.regime else 1.0
    return min(1.0, price_diff + regime_match)


def is_similar_trajectory(
    t1: Trajectory, t2: Trajectory, threshold: float = 0.3
) -> bool:
    return trajectory_distance(t1, t2) < threshold


def jensen_shannon_divergence(p: list[float], q: list[float]) -> float:
    def kl(a, b):
        return sum(
            x * math.log(x / max(y, 1e-10)) for x, y in zip(a, b, strict=False) if x > 0
        )

    m = [(x + y) / 2 for x, y in zip(p, q, strict=False)]
    return 0.5 * kl(p, m) + 0.5 * kl(q, m)


def estimate_q_star(rewards: list[float], method: str = "simple") -> float:
    if not rewards:
        return 0.0
    if method == "simple":
        pos = [max(0, r) for r in rewards]
        neg = [abs(min(0, r)) for r in rewards]
        pos_sum = sum(pos)
        neg_sum = sum(neg)
        if pos_sum + neg_sum == 0:
            return 0.5
        return pos_sum / (pos_sum + neg_sum)
    elif method == "sharpe":
        mean_r = sum(rewards) / len(rewards)
        std_r = (sum((r - mean_r) ** 2 for r in rewards) / len(rewards)) ** 0.5
        if std_r == 0:
            return 0.5
        sharpe = mean_r / std_r
        return max(0, min(1, (sharpe + 3) / 6))
    elif method == "sortino":
        mean_r = sum(rewards) / len(rewards)
        downside = [min(0, r - mean_r) ** 2 for r in rewards]
        down_std = (sum(downside) / len(downside)) ** 0.5
        if down_std == 0:
            return 0.5
        sortino = mean_r / down_std
        return max(0, min(1, (sortino + 3) / 6))
    return 0.5


def select_top_k_trajectories(
    trajectories: list[Trajectory], k: int = 5
) -> list[Trajectory]:
    if len(trajectories) <= k:
        return trajectories
    scored = [
        (t, sum(s.confidence for s in t.steps) / max(len(t.steps), 1))
        for t in trajectories
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [t for t, _ in scored[:k]]


def knn_q_star(
    state: MarketState, buffer_trajectories: list[Trajectory], k: int = 5
) -> float:
    if not buffer_trajectories:
        return estimate_q_star([])
    scored = [
        (t, trajectory_distance(t, trajectory_from_state(state)))
        for t in buffer_trajectories
    ]
    scored.sort(key=lambda x: x[1])
    neighbors = [s for s, d in scored[:k]]
    if not neighbors:
        return 0.5
    rewards = [
        sum(st.confidence / 100.0 for st in t.steps) / max(len(t.steps), 1)
        for t in neighbors
    ]
    return sum(rewards) / len(rewards)
