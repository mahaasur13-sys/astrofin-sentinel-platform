"""
AstroFin Sentinel v5 — Agent Belief Tracker (Bayesian)

Stores per-agent accuracy as a Beta distribution, updated after each session.
Only agents that actually produced a signal are updated.

Beta Distribution (conjugate prior for Bernoulli):
    α = successes + 1
    β = failures + 1
    mean  = α / (α + β)         # posterior mean probability of being correct
    mode  = (α-1) / (α+β-2)     # MAP estimate (defined when α, β > 1)

Success criteria (from session result):
    Agent signal direction aligned with final_signal AND
    final_signal not in (AVOID, NEUTRAL) → SUCCESS
    Otherwise                                    → FAILURE

Schema version: v1
"""
from __future__ import annotations

import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from core.checkpoint import get_project_root
from tools.metrics_server import CACHE_HITS, CACHE_MISSES, THOMPSON_PARAMS

# ─── Paths ─────────────────────────────────────────────────────────────────────


def _belief_db_path() -> Path:
    root = get_project_root()
    db_dir = root / "core"
    db_dir.mkdir(exist_ok=True)
    return db_dir / "belief.db"


# ─── Schema ───────────────────────────────────────────────────────────────────

_INIT_SQL = """
CREATE TABLE IF NOT EXISTS agent_beliefs (
    agent_name      TEXT PRIMARY KEY,
    alpha           REAL NOT NULL DEFAULT 1.0,
    beta            REAL NOT NULL DEFAULT 1.0,
    total_sessions  INTEGER NOT NULL DEFAULT 0,
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS agent_belief_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name      TEXT NOT NULL,
    session_id      TEXT NOT NULL,
    final_signal    TEXT NOT NULL,
    agent_signal    TEXT NOT NULL,
    is_success      INTEGER NOT NULL,
    posterior_alpha REAL NOT NULL,
    posterior_beta  REAL NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_belief_history_agent
    ON agent_belief_history(agent_name, created_at);

CREATE TABLE IF NOT EXISTS agent_selection_log (
    session_id      TEXT NOT NULL,
    agent_name      TEXT NOT NULL,
    pool_name       TEXT NOT NULL,
    was_called      INTEGER NOT NULL CHECK (was_called IN (0, 1)),
    success_flag    INTEGER,  -- NULL if was_called=0, 0/1 if was_called=1
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (session_id, agent_name)
);

CREATE INDEX IF NOT EXISTS idx_selection_log_agent
    ON agent_selection_log(agent_name, created_at);

CREATE INDEX IF NOT EXISTS idx_selection_log_session
    ON agent_selection_log(session_id);
"""


# ─── Data classes ──────────────────────────────────────────────────────────────


@dataclass
class BeliefState:
    """Beta distribution state for one agent."""

    agent_name: str
    alpha: float = 1.0
    beta: float = 1.0
    total_sessions: int = 0

    @property
    def mean(self) -> float:
        """Posterior mean probability of being correct."""
        return self.alpha / (self.alpha + self.beta)

    @property
    def mode(self) -> float | None:
        """MAP estimate (undefined when α ≤ 1 or β ≤ 1)."""
        if self.alpha <= 1 or self.beta <= 1:
            return None
        return (self.alpha - 1) / (self.alpha + self.beta - 2)

    @property
    def std(self) -> float:
        n = self.alpha + self.beta
        return math.sqrt((self.alpha * self.beta) / (n * n * (n + 1)))

    def credibility_interval(self, level: float = 0.95) -> tuple[float, float]:
        """
        Approximate Bayesian credible interval via Wilson score.
        Falls back to mean ± 2σ for extreme parameters.
        """
        p = self.mean
        z = 1.96 if level == 0.95 else 2.576  # z for 95% / 99%
        n = self.alpha + self.beta

        denom = 1 + z * z / n
        center = (p + z * z / (2 * n)) / denom
        margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom

        lo = max(0.0, center - margin)
        hi = min(1.0, center + margin)
        return round(lo, 4), round(hi, 4)

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "alpha": round(self.alpha, 4),
            "beta": round(self.beta, 4),
            "total_sessions": self.total_sessions,
            "mean_accuracy": round(self.mean, 4),
            "mode_accuracy": self.mode,
            "std": round(self.std, 4),
            "ci_95": self.credibility_interval(0.95),
        }


# ─── BeliefTracker ─────────────────────────────────────────────────────────────


class BeliefTracker:
    """
    Tracks per-agent directional accuracy using Bayesian Beta updating.

    Update flow:
        result = await run_sentinel_v5(...)
        tracker.update_from_session(result)

    Success: agent signal aligned with final_signal (not AVOID/NEUTRAL).
    Failure: agent signal did NOT align OR final was AVOID/NEUTRAL.
    """

    _ACTIONABLE = {"LONG", "SHORT", "BUY", "SELL", "STRONG_BUY", "STRONG_SELL"}

    def __init__(self, db_path: Path = None, history_limit: int = 100):
        self.db_path = db_path or _belief_db_path()
        self.history_limit = history_limit
        self._cache: dict[str, BeliefState | None] = {}
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as conn:
            conn.executescript(_INIT_SQL)
            conn.commit()

    # ── Public API ────────────────────────────────────────────────────────────

    def get(self, agent_name: str) -> BeliefState | None:
        """Return Beta state for one agent, or None if unseen (cached)."""
        if agent_name in self._cache:
            CACHE_HITS.inc()
            return self._cache[agent_name]
        CACHE_MISSES.inc()
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM agent_beliefs WHERE agent_name = ?", (agent_name,)).fetchone()
        if not row:
            self._cache[agent_name] = None
            return None
        state = BeliefState(
            agent_name=row["agent_name"],
            alpha=row["alpha"],
            beta=row["beta"],
            total_sessions=row["total_sessions"],
        )
        self._cache[agent_name] = state
        return state

    def get_all(self) -> dict[str, BeliefState]:
        """Return Beta state for all tracked agents."""
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM agent_beliefs ORDER BY total_sessions DESC").fetchall()
        return {
            r["agent_name"]: BeliefState(
                agent_name=r["agent_name"],
                alpha=r["alpha"],
                beta=r["beta"],
                total_sessions=r["total_sessions"],
            )
            for r in rows
        }

    def update_from_session(self, session_result: dict) -> dict[str, bool]:
        """
        Update Beta parameters for every agent that actually produced a signal.
        """
        all_signals = session_result.get("all_signals", [])
        if not all_signals:
            return {}

        final_rec = session_result.get("final_recommendation") or {}
        final_signal = self._normalize(final_rec.get("signal", ""))
        session_id = session_result.get("session_id", "unknown")

        is_actionable = final_signal in self._ACTIONABLE

        results: dict[str, bool] = {}

        for sig in all_signals:
            agent_name = self._get(sig, "agent_name", "")
            if not agent_name or agent_name == "SystemFallback":
                continue

            agent_signal = self._normalize(self._get(sig, "signal", ""))

            if is_actionable and agent_signal == final_signal:
                is_success = True
                alpha_delta, beta_delta = 1.0, 0.0
            else:
                is_success = False
                alpha_delta, beta_delta = 0.0, 1.0

            self._update_agent(
                agent_name=agent_name,
                alpha_delta=alpha_delta,
                beta_delta=beta_delta,
                session_id=session_id,
                final_signal=final_signal,
                agent_signal=agent_signal,
                is_success=is_success,
            )
            self._cache.pop(agent_name, None)  # инвалидируем кеш
            results[agent_name] = is_success

        self._log_session_selections(
            session_id=session_id,
            called_agents=list(results.keys()),
            agent_results=results,
        )
        return results

    def get_agent_history(self, agent_name: str, limit: int = 100) -> list[dict]:
        """Return last N outcomes for one agent."""
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT * FROM agent_belief_history
                WHERE agent_name = ?
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (agent_name, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def leaderboard(self) -> list[dict]:
        """Rank all agents by posterior mean accuracy."""
        all_states = self.get_all()
        if not all_states:
            return []

        rows = []
        for name, state in all_states.items():
            ci_lo, ci_hi = state.credibility_interval(0.95)
            rows.append(
                {
                    "agent_name": name,
                    "mean_accuracy": round(state.mean, 4),
                    "mode_accuracy": state.mode,
                    "ci_95": (ci_lo, ci_hi),
                    "ci_width": round(ci_hi - ci_lo, 4),
                    "total_sessions": state.total_sessions,
                    "alpha": round(state.alpha, 2),
                    "beta": round(state.beta, 2),
                    "std": round(state.std, 4),
                }
            )

        rows.sort(key=lambda r: r["mean_accuracy"], reverse=True)
        return rows

    def reset(self, agent_name: str = None) -> int:
        """
        Reset one agent (or all if agent_name is None).
        Returns number of rows deleted.
        """
        self._cache.clear()  # полностью очищаем кеш
        with self._conn() as conn:
            if agent_name:
                deleted = conn.execute("DELETE FROM agent_beliefs WHERE agent_name = ?", (agent_name,)).rowcount
                conn.execute(
                    "DELETE FROM agent_belief_history WHERE agent_name = ?",
                    (agent_name,),
                )
            else:
                deleted = conn.execute("DELETE FROM agent_beliefs").rowcount
                conn.execute("DELETE FROM agent_belief_history")
            conn.commit()
        return deleted

    # ── Internal ───────────────────────────────────────────────────────────────

    def _update_agent(
        self,
        agent_name: str,
        alpha_delta: float,
        beta_delta: float,
        session_id: str,
        final_signal: str,
        agent_signal: str,
        is_success: bool,
    ):
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO agent_beliefs (agent_name, alpha, beta, total_sessions)
                VALUES (?, 1.0 + ?, 1.0 + ?, 1)
                ON CONFLICT(agent_name) DO UPDATE SET
                    alpha          = alpha          + excluded.alpha,
                    beta           = beta           + excluded.beta,
                    total_sessions = total_sessions  + 1,
                    updated_at     = datetime('now')
            """,
                (agent_name, alpha_delta, beta_delta),
            )

            # Обновляем Prometheus Gauge для Thompson параметров
            current = conn.execute(
                "SELECT alpha, beta FROM agent_beliefs WHERE agent_name = ?",
                (agent_name,),
            ).fetchone()
            if current:
                THOMPSON_PARAMS.labels(agent_name=agent_name, param="alpha").set(current["alpha"])
                THOMPSON_PARAMS.labels(agent_name=agent_name, param="beta").set(current["beta"])
                mean_val = current["alpha"] / (current["alpha"] + current["beta"])
                THOMPSON_PARAMS.labels(agent_name=agent_name, param="mean").set(mean_val)

            conn.execute(
                """
                INSERT INTO agent_belief_history
                    (agent_name, session_id, final_signal, agent_signal,
                     is_success, posterior_alpha, posterior_beta)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    agent_name,
                    session_id,
                    final_signal,
                    agent_signal,
                    int(is_success),
                    1.0 + alpha_delta,
                    1.0 + beta_delta,
                ),
            )

            conn.execute(
                """
                DELETE FROM agent_belief_history
                WHERE agent_name = ?
                AND id NOT IN (
                    SELECT id FROM agent_belief_history
                    WHERE agent_name = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                )
            """,
                (agent_name, agent_name, self.history_limit),
            )

            conn.commit()

    @staticmethod
    def _sample_beta(alpha: float, beta: float) -> float:
        import numpy as np

        return float(np.random.beta(alpha, beta))

    @staticmethod
    def _get(obj, key: str, default=None):
        if hasattr(obj, key):
            return getattr(obj, key)
        if isinstance(obj, dict):
            return obj.get(key, default)
        return default

    @staticmethod
    def _normalize(signal: str) -> str:
        return signal.upper().strip() if signal else ""

    # ── Selection Log ─────────────────────────────────────────────────────────

    _POOL_MAP = {
        "MarketAnalyst": "technical",
        "BullResearcher": "technical",
        "BearResearcher": "technical",
        "TechnicalAgent": "technical",
        "FundamentalAgent": "macro",
        "MacroAgent": "macro",
        "QuantAgent": "macro",
        "OptionsFlowAgent": "macro",
        "SentimentAgent": "macro",
        "GannAgent": "astro",
        "BradleyAgent": "astro",
        "ElliotAgent": "astro",
        "CycleAgent": "astro",
        "TimeWindowAgent": "astro",
        "MuhurtaAgent": "astro",
        "ElectionAgent": "astro",
    }

    def _pool_for(self, agent_name: str) -> str:
        return self._POOL_MAP.get(agent_name, "astro")

    def _log_session_selections(self, session_id: str, called_agents: list[str], agent_results: dict[str, bool]):
        called_set = {a for a in called_agents if a != "SystemFallback"}
        all_pool_agents = set(self._POOL_MAP.keys())
        not_called = all_pool_agents - called_set

        rows: list[tuple] = []
        for name in called_set:
            rows.append((session_id, name, self._pool_for(name), 1, agent_results.get(name)))
        for name in not_called:
            rows.append((session_id, name, self._pool_for(name), 0, None))

        if not rows:
            return

        with self._conn() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO agent_selection_log
                    (session_id, agent_name, pool_name, was_called, success_flag)
                VALUES (?, ?, ?, ?, ?)
            """,
                rows,
            )
            conn.commit()

    def get_selection_log(self, agent_name: str = None, session_id: str = None, limit: int = 100) -> list[dict]:
        with self._conn() as conn:
            if agent_name:
                rows = conn.execute(
                    """
                    SELECT * FROM agent_selection_log
                    WHERE agent_name = ?
                    ORDER BY created_at DESC LIMIT ?
                """,
                    (agent_name, limit),
                ).fetchall()
            elif session_id:
                rows = conn.execute(
                    """
                    SELECT * FROM agent_selection_log
                    WHERE session_id = ?
                    ORDER BY created_at DESC
                """,
                    (session_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM agent_selection_log
                    ORDER BY created_at DESC LIMIT ?
                """,
                    (limit,),
                ).fetchall()
        return [dict(r) for r in rows]


# ─── Module-level convenience ───────────────────────────────────────────────────

_belief_tracker: BeliefTracker | None = None


def get_belief_tracker() -> BeliefTracker:
    global _belief_tracker
    if _belief_tracker is None:
        _belief_tracker = BeliefTracker()
    return _belief_tracker


def update_beliefs_from_session(session_result: dict) -> dict[str, bool]:
    return get_belief_tracker().update_from_session(session_result)
