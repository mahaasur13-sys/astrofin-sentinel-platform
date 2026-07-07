"""amre/trajectory.py — Market state + Trajectory + TrajectoryStep"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TrajectoryStep:
    timestamp: str
    price: float
    regime: str
    signals: dict[str, float]
    confidence: int
    position: str | None = None


@dataclass
class Trajectory:
    steps: list[TrajectoryStep] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TrajectoryMetrics:
    total_reward: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    trade_count: int
    avg_confidence: float
    regime_stability: float


@dataclass
class MarketState:
    symbol: str
    price: float
    timeframe: str
    n_signals: int
    session_id: str
    timestamp: str
    regime: str = "NORMAL"
    trajectory: Trajectory | None = None
    reward: float | None = None
    confidence: int | None = None
    signal_diversity: int | None = None
    regime_stability: float | None = None
    market_regime: str | None = None
    is_contrarian: bool | None = None
    volatility_score: float | None = None


def market_state_hash(ms: MarketState) -> str:
    import hashlib

    data = f"{ms.symbol}:{ms.price}:{ms.timeframe}:{ms.n_signals}:{ms.regime}"
    return hashlib.md5(data.encode()).hexdigest()[:12]


def trajectory_from_state(ms: MarketState) -> Trajectory:
    step = TrajectoryStep(
        timestamp=ms.timestamp,
        price=ms.price,
        regime=ms.regime,
        signals={},
        confidence=ms.confidence or 50,
        position=None,
    )
    return Trajectory(steps=[step])


def compute_trajectory_metrics(traj: Trajectory) -> TrajectoryMetrics:
    if not traj.steps:
        return TrajectoryMetrics(0.0, 0.0, 0.0, 0.0, 0, 50.0, 0.0)
    rewards = [s.confidence / 100.0 for s in traj.steps]
    total = sum(rewards)
    avg = total / len(rewards) if rewards else 0
    win_rate = sum(1 for r in rewards if r > 0.5) / len(rewards) if rewards else 0
    peak = rewards[0] if rewards else 0
    dd = 0.0
    for r in rewards:
        peak = max(peak, r)
        dd = max(dd, (peak - r) / peak if peak > 0 else 0)
    variance = sum((r - avg) ** 2 for r in rewards) / len(rewards) if rewards else 0
    sharpe = (avg / (variance**0.5)) if variance > 0 else 0
    return TrajectoryMetrics(
        total_reward=round(total, 4),
        sharpe_ratio=round(sharpe, 4),
        max_drawdown=round(dd, 4),
        win_rate=round(win_rate, 4),
        trade_count=len(traj.steps),
        avg_confidence=round(sum(s.confidence for s in traj.steps) / len(traj.steps), 1),
        regime_stability=round(1.0 - dd, 4),
    )


def trajectory_to_dict(traj: Trajectory) -> dict:
    return {
        "steps": [{"timestamp": s.timestamp, "price": s.price, "regime": s.regime} for s in traj.steps],
        "metadata": traj.metadata,
    }


def trajectory_from_dict(data: dict) -> Trajectory:
    steps = [TrajectoryStep(**s) for s in data.get("steps", [])]
    return Trajectory(steps=steps, metadata=data.get("metadata", {}))
