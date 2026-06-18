-- AstroFin Sentinel V5 — Schema v1 (2026-03-26)
-- Base schema: sessions from core/history_db.py

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

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

-- Metadata
CREATE TABLE IF NOT EXISTS _schema_version (
    version    INTEGER PRIMARY KEY,
    applied_at TEXT    NOT NULL DEFAULT (datetime('now')),
    note       TEXT    NOT NULL DEFAULT ''
);
INSERT OR IGNORE INTO _schema_version (version, note) VALUES (1, 'initial_sessions');
