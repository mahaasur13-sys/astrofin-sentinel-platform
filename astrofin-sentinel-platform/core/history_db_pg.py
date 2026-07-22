"""
core/history_db_pg.py

PostgreSQL adapter for HistoryDB, implementing identical interface.
Auto-selected when DATABASE_URL starts with 'postgresql://'.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None

from core.history_db import HistoryDB, save_session, get_session, list_sessions, session_stats


_INIT_PG_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    id               SERIAL PRIMARY KEY,
    session_id       TEXT    NOT NULL UNIQUE,
    symbol           TEXT    NOT NULL,
    timeframe        TEXT    NOT NULL,
    query_type       TEXT    NOT NULL,
    current_price    REAL    NOT NULL DEFAULT 0.0,
    flows_run        JSONB   NOT NULL DEFAULT '{}',
    agent_count      INTEGER NOT NULL DEFAULT 0,
    final_signal     TEXT    NOT NULL DEFAULT 'NEUTRAL',
    final_confidence INTEGER NOT NULL DEFAULT 50,
    final_reasoning  TEXT    NOT NULL DEFAULT '',
    final_output     JSONB   NOT NULL DEFAULT '{}',
    started_at       TEXT    NOT NULL DEFAULT '',
    finished_at      TEXT    NOT NULL DEFAULT '',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pg_sessions_symbol    ON sessions(symbol);
CREATE INDEX IF NOT EXISTS idx_pg_sessions_timeframe ON sessions(timeframe);
CREATE INDEX IF NOT EXISTS idx_pg_sessions_timestamp ON sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_pg_sessions_signal    ON sessions(final_signal);
"""


class PostgresHistoryDB(HistoryDB):
    """PostgreSQL-backed HistoryDB, matching SQLite HistoryDB interface."""

    def __init__(self, dsn: str = None):
        self.dsn = dsn or os.environ.get("DATABASE_URL", "")
        if not self.dsn.startswith("postgresql"):
            raise ValueError(f"DATABASE_URL must start with postgresql://, got: {self.dsn[:20]}...")
        if psycopg2 is None:
            raise ImportError("psycopg2 is required for PostgreSQL backend. Install: pip install psycopg2-binary")
        self._init_db()

    def _conn(self):
        conn = psycopg2.connect(self.dsn)
        conn.autocommit = False
        return conn

    def _init_db(self):
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_INIT_PG_SQL)
            conn.commit()

    def save(self, result: dict) -> str:
        session_id = result.get("session_id", "")
        symbol = result.get("symbol", "BTCUSDT")
        timeframe = result.get("timeframe", "SWING")
        query_type = result.get("query_type", "unknown")
        price = result.get("current_price", 0.0)
        flows_run = json.dumps(result.get("flows_run", {}))
        agent_count = result.get("agent_count", 0)
        started_at = result.get("started_at", "")
        finished_at = result.get("timestamp", "")

        rec = result.get("final_recommendation") or {}
        if isinstance(rec, dict):
            signal = rec.get("signal", "NEUTRAL")
            confidence = rec.get("confidence", 50)
            reasoning = rec.get("reasoning", "")[:500]
        else:
            signal, confidence, reasoning = "NEUTRAL", 50, ""

        final_output = json.dumps(result, default=str, ensure_ascii=False)

        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO sessions (
                        session_id, symbol, timeframe, query_type, current_price,
                        flows_run, agent_count, final_signal, final_confidence,
                        final_reasoning, final_output, started_at, finished_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (session_id) DO UPDATE SET
                        final_signal    = EXCLUDED.final_signal,
                        final_confidence = EXCLUDED.final_confidence,
                        final_output    = EXCLUDED.final_output,
                        finished_at     = EXCLUDED.finished_at
                    """,
                    (
                        session_id, symbol, timeframe, query_type, price,
                        flows_run, agent_count, signal, confidence,
                        reasoning, final_output, started_at, finished_at,
                    ),
                )
            conn.commit()
        return session_id

    def get(self, session_id: str) -> dict | None:
        with self._conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM sessions WHERE session_id = %s", (session_id,)
                )
                row = cur.fetchone()
        if not row:
            return None
        return self._row_to_full_output(dict(row))

    def list(self, symbol: str = None, signal: str = None,
             limit: int = 20, offset: int = 0) -> list[dict]:
        sql = ["SELECT * FROM sessions WHERE 1=1"]
        args = []

        if symbol:
            sql.append("AND symbol = %s")
            args.append(symbol)
        if signal:
            sql.append("AND final_signal = %s")
            args.append(signal.upper())

        sql.append("ORDER BY created_at DESC LIMIT %s OFFSET %s")
        args.extend([limit, offset])

        with self._conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(" ".join(sql), args)
                rows = cur.fetchall()
        return [dict(r) for r in rows]

    def stats(self, symbol: str = None, days: int = 30) -> dict:
        where = "WHERE created_at >= NOW() - INTERVAL %s"
        if symbol:
            where += " AND symbol = %s"
            args = (f"{days} days", symbol)
        else:
            args = (f"{days} days",)

        with self._conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                meta_sql = f"""SELECT COUNT(*) AS total, AVG(final_confidence) AS avg_conf,
                    MIN(final_confidence) AS min_conf, MAX(final_confidence) AS max_conf
                    FROM sessions {where}"""
                cur.execute(meta_sql, args)
                meta = cur.fetchone()

                dist_sql = f"""SELECT final_signal, COUNT(*) AS cnt FROM sessions {where}
                    GROUP BY final_signal ORDER BY cnt DESC"""
                cur.execute(dist_sql, args)
                dist_rows = cur.fetchall()

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
        }

    def clear(self, older_than_days: int = None) -> int:
        if older_than_days is None:
            sql = "DELETE FROM sessions"
        else:
            sql = f"DELETE FROM sessions WHERE created_at < NOW() - INTERVAL '{older_than_days} days'"
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                deleted = cur.rowcount
            conn.commit()
        return deleted

    def _row_to_full_output(self, row: dict) -> dict:
        row = dict(row)
        flows_run = row.pop("flows_run", "{}")
        if isinstance(flows_run, str):
            flows_run = json.loads(flows_run)
        final_output = row.pop("final_output", "{}")
        if isinstance(final_output, str):
            final_output = json.loads(final_output)
        row.pop("id", None)
        row["flows_run"] = flows_run
        row["final_recommendation"] = final_output.get("final_recommendation")
        row["final_report"] = final_output.get("final_report")
        return row


def get_db() -> HistoryDB:
    """Auto-select backend: PostgreSQL if DATABASE_URL is set, else SQLite."""
    dsn = os.environ.get("DATABASE_URL", "")
    if dsn.startswith("postgresql"):
        return PostgresHistoryDB(dsn)
    return HistoryDB()
