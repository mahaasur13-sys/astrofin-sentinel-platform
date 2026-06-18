"""
AstroFin Sentinel v5 — Persistent Session History (R-08)

SQLite-backed session history. Every run_sentinel_v5() call is persisted.
Supports: save, get, list, stats, clear.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from core.checkpoint import get_project_root

# ─── Database Path ─────────────────────────────────────────────────────────────


def _db_path() -> Path:
    root = get_project_root()
    db_dir = root / "core"
    db_dir.mkdir(exist_ok=True)
    return db_dir / "history.db"


# ─── Schema ───────────────────────────────────────────────────────────────────

_INIT_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id        TEXT    NOT NULL UNIQUE,
    symbol            TEXT    NOT NULL,
    timeframe         TEXT    NOT NULL,
    query_type        TEXT    NOT NULL,
    current_price     REAL    NOT NULL DEFAULT 0.0,
    flows_run         TEXT    NOT NULL DEFAULT '{}',
    agent_count       INTEGER NOT NULL DEFAULT 0,
    final_signal      TEXT    NOT NULL DEFAULT 'NEUTRAL',
    final_confidence  INTEGER NOT NULL DEFAULT 50,
    final_reasoning   TEXT    NOT NULL DEFAULT '',
    final_output      TEXT    NOT NULL DEFAULT '{}',
    started_at        TEXT    NOT NULL DEFAULT '',
    finished_at       TEXT    NOT NULL DEFAULT '',
    created_at        TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_sessions_symbol    ON sessions(symbol);
CREATE INDEX IF NOT EXISTS idx_sessions_timeframe ON sessions(timeframe);
CREATE INDEX IF NOT EXISTS idx_sessions_timestamp ON sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_signal    ON sessions(final_signal);
"""


# ─── HistoryDB ────────────────────────────────────────────────────────────────


class HistoryDB:
    """
    Persists every sentinel run. Thread-safe using connection per call.

    Methods:
        save(result)          — persist a full run_sentinel_v5() output
        get(session_id)       — retrieve a single session
        list(symbol, limit)    — recent sessions, optionally filtered
        stats(symbol)         — aggregate stats per symbol
        clear(older_than_days) — vacuum
    """

    def __init__(self, db_path: Path = None):
        self.db_path = db_path or _db_path()
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10, isolation_level="IMMEDIATE")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as conn:
            conn.executescript(_INIT_SQL)
            conn.commit()

    # ── Public API ────────────────────────────────────────────────────────────

    def save(self, result: dict) -> str:
        """
        Persist a run_sentinel_v5() result dict.

        Extracts flat fields from the nested output for efficient querying.
        Returns the session_id.
        """
        session_id = result.get("session_id", "")
        symbol = result.get("symbol", "BTCUSDT")
        timeframe = result.get("timeframe", "SWING")
        query_type = result.get("query_type", "unknown")
        price = result.get("current_price", 0.0)
        flows_run = json.dumps(result.get("flows_run", {}))
        agent_count = result.get("agent_count", 0)
        started_at = result.get("started_at", "")
        finished_at = result.get("timestamp", "")

        # Flatten final_recommendation
        rec = result.get("final_recommendation") or {}
        if isinstance(rec, dict):
            signal = rec.get("signal", "NEUTRAL")
            confidence = rec.get("confidence", 50)
            reasoning = rec.get("reasoning", "")[:500]  # truncate for column
        else:
            signal, confidence, reasoning = "NEUTRAL", 50, ""

        final_output = json.dumps(result, default=str, ensure_ascii=False)

        with self._conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO sessions (
                    session_id, symbol, timeframe, query_type, current_price,
                    flows_run, agent_count, final_signal, final_confidence,
                    final_reasoning, final_output, started_at, finished_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    session_id,
                    symbol,
                    timeframe,
                    query_type,
                    price,
                    flows_run,
                    agent_count,
                    signal,
                    confidence,
                    reasoning,
                    final_output,
                    started_at,
                    finished_at,
                ),
            )
            conn.commit()

        return session_id

    def get(self, session_id: str) -> dict | None:
        """Retrieve a session by session_id. Returns None if not found."""
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)).fetchone()

        if not row:
            return None
        return self._row_to_full_output(dict(row))

    def list(
        self,
        symbol: str = None,
        signal: str = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """
        List recent sessions, optionally filtered.

        Returns flat session records (final_output not expanded).
        """
        sql = ["SELECT * FROM sessions WHERE 1=1"]
        args = []

        if symbol:
            sql.append("AND symbol = ?")
            args.append(symbol)
        if signal:
            sql.append("AND final_signal = ?")
            args.append(signal.upper())

        sql.append("ORDER BY created_at DESC LIMIT ? OFFSET ?")
        args.extend([limit, offset])

        with self._conn() as conn:
            rows = conn.execute(" ".join(sql), args).fetchall()

        return [dict(r) for r in rows]

    def stats(self, symbol: str = None, days: int = 30) -> dict:
        """
        Aggregate statistics for a symbol (or all) over the last N days.

        Returns: win_rate, avg_confidence, total_sessions, signal_distribution
        """
        where = "WHERE created_at >= datetime('now', ?)"
        days_arg = f"-{days} days"

        if symbol:
            where += " AND symbol = ?"
            args = (days_arg, symbol)
        else:
            args = (days_arg,)

        with self._conn() as conn:
            # Count + avg confidence
            meta = conn.execute(
                f"""
                SELECT
                    COUNT(*)                          AS total,
                    AVG(final_confidence)              AS avg_conf,
                    MIN(final_confidence)              AS min_conf,
                    MAX(final_confidence)              AS max_conf
                FROM sessions {where}
            """,
                args,
            ).fetchone()

            # Signal distribution
            dist_rows = conn.execute(
                f"""
                SELECT final_signal, COUNT(*) AS cnt
                FROM sessions {where}
                GROUP BY final_signal
                ORDER BY cnt DESC
            """,
                args,
            ).fetchall()

            # Recent trend: LONG vs SHORT ratio per day (last 7 days)
            trend_sql = """
                SELECT
                    DATE(created_at)                    AS day,
                    SUM(CASE WHEN final_signal = 'LONG'  THEN 1 ELSE 0 END) AS longs,
                    SUM(CASE WHEN final_signal = 'SHORT' THEN 1 ELSE 0 END) AS shorts,
                    AVG(final_confidence)                AS avg_conf
                FROM sessions
                WHERE created_at >= datetime('now', '-7 days')
            """
            trend_args: tuple = ()
            if symbol:
                trend_sql += " AND symbol = ?"
                trend_args = (symbol,)

            trend_rows = conn.execute(trend_sql + " GROUP BY DATE(created_at) ORDER BY day DESC", trend_args).fetchall()

        dist = {r["final_signal"]: r["cnt"] for r in dist_rows}
        total = meta["total"] or 0

        long_cnt = dist.get("LONG", 0)
        short_cnt = dist.get("SHORT", 0)
        win_rate = round(long_cnt / (long_cnt + short_cnt), 4) if (long_cnt + short_cnt) > 0 else None

        return {
            "total_sessions": total,
            "avg_confidence": round(meta["avg_conf"] or 0, 1),
            "min_confidence": meta["min_conf"] or 0,
            "max_confidence": meta["max_conf"] or 0,
            "signal_distribution": dist,
            "win_rate_long": win_rate,
            "recent_trend": [dict(r) for r in trend_rows],
        }

    def clear(self, older_than_days: int = None) -> int:
        """
        Delete sessions older than N days. If days is None, clears all.
        Returns number of deleted rows.
        """
        if older_than_days is None:
            deleted = 0
            with self._conn() as conn:
                deleted = conn.execute("DELETE FROM sessions").rowcount
                conn.commit()
            # VACUUM must run outside any transaction
            with self._conn() as conn:
                conn.execute("VACUUM")
        else:
            with self._conn() as conn:
                deleted = conn.execute(
                    "DELETE FROM sessions WHERE created_at < datetime('now', ?)",
                    (f"-{older_than_days} days",),
                ).rowcount
                conn.commit()
        return deleted

    # ── Internal ─────────────────────────────────────────────────────────────

    def _row_to_full_output(self, row: dict) -> dict:
        """Reconstruct the original full result dict from a DB row."""
        row = dict(row)
        flows_run = json.loads(row.pop("flows_run", "{}"))
        final_output = json.loads(row.pop("final_output", "{}"))
        row.pop("id", None)
        row["flows_run"] = flows_run
        row["final_recommendation"] = final_output.get("final_recommendation")
        row["final_report"] = final_output.get("final_report")
        return row


# ─── Module-level convenience ─────────────────────────────────────────────────

_db: HistoryDB | None = None


def get_db() -> HistoryDB:
    global _db
    if _db is None:
        _db = HistoryDB()
    return _db


def save_session(result: dict) -> str:
    return get_db().save(result)


def get_session(session_id: str) -> dict | None:
    return get_db().get(session_id)


def list_sessions(symbol: str = None, limit: int = 20) -> list[dict]:
    return get_db().list(symbol=symbol, limit=limit)


def session_stats(symbol: str = None, days: int = 30) -> dict:
    return get_db().stats(symbol=symbol, days=days)
