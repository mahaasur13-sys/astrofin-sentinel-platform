-- Migration 0010: session/signal/decision IDs UUID -> VARCHAR
-- Purpose: app code writes short/variable-length string IDs
--          (str(uuid.uuid4())[:8], "KARL_0001_BTC", "DR-ABCD1234", "bt_..."),
--          not PostgreSQL UUIDs. Align column types with the app contract.
-- Related: db/models.py (KARLDecisionRecord already uses String(255)).

-- ══════════════════════════════ UP ══════════════════════════════
-- Run inside a transaction; PostgreSQL rebuilds FK constraints automatically
-- when both the referenced and referencing columns are altered.

ALTER TABLE sessions
    ALTER COLUMN session_id TYPE VARCHAR(255) USING session_id::text;

ALTER TABLE agent_signals
    ALTER COLUMN signal_id TYPE VARCHAR(255) USING signal_id::text;

ALTER TABLE agent_signals
    ALTER COLUMN session_id TYPE VARCHAR(255) USING session_id::text;

ALTER TABLE astro_positions
    ALTER COLUMN session_id TYPE VARCHAR(255) USING session_id::text;

ALTER TABLE audit_log
    ALTER COLUMN session_id TYPE VARCHAR(255) USING session_id::text;

ALTER TABLE audit_log
    ALTER COLUMN decision_id TYPE VARCHAR(255) USING decision_id::text;

ALTER TABLE agent_belief_history
    ALTER COLUMN session_id TYPE VARCHAR(255) USING session_id::text;

ALTER TABLE agent_selection_log
    ALTER COLUMN session_id TYPE VARCHAR(255) USING session_id::text;

ALTER TABLE oap_validation_history
    ALTER COLUMN decision_id TYPE VARCHAR(255) USING decision_id::text;

ALTER TABLE kpi_metrics
    ALTER COLUMN decision_id TYPE VARCHAR(255) USING decision_id::text;

ALTER TABLE backtest_runs
    ALTER COLUMN session_id TYPE VARCHAR(255) USING session_id::text;

-- ══════════════════════════════ DOWN ══════════════════════════════
-- Best-effort. IRREVERSIBLE once non-UUID values (e.g. "abc12345",
-- "KARL_0001_BTC", "DR-...") are written: the ::uuid cast below will fail.
-- Only valid if every existing value parses as a UUID.

-- ALTER TABLE sessions            ALTER COLUMN session_id  TYPE UUID USING session_id::uuid;
-- ALTER TABLE agent_signals       ALTER COLUMN signal_id   TYPE UUID USING signal_id::uuid;
-- ALTER TABLE agent_signals       ALTER COLUMN session_id  TYPE UUID USING session_id::uuid;
-- ALTER TABLE astro_positions     ALTER COLUMN session_id  TYPE UUID USING session_id::uuid;
-- ALTER TABLE audit_log           ALTER COLUMN session_id  TYPE UUID USING session_id::uuid;
-- ALTER TABLE audit_log           ALTER COLUMN decision_id TYPE UUID USING decision_id::uuid;
-- ALTER TABLE agent_belief_history ALTER COLUMN session_id TYPE UUID USING session_id::uuid;
-- ALTER TABLE agent_selection_log ALTER COLUMN session_id  TYPE UUID USING session_id::uuid;
-- ALTER TABLE oap_validation_history ALTER COLUMN decision_id TYPE UUID USING decision_id::uuid;
-- ALTER TABLE kpi_metrics         ALTER COLUMN decision_id TYPE UUID USING decision_id::uuid;
-- ALTER TABLE backtest_runs       ALTER COLUMN session_id  TYPE UUID USING session_id::uuid;
