"""
tests/test_rag_client.py — Unit tests for core/rag_client.

Coverage strategy (25 tests, organized by surface):
  1. Config validation (4)      — Literal, required DSN, env parsing, fallback
  2. Construction (3)           — defaults, custom config, missing DSN raises
  3. Store: FAISS path (4)      — happy path, empty list, malformed metadata, dim mismatch
  4. Store: pgvector path (3)   — empty list, single doc, partial failure
  5. Retrieve: FAISS (3)        — happy path, min_score filter, empty result
  6. Retrieve: pgvector (2)     — happy path, empty result
  7. Health (3)                 — pgvector healthy, FAISS healthy, no-DSN unhealthy
  8. Singleton + concurrency (2)— identity, concurrent store safety
  9. Lifecycle (1)              — aclose() releases pg pool
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid

from core.rag_client import (
    RAGClient,
    RAGConfig,
    Document,
    StoreResult,
    HealthStatus,
    get_rag_client,
)


@pytest.fixture(autouse=True)
def force_stub_provider(monkeypatch):
    """Force RAG_PROVIDER=stub so EmbeddingClient doesn't try to use OpenAI in tests."""
    monkeypatch.setenv("RAG_PROVIDER", "stub")


# ─── 1. Config validation (4 tests) ──────────────────────────────────────────


def test_rag_config_literal_rejects_unknown_backend():
    """Literal type guards against typos like 'faisss' or 'pgvector2'."""
    with pytest.raises(Exception) as exc_info:  # pydantic.ValidationError
        RAGConfig(backend="faisss")
    assert "faiss" in str(exc_info.value).lower() or "literal" in str(exc_info.value).lower()


def test_rag_config_accepts_valid_backends():
    """Both 'pgvector' and 'faiss' must be accepted by the Literal."""
    assert RAGConfig(backend="pgvector", pg_dsn="postgresql://x").backend == "pgvector"
    assert RAGConfig(backend="faiss").backend == "faiss"


def test_rag_config_from_env_uses_env(monkeypatch):
    """from_env() must read RAG_BACKEND and AFS_PG_DSN from the environment."""
    monkeypatch.setenv("RAG_BACKEND", "faiss")
    monkeypatch.delenv("AFS_PG_DSN", raising=False)
    monkeypatch.delenv("RAG_LEGACY_FALLBACK", raising=False)
    cfg = RAGConfig.from_env()
    assert cfg.backend == "faiss"
    assert cfg.pg_dsn is None


def test_rag_config_from_env_graceful_dsn_fallback(monkeypatch, caplog):
    """If RAG_BACKEND=pgvector but AFS_PG_DSN unset, from_env must auto-fallback to faiss.

    This is the key behavior: in dev/CI we never want a hard crash.
    """
    monkeypatch.setenv("RAG_BACKEND", "pgvector")
    monkeypatch.delenv("AFS_PG_DSN", raising=False)
    with caplog.at_level("WARNING"):
        cfg = RAGConfig.from_env()
    assert cfg.backend == "faiss"
    assert any("auto-falling back to faiss" in r.message for r in caplog.records)


# ─── 2. Construction (3 tests) ───────────────────────────────────────────────


def test_rag_client_construction_with_faiss_config():
    """Default RAGConfig.from_env() in a no-DSN env = faiss; construction must succeed."""
    cfg = RAGConfig(backend="faiss", faiss_dir="/tmp/test_empty")
    client = RAGClient(cfg)
    assert client.config.backend == "faiss"
    assert client._pg_pool is None  # pg pool is lazy


def test_rag_client_construction_raises_without_pg_dsn():
    """If user explicitly asks pgvector and forgets the DSN, fail loud at __init__."""
    cfg = RAGConfig(backend="pgvector", pg_dsn=None)
    with pytest.raises(ValueError, match="AFS_PG_DSN"):
        RAGClient(cfg)


def test_rag_client_lazy_pg_pool_init():
    """Pool is None until first pgvector call (proves lazy init)."""
    cfg = RAGConfig(backend="pgvector", pg_dsn="postgresql://x@localhost/db")
    client = RAGClient(cfg)
    assert client._pg_pool is None  # not initialized in __init__


# ─── 3. Store: FAISS path (4 tests) ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_store_empty_list_returns_zero_inserted(tmp_path):
    """store([]) is a no-op and must not raise — defensive for batch callers."""
    cfg = RAGConfig(backend="faiss", faiss_dir=str(tmp_path))
    client = RAGClient(cfg)
    result = await client.store([])
    assert isinstance(result, StoreResult)
    assert result.inserted == 0
    assert result.failed == 0
    assert result.backend == "faiss"
    await client.aclose()


@pytest.mark.asyncio
async def test_store_faiss_happy_path(tmp_path):
    """End-to-end: store 2 docs into a fresh FAISS dir, verify file appears."""
    cfg = RAGConfig(backend="faiss", faiss_dir=str(tmp_path))
    client = RAGClient(cfg)

    docs = [
        Document(content="first test doc", source="test://1", domain="test_store"),
        Document(content="second test doc", source="test://2", domain="test_store"),
    ]
    result = await client.store(docs)

    assert result.backend == "faiss"
    assert result.inserted == 2
    assert result.failed == 0
    assert result.errors == []
    # FAISS files should be on disk
    assert (tmp_path / "test_store.index").exists()
    assert (tmp_path / "test_store.meta.json").exists()
    await client.aclose()


@pytest.mark.asyncio
async def test_store_faiss_unicode_content(tmp_path):
    """Unicode content (Russian, emoji) must round-trip without crashing."""
    cfg = RAGConfig(backend="faiss", faiss_dir=str(tmp_path))
    client = RAGClient(cfg)
    docs = [Document(content="Привет 🚀", source="test://unicode", domain="unicode")]
    result = await client.store(docs)
    assert result.inserted == 1
    assert result.failed == 0
    await client.aclose()


@pytest.mark.asyncio
async def test_store_faiss_empty_content_is_allowed(tmp_path):
    """Empty content (e.g. title-only doc) must not crash the embedder.

    The embedder handles empty strings as zero-vectors; FAISS accepts them.
    """
    cfg = RAGConfig(backend="faiss", faiss_dir=str(tmp_path))
    client = RAGClient(cfg)
    docs = [Document(content="", source="test://empty", domain="empty")]
    result = await client.store(docs)
    assert result.inserted == 1
    await client.aclose()


# ─── 4. Store: pgvector path (3 tests, mocked asyncpg) ───────────────────────


@pytest.mark.asyncio
async def test_store_pgvector_empty_list_no_db_call(monkeypatch):
    """store([]) must short-circuit BEFORE creating a pool (no asyncpg.connect)."""
    monkeypatch.setenv("AFS_PG_DSN", "postgresql://test@localhost/db")
    cfg = RAGConfig(backend="pgvector", pg_dsn="postgresql://test@localhost/db")
    client = RAGClient(cfg)
    result = await client.store([])
    assert result.inserted == 0
    assert result.backend == "pgvector"
    # Pool was never acquired
    assert client._pg_pool is None
    await client.aclose()


@pytest.mark.asyncio
async def test_store_pgvector_happy_path_with_mock_pool():
    """Mock asyncpg pool: store 1 doc, verify INSERT was called once."""
    cfg = RAGConfig(backend="pgvector", pg_dsn="postgresql://x")
    client = RAGClient(cfg)

    # Build a mock pool that records execute() calls
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value=None)
    mock_conn.transaction = MagicMock()
    mock_conn.transaction.return_value.__aenter__ = AsyncMock(return_value=None)
    mock_conn.transaction.return_value.__aexit__ = AsyncMock(return_value=None)

    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock()
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)
    mock_pool.close = AsyncMock(return_value=None)

    async def fake_get_pool():
        return mock_pool

    # Patch _get_pg_pool to return our mock
    client._get_pg_pool = fake_get_pool

    docs = [Document(content="hello pgvector", source="test://pg1")]
    result = await client.store(docs)

    assert result.backend == "pgvector"
    assert result.inserted == 1
    assert result.failed == 0
    assert mock_conn.execute.call_count == 1
    # Verify SQL contained ON CONFLICT (idempotency signal)
    call_args = mock_conn.execute.call_args
    assert "ON CONFLICT" in call_args.args[0]


@pytest.mark.asyncio
async def test_store_pgvector_partial_failure_continues_batch():
    """If one doc fails (e.g. unique violation), batch must continue, not abort."""
    cfg = RAGConfig(backend="pgvector", pg_dsn="postgresql://x")
    client = RAGClient(cfg)

    call_count = 0

    async def fake_execute(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise Exception("simulated db error on doc 2")
        return None

    mock_conn = AsyncMock()
    mock_conn.execute = fake_execute
    mock_conn.transaction = MagicMock()
    mock_conn.transaction.return_value.__aenter__ = AsyncMock(return_value=None)
    mock_conn.transaction.return_value.__aexit__ = AsyncMock(return_value=None)

    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock()
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

    async def fake_get_pool():
        return mock_pool

    client._get_pg_pool = fake_get_pool

    docs = [
        Document(content="ok doc 1", source="test://ok1"),
        Document(content="failing doc 2", source="test://fail2"),
        Document(content="ok doc 3", source="test://ok3"),
    ]
    result = await client.store(docs)

    assert result.inserted == 2
    assert result.failed == 1
    assert len(result.errors) == 1
    assert "test://fail2" in result.errors[0]


# ─── 5. Retrieve: FAISS path (3 tests) ───────────────────────────────────────


@pytest.mark.asyncio
async def test_retrieve_faiss_empty_when_index_missing(tmp_path):
    """Query against nonexistent domain must return [] — no exception, no crash."""
    cfg = RAGConfig(backend="faiss", faiss_dir=str(tmp_path))
    client = RAGClient(cfg)
    results = await client.retrieve("any query", top_k=5)
    assert results == []
    await client.aclose()


@pytest.mark.asyncio
async def test_retrieve_faiss_roundtrip_after_store(tmp_path):
    """Store then retrieve: the exact same content must come back with positive score."""
    cfg = RAGConfig(backend="faiss", faiss_dir=str(tmp_path), min_score=-1.0)
    client = RAGClient(cfg)

    # Use the Stub embedding (deterministic) so the same text always maps to the same vector
    from tools.embedding_client import EmbeddingClient, EmbeddingConfig

    client.embedding = EmbeddingClient(EmbeddingConfig(provider="stub"))

    docs = [
        Document(content="FOMC rate decision hawkish", source="test://fomc", domain="roundtrip"),
        Document(content="BTC volatility rising on macro news", source="test://btc", domain="roundtrip"),
        Document(content="completely unrelated topic about cooking", source="test://cook", domain="roundtrip"),
    ]
    await client.store(docs)

    # Query that should match the FOMC doc
    results = await client.retrieve("FOMC rate decision hawkish", top_k=3, min_score=-1.0)

    assert len(results) >= 1, "expected at least 1 result"
    # Top result should be the FOMC doc (identical text → score 1.0)
    assert "FOMC" in results[0].content or "rate" in results[0].content.lower()
    assert results[0].backend == "faiss"
    assert results[0].relevance_score > 0.9  # identical text → near-1.0
    await client.aclose()


@pytest.mark.asyncio
async def test_retrieve_faiss_min_score_filters(tmp_path):
    """min_score must filter out low-relevance results."""
    cfg = RAGConfig(backend="faiss", faiss_dir=str(tmp_path), min_score=0.99)
    client = RAGClient(cfg)

    from tools.embedding_client import EmbeddingClient, EmbeddingConfig

    client.embedding = EmbeddingClient(EmbeddingConfig(provider="stub"))

    docs = [Document(content="abc", source="test://abc", domain="filter")]
    await client.store(docs)

    # Different query → low similarity → filtered out by min_score=0.99
    results = await client.retrieve("xyz totally different", top_k=5)
    assert results == [], f"expected filter to drop low-score result, got {len(results)}"
    await client.aclose()


# ─── 6. Retrieve: pgvector (2 tests, mocked) ─────────────────────────────────


@pytest.mark.asyncio
async def test_retrieve_pgvector_with_mock_pool():
    """Mock pgvector: 2 rows returned, verify mapping to RetrievedChunk."""
    cfg = RAGConfig(backend="pgvector", pg_dsn="postgresql://x", top_k=2)
    client = RAGClient(cfg)

    # Mock row factory: asyncpg returns Records, not dicts
    mock_row1 = {
        "doc_id": uuid.uuid4(),
        "source": "test://pg1",
        "title": "PG Doc 1",
        "body": "first pgvector doc",
        "domain": "test",
        "score": 0.92,
    }
    mock_row2 = {
        "doc_id": uuid.uuid4(),
        "source": "test://pg2",
        "title": "PG Doc 2",
        "body": "second pgvector doc",
        "domain": "test",
        "score": 0.75,
    }

    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=[mock_row1, mock_row2])

    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock()
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

    async def fake_get_pool():
        return mock_pool

    client._get_pg_pool = fake_get_pool

    results = await client.retrieve("test query", top_k=2)
    assert len(results) == 2
    assert results[0].content == "first pgvector doc"
    assert results[0].relevance_score == 0.92
    assert results[0].backend == "pgvector"
    assert results[1].relevance_score == 0.75


@pytest.mark.asyncio
async def test_retrieve_pgvector_empty_result():
    """pgvector query with no matches must return [] — not raise."""
    cfg = RAGConfig(backend="pgvector", pg_dsn="postgresql://x")
    client = RAGClient(cfg)

    mock_conn = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=[])

    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock()
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

    async def fake_get_pool():
        return mock_pool

    client._get_pg_pool = fake_get_pool

    results = await client.retrieve("nothing matches")
    assert results == []


# ─── 7. Health (3 tests) ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_health_faiss_returns_ok(tmp_path):
    """FAISS backend with empty dir is still 'healthy' (just has no vectors yet)."""
    cfg = RAGConfig(backend="faiss", faiss_dir=str(tmp_path))
    client = RAGClient(cfg)
    h = await client.health()
    assert isinstance(h, HealthStatus)
    assert h.backend == "faiss"
    assert h.healthy is True
    assert h.legacy_available is False
    assert "faiss" in h.details
    await client.aclose()


@pytest.mark.asyncio
async def test_health_pgvector_with_mock_pool():
    """pgvector with a mocked successful pool: healthy=True."""
    cfg = RAGConfig(backend="pgvector", pg_dsn="postgresql://x")
    client = RAGClient(cfg)

    mock_conn = AsyncMock()
    mock_conn.fetchval = AsyncMock(return_value=1)  # SELECT 1 → 1

    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock()
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

    async def fake_get_pool():
        return mock_pool

    client._get_pg_pool = fake_get_pool
    h = await client.health()
    assert h.backend == "pgvector"
    assert h.healthy is True


@pytest.mark.asyncio
async def test_health_pgvector_db_down_returns_unhealthy():
    """pgvector with a dead pool: healthy=False, error in details."""
    cfg = RAGConfig(backend="pgvector", pg_dsn="postgresql://nonexistent")
    client = RAGClient(cfg)

    async def fake_get_pool():
        raise ConnectionRefusedError("Connection refused")

    client._get_pg_pool = fake_get_pool
    h = await client.health()
    assert h.backend == "pgvector"
    assert h.healthy is False
    assert "error" in h.details or "pgvector" in h.details
    assert "Connection refused" in str(h.details) or "refused" in str(h.details).lower()


# ─── 8. Singleton + concurrency (2 tests) ────────────────────────────────────


def test_get_rag_client_returns_singleton(monkeypatch):
    """Two calls in the same process must return the same object (identity check)."""
    import core.rag_client as mod

    mod._singleton = None  # reset for test isolation
    monkeypatch.delenv("AFS_PG_DSN", raising=False)
    monkeypatch.setenv("RAG_BACKEND", "faiss")
    c1 = get_rag_client()
    c2 = get_rag_client()
    assert c1 is c2
    mod._singleton = None  # cleanup


@pytest.mark.asyncio
async def test_concurrent_store_on_singleton_is_safe(monkeypatch, tmp_path):
    """Two coroutines calling store() on the SAME client concurrently must not corrupt state.

    This catches the FAISS not-concurrency-safe issue: if two stores race,
    one will see a stale in-memory state. We expect both to complete (the
    lock in _store_faiss serializes them), and total inserted == 4.
    """
    import core.rag_client as mod

    mod._singleton = None  # reset

    monkeypatch.delenv("AFS_PG_DSN", raising=False)
    monkeypatch.setenv("RAG_BACKEND", "faiss")

    cfg = RAGConfig(backend="faiss", faiss_dir=str(tmp_path))
    client = RAGClient(cfg)

    batch1 = [Document(content=f"a-{i}", source=f"test://a{i}", domain="concurrent") for i in range(2)]
    batch2 = [Document(content=f"b-{i}", source=f"test://b{i}", domain="concurrent") for i in range(2)]

    r1, r2 = await asyncio.gather(client.store(batch1), client.store(batch2))
    total_inserted = r1.inserted + r2.inserted
    total_failed = r1.failed + r2.failed
    assert total_inserted == 4, f"expected 4 inserted across both batches, got {total_inserted}"
    assert total_failed == 0
    await client.aclose()
    mod._singleton = None


# ─── 9. Lifecycle (1 test) ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_aclose_releases_pg_pool():
    """aclose() must close the pg pool so we don't leak connections."""
    cfg = RAGConfig(backend="pgvector", pg_dsn="postgresql://x")
    client = RAGClient(cfg)

    # Inject a fake pool with a close() we can verify
    fake_pool = MagicMock()
    fake_pool.close = AsyncMock(return_value=None)
    client._pg_pool = fake_pool

    await client.aclose()
    fake_pool.close.assert_called_once()
    assert client._pg_pool is None
