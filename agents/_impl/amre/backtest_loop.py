"""amre/backtest_loop.py — Backtest-as-a-Service (ATOM-KARL-010)
Непрерывный backtest loop для честной оценки и накопления buffer.
Каждый тик исторических данных проходит через:
state → decision → reward_evaluation → buffer.add
"""

from __future__ import annotations

from collections.abc import Callable, Generator
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from .replay_buffer import BufferEntry, ReplayBuffer, get_default_buffer
from .trajectory import MarketState, compute_trajectory_metrics, trajectory_from_state


class BacktestRegime(Enum):
    """Режимы backtest"""

    WALK_FORWARD = "walk_forward"  # Forward testing on unseen data
    RETRAIN_ON_HISTORY = "retrain"  # Retrain on historical window
    CONTINUOUS = "continuous"  # Rolling window continuous
    OOS_VALIDATION = "oos"  # Out-of-sample validation only


@dataclass
class BacktestStep:
    """Один шаг backtest"""

    step_id: int
    timestamp: str
    price: float
    regime: str
    decision: str
    confidence: int
    position_pct: float
    reward_actual: float
    reward_predicted: float
    error: float
    is_oos: bool


@dataclass
class BacktestResult:
    """Результат backtest сессии"""

    session_id: str
    start_date: str
    end_date: str
    total_steps: int
    oos_steps: int

    # Метрики
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    total_return: float
    avg_confidence: float
    avg_error: float

    # Q* метрики
    q_star_initial: float
    q_star_final: float
    q_star_improvement: float

    # OOS метрики
    oos_win_rate: float
    oos_avg_error: float

    # Режим
    regime: BacktestRegime

    # Детали
    steps: list[BacktestStep]

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "total_steps": self.total_steps,
            "oos_steps": self.oos_steps,
            "win_rate": round(self.win_rate, 4),
            "sharpe_ratio": round(self.sharpe_ratio, 4),
            "max_drawdown": round(self.max_drawdown, 4),
            "total_return": round(self.total_return, 4),
            "avg_confidence": round(self.avg_confidence, 2),
            "avg_error": round(self.avg_error, 4),
            "q_star_initial": round(self.q_star_initial, 4),
            "q_star_final": round(self.q_star_final, 4),
            "q_star_improvement": round(self.q_star_improvement, 4),
            "oos_win_rate": round(self.oos_win_rate, 4),
            "oos_avg_error": round(self.oos_avg_error, 4),
            "regime": self.regime.value,
        }


class ContinuousBacktest:
    """
    Backtest-as-a-Service:

    Loop:
        for t in historical_data:
            state = build_state(t)
            decision = agent.run(state)
            reward = evaluate_future(t, horizon=H)
            buffer.add(decision, reward)

    Особенности:
    - Walk-forward validation
    - Rolling window для retrain
    - OOS evaluation на каждом шаге
    - Accumulating replay buffer
    """

    def __init__(
        self,
        buffer: ReplayBuffer | None = None,
        horizon: int = 5,
        oos_ratio: float = 0.2,
        window_size: int = 100,
    ):
        self.buffer = buffer or get_default_buffer()
        self.horizon = horizon  # Горизонт для reward evaluation
        self.oos_ratio = oos_ratio  # Доля OOS данных
        self.window_size = window_size  # Размер окна для rolling

        self.results: list[BacktestResult] = []
        self._q_star_history: list[float] = []

    def run_on_data(
        self,
        historical_data: list[dict[str, Any]],
        agent_fn: Callable[[MarketState], dict[str, Any]],
        regime_splitter: Callable[[float], str] | None = None,
    ) -> BacktestResult:
        """
        Запустить backtest на исторических данных.

        Args:
            historical_data: List of {timestamp, price, ...}
            agent_fn: Функция агента которая принимает MarketState и возвращает {signal, confidence, ...}
            regime_splitter: Функция определения regime по цене
        """
        if len(historical_data) < self.horizon + 10:
            raise ValueError(f"Need at least {self.horizon + 10} data points")

        # Определяем split point
        split_idx = int(len(historical_data) * self.oos_ratio)
        train_data = historical_data[split_idx:]
        oos_data = historical_data[:split_idx]

        steps: list[BacktestStep] = []
        q_star_initial = self._estimate_q_star()

        # Первая фаза: train (walk forward)
        all_train_rewards = []
        for i, bar in enumerate(train_data):
            state = self._build_state(bar, regime_splitter)

            # Decision
            decision = agent_fn(state)

            # Reward evaluation через horizon шагов вперёд
            reward_actual, reward_predicted = self._evaluate_reward(
                historical_data, split_idx + i, horizon=self.horizon
            )

            step_error = abs(reward_actual - reward_predicted)
            all_train_rewards.append(reward_actual)

            # Добавляем в buffer
            self._add_to_buffer(state, decision, reward_actual)

            step = BacktestStep(
                step_id=i,
                timestamp=bar.get("timestamp", ""),
                price=bar.get("price", 0.0),
                regime=state.regime,
                decision=decision.get("signal", "NEUTRAL"),
                confidence=decision.get("confidence", 50),
                position_pct=decision.get("position_pct", 0.0),
                reward_actual=reward_actual,
                reward_predicted=reward_predicted,
                error=step_error,
                is_oos=False,
            )
            steps.append(step)

        # Вторая фаза: OOS validation
        all_oos_rewards = []
        oos_steps = []
        for i, bar in enumerate(oos_data):
            state = self._build_state(bar, regime_splitter)
            decision = agent_fn(state)

            reward_actual, reward_predicted = self._evaluate_reward(
                historical_data, i, horizon=self.horizon
            )

            step_error = abs(reward_actual - reward_predicted)
            all_oos_rewards.append(reward_actual)

            step = BacktestStep(
                step_id=len(steps) + i,
                timestamp=bar.get("timestamp", ""),
                price=bar.get("price", 0.0),
                regime=state.regime,
                decision=decision.get("signal", "NEUTRAL"),
                confidence=decision.get("confidence", 50),
                position_pct=decision.get("position_pct", 0.0),
                reward_actual=reward_actual,
                reward_predicted=reward_predicted,
                error=step_error,
                is_oos=True,
            )
            oos_steps.append(step)

        # Собираем метрики
        all_steps = steps + oos_steps

        # Q* evolution
        q_star_final = self._estimate_q_star()

        # Win rate
        train_wins = [s for s in steps if s.reward_actual > 0]
        oos_wins = [s for s in oos_steps if s.reward_actual > 0]

        result = BacktestResult(
            session_id=f"bt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            start_date=historical_data[0].get("timestamp", ""),
            end_date=historical_data[-1].get("timestamp", ""),
            total_steps=len(all_steps),
            oos_steps=len(oos_steps),
            win_rate=len(train_wins) / len(steps) if steps else 0,
            sharpe_ratio=self._compute_sharpe(all_train_rewards),
            max_drawdown=self._compute_max_drawdown(all_train_rewards),
            total_return=sum(all_train_rewards),
            avg_confidence=(
                sum(s.confidence for s in steps) / len(steps) if steps else 0
            ),
            avg_error=sum(s.error for s in steps) / len(steps) if steps else 0,
            q_star_initial=q_star_initial,
            q_star_final=q_star_final,
            q_star_improvement=q_star_final - q_star_initial,
            oos_win_rate=len(oos_wins) / len(oos_steps) if oos_steps else 0,
            oos_avg_error=(
                sum(s.error for s in oos_steps) / len(oos_steps) if oos_steps else 0
            ),
            regime=BacktestRegime.WALK_FORWARD,
            steps=all_steps,
        )

        self.results.append(result)
        self._q_star_history.append(q_star_final)

        return result

    def run_rolling(
        self,
        historical_data: list[dict[str, Any]],
        agent_fn: Callable[[MarketState], dict[str, Any]],
        regime_splitter: Callable[[float], str] | None = None,
    ) -> Generator[BacktestResult, None, None]:
        """
        Rolling backtest — окно двигается на 1 шаг за раз.
        Возвращает generator для пошагового анализа.
        """
        window_data = historical_data[: self.window_size]

        for i in range(self.window_size, len(historical_data)):
            # Rolling window
            window_data = historical_data[i - self.window_size : i]

            result = self.run_on_window(
                window_data,
                agent_fn,
                regime_splitter,
            )
            yield result

    def run_on_window(
        self,
        window_data: list[dict[str, Any]],
        agent_fn: Callable[[MarketState], dict[str, Any]],
        regime_splitter: Callable[[float], str] | None = None,
    ) -> BacktestResult:
        """Backtest на одном окне данных"""
        return self.run_on_data(window_data, agent_fn, regime_splitter)

    def _build_state(
        self,
        bar: dict[str, Any],
        regime_splitter: Callable[[float], str] | None = None,
    ) -> MarketState:
        """Build MarketState из одного бара данных"""
        price = bar.get("price", 0.0)
        regime = regime_splitter(price) if regime_splitter else "NORMAL"

        return MarketState(
            symbol=bar.get("symbol", "UNKNOWN"),
            price=price,
            timeframe=bar.get("timeframe", "1D"),
            n_signals=bar.get("n_signals", 0),
            session_id=f"bt_{bar.get('timestamp', '')}",
            timestamp=bar.get("timestamp", ""),
            regime=regime,
            volatility_score=bar.get("volatility", 0.5),
        )

    def _evaluate_reward(
        self,
        data: list[dict[str, Any]],
        current_idx: int,
        horizon: int,
    ) -> tuple[float, float]:
        """
        Вычисляет reward через horizon шагов вперёд.
        Returns: (actual_reward, predicted_reward)
        """
        if current_idx + horizon >= len(data):
            return 0.0, 0.0

        current_price = data[current_idx].get("price", 0.0)
        future_price = data[current_idx + horizon].get("price", 0.0)

        if current_price == 0:
            return 0.0, 0.0

        # Actual return
        actual_return = (future_price - current_price) / current_price

        # Normalize к [-1, 1]
        reward_actual = max(-1, min(1, actual_return * 10))

        # Predicted reward (from agent's confidence as proxy)
        # В реальной реализации — из trajectory prediction
        reward_predicted = 0.0

        return reward_actual, reward_predicted

    def _add_to_buffer(
        self,
        state: MarketState,
        decision: dict[str, Any],
        reward: float,
    ):
        """Добавить опыт в replay buffer"""
        traj = trajectory_from_state(state)
        metrics = compute_trajectory_metrics(traj)

        entry = BufferEntry(
            trajectory=traj,
            metrics=metrics,
            outcome=reward,
            market_context={
                "symbol": state.symbol,
                "regime": state.regime,
                "decision": decision.get("signal", "NEUTRAL"),
                "confidence": decision.get("confidence", 50),
            },
            created_at=state.timestamp,
        )
        self.buffer.add(entry)

    def _estimate_q_star(self) -> float:
        """Estimate Q* from buffer"""
        trajs = self.buffer.get_all_trajectories()
        if not trajs:
            return 0.5

        rewards = [t.steps[0].confidence / 100 for t in trajs if t.steps]
        if not rewards:
            return 0.5

        return sum(rewards) / len(rewards)

    def _compute_sharpe(self, rewards: list[float]) -> float:
        if not rewards or len(rewards) < 2:
            return 0.0

        mean = sum(rewards) / len(rewards)
        variance = sum((r - mean) ** 2 for r in rewards) / len(rewards)

        if variance == 0:
            return 0.0

        return mean / (variance**0.5)

    def _compute_max_drawdown(self, rewards: list[float]) -> float:
        if not rewards:
            return 0.0

        peak = rewards[0]
        max_dd = 0.0

        for r in rewards:
            peak = max(peak, r)
            dd = (peak - r) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)

        return max_dd

    def get_trajectory_insights(self) -> dict[str, Any]:
        """Анализ накопленных траекторий"""
        trajs = self.buffer.get_all_trajectories()
        if not trajs:
            return {"count": 0, "avg_confidence": 0}

        rewards = [t.steps[0].confidence / 100 for t in trajs if t.steps]
        q_star = self._estimate_q_star()

        return {
            "count": len(trajs),
            "q_star": round(q_star, 4),
            "avg_confidence": round(sum(rewards) / len(rewards) * 100, 1),
            "q_star_history": [round(q, 4) for q in self._q_star_history[-10:]],
            "backtest_runs": len(self.results),
        }

    def summary(self) -> dict[str, Any]:
        """Общая статистика backtest"""
        if not self.results:
            return {"runs": 0}

        latest = self.results[-1]

        return {
            "total_runs": len(self.results),
            "latest": latest.to_dict(),
            "q_star_trend": self._q_star_history[-10:],
            "buffer_size": self.buffer.size(),
        }


# =============================================================================
# Convenience runners
# =============================================================================


# =============================================================================
# EvoX Genesis — Project as permanent, agents promote verified changes
# =============================================================================

@dataclass
class StrategySnapshot:
    """Слепок стратегии в момент оценки — сериализуемый"""
    strategy_id: str
    name: str
    weights: dict[str, float]
    params: dict[str, Any]
    oos_sharpe: float = 0.0
    oos_win_rate: float = 0.0
    oos_max_dd: float = 0.0
    is_promoted: bool = False
    promoted_at: str = ""
    evaluated_at: str = ""

    def to_dict(self) -> dict:
        from dataclasses import asdict
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "StrategySnapshot":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class BacktestProject:
    """Постоянный проект (EvoX Genesis) — стратегия живёт, агенты продвигают изменения.

    State persists in SQLite. Agents propose changes via promote(),
    backtest validates OOS, only verified changes become active.
    """

    def __init__(self, db_path: str = "data/backtest_project.db", project_id: str = "default"):
        import sqlite3
        self.db_path = db_path
        self.project_id = project_id
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS project_state (
                project_id TEXT PRIMARY KEY,
                active_strategy_id TEXT,
                active_weights TEXT DEFAULT '{}',
                total_promotions INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS strategy_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                strategy_id TEXT NOT NULL,
                name TEXT,
                weights TEXT DEFAULT '{}',
                params TEXT DEFAULT '{}',
                oos_sharpe REAL DEFAULT 0.0,
                oos_win_rate REAL DEFAULT 0.0,
                oos_max_dd REAL DEFAULT 0.0,
                is_promoted INTEGER DEFAULT 0,
                promoted_at TEXT,
                evaluated_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (project_id) REFERENCES project_state(project_id)
            );
            CREATE TABLE IF NOT EXISTS promotion_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                old_strategy_id TEXT,
                new_strategy_id TEXT NOT NULL,
                sharpe_improvement REAL,
                win_rate_delta REAL,
                promoted_at TEXT DEFAULT (datetime('now')),
                reason TEXT
            );
            INSERT OR IGNORE INTO project_state (project_id) VALUES (?);
        """, (self.project_id,))
        self._conn.commit()

    def snapshot(self, strategy_id: str, name: str, weights: dict, params: dict,
                 oos_sharpe: float, oos_win_rate: float, oos_max_dd: float) -> StrategySnapshot:
        """Create a strategy snapshot — proposed change, not yet promoted."""
        import json
        snap = StrategySnapshot(
            strategy_id=strategy_id, name=name, weights=weights, params=params,
            oos_sharpe=oos_sharpe, oos_win_rate=oos_win_rate, oos_max_dd=oos_max_dd,
            evaluated_at=datetime.now().isoformat(),
        )
        self._conn.execute(
            "INSERT INTO strategy_snapshots (project_id, strategy_id, name, weights, params, "
            "oos_sharpe, oos_win_rate, oos_max_dd, evaluated_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (self.project_id, snap.strategy_id, snap.name, json.dumps(weights),
             json.dumps(params), snap.oos_sharpe, snap.oos_win_rate, snap.oos_max_dd,
             snap.evaluated_at),
        )
        self._conn.commit()
        return snap

    def promote(self, strategy_id: str, min_sharpe: float = 0.5,
                min_win_rate: float = 0.45, max_dd: float = 999.0) -> bool:
        """Promote a strategy to active IF OOS metrics pass thresholds.

        Gate conditions (configurable):
        - OOS Sharpe >= min_sharpe
        - OOS Win Rate >= min_win_rate
        - OOS Max DD <= max_dd

        Returns True if promoted, False if rejected.
        """
        row = self._conn.execute(
            "SELECT * FROM strategy_snapshots WHERE project_id = ? AND strategy_id = ? AND is_promoted = 0 "
            "ORDER BY evaluated_at DESC LIMIT 1",
            (self.project_id, strategy_id),
        ).fetchone()

        if not row:
            return False

        snap = dict(row)
        sharpe = float(snap["oos_sharpe"] or 0)
        win_rate = float(snap["oos_win_rate"] or 0)
        dd = float(snap["oos_max_dd"] or 0)

        if sharpe < min_sharpe or win_rate < min_win_rate or dd > max_dd:
            self._conn.execute(
                "INSERT INTO promotion_log (project_id, old_strategy_id, new_strategy_id, "
                "sharpe_improvement, win_rate_delta, reason) VALUES (?,?,?,?,?,?)",
                (self.project_id, "", strategy_id, 0.0, 0.0,
                 f"REJECTED: sharpe={sharpe:.2f}(min={min_sharpe}) win_rate={win_rate:.2%}(min={min_win_rate}) dd={dd:.2%}(max={max_dd})"),
            )
            self._conn.commit()
            return False

        # Promote: mark snapshot as active, update project state
        old_active = self._conn.execute(
            "SELECT active_strategy_id FROM project_state WHERE project_id = ?",
            (self.project_id,),
        ).fetchone()

        old_id = old_active["active_strategy_id"] if old_active else ""

        now = datetime.now().isoformat()
        self._conn.execute(
            "UPDATE strategy_snapshots SET is_promoted = 1, promoted_at = ? "
            "WHERE project_id = ? AND strategy_id = ?",
            (now, self.project_id, strategy_id),
        )
        self._conn.execute(
            "UPDATE project_state SET active_strategy_id = ?, active_weights = ?, "
            "total_promotions = total_promotions + 1, updated_at = ? WHERE project_id = ?",
            (strategy_id, snap["weights"], now, self.project_id),
        )
        self._conn.execute(
            "INSERT INTO promotion_log (project_id, old_strategy_id, new_strategy_id, "
            "sharpe_improvement, win_rate_delta, reason) VALUES (?,?,?,?,?,?)",
            (self.project_id, old_id, strategy_id,
             round(sharpe - 0.0, 4), round(win_rate - 0.0, 4), "PROMOTED"),
        )
        self._conn.commit()
        return True

    def active_strategy(self) -> dict | None:
        """Return the currently active (promoted) strategy."""
        row = self._conn.execute(
            "SELECT * FROM project_state WHERE project_id = ?", (self.project_id,),
        ).fetchone()
        if not row or not row["active_strategy_id"]:
            return None
        return dict(row)

    def history(self, limit: int = 20) -> list[dict]:
        """Return promotion history log."""
        rows = self._conn.execute(
            "SELECT * FROM promotion_log WHERE project_id = ? ORDER BY promoted_at DESC LIMIT ?",
            (self.project_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def snapshots(self, limit: int = 20) -> list[dict]:
        """Return all strategy snapshots."""
        rows = self._conn.execute(
            "SELECT * FROM strategy_snapshots WHERE project_id = ? ORDER BY evaluated_at DESC LIMIT ?",
            (self.project_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self):
        self._conn.close()


def create_backtest_runner(
    horizon: int = 5,
    oos_ratio: float = 0.2,
) -> ContinuousBacktest:
    """Factory для создания backtest runner"""
    return ContinuousBacktest(
        horizon=horizon,
        oos_ratio=oos_ratio,
    )


def run_backtest_on_bars(
    bars: list[dict[str, Any]],
    agent_fn: Callable[[MarketState], dict[str, Any]],
    horizon: int = 5,
) -> BacktestResult:
    """Quick backtest на барах"""
    runner = create_backtest_runner(horizon=horizon)
    return runner.run_on_data(bars, agent_fn)
