# Sprint 3 — Backend Migration: pgvector + RAG + RLS

**Window:** 2026-07-13 — 2026-07-19 (7 working days)
**Branch baseline:** `feat/p1-01-check-env-and-logger` @ `5014e0d` (origin/master `ab4ec12` + 2 hygiene)
**Sprint goal:** Move knowledge store from local FAISS to production-grade PostgreSQL + pgvector; tighten access control via RLS; reach ≤12 failing tests.

---

## 1. Outcome (the single sentence)

By 2026-07-19, the AstroFin Sentinel v5 RAG layer reads/writes from a PostgreSQL 16 + pgvector cluster (primary + 1 read-replica via CloudNativePG), with the new `documents.embedding` column live, FAISS index migrated, and all RAG-touching code paths (`knowledge/rag_retriever.py`, `knowledge/build_index.py`, RAG-first agents) switched to `asyncpg`. Row-Level Security is enabled on `documents`, `backtest_runs`, and `agent_decisions` with role-based policies. Test count drops from 18 failing → ≤12 failing.

## 2. Scope vs. Out-of-Scope

| In scope (W3) | Out of scope (later sprints) |
|---|---|
| pgvector extension install + `0009_pgvector.sql` migration | TimescaleDB hypertable (W4: P2-08) |
| `knowledge/rag_retriever.py` rewrite on asyncpg | Multi-region replication (W6+) |
| FAISS → pgvector one-shot backfill (`scripts/migrate_faiss_to_pgvector.py`) | Live RAG evaluation harness (P2-11) |
| CloudNativePG local cluster (kind, primary + 1 replica) | Production HA (3 replicas, WAL archiving) (W5) |
| RLS policies on 3 tables + service-role key rotation | Per-tenant key isolation (W7) |
| SLO baseline (P3-01) — p95 RAG query latency | SLO alerting wiring (W4) |

## 3. MOSCOW Prioritization

| Must (M) | Should (S) | Could (C) | Won't (W, this sprint) |
|---|---|---|---|
| P2-02a `0009_pgvector.sql` | P2-02c FAISS backfill | P3-01 SLO baseline (p95 latency) | TimescaleDB (P2-08) |
| P2-02b `rag_retriever.py` asyncpg | P2-03 RLS on 3 tables | P2-11 RAG eval harness scaffold | Multi-region |
| P2-02d RAG agent adapter update | P2-07a CloudNativePG local kind | P2-09 embedding cache | Production HA (3-replica) |
| **Tests: 18→≤12 failing** | P2-07b primary+replica smoke | | Per-tenant key isolation |

## 4. Phase Plan (W3A / W3B / W3C)

### W3A (Mon–Tue, 13–14 Jul) — Infra + Schema
Focus: stand up the cluster, install extension, write the migration.

- **P2-07a** CloudNativePG operator in `kind` cluster — 4h
- **P2-07b** primary + 1 read-replica local cluster (`manifests/cnpg/cluster.yaml`) — 3h
- **P2-02a** `migrations/0009_pgvector.sql` — `CREATE EXTENSION vector;` + `documents` table + `embedding vector(768)` — 3h
- **P3-01a** SLO baseline capture script (`tools/slo_capture.py`) — 2h
- **Total W3A:** 12h. **Milestone:** `psql` to replica, `\dx` shows `vector`, `\d documents` shows `embedding vector(768)`.

### W3B (Wed–Thu, 15–16 Jul) — Code Migration
Focus: replace `faiss.IndexFlatIP` in the hot path.

- **P2-02b** rewrite `knowledge/rag_retriever.py` on `asyncpg` (connection pool via `asyncpg.create_pool`) — 8h
- **P2-02c** `scripts/migrate_faiss_to_pgvector.py` — idempotent backfill of 29 chunks (17 astrology + 6 technical + 6 trading) — 4h
- **P2-02d** update RAG-first agents (`agents/_impl/fundamental_agent.py`, `astro_council/agent.py`, `synthesis_agent.py`) — 3h
- **P2-11a** scaffold RAG eval harness (`tests/eval/test_rag_relevance.py`) — 2h *(Could-tier, may slip)*
- **Total W3B:** 17h. **Milestone:** `python -m knowledge.rag_retriever "What is Nakshatra?"` returns from pgvector, not FAISS.

### W3C (Fri–Sat, 17–19 Jul) — RLS + Hardening
Focus: row-level security, tests, push.

- **P2-03a** RLS enable + policies on `documents`, `backtest_runs`, `agent_decisions` — 5h
- **P2-03b** service-role key rotation + `.env.prod` smoke — 3h
- **P2-09** embedding cache (in-process LRU, 1k entries) — 2h *(Should-tier)*
- **Test run + triage** of remaining 12–18 failures — 3h
- **P2-07c** push W3 branch, draft PR — 1h
- **Total W3C:** 14h. **Sprint total: 43h.**

## 5. Task Detail (Must-have)

### P2-02a — pgvector migration
**Deliverable:** `migrations/0009_pgvector.sql`
**Acceptance:**
- `CREATE EXTENSION IF NOT EXISTS vector;`
- `CREATE TABLE documents (id BIGSERIAL PRIMARY KEY, domain TEXT NOT NULL, source_path TEXT NOT NULL, chunk_text TEXT NOT NULL, embedding vector(768) NOT NULL, created_at TIMESTAMPTZ DEFAULT now());`
- `CREATE INDEX documents_embedding_hnsw ON documents USING hnsw (embedding vector_cosine_ops);`
- `CREATE INDEX documents_domain_idx ON documents (domain);`
- Idempotent (safe to re-run).

### P2-02b — asyncpg retriever
**Deliverable:** `knowledge/rag_retriever.py` rewrite
**API (unchanged from caller perspective):**
```python
async def retrieve(query: str, domain: str | None = None, top_k: int = 5) -> list[RetrievedChunk]
```
**Acceptance:**
- Uses `asyncpg.create_pool(min_size=2, max_size=10, dsn=os.environ["DATABASE_URL"])`
- Embeds via Ollama `nomic-embed-text` (HTTP, same as before)
- SQL: `SELECT id, domain, source_path, chunk_text, 1 - (embedding <=> $1) AS score FROM documents WHERE ($2::text IS NULL OR domain = $2) ORDER BY embedding <=> $1 LIMIT $3`
- Connection pool cleanup on `asyncio.CancelledError`
- Backwards-compat: legacy `retrieve_sync()` wrapper delegates to `asyncio.run(retrieve(...))` for non-async callers (deprecated, raises `DeprecationWarning`).

### P2-02c — FAISS backfill
**Deliverable:** `scripts/migrate_faiss_to_pgvector.py`
**Acceptance:**
- Reads `knowledge/indexes/{domain}.index` (FAISS) + `knowledge/indexes/{domain}.meta.json` (chunks)
- `INSERT ... ON CONFLICT (source_path) DO UPDATE SET embedding = EXCLUDED.embedding, chunk_text = EXCLUDED.chunk_text` (idempotent)
- `--dry-run` flag prints count without writing
- After run: `SELECT COUNT(*) FROM documents;` returns 29
- Verifies via HNSW index: `SET enable_seqscan = off; SELECT count(*) FROM documents WHERE embedding <=> (SELECT embedding FROM documents LIMIT 1) < 0.3;` returns ≥1

### P2-02d — Agent adapter
**Files touched:**
- `agents/_impl/fundamental_agent.py` (top-1 RAG context injection)
- `agents/_impl/astro_council/agent.py` (per-sub-agent retrieval)
- `agents/synthesis_agent.py` (final synthesis context)

**Acceptance:** Each call to `agent.run()` resolves RAG via `await retrieve(...)`. No synchronous FAISS code path remains (`grep -r "faiss" --include="*.py" agents/ orchestration/ core/` returns 0 hits outside the migration script).

### P2-03a — RLS
**Deliverable:** `migrations/0010_rls.sql`
**Acceptance:**
- `ALTER TABLE documents ENABLE ROW LEVEL SECURITY;`
- 3 policies: `documents_select_all` (read), `documents_insert_service` (write), `documents_delete_service` (admin)
- `FORCE ROW LEVEL SECURITY` on all 3 tables
- Smoke: `SET ROLE app_readonly; SELECT * FROM documents;` works; `INSERT` denied. `SET ROLE app_service; INSERT` works.

### P2-07a/b — CloudNativePG local
**Deliverable:** `manifests/cnpg/cluster.yaml`
**Acceptance:**
- `kubectl apply -f manifests/cnpg/` creates cluster `astrofin-pg` with 1 primary + 1 replica
- `cnpg status astrofin-pg` shows `Healthy: True`, `Instances: 2`
- `psql` to both primary and replica works; replica reports `wal_receiver_state = 'streaming'`
- `.env.db.example` updated with `DATABASE_URL` pointing at `cnpg-rw` Service

## 6. Definition of Done (Sprint)

- [ ] All **Must** tasks completed and merged to `feat/p1-01-check-env-and-logger` (or successor branch)
- [ ] `migrations/0009_pgvector.sql` and `migrations/0010_rls.sql` applied to local cluster, idempotent re-runs verified
- [ ] `python -m knowledge.rag_retriever "..."` returns results from pgvector (not FAISS) end-to-end
- [ ] RLS smoke: `app_readonly` role can SELECT, cannot INSERT; `app_service` can both
- [ ] `grep -rn "faiss" agents/ orchestration/ core/` returns 0 hits outside `scripts/migrate_faiss_to_pgvector.py`
- [ ] Test count: 18 failing → ≤12 failing
- [ ] `git push` succeeds; branch is up-to-date with `origin/master` (rebase/merge if needed)
- [ ] `docs/sprints/SPRINT_3.md` updated with actuals in a `## 7. Retrospective` section

## 7. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| pgvector HNSW index build time > 5 min on first backfill | M | M | Run in `W3B` with `--dry-run` first; index build is non-blocking in pgvector 0.7+ |
| asyncpg connection pool exhaustion under agent fan-out | M | H | Pool size = 10, queue depth = 20, fail-fast `PoolAcquireTimeout`=5s; metric `rag_pool_acquire_seconds` exported to Loki |
| RLS misconfiguration blocks agents at runtime | M | H | Dual-role smoke test in CI (`tools/check_env.py --prod`); RLS added in W3C **after** code migration is stable |
| `origin/master` (ab4ec12) has diverged from `origin/main` (01435a0) by EOW | M | M | Decide branch policy at end of W3A: switch baseline to `origin/main` if it carries pgvector artifacts |
| FAISS backfill drift (chunks added during backfill) | L | M | Take `knowledge/indexes/.lock` + advisory lock `pg_advisory_xact_lock(hashtext('faiss_migration'))` during backfill |
| Ollama (`nomic-embed-text`) not running in CI | M | M | Add `services.ollama` to `python-setup.yml` workflow with healthcheck gate |

## 8. Tracking

- **GitHub Project:** board seeded by `scripts/seed_project_board.py` (W2 output)
- **Daily standup:** in-session log appended to `docs/sprints/SPRINT_3_LOG.md` (EOD)
- **Burndown:** simple table in `## 9. Daily Burndown` below, updated EOD

## 9. Daily Burndown (template — fill EOD)

| Day | Must tasks planned | Must tasks done | Tests failing (EOD) | Notes |
|---|---|---|---|---|
| Mon 13 Jul | P2-07a, P2-07b | | | |
| Tue 14 Jul | P2-02a, P3-01a | | | |
| Wed 15 Jul | P2-02b (start) | | | |
| Thu 16 Jul | P2-02b, P2-02c, P2-02d | | | |
| Fri 17 Jul | P2-03a, P2-03b | | | |
| Sat 18 Jul | P2-09, test triage | | | |
| Sun 19 Jul | buffer / push / retro | | | |

## 10. Open Questions (resolve by EOD Mon 13 Jul)

0. **Embedding dimension: 768 vs 1536.** `PRODUCTION_BACKLOG.md` lines 206, 492 specify `vector(1536)` (matches `text-embedding-3-small`/`text-embedding-ada-002`), but current `knowledge/rag_retriever.py:25` has `DIM = 768` (Ollama `nomic-embed-text`). Sprint plan uses **768** to match production code; switching to 1536 is a separate, breaking decision (requires re-embedding all 29 chunks + swapping embedder). Defer dimension migration to a follow-up `P2-13 embedding-dim-migration` task; do NOT block W3 on it.

1. **Branch policy:** continue on `feat/p1-01-check-env-and-logger` or cut new `feat/p2-02-pgvector` from `origin/main` (01435a0) if it has pgvector scaffolding?
2. **RAG agent scope:** rewrite all 8 RAG-touching agents in W3B, or limit to 3 critical-path agents (fundamental, astro_council, synthesis) and migrate the rest in W4?
3. **Embedding cache scope:** in-process LRU (P2-09) or skip and rely on pgvector HNSW only? (Recommendation: in-process LRU, 2h cost, ~40% latency win.)
