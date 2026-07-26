-- =============================================================================
-- Migration 0010 — AstroFin V5 TimescaleDB Hypertables
-- Converts time-series tables to TimescaleDB hypertables for performance
-- and automatic partitioning.
-- Run: psql -d postgresql://astrofin:astrofin@localhost:5432/astrofin -f 0010_astrofin_hypertables.sql
-- =============================================================================

-- Extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- ── sessions — trading session time-series ───────────────────────────────
SELECT create_hypertable(
    'sessions', 'created_at',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- ── agent_signals — agent output time-series ─────────────────────────────
SELECT create_hypertable(
    'agent_signals', 'created_at',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- ── karl_decision_records — KARL decisions time-series ───────────────────
SELECT create_hypertable(
    'karl_decision_records', 'created_at',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- ── karl_trajectories — replay buffer time-series ────────────────────────
SELECT create_hypertable(
    'karl_trajectories', 'created_at',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- ── backtest_runs — backtest results time-series ─────────────────────────
SELECT create_hypertable(
    'backtest_runs', 'created_at',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- ── agent_belief_history — Bayesian belief time-series ───────────────────
SELECT create_hypertable(
    'agent_belief_history', 'created_at',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- ── agent_selection_log — Thompson sampling time-series ──────────────────
SELECT create_hypertable(
    'agent_selection_log', 'created_at',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- ── kpi_metrics — KPI time-series ────────────────────────────────────────
SELECT create_hypertable(
    'kpi_metrics', 'created_at',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- ── oap_validation_history — validation event time-series ────────────────
SELECT create_hypertable(
    'oap_validation_history', 'created_at',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- ── Compression policies (7-day lag, save ~90% storage) ──────────────────
DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOREACH tbl IN ARRAY ARRAY[
        'sessions', 'agent_signals', 'karl_decision_records',
        'karl_trajectories', 'backtest_runs', 'agent_belief_history',
        'agent_selection_log', 'kpi_metrics', 'oap_validation_history'
    ] LOOP
        EXECUTE format(
            'ALTER TABLE %I SET (timescaledb.compress, timescaledb.compress_segmentby = '''' )',
            tbl
        );
        EXECUTE format(
            'SELECT add_compression_policy(%L, INTERVAL ''%s'')',
            tbl,
            CASE WHEN tbl = 'agent_belief_history' THEN '14 days' ELSE '7 days' END
        );
    END LOOP;
END $$;

-- ── Retention policies ───────────────────────────────────────────────────
SELECT add_retention_policy('sessions', INTERVAL '90 days', if_not_exists => TRUE);
SELECT add_retention_policy('agent_signals', INTERVAL '90 days', if_not_exists => TRUE);
SELECT add_retention_policy('agent_selection_log', INTERVAL '90 days', if_not_exists => TRUE);
SELECT add_retention_policy('kpi_metrics', INTERVAL '365 days', if_not_exists => TRUE);
SELECT add_retention_policy('oap_validation_history', INTERVAL '90 days', if_not_exists => TRUE);

-- ── Materialized continuous aggregates ───────────────────────────────────

-- Session counts per hour
CREATE MATERIALIZED VIEW IF NOT EXISTS sessions_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', created_at) AS bucket,
    symbol,
    COUNT(*) AS session_count,
    AVG(final_confidence) AS avg_confidence,
    COUNT(*) FILTER (WHERE final_signal = 'LONG') AS long_count,
    COUNT(*) FILTER (WHERE final_signal = 'SHORT') AS short_count,
    COUNT(*) FILTER (WHERE final_signal = 'NEUTRAL') AS neutral_count
FROM sessions
WHERE created_at > NOW() - INTERVAL '90 days'
GROUP BY bucket, symbol
WITH NO DATA;

SELECT add_continuous_aggregate_policy('sessions_hourly',
    start_offset      => INTERVAL '3 hours',
    end_offset        => INTERVAL '1 hour',
    schedule_interval => INTERVAL '10 minutes',
    if_not_exists     => TRUE
);

-- Agent performance aggregate
CREATE MATERIALIZED VIEW IF NOT EXISTS agent_performance_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', created_at) AS bucket,
    agent_name,
    agent_pool,
    COUNT(*) AS signal_count,
    AVG(confidence) AS avg_confidence
FROM agent_signals
WHERE created_at > NOW() - INTERVAL '90 days'
GROUP BY bucket, agent_name, agent_pool
WITH NO DATA;

SELECT add_continuous_aggregate_policy('agent_performance_daily',
    start_offset      => INTERVAL '3 days',
    end_offset        => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists     => TRUE
);

-- KARL decisions by regime
CREATE MATERIALIZED VIEW IF NOT EXISTS karl_decisions_by_regime
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', created_at) AS bucket,
    regime,
    COUNT(*) AS decision_count,
    AVG(confidence_final) AS avg_confidence,
    AVG(position_pct) AS avg_position_pct,
    AVG(uncertainty_total) AS avg_uncertainty
FROM karl_decision_records
WHERE created_at > NOW() - INTERVAL '90 days'
GROUP BY bucket, regime
WITH NO DATA;

SELECT add_continuous_aggregate_policy('karl_decisions_by_regime',
    start_offset      => INTERVAL '3 hours',
    end_offset        => INTERVAL '1 hour',
    schedule_interval => INTERVAL '15 minutes',
    if_not_exists     => TRUE
);

-- Refresh all
CALL refresh_continuous_aggregate('sessions_hourly', NULL, NULL);
CALL refresh_continuous_aggregate('agent_performance_daily', NULL, NULL);
CALL refresh_continuous_aggregate('karl_decisions_by_regime', NULL, NULL);
