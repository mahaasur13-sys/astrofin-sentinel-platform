-- AstroFin Sentinel V5 — Schema v3 (2026-03-26)
-- Monitoring snapshots from tools/db_monitor.py

CREATE TABLE IF NOT EXISTS _row_count_snapshots (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    db_name       TEXT    NOT NULL,
    table_name    TEXT    NOT NULL,
    row_count     INTEGER NOT NULL,
    snapshot_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_snap_db_table ON _row_count_snapshots(db_name, table_name);

INSERT OR IGNORE INTO _schema_version (version, note) VALUES (3, 'db_monitor_snapshots');
