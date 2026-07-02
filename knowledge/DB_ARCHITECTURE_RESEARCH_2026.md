# AstroFin Sentinel V5 — Database Architecture Research 2026

## Role: Senior Database Architect & AI Systems Engineer

**15+ years** designing high-performance, time-series, and vector-enabled databases for financial and AI-agent systems.


## Project Context

**AstroFinSentinelV5** — multi-agent trading system combining:

- **Real-time + historical data**: Metals (Gold, Silver, Nickel, Platinum, Palladium, Copper) and cryptocurrencies (BTC, ETH, XMR, etc.)
- **Astrological data**: Planetary positions, aspects, retrogrades, lunar phases via Swiss Ephemeris
- **KARL approach**: OAP + TTC + DecisionRecord + AuditLog + replay buffer
- **Multi-agent architecture**: Semantic memory, grounding, uncertainty estimation, self-questioning

---

## 1. Requirements Analysis

### Data Types & Volumes

| Category | Data Type | Volume (1Y) | Volume (3Y) | Volume (5Y) | Access Pattern |
|----------|-----------|-------------|-------------|-------------|----------------|
| **Market OHLCV** | Time-series | ~500MB | ~2GB | ~5GB | Read-heavy, daily aggregation |
| **Agent Signals** | Relational + JSON | ~50MB | ~200MB | ~500MB | Random access, full scans for backtest |
| **Planetary Positions** | Time-series | ~100MB | ~300MB | ~500MB | Read-heavy, interpolation |
| **Decision Records** | Audit (append-only) | ~200MB | ~1GB | ~3GB | Sequential writes, rare updates |
| **Vector Embeddings** | Vector (1536-dim) | ~500MB | ~2GB | ~5GB | ANN search, HNSW |
| **Thompson Beliefs** | Relational | <1MB | <1MB | <1MB | Random access, per-session updates |
| **Backtest Results** | Analytical | ~20MB | ~100MB | ~300MB | Full table scans |
| **Lunar Phases** | Time-series | ~10MB | ~30MB | ~50MB | Read-heavy |

**Total 5Y estimate**: ~15GB (uncompressed), ~3GB (with TimescaleDB compression)

### Critical Use Cases

| Priority | Use Case | Latency | Frequency | Data Size |
|----------|----------|---------|-----------|----------|
| P0 | **Real-time signals** | <100ms | On-demand | <1MB per query |
| P0 | **Thompson sampling** | <10ms | Per session | <1KB per agent |
| P1 | **Backtesting** | <10s | Daily | 71+ sessions full scan |
| P1 | **KARL learning** | <1s | Continuous | 100-1000 trajectories |
| P2 | **RAG retrieval** | <50ms | Per agent call | Top-5 vectors |
| P2 | **Audit reproduction** | <1s | On-demand | 1 decision record |

---

## 2. Technology Comparison (2026)

### Comparison Table

| Technology | Time-Series Perf | Vector Search | ACID | Cost | Scalability | LangGraph Compatible | Python Ecosystem |
|-----------|-----------------|---------------|------|------|-------------|---------------------|------------------|
| **PostgreSQL + pgvector + TimescaleDB** | ⭐⭐⭐⭐⭐ (native hypertable) | ⭐⭐⭐⭐ (pgvector HNSW) | ✅ Full | $ (managed or self-hosted) | ⭐⭐⭐⭐ (vertical + read replicas) | ✅ Native checkpointing | ✅ Excellent |
| **ClickHouse** | ⭐⭐⭐⭐⭐ (columnar, vectorized) | ⭐⭐⭐ (external vectors only) | ⚠️ Eventual by default | $$ (expensive managed) | ⭐⭐⭐⭐⭐ (horizontal sharding) | ⚠️ External state | ⚠️ Moderate |
| **Cassandra / ScyllaDB** | ⭐⭐⭐⭐ (wide rows) | ❌ No native | ⚠️ Tunable consistency | $ (self-hosted) | ⭐⭐⭐⭐⭐ (multi-DC) | ❌ No native | ⚠️ Moderate |
| **DuckDB / MotherDuck** | ⭐⭐⭐ (analytical only) | ⭐⭐⭐ (via extensions) | ⚠️ Single-file | $ (MotherDuck serverless) | ⭐⭐⭐ (single node, vertical) | ⚠️ Limited | ✅ Excellent (pandas-like) |
| **Qdrant** | N/A | ⭐⭐⭐⭐⭐ (HNSW, quantization) | ⚠️ Eventual | $$ (cloud or self-hosted) | ⭐⭐⭐⭐ (horizontal) | ⚠️ Needs wrapper | ✅ Good |
| **Weaviate** | N/A | ⭐⭐⭐⭐⭐ (HNSW, BM25 hybrid) | ⚠️ Eventual | $$ (cloud or self-hosted) | ⭐⭐⭐⭐ (horizontal) | ⚠️ Needs wrapper | ✅ Good |
| **Pinecone** | N/A | ⭐⭐⭐⭐⭐ (serverless) | ⚠️ Eventual | $$$ (premium pricing) | ⭐⭐⭐⭐⭐ (serverless) | ⚠️ Needs wrapper | ✅ Good |
| **Milvus** | N/A | ⭐⭐⭐⭐ (HNSW, DiskANN) | ⚠️ Eventual | $ (self-hosted) | ⭐⭐⭐⭐⭐ (horizontal) | ⚠️ Needs wrapper | ✅ Good |

### Analysis

**PostgreSQL + pgvector + TimescaleDB** is the **optimal choice** for AstroFinSentinelV5 because:

1. **Unified architecture**: Single database for relational (beliefs, sessions), time-series (OHLCV, planetary), and vector (embeddings) data
2. **TimescaleDB**: Native hypertables for automatic time-series partitioning and compression (10-100x compression!)
3. **pgvector**: HNSW index support since v0.5, competitive with specialized vector DBs
4. **ACID compliance**: Critical for financial audit requirements
5. **LangGraph compatibility**: Native checkpointing support, mature Python drivers
6. **Cost efficiency**: Self-hosted on $20/month VPS or managed at $100-500/month

**When to add Qdrant**: If vector search latency exceeds 50ms or recall <95%, add Qdrant as sidecar for embeddings only.

**Why NOT ClickHouse**: No native vector search, eventual consistency, expensive managed, complex operational overhead.

---

## 3. Recommended Architecture

### Primary: PostgreSQL 16 + TimescaleDB 2.14 + pgvector 0.7

```bash
# docker-compose.yml
services:
  postgres:
    image: timescale/timescaledb:latest-pg16
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    command: -c shared_preload_libraries=vector
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Hot / Warm / Cold Data Strategy

| Tier | Data | Storage | Retention | Compression |
|------|------|---------|-----------|------------|
| **Hot** (SSD NVMe) | sessions, agent_beliefs, decision_records (current month) | TimescaleDB SSD | 0-30 days | 3-5x |
| **Warm** (HDD) | decision_records (history), replay_buffer | TimescaleDB HDD | 30-365 days | 10-20x |
| **Cold** (S3) | ohlcv_1h, planetary_positions | TimescaleDB + S3 | 1-5 years | 50-100x |

### Schema Design

```sql
-- ==============================================
-- CORE: Sessions (Hypertable)
-- ==============================================

CREATE TABLE sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      TEXT UNIQUE NOT NULL,
    symbol          TEXT NOT NULL,
    timeframe       TEXT NOT NULL,
    query_type      TEXT NOT NULL,
    current_price   NUMERIC(18, 8) NOT NULL,
    flows_run       JSONB NOT NULL DEFAULT '{}',
    agent_count     INTEGER NOT NULL DEFAULT 0,
    final_signal    TEXT NOT NULL,
    final_confidence INTEGER NOT NULL DEFAULT 50,
    final_reasoning TEXT,
    final_output    JSONB,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    thompson_selections JSONB,
    technical_agent_count  INTEGER DEFAULT 0,
    astro_agent_count      INTEGER DEFAULT 0,
    macro_agent_count     INTEGER DEFAULT 0,
    electoral_agent_count  INTEGER DEFAULT 0
);
SELECT create_hypertable('sessions', 'created_at', chunk_time_interval => INTERVAL '1 day');
CREATE INDEX idx_sessions_symbol_time ON sessions (symbol, created_at DESC);
CREATE INDEX idx_sessions_signal ON sessions (final_signal, created_at DESC);

-- ==============================================
-- KARL: Decision Records (Partitioned, Immutable)
-- ==============================================

CREATE TABLE decision_records (
    id                  SERIAL PRIMARY KEY,
    decision_id          TEXT UNIQUE NOT NULL,
    session_id           TEXT NOT NULL,
    symbol               TEXT NOT NULL,
    price                NUMERIC(18, 8) NOT NULL,
    timeframe            TEXT NOT NULL,
    regime               TEXT NOT NULL,
    state_hash           TEXT NOT NULL,  -- SHA-256 of market state
    top_trajectories     JSONB,
    selected_ensemble    JSONB,
    q_values             JSONB,
    q_star               REAL NOT NULL,
    advantage            REAL NOT NULL,
    uncertainty_aleatoric REAL NOT NULL,
    uncertainty_epistemic REAL NOT NULL,
    uncertainty_total     REAL NOT NULL,
    confidence_raw        INTEGER NOT NULL,
    confidence_final      INTEGER NOT NULL,
    confidence_adjustments JSONB,
    final_action         TEXT NOT NULL,
    position_pct         REAL NOT NULL,
    kpi_snapshot         JSONB,
    metadata             JSONB,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Monthly partitions
CREATE TABLE decision_records_2026_03 PARTITION OF decision_records
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');
CREATE TABLE decision_records_2026_04 PARTITION OF decision_records
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');

-- ==============================================
-- KARL: Replay Buffer (Vector-Enabled)
-- ==============================================

CREATE TABLE replay_buffer (
    id                  SERIAL PRIMARY KEY,
    trajectory_id        TEXT NOT NULL,
    session_id           TEXT,
    symbol               TEXT NOT NULL,
    regime               TEXT NOT NULL,
    trajectory_data      JSONB NOT NULL,
    trajectory_metrics   JSONB NOT NULL,
    outcome              REAL NOT NULL,
    market_context       JSONB,
    embedding            VECTOR(1536),  -- nomic-embed-text
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- HNSW index for ANN search
CREATE INDEX idx_buffer_embedding ON replay_buffer
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
-- IVFFlat for memory efficiency
CREATE INDEX idx_buffer_embedding_ivf ON replay_buffer
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
CREATE INDEX idx_buffer_symbol_regime ON replay_buffer (symbol, regime);

-- ==============================================
-- AGENT BELIEFS (Thompson Sampling)
-- ==============================================

CREATE TABLE agent_beliefs (
    agent_name      TEXT PRIMARY KEY,
    pool_name       TEXT NOT NULL,  -- TECHNICAL, MACRO, ASTRO, ELECTORAL
    alpha           REAL NOT NULL DEFAULT 1.0,
    beta            REAL NOT NULL DEFAULT 1.0,
    total_sessions  INTEGER NOT NULL DEFAULT 0,
    last_signal     TEXT,
    last_confidence INTEGER,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE agent_selection_log (
    id              SERIAL PRIMARY KEY,
    session_id      TEXT NOT NULL,
    agent_name      TEXT NOT NULL,
    pool_name       TEXT NOT NULL,
    was_called      BOOLEAN NOT NULL,
    sampled_theta   REAL,
    selected_top_k  BOOLEAN,
    success_flag   INTEGER,  -- 1=profitable, 0=loss, NULL=unknown
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==============================================
-- MARKET DATA (Hypertable with Compression)
-- ==============================================

CREATE TABLE ohlcv_1h (
    symbol          TEXT NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL,
    open            NUMERIC(18, 8) NOT NULL,
    high            NUMERIC(18, 8) NOT NULL,
    low             NUMERIC(18, 8) NOT NULL,
    close           NUMERIC(18, 8) NOT NULL,
    volume          NUMERIC(18, 2),
    PRIMARY KEY (symbol, timestamp)
) PARTITION BY RANGE (timestamp);
SELECT create_hypertable('ohlcv_1h', 'timestamp', chunk_time_interval => INTERVAL '7 days');

-- Enable compression for old chunks
ALTER TABLE ohlcv_1h SET (
    timescaledb.compress = true,
    timescaledb.compress_segmentby = 'symbol'
);

-- ==============================================
-- ASTROLOGICAL DATA (Hypertable)
-- ==============================================

CREATE TABLE planetary_positions (
    id              SERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL,
    planet          TEXT NOT NULL,  -- Sun, Moon, Mercury...
    longitude       REAL NOT NULL,
    latitude        REAL NOT NULL,
    distance_au     REAL NOT NULL,
    speed_deg_day   REAL NOT NULL,
    nakshatra       INTEGER,
    nakshatra_name  TEXT,
    rashi           INTEGER,
    zodiac_name     TEXT,
    UNIQUE (timestamp, planet)
) PARTITION BY RANGE (timestamp);
SELECT create_hypertable('planetary_positions', 'timestamp', chunk_time_interval => INTERVAL '1 day');
CREATE INDEX idx_planets_nakshatra ON planetary_positions (nakshatra, timestamp DESC);

-- ==============================================
-- BACKTEST RESULTS
-- ==============================================

CREATE TABLE backtest_runs (
    id                  SERIAL PRIMARY KEY,
    session_id          TEXT,
    symbol              TEXT NOT NULL,
    start_date          DATE NOT NULL,
    end_date            DATE NOT NULL,
    timeframe           TEXT NOT NULL,
    win_rate            REAL NOT NULL,
    sharpe_ratio        REAL NOT NULL,
    total_trades        INTEGER NOT NULL,
    winning_trades      INTEGER NOT NULL,
    losing_trades       INTEGER NOT NULL,
    avg_win_pct         REAL NOT NULL,
    avg_loss_pct        REAL NOT NULL,
    total_return_pct   REAL NOT NULL,
    max_drawdown_pct    REAL NOT NULL,
    avg_confidence      REAL NOT NULL,
    initial_capital     REAL NOT NULL,
    final_capital       REAL NOT NULL,
    metadata            JSONB,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_backtest_sharpe ON backtest_runs (sharpe_ratio DESC);
```

## 4. Performance & Scalability

### Query Patterns & Optimization

| Query | Pattern | Optimization |
|-------|---------|---------------|
| Real-time signal | Point query on session_id | Primary key index |
| Backtest full scan | Range query on created_at + symbol | BRIN index on timestamp |
| Thompson belief update | Point update on agent_name | Primary key |
| Vector similarity search | ANN on embedding | HNSW index (m=16, ef=100) |
| Planetary positions | Range query on timestamp | BRIN index |
| KARL trajectory lookup | Point query on state_hash | Hash index |

### Index Strategy

```sql
-- BRIN for time-series (low overhead)
CREATE INDEX idx_sessions_created_brin ON sessions USING BRIN (created_at);
CREATE INDEX idx_decision_created_brin ON decision_records USING BRIN (created_at);

-- GIN for JSONB queries
CREATE INDEX idx_sessions_flows_gin ON sessions USING GIN (flows_run);
CREATE INDEX idx_decision_ensemble_gin ON decision_records USING GIN (selected_ensemble);

-- Composite for common queries
CREATE INDEX idx_sessions_symbol_time ON sessions (symbol, created_at DESC);
CREATE INDEX idx_buffer_symbol_regime ON replay_buffer (symbol, regime, outcome DESC);
```

### Retention Policy

```sql
-- Compress chunks older than 7 days
SELECT add_retention_policy('sessions', INTERVAL '30 days');
SELECT add_retention_policy('decision_records', INTERVAL '365 days');
SELECT add_retention_policy('ohlcv_1h', INTERVAL '5 years');

-- Continuous aggregate for daily summaries (for fast dashboards)
CREATE MATERIALIZED VIEW sessions_daily_summary
WITH (timescaledb.continuous) AS
SELECT time_bucket('1 day', created_at) AS ts,
       symbol,
       COUNT(*) AS session_count,
       AVG(final_confidence) AS avg_confidence,
       SUM(CASE WHEN final_signal IN ('BUY','LONG') THEN 1 ELSE 0 END)::float / COUNT(*) AS bullish_ratio
FROM sessions
GROUP BY 1, 2;
```

### Caching Strategy (Redis)

```python
# Cache hot data
REDIS_KEYS = {
    'beliefs': 'astrofin:beliefs:{agent_name}',      # TTL: 5min
    'session_latest': 'astrofin:session:latest:{symbol}',  # TTL: 1min
    'ohlcv_recent': 'astrofin:ohlcv:1h:{symbol}:latest',  # TTL: 1min
    'planets_current': 'astrofin:planets:current',  # TTL: 1min
}

# Invalidate on write
async def update_belief_and_invalidate(agent_name, belief):
    await redis.setex(f'astrofin:beliefs:{agent_name}', 300, json.dumps(belief))
```

---

## 5. Security & Compliance

### Row Level Security (RLS)

```sql
-- Enable RLS
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_beliefs ENABLE ROW LEVEL SECURITY;

-- Policy: users see only their own sessions
CREATE POLICY user_sessions ON sessions
    FOR ALL USING (user_id = current_user);

-- Decision records: immutable, no deletes
REVOKE DELETE ON decision_records FROM PUBLIC;
-- Audit log: append-only via trigger
CREATE OR REPLACE FUNCTION prevent_delete()
RETURNS TRIGGER AS $$
BEGIN RAISE EXCEPTION 'Deletes not allowed'; END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER no_delete_decision_records
    BEFORE DELETE ON decision_records
    FOR EACH ROW EXECUTE FUNCTION prevent_delete();
```

### Immutable Audit Logs

```sql
-- Decision records: never update, only insert
REVOKE UPDATE, DELETE ON decision_records FROM PUBLIC;

-- Separate immutable_audit table for compliance
CREATE TABLE immutable_audit (
    id          BIGSERIAL PRIMARY KEY,
    action      TEXT NOT NULL,  -- INSERT, UPDATE, DELETE
    table_name  TEXT NOT NULL,
    row_data    JSONB NOT NULL,
    changed_by  TEXT,
    changed_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- Only INSERT allowed
REVOKE UPDATE, DELETE ON immutable_audit FROM PUBLIC;
```

---

## 6. Integration with Project

### LangGraph Checkpointing

```python
# Option 1: PostgreSQL checkpointer (recommended)
from langgraph.checkpoint.postgres import PostgresSaver

checkpointer = PostgresSaver.from_conn_string(DATABASE_URL)
checkpointer.setup()  # Creates schema

graph.compile(checkpointer=checkpointer)

# Option 2: TimescaleDB-aware checkpointer
from langgraph.checkpoint.timescale import TimescaleSaver
ts_saver = TimescaleSaver.from_conn_string(DATABASE_URL)
```

### KARL Integration

```python
# OAP: Store in replay_buffer with vector embedding
INSERT INTO replay_buffer (trajectory_id, symbol, regime, trajectory_data, embedding)
VALUES ($1, $2, $3, $4, $5)
WHERE embedding = embedding_from_nomic(state_description);

# TTC: Query similar trajectories
SELECT * FROM replay_buffer
WHERE symbol = $1 AND regime = $2
ORDER BY embedding <=> $3  -- Cosine distance
LIMIT 10;

# DecisionRecord: Immutable audit
INSERT INTO decision_records (decision_id, session_id, state_hash, final_action, q_star, ...)
VALUES ($1, $2, $3, $4, $5, ...);
-- No UPDATE/DELETE permissions for application user
```

### Migration (Alembic)

```bash
# Install dependencies
pip install alembic psycopg2-binary asyncpg sqlalchemy[tgresql]

# Initialize
alembic init migrations

# env.py
from sqlalchemy import create_engine
from timescale_sqlalchemy import Timescale
config.set_main_option('sqlalchemy.url', DATABASE_URL)

# migration example
alembic revision --autogenerate -m "Add decision_records partition"
```

### Docker / Kubernetes

```yaml
# docker-compose.yml (production-ready)
version: '3.8'
services:
  postgres:
    image: timescale/timescaledb:latest-pg16
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru

volumes:
  postgres_data:
  redis_data:
```

---

## 7. Risks & Alternatives

### Risks of PostgreSQL + TimescaleDB + pgvector

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Vector recall < 95% | Medium | Medium | Use Qdrant as sidecar for embeddings |
| TimescaleDB licensing (Apache 2) | Low | Low | Self-hosted or Timescale Cloud |
| pgvector slower than specialized | Medium | Low | HNSW tuning (m=16, ef=100) |
| Connection pooling overhead | Medium | Low | PgBouncer for 1000+ connections |
| Single-region latency | Low | Medium | Read replicas in multiple regions |

### When to Use Multi-DB Architecture

- **ClickHouse**: If analytical queries > 10s and you can accept eventual consistency
- **Qdrant**: If vector latency > 50ms or need >1M vectors with >95% recall
- **Redis**: For real-time caching of hot data (agent beliefs, current prices)

---

## 8. Recommendations & Implementation Plan

### Decision Summary

| Component | Choice | Justification |
|-----------|--------|----------------|
| **Primary DB** | PostgreSQL 16 + TimescaleDB 2.14 | Unified relational + time-series + vector |
| **Vector** | pgvector 0.7 (HNSW) | Integrated, ACID, good enough for <1M vectors |
| **Cache** | Redis 7 | Hot data (beliefs, OHLCV), connection pooling |
| **ORM** | SQLAlchemy 2.0 + Alembic | Type safety, async support |
| **LangGraph** | PostgresSaver | Native checkpointing |
| **Cost** | $50-200/month | Self-hosted on VPS + managed TimescaleDB |

### Implementation Plan (3 Steps)

#### Step 1: Migration (Week 1-2)
```bash
# 1. Set up PostgreSQL + TimescaleDB + pgvector
docker run -d --name astrofin-db \
  -e POSTGRES_PASSWORD=secret \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  timescale/timescaledb:latest-pg16

# 2. Install dependencies
pip install psycopg2-binary asyncpg sqlalchemy[tigkeits]

# 3. Migrate data with pgloader
pgloader core/belief.db postgresql://user:pass@localhost/astrofin
pgloader core/history.db postgresql://user:pass@localhost/astrofin
```

#### Step 2: KARL Integration (Week 3-4)
```python
# 1. Update core/history_db.py to use PostgreSQL
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(os.environ['DATABASE_URL'])
Session = sessionmaker(bind=engine)

# 2. Add replay_buffer with embeddings
# 3. Add decision_records partitioning
# 4. Add LangGraph PostgresSaver
```

#### Step 3: Performance Optimization (Week 5-6)
```sql
-- Enable compression for all hypertables
ALTER TABLE sessions SET (timescaledb.compress = true);
-- Add retention policies
SELECT add_retention_policy('sessions', INTERVAL '90 days');
-- Tune HNSW
-- Test with pgbench
```

---

## Quick Reference: Connection String

```bash
# For local development
DATABASE_URL=postgresql://postgres:secret@localhost:5432/astrofin

# For TimescaleDB Cloud
DATABASE_URL=postgresql://user:pass@host.cloud.timescale.io:port/dbname?sslmode=require

# For LangGraph checkpointer
CHECKPOINT_URL=postgresql://user:pass@host:5432/astrofin_checkpoints
```

**File created**: `knowledge/DB_ARCHITECTURE_RESEARCH_2026.md`
