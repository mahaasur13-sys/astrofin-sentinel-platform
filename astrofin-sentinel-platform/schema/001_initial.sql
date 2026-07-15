-- AstroFin Sentinel V5 - Initial Schema
-- PostgreSQL 16 + TimescaleDB 2.14 + pgvector 0.7
-- Generated: 2026-03-29
-- Note: Extensions are created by init-timescale.sql

-- Extensions are now in schema/init-timescale.sql
-- CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
-- CREATE EXTENSION IF NOT EXISTS vector CASCADE;
-- CREATE EXTENSION IF NOT EXISTS pgcrypto CASCADE;
-- CREATE EXTENSION IF NOT EXISTS hll CASCADE;

-- Enums
CREATE TYPE signal_direction AS ENUM ('BUY', 'LONG', 'SELL', 'SHORT', 'NEUTRAL', 'HOLD', 'AVOID', 'STRONG_BUY', 'STRONG_SELL');
CREATE TYPE volatility_regime AS ENUM ('LOW', 'NORMAL', 'HIGH', 'EXTREME');
CREATE TYPE query_type AS ENUM ('NATURAL', 'TECHNICAL', 'FUNDAMENTAL', 'MACRO', 'QUANT', 'OPTIONS', 'SENTIMENT', 'ASTRO', 'ELECTION');
CREATE TYPE session_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
CREATE TYPE agent_pool AS ENUM ('TECHNICAL', 'MACRO', 'ASTRO', 'ELECTION', 'SENTIMENT', 'QUANT', 'FUNDAMENTAL', 'OPTIONS');

-- Sessions
CREATE TABLE sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(20) NOT NULL,
    query_type query_type NOT NULL,
    current_price NUMERIC(20,8),
    session_status session_status NOT NULL DEFAULT 'pending',
    final_signal signal_direction,
    final_confidence INTEGER,
    regime volatility_regime DEFAULT 'NORMAL',
    flows_run JSONB,
    thompson_selections JSONB,
    agent_count INTEGER DEFAULT 0,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

SELECT create_hypertable('sessions', 'created_at', migrate_data => true, chunk_interval => '7 days');

CREATE INDEX idx_sessions_symbol_timeframe ON sessions (symbol, timeframe);
CREATE INDEX idx_sessions_created_date ON sessions (created_at DATE);
CREATE INDEX idx_sessions_final_signal ON sessions (final_signal);
CREATE INDEX idx_sessions_regime ON sessions (regime);

-- Agent Signals
CREATE TABLE agent_signals (
    signal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,
    agent_pool agent_pool,
    signal signal_direction,
    confidence INTEGER,
    reasoning TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

SELECT create_hypertable('agent_signals', 'created_at', migrate_data => true, chunk_interval => '7 days');
CREATE INDEX idx_agent_signals_session ON agent_signals (session_id);
CREATE INDEX idx_agent_signals_agent ON agent_signals (agent_name);

-- Agent Beliefs (Thompson Sampling)
CREATE TABLE agent_beliefs (
    agent_name VARCHAR(100) PRIMARY KEY,
    pool_name agent_pool NOT NULL,
    alpha NUMERIC(10,4) DEFAULT 1.0,
    beta NUMERIC(10,4) DEFAULT 1.0,
    total_sessions INTEGER DEFAULT 0,
    total_successes INTEGER DEFAULT 0,
    avg_confidence NUMERIC(5,2) DEFAULT 50.0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Agent Belief History
CREATE TABLE agent_belief_history (
    id BIGSERIAL PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL,
    session_id UUID REFERENCES sessions(session_id) ON DELETE SET NULL,
    prior_alpha NUMERIC(10,4),
    prior_beta NUMERIC(10,4),
    posterior_alpha NUMERIC(10,4),
    posterior_beta NUMERIC(10,4),
    was_selected BOOLEAN,
    was_successful BOOLEAN,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_belief_history_agent ON agent_belief_history (agent_name);

-- Agent Selection Log
CREATE TABLE agent_selection_log (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,
    pool_name agent_pool NOT NULL,
    was_called BOOLEAN NOT NULL,
    success_flag BOOLEAN,
    reward NUMERIC(10,6),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

SELECT create_hypertable('agent_selection_log', 'created_at', migrate_data => true, chunk_interval => '7 days');
CREATE INDEX idx_selection_log_session ON agent_selection_log (session_id);
CREATE INDEX idx_selection_log_agent ON agent_selection_log (agent_name);

-- KARL Decision Records
CREATE TABLE karl_decision_records (
    decision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(session_id) ON DELETE SET NULL,
    symbol VARCHAR(20),
    price NUMERIC(20,8),
    timeframe VARCHAR(20),
    regime volatility_regime,
    state_hash VARCHAR(32),
    top_trajectories JSONB,
    selected_ensemble JSONB,
    q_values JSONB,
    q_star NUMERIC(8,6),
    advantage NUMERIC(8,6),
    uncertainty_aleatoric NUMERIC(6,4),
    uncertainty_epistemic NUMERIC(6,4),
    uncertainty_total NUMERIC(6,4),
    confidence_raw INTEGER,
    confidence_final INTEGER,
    confidence_adjustments JSONB,
    final_action signal_direction,
    position_pct NUMERIC(6,4),
    kpi_snapshot JSONB,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

SELECT create_hypertable('karl_decision_records', 'created_at', migrate_data => true, chunk_interval => '1 day');
CREATE INDEX idx_karl_session ON karl_decision_records (session_id);
CREATE INDEX idx_karl_symbol ON karl_decision_records (symbol);
CREATE INDEX idx_karl_regime ON karl_decision_records (regime);

-- OAP Validation History
CREATE TABLE oap_validation_history (
    id BIGSERIAL PRIMARY KEY,
    decision_id UUID,
    status VARCHAR(20),
    confidence INTEGER,
    position_pct NUMERIC(6,4),
    confidence_boost INTEGER,
    regime volatility_regime,
    issues JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

SELECT create_hypertable('oap_validation_history', 'created_at', migrate_data => true, chunk_interval => '1 day');

-- KPI Metrics (TTD/TTC/Out-of-sample)
CREATE TABLE kpi_metrics (
    id BIGSERIAL PRIMARY KEY,
    decision_id UUID,
    metric_name VARCHAR(50) NOT NULL,
    metric_value NUMERIC(12,6),
    regime volatility_regime,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

SELECT create_hypertable('kpi_metrics', 'created_at', migrate_data => true, chunk_interval => '1 day');
CREATE INDEX idx_kpi_metrics_name ON kpi_metrics (metric_name);
CREATE INDEX idx_kpi_metrics_decision ON kpi_metrics (decision_id);

-- Reward Calibration
CREATE TABLE reward_calibration (
    id BIGSERIAL PRIMARY KEY,
    n_bins INTEGER DEFAULT 10,
    slope NUMERIC(8,6) DEFAULT 1.0,
    intercept NUMERIC(8,6) DEFAULT 0.0,
    calibration_error NUMERIC(8,6),
    fitted BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Backtest Runs
CREATE TABLE backtest_runs (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID REFERENCES sessions(session_id) ON DELETE SET NULL,
    symbol VARCHAR(20) NOT NULL,
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    timeframe VARCHAR(20),
    win_rate NUMERIC(5,4),
    sharpe_ratio NUMERIC(8,4),
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    avg_win_pct NUMERIC(8,4),
    avg_loss_pct NUMERIC(8,4),
    total_return_pct NUMERIC(10,4),
    max_drawdown_pct NUMERIC(10,4),
    avg_confidence NUMERIC(5,2),
    initial_capital NUMERIC(20,8),
    final_capital NUMERIC(20,8),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_backtest_symbol ON backtest_runs (symbol);
CREATE INDEX idx_backtest_dates ON backtest_runs (start_date, end_date);

-- Vector Embeddings for RAG
CREATE TABLE rag_embeddings (
    id BIGSERIAL PRIMARY KEY,
    chunk_id VARCHAR(100) NOT NULL,
    domain VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1024),
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rag_domain ON rag_embeddings (domain);
CREATE INDEX idx_rag_chunk ON rag_embeddings (chunk_id);
CREATE INDEX idx_rag_embedding ON rag_embeddings USING hnsw (embedding vector_cosine_ops);

-- Immutable Audit Log
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id UUID,
    action VARCHAR(20) NOT NULL,
    old_data JSONB,
    new_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

SELECT create_hypertable('audit_log', 'created_at', migrate_data => true, chunk_interval => '1 month');
CREATE INDEX idx_audit_table ON audit_log (table_name);
CREATE INDEX idx_audit_record ON audit_log (record_id);

-- Retention Policies (TimescaleDB)
SELECT add_retention_policy('sessions', INTERVAL '90 days');
SELECT add_retention_policy('agent_signals', INTERVAL '90 days');
SELECT add_retention_policy('agent_selection_log', INTERVAL '90 days');
SELECT add_retention_policy('karl_decision_records', INTERVAL '90 days');
SELECT add_retention_policy('oap_validation_history', INTERVAL '90 days');
SELECT add_retention_policy('kpi_metrics', INTERVAL '90 days');
SELECT add_retention_policy('audit_log', INTERVAL '2 years');

-- Compression (TimescaleDB)
ALTER TABLE sessions SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol'
);
SELECT add_compression_policy('sessions', INTERVAL '1 day');

ALTER TABLE agent_signals SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'agent_name'
);
SELECT add_compression_policy('agent_signals', INTERVAL '1 day');

ALTER TABLE karl_decision_records SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol'
);
SELECT add_compression_policy('karl_decision_records', INTERVAL '1 day');

-- RLS Policies
ALTER TABLE agent_beliefs ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_belief_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_selection_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE karl_decision_records ENABLE ROW LEVEL SECURITY;

CREATE POLICY admin_all ON agent_beliefs FOR ALL TO postgres USING (true);
CREATE POLICY admin_all ON agent_belief_history FOR ALL TO postgres USING (true);
CREATE POLICY admin_all ON agent_selection_log FOR ALL TO postgres USING (true);
CREATE POLICY admin_all ON karl_decision_records FOR ALL TO postgres USING (true);

-- Immutable: no DELETE/UPDATE on audit_log
CREATE POLICY no_modify_audit ON audit_log FOR ALL TO postgres USING (false) WITH CHECK (false);

-- Seed data for agent beliefs
INSERT INTO agent_beliefs (agent_name, pool_name, alpha, beta, total_sessions, avg_confidence) VALUES
    ('FundamentalAgent', 'FUNDAMENTAL', 1.0, 1.0, 0, 50.0),
    ('QuantAgent', 'QUANT', 1.0, 1.0, 0, 50.0),
    ('MacroAgent', 'MACRO', 1.0, 1.0, 0, 50.0),
    ('OptionsFlowAgent', 'OPTIONS', 1.0, 1.0, 0, 50.0),
    ('SentimentAgent', 'SENTIMENT', 1.0, 1.0, 0, 50.0),
    ('TechnicalAgent', 'TECHNICAL', 1.0, 1.0, 0, 50.0),
    ('MarketAnalyst', 'TECHNICAL', 1.0, 1.0, 0, 50.0),
    ('BullResearcher', 'TECHNICAL', 1.0, 1.0, 0, 50.0),
    ('BearResearcher', 'TECHNICAL', 1.0, 1.0, 0, 50.0),
    ('BradleyAgent', 'ASTRO', 1.0, 1.0, 0, 50.0),
    ('GannAgent', 'ASTRO', 1.0, 1.0, 0, 50.0),
    ('CycleAgent', 'ASTRO', 1.0, 1.0, 0, 50.0),
    ('ElectoralAgent', 'ELECTION', 1.0, 1.0, 0, 50.0),
    ('TimeWindowAgent', 'ASTRO', 1.0, 1.0, 0, 50.0),
    ('MLPredictorAgent', 'QUANT', 1.0, 1.0, 0, 50.0),
    ('InsiderAgent', 'FUNDAMENTAL', 1.0, 1.0, 0, 50.0);
