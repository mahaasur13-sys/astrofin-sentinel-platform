-- AstroFin Sentinel V5 — Schema v2 (2026-03-26)
-- Backtest metrics from backtest/engine.py

CREATE TABLE IF NOT EXISTS backtest_runs (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id        TEXT    NOT NULL UNIQUE,
    symbol            TEXT    NOT NULL,
    start_date        TEXT    NOT NULL,
    end_date          TEXT    NOT NULL,
    timeframe         TEXT    NOT NULL DEFAULT 'SWING',
    win_rate          REAL    DEFAULT 0.0,
    sharpe_ratio      REAL    DEFAULT 0.0,
    total_trades      INTEGER DEFAULT 0,
    winning_trades    INTEGER DEFAULT 0,
    losing_trades     INTEGER DEFAULT 0,
    avg_win_pct       REAL    DEFAULT 0.0,
    avg_loss_pct      REAL    DEFAULT 0.0,
    total_return_pct  REAL    DEFAULT 0.0,
    max_drawdown_pct  REAL    DEFAULT 0.0,
    avg_confidence    REAL    DEFAULT 0.0,
    initial_capital   REAL    DEFAULT 0.0,
    final_capital     REAL    DEFAULT 0.0,
    created_at        TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_bt_symbol   ON backtest_runs(symbol);
CREATE INDEX IF NOT EXISTS idx_bt_session  ON backtest_runs(session_id);
CREATE INDEX IF NOT EXISTS idx_bt_created  ON backtest_runs(created_at);

INSERT OR IGNORE INTO _schema_version (version, note) VALUES (2, 'initial_backtest');
