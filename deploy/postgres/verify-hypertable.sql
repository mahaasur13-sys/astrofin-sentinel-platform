-- =============================================================================
-- verify-hypertable.sql — Post-deploy verification
-- Run: psql -d postgresql://astrofin:astrofin@localhost:5432/astrofin -f verify-hypertable.sql
-- =============================================================================

\echo '=== TimescaleDB version ==='
SELECT extversion FROM pg_extension WHERE extname = 'timescaledb';

\echo ''
\echo '=== Hypertables ==='
SELECT
    hypertable_name,
    total_chunks,
    pg_size_pretty(hypertable_size(hypertable_name::regclass)) AS size,
    compression_enabled
FROM timescaledb_information.hypertables
ORDER BY hypertable_name;

\echo ''
\echo '=== Compression policies ==='
SELECT
    hypertable_name,
    compress_after,
    schedule_interval
FROM timescaledb_information.jobs
WHERE application_name LIKE '%%Compression%%'
ORDER BY hypertable_name;

\echo ''
\echo '=== Retention policies ==='
SELECT
    hypertable_name,
    retention_window
FROM timescaledb_information.jobs
WHERE application_name LIKE '%%Retention%%';

\echo ''
\echo '=== Continuous aggregates ==='
SELECT
    view_name,
    materialized_hypertable_name,
    refresh_interval
FROM timescaledb_information.continuous_aggregates
ORDER BY view_name;

\echo ''
\echo '=== Chunk distribution (last 7 days) ==='
SELECT
    hypertable_name,
    range_start,
    range_end,
    is_compressed
FROM timescaledb_information.chunks
WHERE range_start > NOW() - INTERVAL '7 days'
ORDER BY hypertable_name, range_start DESC
LIMIT 20;
