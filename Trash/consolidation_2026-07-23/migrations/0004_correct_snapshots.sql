-- AstroFin Sentinel V5 — Schema v4 (2026-03-26)
-- Corrective: _row_count_snapshots had wrong schema (ts/source/count from early db_monitor.py)
-- Correct schema: db_name, table_name, row_count, snapshot_at

-- Step 1: preserve old data
CREATE TABLE IF NOT EXISTS _row_count_snapshots_old AS
SELECT * FROM _row_count_snapshots WHERE 1=0;  -- structure only

-- Step 2: migrate data if old rows exist
INSERT INTO _row_count_snapshots_old (ts, source, count, distribution)
SELECT ts, source, count, distribution FROM _row_count_snapshots;

-- Step 3: drop wrong table
PRAGMA legacy_alter_table=ON;
DROP TABLE IF EXISTS _row_count_snapshots;

-- Step 4: create correct table
CREATE TABLE IF NOT EXISTS _row_count_snapshots (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    db_name       TEXT    NOT NULL,
    table_name    TEXT    NOT NULL,
    row_count     INTEGER NOT NULL,
    snapshot_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_snap_db_table ON _row_count_snapshots(db_name, table_name);

-- Step 5: migrate data into new schema
--   Old: ts (datetime), source (like "sessions"), count (int), distribution (JSON/None)
--   New: db_name, table_name, row_count, snapshot_at
INSERT INTO _row_count_snapshots (db_name, table_name, row_count, snapshot_at)
SELECT
    CASE
        WHEN source LIKE '%backtest%' THEN 'backtest'
        ELSE 'sessions'
    END,
    source,
    count,
    COALESCE(ts, datetime('now'))
FROM _row_count_snapshots_old;

-- Step 6: clean up
DROP TABLE IF EXISTS _row_count_snapshots_old;

INSERT OR IGNORE INTO _schema_version (version, note) VALUES (4, 'correct_snapshots_schema');
