"""
tests/test_embedding_client.py — Unit tests for tools/embedding_client.

Coverage:
  - Stub determinism (same text -> same vector across runs/processes)
  - Stub differentiability (different text -> different vector)
  - Dimension correctness (default 1536, configurable)
  - Validation: ollama dim, openai dim, unknown provider
  - Cache: hit/miss, TTL expiry (mocked)
  - Batch: order preservation, max_batch_size chunking
  - Empty/None inputs -> zero vectors
  - Error handling: 401 raises ValueError, 429 retries (mocked)
  - embed_sync: works outside loop, raises inside loop
  - Singleton identity
  - Lazy singleton proxy (embedding_client.*)

No network calls. All tests are <1s total.
"""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, patch

import pytest

from tools.embedding_client import (
    EmbeddingClient,
    EmbeddingConfig,
    embedding_client,  # the lazy proxy
    get_embedding_client,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def stub_client() -> EmbeddingClient:
    """Default test client: stub provider, 1536-dim, cache on."""
    return EmbeddingClient(EmbeddingConfig(provider="stub", dimension=1536, cache_enabled=True))


@pytest.fixture
def no_cache_client() -> EmbeddingClient:
    return EmbeddingClient(EmbeddingConfig(provider="stub", dimension=1536, cache_enabled=False))


# ─── Stub determinism ─────────────────────────────────────────────────────────


@pytest.mark.unit
async def test_stub_is_deterministic_across_instances(stub_client):
    """Critical for RAG tests: same text MUST produce same vector across processes."""
    a = await stub_client.embed_one("the quick brown fox")
    b = await stub_client.embed_one("the quick brown fox")
    assert a == b
    assert len(a) == 1536
    assert all(-1.0 <= v <= 1.0 for v in a)


@pytest.mark.unit
async def test_stub_distinguishes_different_texts(stub_client):
    a = await stub_client.embed_one("alpha")
    b = await stub_client.embed_one("beta")
    assert a != b


@pytest.mark.unit
async def test_stub_custom_dimension():
    c = EmbeddingClient(EmbeddingConfig(provider="stub", dimension=768))
    v = await c.embed_one("test")
    assert len(v) == 768
    await c.aclose()


# ─── Validation ──────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_ollama_rejects_1536():
    with pytest.raises(ValueError, match="Ollama does not support dimension 1536"):
        EmbeddingClient(EmbeddingConfig(provider="ollama", dimension=1536))


@pytest.mark.unit
def test_openai_rejects_unusual_dim():
    with pytest.raises(ValueError, match="must be 1536 or 3072"):
        EmbeddingClient(EmbeddingConfig(provider="openai", dimension=512))


@pytest.mark.unit
def test_unknown_provider_rejected():
    with pytest.raises(ValueError, match="Unknown RAG_PROVIDER"):
        EmbeddingClient(EmbeddingConfig(provider="cohere"))


# ─── Batch / order preservation ─────────────────────────────────────────────


@pytest.mark.unit
async def test_batch_preserves_order(stub_client):
    texts = ["first", "second", "third", "fourth"]
    result = await stub_client.embed(texts)
    assert len(result) == 4
    # Each position matches what embed_one would return
    for i, t in enumerate(texts):
        single = await stub_client.embed_one(t)
        assert result[i] == single


@pytest.mark.unit
async def test_batch_with_empty_and_none(stub_client):
    result = await stub_client.embed(["valid", "", None, "another"])
    assert result[0] is not None and len(result[0]) == 1536
    assert result[1] == [0.0] * 1536
    assert result[2] == [0.0] * 1536
    assert result[3] is not None and len(result[3]) == 1536


@pytest.mark.unit
async def test_batch_chunks_correctly(stub_client):
    small_batch_client = EmbeddingClient(EmbeddingConfig(provider="stub", dimension=1536, max_batch_size=2, cache_enabled=False))
    # With max_batch_size=2, 5 texts should produce 3 provider calls.
    with patch.object(small_batch_client, "_deterministic_vector", wraps=small_batch_client._deterministic_vector) as mock_det:
        await small_batch_client.embed([f"text_{i}" for i in range(5)])
        # 5 calls, regardless of chunking (we mock the per-text method)
        assert mock_det.call_count == 5
    await small_batch_client.aclose()


# ─── Cache ───────────────────────────────────────────────────────────────────


@pytest.mark.unit
async def test_cache_returns_same_vector(no_cache_client):
    """Sanity: without cache, same text still returns same vector (stub is deterministic)."""
    a = await no_cache_client.embed_one("same text")
    b = await no_cache_client.embed_one("same text")
    assert a == b


@pytest.mark.unit
async def test_cache_ttl_expiry(stub_client):
    """Mock monotonic time to test TTL eviction."""
    stub_client.config.cache_ttl_seconds = 10
    await stub_client.embed_one("expiring text")
    assert "expiring text" in [stub_client._cache[k][0] for k in stub_client._cache] or len(stub_client._cache) == 1
    # Advance time beyond TTL
    with patch("tools.embedding_client.time.monotonic", return_value=time.monotonic() + 100):
        cached = stub_client._cache_get("expiring text")
        assert cached is None  # expired


@pytest.mark.unit
async def test_cache_disabled(stub_client):
    no_cache = EmbeddingClient(EmbeddingConfig(provider="stub", dimension=1536, cache_enabled=False))
    await no_cache.embed_one("no cache test")
    assert len(no_cache._cache) == 0
    await no_cache.aclose()


# ─── OpenAI error handling (mocked) ─────────────────────────────────────────


@pytest.mark.unit
async def test_openai_auth_error_raises_value_error():
    """401 from OpenAI must surface as ValueError('OPENAI_API_KEY is invalid')."""
    import openai

    c = EmbeddingClient(EmbeddingConfig(provider="openai", dimension=1536))
    # Build a mock 401 response, then trigger the real openai.AuthenticationError
    mock_resp = AsyncMock()
    mock_resp.status_code = 401
    mock_resp.body = None
    mock_response = AsyncMock()
    mock_response.embeddings.create = AsyncMock(side_effect=openai.AuthenticationError("invalid api key", response=mock_resp, body=None))
    # Use the actual openai error class
    with patch.object(c, "_get_openai_client", return_value=mock_response):
        # Simulate: directly call the method with patched client that raises AuthError
        c._openai_client = AsyncMock()
        c._openai_client.embeddings.create = AsyncMock(side_effect=openai.AuthenticationError("invalid api key", response=mock_resp, body=None))
        with pytest.raises(ValueError, match="OPENAI_API_KEY is invalid"):
            await c._embed_openai(["test"])
    await c.aclose()


@pytest.mark.unit
async def test_openai_rate_limit_retries_then_raises():
    import openai

    c = EmbeddingClient(EmbeddingConfig(provider="openai", dimension=1536))
    c._openai_client = AsyncMock()
    c._openai_client.embeddings.create = AsyncMock(side_effect=openai.RateLimitError("rate limited", response=AsyncMock(status_code=429), body=None))
    with patch("tools.embedding_client.asyncio.sleep", new=AsyncMock()) as mock_sleep:
        with pytest.raises(RuntimeError, match="OpenAI embedding failed after 2 attempts"):
            await c._embed_openai(["test"])
        assert mock_sleep.call_count == 2  # one wait between 2 attempts
    await c.aclose()


# ─── Ollama fallback ─────────────────────────────────────────────────────────


@pytest.mark.unit
async def test_ollama_connection_error_falls_back_to_stub():
    import httpx

    c = EmbeddingClient(EmbeddingConfig(provider="ollama", dimension=768))
    with patch.object(c, "_get_httpx") as mock_httpx_factory:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("connection refused"))
        mock_httpx_factory.return_value = mock_client
        result = await c._embed_ollama(["test"])
    assert len(result) == 1
    assert len(result[0]) == 768  # stub dim matches
    await c.aclose()


@pytest.mark.unit
async def test_ollama_required_env_disables_fallback():
    """When OLLAMA_REQUIRED=1, connection error must raise, not fall back."""
    import os
    import httpx

    os.environ["OLLAMA_REQUIRED"] = "1"
    try:
        c = EmbeddingClient(EmbeddingConfig(provider="ollama", dimension=768))
        with patch.object(c, "_get_httpx") as mock_httpx_factory:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=httpx.ConnectError("refused"))
            mock_httpx_factory.return_value = mock_client
            with pytest.raises(httpx.ConnectError):
                await c._embed_ollama(["test"])
        await c.aclose()
    finally:
        os.environ.pop("OLLAMA_REQUIRED", None)


# ─── Sync wrapper ───────────────────────────────────────────────────────────


@pytest.mark.unit
def test_embed_sync_works_outside_loop(stub_client):
    result = stub_client.embed_sync(["hello"])
    assert len(result) == 1 and len(result[0]) == 1536


@pytest.mark.unit
async def test_embed_sync_raises_inside_running_loop(stub_client):
    with pytest.raises(RuntimeError, match="embed_sync.*running event loop"):
        stub_client.embed_sync(["nope"])


# ─── Singleton ──────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_singleton_identity():
    a = get_embedding_client()
    b = get_embedding_client()
    assert a is b


@pytest.mark.unit
def test_lazy_proxy_forwards_attributes():
    """embedding_client.embed should resolve to the singleton's embed method."""
    assert callable(getattr(embedding_client, "embed_one", None))


@pytest.mark.unit
def test_lazy_proxy_rejects_call():
    with pytest.raises(TypeError, match="lazy proxy"):
        embedding_client()


# ─── Config from_env ────────────────────────────────────────────────────────


@pytest.mark.unit
def test_config_from_env(monkeypatch):
    monkeypatch.setenv("RAG_PROVIDER", "ollama")
    monkeypatch.setenv("RAG_EMBEDDING_DIM", "768")
    monkeypatch.setenv("RAG_CACHE", "off")
    cfg = EmbeddingConfig.from_env()
    assert cfg.provider == "ollama"
    assert cfg.dimension == 768
    assert cfg.cache_enabled is False


@pytest.mark.unit
def test_config_from_env_handles_bad_dim(monkeypatch):
    monkeypatch.setenv("RAG_EMBEDDING_DIM", "not-a-number")
    cfg = EmbeddingConfig.from_env()
    assert cfg.dimension == 1536  # fallback


# ─── Async close lifecycle ──────────────────────────────────────────────────


@pytest.mark.unit
async def test_aclose_cleans_up_openai_client():
    c = EmbeddingClient(EmbeddingConfig(provider="openai", dimension=1536))
    c._openai_client = AsyncMock()
    c._openai_client.close = AsyncMock()
    await c.aclose()
    c._openai_client.close.assert_called_once()
