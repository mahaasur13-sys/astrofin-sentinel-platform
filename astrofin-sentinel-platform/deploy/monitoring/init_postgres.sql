-- =============================================================================
-- TimescaleDB initialisation — AstroFin Sentinel Platform
-- Loaded automatically by postgres docker-entrypoint on first boot.
-- =============================================================================

-- Required extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- -----------------------------------------------------------------------
-- ML inference predictions
-- -----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ml_predictions (
    prediction_id    UUID PRIMARY KEY,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    node_id          TEXT NOT NULL,
    risk_score       REAL NOT NULL,
    risk_label       TEXT NOT NULL,
    model_version    TEXT,
    features         JSONB
);

CREATE INDEX IF NOT EXISTS idx_ml_predictions_node_time
    ON ml_predictions (node_id, created_at DESC);

SELECT create_hypertable('ml_predictions', 'created_at',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE);

-- -----------------------------------------------------------------------
-- AstroFin Sentinel signals
-- -----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS astrofin_signals (
    id              BIGSERIAL PRIMARY KEY,
    signal_time     TIMESTAMPTZ NOT NULL DEFAULT now(),
    symbol          TEXT NOT NULL,
    direction       TEXT NOT NULL,  -- 'LONG' | 'SHORT' | 'NEUTRAL'
    confidence      REAL NOT NULL,
    payload         JSONB
);

CREATE INDEX IF NOT EXISTS idx_astrofin_signals_symbol_time
    ON astrofin_signals (symbol, signal_time DESC);

SELECT create_hypertable('astrofin_signals', 'signal_time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE);

-- -----------------------------------------------------------------------
-- Feature pipeline metrics
-- -----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS feature_metrics (
    id              BIGSERIAL PRIMARY KEY,
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    node_id         TEXT NOT NULL,
    feature_count   INTEGER NOT NULL,
    pipeline_run_ms REAL NOT NULL
);

SELECT create_hypertable('feature_metrics', 'recorded_at',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE);

-- -----------------------------------------------------------------------
-- Done.
-- -----------------------------------------------------------------------