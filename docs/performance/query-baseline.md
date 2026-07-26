# Query Performance Baseline — Sprint E

## Top 3 Queries (EXPLAIN ANALYZE)

### 1. Dashboard Price Query

```sql
-- GET /api/v1/dashboard?symbol=BTCUSDT
SELECT timestamp, open, high, low, close, volume
FROM market_data
WHERE symbol = 'BTCUSDT'
ORDER BY timestamp DESC
LIMIT 90;
```

**Expected:** Index scan on (symbol, timestamp), <5ms on <1M rows.

### 2. Agent History Query

```sql
-- Core agent state retrieval
SELECT session_id, symbol, action, confidence, timestamp
FROM agent_decisions
WHERE session_id = $1
ORDER BY timestamp DESC
LIMIT 50;
```

**Expected:** Index scan on (session_id, timestamp), <3ms.

### 3. RAG Inference Query

```sql
-- Knowledge base retrieval
SELECT chunk_id, content, embedding <=> $1 AS distance
FROM knowledge_chunks
ORDER BY embedding <=> $1
LIMIT 5;
```

**Expected:** pgvector IVFFlat index, <10ms on 2000 chunks.

## Compression Policy

- `market_data`: 7-day delay, segment by `symbol`, order by `timestamp DESC`
- Migration: `0009_compression_policy.sql`

## Connection Pool

- asyncpg pool: min_size=5, max_size=20, command_timeout=30s
- Config: `POSTGRES_POOL_MIN`, `POSTGRES_POOL_MAX` env vars

## Redundancy

- TimescaleDB built-in WAL replication (via WAL-G sidecar)
- Read replicas: not applicable (single-node)
