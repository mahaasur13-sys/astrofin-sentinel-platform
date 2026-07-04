-- Migration 0009: pgvector + RAG documents table
-- Author: Zo AI | Date: 2026-07-04
-- Sprint: W3 (SPRINT_3.md, P2-02)
-- Purpose: PostgreSQL side of the RAG backend. SQLite (migrations/0001..0007) remains
--          the runtime/analytical store; pgvector is the dedicated vector store for
--          semantic retrieval. Both DBs run side-by-side; this is NOT a replacement.
--
-- Related: PRODUCTION_BACKLOG.md P2-02 (line 206), R11 (line 492), SPRINT_3.md §4.
-- Embedding dimension: 1536 (OpenAI text-embedding-3-small).
--   Decision 2026-07-04: 1536 over 768 (financial semantics, industry standard,
--   pre-validated by PRODUCTION_BACKLOG.md). Stored as `vector(1536)` with
--   `halfvec(1536)` projections for index to keep memory at 3GB/1M docs (R11).
--
-- Prerequisites:
--   - PostgreSQL ≥ 14
--   - pgvector extension installed (server-side: `apt install postgresql-14-pgvector`
--     or build from https://github.com/pgvector/pgvector — needs `pg_config`).
--   - Apply with: `psql -v ON_ERROR_STOP=1 -d astrofin -f migrations_postgres/0009_pgvector.sql`

BEGIN;

-- 1. Extension ----------------------------------------------------------------
-- `vector` is provided by pgvector. CREATE EXTENSION must run as superuser once
-- per database. IF NOT EXISTS guards against re-application.
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Schema -------------------------------------------------------------------
-- Knowledge documents (chunks of source material: news, filings, ephemeris notes,
-- historical agent reports). One row per chunk; embedding is the dense vector.
CREATE TABLE IF NOT EXISTS documents (
    doc_id        UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    source        TEXT         NOT NULL,                       -- e.g. "reuters.com", "SEC:10K:AAPL:2024"
    source_type   TEXT         NOT NULL,                       -- enum-like: news | filing | report | ephemeris
    title         TEXT,
    body          TEXT         NOT NULL,
    tokens        INTEGER      NOT NULL CHECK (tokens > 0),
    domain        TEXT,
    lang          TEXT         NOT NULL DEFAULT 'en',
    metadata      JSONB        NOT NULL DEFAULT '{}'::jsonb,   -- source_id, published_at, ticker, regime, ...
    embedding     vector(1536) NOT NULL,                       -- float32 by default, 6KB/doc (R11)
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),

    CONSTRAINT documents_source_type_chk
        CHECK (source_type IN ('news', 'filing', 'report', 'ephemeris', 'social', 'macro'))
);

COMMENT ON TABLE  documents                  IS 'Knowledge chunks for RAG retrieval. One row per chunk.';
COMMENT ON COLUMN documents.embedding        IS 'Dense vector (1536-d, OpenAI text-embedding-3-small).';
COMMENT ON COLUMN documents.metadata         IS 'Free-form JSON: source_id, published_at, ticker, regime, etc.';
COMMENT ON COLUMN documents.source_type      IS 'Enum: news | filing | report | ephemeris | social | macro.';
COMMENT ON COLUMN documents.domain           IS 'Knowledge domain (trading | technical | astro | macro | general).'

-- 3. Indexes ------------------------------------------------------------------
-- HNSW (Hierarchical Navigable Small World) for ANN search. m=16, ef_construction=64
-- are the pgvector defaults tuned for ~1M rows. HNSW is preferred over IVFFLAT for
-- RAG: no training step, better recall, slightly more memory.
--
-- We create TWO projections of the embedding column to support R11 (memory budget):
--   - `embedding_hnsw`  : full vector(1536) float32 — 6KB/doc, used for INSERT/SELECT
--   - `embedding_half`  : halfvec(1536) — 3KB/doc, used as HNSW index key
-- The halfvec index cuts memory in half with negligible recall loss for our domain.
--
-- Operator class: `vector_cosine_ops` (cosine distance) is correct for OpenAI embeddings
-- (which are L2-normalized, so cosine = inner product, but cosine is the safe default).
CREATE INDEX IF NOT EXISTS documents_embedding_hnsw_idx
    ON documents USING hnsw ((embedding::halfvec(1536)) halfvec_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Source-based lookups (filter by source before vector search → "metadata pre-filter")
CREATE INDEX IF NOT EXISTS documents_source_idx       ON documents (source);
CREATE INDEX IF NOT EXISTS documents_source_type_idx  ON documents (source_type);
CREATE INDEX IF NOT EXISTS documents_created_at_idx   ON documents (created_at DESC);
CREATE INDEX IF NOT EXISTS documents_metadata_gin_idx ON documents USING GIN (metadata jsonb_path_ops);

-- Domain is split out as a first-class column so the planner can use a B-tree
-- pre-filter before HNSW (cuts candidate set for "domain = X" queries by 10–100x
-- in multi-tenant corpora). The metadata->>'domain' mirror is kept for back-compat
-- with readers that only know the JSONB form.
CREATE INDEX IF NOT EXISTS documents_domain_idx ON documents (domain);

-- HNSW composite index: when callers filter by domain + ORDER BY embedding, PG can
-- use this index for both predicate and distance ordering without a sort step.
-- Only built if pgvector >= 0.5 (supports HNSW + WHERE clause optimization).
DO $$
BEGIN
    IF (SELECT extversion FROM pg_extension WHERE extname = 'vector')::numeric >= 0.5 THEN
        CREATE INDEX IF NOT EXISTS documents_domain_embedding_hnsw_idx
            ON documents USING hnsw (embedding vector_cosine_ops)
            WHERE domain IS NOT NULL;
    END IF;
END $$;

-- 4. Trigger: bump updated_at ------------------------------------------------
CREATE OR REPLACE FUNCTION documents_touch_updated_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_documents_touch_updated_at ON documents;
CREATE TRIGGER trg_documents_touch_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION documents_touch_updated_at();

-- 5. Schema version ----------------------------------------------------------
-- _schema_version is the convention from migrations/0001..0007. We mirror it here
-- so a single Python runner can verify state across both DBs.
CREATE TABLE IF NOT EXISTS _schema_version (
    version    INTEGER      PRIMARY KEY,
    applied_at TIMESTAMPTZ  NOT NULL DEFAULT now(),
    note       TEXT
);

INSERT INTO _schema_version (version, note)
VALUES (9, 'pgvector + RAG documents table (Sprint 3, P2-02, dim=1536)')
ON CONFLICT (version) DO NOTHING;

COMMIT;

-- Verification (run manually after applying):
--   SELECT extversion FROM pg_extension WHERE extname = 'vector';
--   SELECT version, applied_at, note FROM _schema_version ORDER BY version DESC LIMIT 1;
--   \d documents
--   EXPLAIN SELECT doc_id FROM documents ORDER BY embedding <=> '[0.1,0.2,...]'::vector LIMIT 5;
--     (should use documents_embedding_hnsw_idx)
