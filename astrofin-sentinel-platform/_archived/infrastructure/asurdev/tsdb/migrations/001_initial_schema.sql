-- =============================================================================
-- TimescaleDB schema — home-cluster metrics store
-- Run: psql -d postgresql://cluster:password@localhost:5432/cluster_metrics -f 001_initial_schema.sql
-- =============================================================================

-- Extension (run once per database)
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- ---- Metrics raw table -------------------------------------------------------
CREATE TABLE IF NOT EXISTS metrics (
    time        TIMESTAMPTZ NOT NULL,
    node_id     TEXT        NOT NULL,
    metric      TEXT        NOT NULL,
    value       DOUBLE PRECISION,
    labels      JSONB       DEFAULT '{}'
);

SELECT create_hypertable('metrics', 'time', chunk_time_interval => INTERVAL '1 hour');

CREATE INDEX idx_metrics_node_metric_time ON metrics (node_id, metric, time DESC);
CREATE INDEX idx_metrics_metric ON metrics (metric, time DESC);

-- ---- Job events table (already exists in state_store, mirror here for TSDB join) ----
CREATE TABLE IF NOT EXISTS job_events (
    time        TIMESTAMPTZ NOT NULL,
    job_id      BIGINT      NOT NULL,
    node_id     TEXT,
    event_type  TEXT        NOT NULL,  -- ADMITTED / SCHEDULED / RUNNING / SUCCESS / FAIL
    duration_s  DOUBLE PRECISION,
    exit_code   INTEGER,
    labels      JSONB       DEFAULT '{}'
);

SELECT create_hypertable('job_events', 'time', chunk_time_interval => INTERVAL '1 hour');

-- ---- Continuous aggregates ----------------------------------------------------
-- 1-minute aggregates (raw-like, for backfill)
CREATE MATERIALIZED VIEW metrics_1m
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', time) AS bucket,
    node_id,
    metric,
    COUNT(*)  AS sample_count,
    AVG(value) AS avg,
    MIN(value) AS min,
    MAX(value) AS max,
    STDDEV(value) AS stddev
FROM metrics
GROUP BY bucket, node_id, metric
WITH NO DATA;

SELECT add_continuous_aggregate_policy('metrics_1m',
    start_offset          => INTERVAL '3 hours',
    end_offset            => INTERVAL '1 hour',
    schedule_interval     => INTERVAL '5 minutes');

-- 5-minute aggregates (primary for feature_pipeline)
CREATE MATERIALIZED VIEW metrics_5m
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('5 minutes', time) AS bucket,
    node_id,
    metric,
    COUNT(*)  AS sample_count,
    AVG(value) AS avg,
    MIN(value) AS min,
    MAX(value) AS max,
    STDDEV(value) AS stddev,
    -- Percentiles via APPROXIMATE percentiles
    APPROX_PERCENTILE(0.50) WITHIN GROUP (ORDER BY value) AS p50,
    APPROX_PERCENTILE(0.95) WITHIN GROUP (ORDER BY value) AS p95,
    APPROX_PERCENTILE(0.99) WITHIN GROUP (ORDER BY value) AS p99
FROM metrics
WHERE time > NOW() - INTERVAL '4 weeks'
GROUP BY bucket, node_id, metric
WITH NO DATA;

SELECT add_continuous_aggregate_policy('metrics_5m',
    start_offset          => INTERVAL '3 hours',
    end_offset            => INTERVAL '10 minutes',
    schedule_interval     => INTERVAL '5 minutes');

-- 15-minute aggregates (for ML training)
CREATE MATERIALIZED VIEW metrics_15m
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('15 minutes', time) AS bucket,
    node_id,
    metric,
    COUNT(*)  AS sample_count,
    AVG(value) AS avg,
    MIN(value) AS min,
    MAX(value) AS max,
    STDDEV(value) AS stddev,
    APPROX_PERCENTILE(0.95) WITHIN GROUP (ORDER BY value) AS p95
FROM metrics
WHERE time > NOW() - INTERVAL '4 weeks'
GROUP BY bucket, node_id, metric
WITH NO DATA;

SELECT add_continuous_aggregate_policy('metrics_15m',
    start_offset          => INTERVAL '6 hours',
    end_offset            => INTERVAL '30 minutes',
    schedule_interval     => INTERVAL '15 minutes');

-- 1-hour aggregates (long-term storage)
CREATE MATERIALIZED VIEW metrics_1h
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    node_id,
    metric,
    COUNT(*)  AS sample_count,
    AVG(value) AS avg,
    MIN(value) AS min,
    MAX(value) AS max,
    STDDEV(value) AS stddev,
    APPROX_PERCENTILE(0.95) WITHIN GROUP (ORDER BY value) AS p95
FROM metrics
GROUP BY bucket, node_id, metric
WITH NO DATA;

SELECT add_continuous_aggregate_policy('metrics_1h',
    start_offset          => INTERVAL '13 months',
    end_offset            => INTERVAL '2 hours',
    schedule_interval     => INTERVAL '1 hour');

-- ---- Refresh all -------------------------------------------------------
CALL refresh_continuous_aggregate('metrics_1m', NULL, NULL);
CALL refresh_continuous_aggregate('metrics_5m', NULL, NULL);
CALL refresh_continuous_aggregate('metrics_15m', NULL, NULL);
CALL refresh_continuous_aggregate('metrics_1h', NULL, NULL);
