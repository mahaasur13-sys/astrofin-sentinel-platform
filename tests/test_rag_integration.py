"""Tests for RAG integration (Phase 6.1)."""
from __future__ import annotations

import os
from unittest.mock import patch, MagicMock

import pytest

os.environ.setdefault("RAG_ENABLED", "true")
os.environ.setdefault("RAG_MODEL_NAME", "test-model")

from core.base_agent import BaseAgent, get_rag


@pytest.fixture(autouse=True)
def reset_rag_singleton():
    import core.base_agent as mod
    mod._rag_instance = None
    yield
    mod._rag_instance = None


class TestRAGSingleton:
    def test_get_rag_returns_none_when_disabled(self):
        with patch.dict(os.environ, {"RAG_ENABLED": "false"}):
            result = get_rag()
            assert result is None

    def test_get_rag_returns_singleton(self):
        r1 = get_rag()
        r2 = get_rag()
        assert r1 is r2
