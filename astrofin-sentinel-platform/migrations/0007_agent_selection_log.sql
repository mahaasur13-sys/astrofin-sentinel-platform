-- Migration 0007: Agent Selection Log
-- Author: Zo AI | Date: 2026-03-26
-- Purpose: Track which agents were called per session and their outcomes

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

INSERT OR IGNORE INTO _schema_version (version, applied_at)
VALUES (7, datetime('now'));
