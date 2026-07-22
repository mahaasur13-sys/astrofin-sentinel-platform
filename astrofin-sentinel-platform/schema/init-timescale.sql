-- schema/init-timescale.sql
-- Applied automatically by TimescaleDB docker on first container start
-- ATOM-DB-MIGRATION-002

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
CREATE EXTENSION IF NOT EXISTS vector CASCADE;
CREATE EXTENSION IF NOT EXISTS pgcrypto CASCADE;
CREATE EXTENSION IF NOT EXISTS hll CASCADE;

-- Grant usage on hll to public (needed for hypertables)
GRANT USAGE ON EXTENSION hll TO PUBLIC;

\i /schema/001_initial.sql

-- Verify hypertables
SELECT hypertable_name, num_chunks
FROM timescaledb_information.hypertables
WHERE hypertable_name IN (
    'sessions', 'agent_signals', 'karl_decision_records',
    'oap_validation_history', 'kpi_metrics', 'audit_log'
);

SELECT 'TimescaleDB init complete' AS status;
