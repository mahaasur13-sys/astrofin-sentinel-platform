-- Migration 0006: Thompson Sampling Selections
-- Author: Zo AI | Date: 2026-03-26

-- Store which agents were Thompson-selected per flow
ALTER TABLE sessions ADD COLUMN thompson_selections TEXT NOT NULL DEFAULT '{}';

-- Pre-calculated per-flow agent counts (denormalized for faster queries)
ALTER TABLE sessions ADD COLUMN technical_agent_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE sessions ADD COLUMN astro_agent_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE sessions ADD COLUMN electoral_agent_count INTEGER NOT NULL DEFAULT 0;

INSERT OR IGNORE INTO _schema_version (version, applied_at)
VALUES (6, datetime('now'));
