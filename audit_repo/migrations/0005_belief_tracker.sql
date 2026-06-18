-- Migration 0005: Agent Belief Tracker (v1)
-- Beta- Bayesian per-agent accuracy tracking
-- Author: Zo AI | Date: 2026-03-26

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

INSERT OR IGNORE INTO _schema_version (version, applied_at)
VALUES (5, datetime('now'));
