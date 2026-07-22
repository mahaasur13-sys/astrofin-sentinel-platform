"""db/karl_replay.py — PostgresReplayBuffer (ATOM-019)
Stores KARL trajectories in PostgreSQL + TimescaleDB.
"""

import json
from typing import Any

from db.models import KARLTrajectory
from db.session import pg_session


class PostgresReplayBuffer:
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size

    def add(
        self,
        trajectory: dict[str, Any],
        metrics: dict[str, Any],
        outcome: float,
        market_context: dict[str, Any],
    ) -> None:
        with pg_session() as s:
            traj = KARLTrajectory(
                trajectory_id=trajectory.get("id", "unknown"),
                symbol=market_context.get("symbol", "BTCUSDT"),
                regime=market_context.get("regime", "NORMAL"),
                outcome=outcome,
                total_reward=metrics.get("total_reward", 0),
                sharpe_ratio=metrics.get("sharpe_ratio", 0),
                max_drawdown=metrics.get("max_drawdown", 0),
                win_rate=metrics.get("win_rate", 0),
                trade_count=metrics.get("trade_count", 0),
                avg_confidence=metrics.get("avg_confidence", 50),
                regime_stability=metrics.get("regime_stability", 1.0),
                steps_json=json.dumps(trajectory.get("steps", [])),
                metadata_json=json.dumps(trajectory.get("metadata", {})),
            )
            s.add(traj)

    def get_all(self, limit: int = 1000) -> list[dict]:
        with pg_session() as s:
            rows = s.query(KARLTrajectory).order_by(KARLTrajectory.created_at.desc()).limit(limit).all()
            return [self._row_to_dict(r) for r in rows]

    def get_by_symbol(self, symbol: str, limit: int = 100) -> list[dict]:
        with pg_session() as s:
            rows = (
                s.query(KARLTrajectory)
                .filter(KARLTrajectory.symbol == symbol)
                .order_by(KARLTrajectory.created_at.desc())
                .limit(limit)
                .all()
            )
            return [self._row_to_dict(r) for r in rows]

    def get_similar(self, regime: str, action: str, limit: int = 10) -> list[dict]:
        with pg_session() as s:
            rows = (
                s.query(KARLTrajectory)
                .filter(KARLTrajectory.regime == regime)
                .order_by(KARLTrajectory.outcome.desc())
                .limit(limit)
                .all()
            )
            return [self._row_to_dict(r) for r in rows]

    def size(self) -> int:
        with pg_session() as s:
            from sqlalchemy import func

            return s.query(func.count(KARLTrajectory.id)).scalar() or 0

    def _row_to_dict(self, row) -> dict:
        return {
            "id": row.id,
            "trajectory_id": row.trajectory_id,
            "symbol": row.symbol,
            "regime": row.regime,
            "outcome": row.outcome,
            "total_reward": row.total_reward,
            "sharpe_ratio": row.sharpe_ratio,
            "max_drawdown": row.max_drawdown,
            "win_rate": row.win_rate,
            "trade_count": row.trade_count,
            "avg_confidence": row.avg_confidence,
            "regime_stability": row.regime_stability,
            "steps": json.loads(row.steps_json or "[]"),
            "metadata": json.loads(row.metadata_json or "{}"),
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }


_PG_BUFFER: PostgresReplayBuffer | None = None


def get_default_pg_buffer() -> PostgresReplayBuffer:
    global _PG_BUFFER
    if _PG_BUFFER is None:
        _PG_BUFFER = PostgresReplayBuffer()
    return _PG_BUFFER
