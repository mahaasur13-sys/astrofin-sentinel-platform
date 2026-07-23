-- Migration 0008: TimescaleDB extension
-- G2 (P2-01): hypertable for ohlcv_bars, agent_decisions, backtest_runs
-- 7-day chunks, 2-year retention
--
-- NOTE: do NOT wrap this file in BEGIN/COMMIT — tools/migrate_postgres.py
-- already runs every statement inside `conn.transaction()`. Nested
-- BEGIN/COMMIT breaks asyncpg and aborts the migration.

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ohlcv_bars: market data (time-series)
CREATE TABLE IF NOT EXISTS ohlcv_bars (
    ts          TIMESTAMPTZ NOT NULL,
    symbol      TEXT        NOT NULL,
    timeframe   TEXT        NOT NULL,
    open        NUMERIC(20, 8) NOT NULL,
    high        NUMERIC(20, 8) NOT NULL,
    low         NUMERIC(20, 8) NOT NULL,
    close       NUMERIC(20, 8) NOT NULL,
    volume      NUMERIC(20, 8) NOT NULL,
    PRIMARY KEY (ts, symbol, timeframe)
);

SELECT create_hypertable(
    'ohlcv_bars', 'ts',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- agent_decisions: multi-agent council votes
CREATE TABLE IF NOT EXISTS agent_decisions (
    ts          TIMESTAMPTZ NOT NULL,
    session_id  TEXT        NOT NULL,
    agent_name  TEXT        NOT NULL,
    symbol      TEXT        NOT NULL,
    direction   TEXT        NOT NULL,
    confidence  NUMERIC(5,4) NOT NULL,
    reasoning   TEXT,
    PRIMARY KEY (ts, session_id, agent_name)
);

SELECT create_hypertable(
    'agent_decisions', 'ts',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- backtest_runs: AMRE continuous backtest results
CREATE TABLE IF NOT EXISTS backtest_runs (
    ts          TIMESTAMPTZ NOT NULL,
    run_id      TEXT        NOT NULL,
    strategy    TEXT        NOT NULL,
    symbol      TEXT        NOT NULL,
    period      TEXT        NOT NULL,
    sharpe      NUMERIC(10,4),
    sortino     NUMERIC(10,4),
    max_dd      NUMERIC(10,4),
    win_rate    NUMERIC(5,4),
    total_pnl   NUMERIC(20,8),
    PRIMARY KEY (ts, run_id)
);

SELECT create_hypertable(
    'backtest_runs', 'ts',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- 1. Enable compression on each hypertable (required before add_compression_policy).
--    Use transaction_per_chunk so the ALTER on already-populated hypertables does
--    not take a long ACCESS EXCLUSIVE lock on the whole table.
ALTER TABLE ohlcv_bars       SET (timescaledb.compress = true);
ALTER TABLE agent_decisions  SET (timescaledb.compress = true);
ALTER TABLE backtest_runs    SET (timescaledb.compress = true);

-- 2. Compression policy: chunks older than 30 days
SELECT add_compression_policy('ohlcv_bars',       INTERVAL '30 days');
SELECT add_compression_policy('agent_decisions',  INTERVAL '30 days');
SELECT add_compression_policy('backtest_runs',    INTERVAL '30 days');

-- 3. Retention policy: 2 years (730 days)
SELECT add_retention_policy('ohlcv_bars',       INTERVAL '730 days');
SELECT add_retention_policy('agent_decisions',  INTERVAL '730 days');
SELECT add_retention_policy('backtest_runs',    INTERVAL '730 days');

-- 4. Indexes for symbol/strategy lookups.
--    These still use plain CREATE INDEX; for already-populated hypertables run
--    tools/migrate_postgres_indexes.py (uses timescaledb.transaction_per_chunk)
--    during a maintenance window. Kept here so a fresh DB gets them too.
CREATE INDEX IF NOT EXISTS ohlcv_bars_symbol_idx          ON ohlcv_bars       (symbol,    ts DESC);
CREATE INDEX IF NOT EXISTS ohlcv_bars_tf_idx              ON ohlcv_bars       (timeframe, ts DESC);
CREATE INDEX IF NOT EXISTS agent_decisions_session_idx    ON agent_decisions  (session_id, ts DESC);
CREATE INDEX IF NOT EXISTS agent_decisions_symbol_idx     ON agent_decisions  (symbol,     ts DESC);
CREATE INDEX IF NOT EXISTS backtest_runs_strategy_idx     ON backtest_runs    (strategy,   ts DESC);

-- 5. Schema version (mirror 0001-0009 pattern)
CREATE TABLE IF NOT EXISTS _schema_version (
    version    INTEGER      PRIMARY KEY,
    applied_at TIMESTAMPTZ  NOT NULL DEFAULT now(),
    note       TEXT
);
INSERT INTO _schema_version (version, note)
VALUES (8, 'TimescaleDB extension + 3 hypertables (ohlcv_bars, agent_decisions, backtest_runs) + compression/retention')
ON CONFLICT (version) DO NOTHING;
