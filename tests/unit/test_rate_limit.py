"""Tests for core.rate_limit (issue #98).

Covers:
  - Limiter is created (either Redis-backed or in-memory).
  - is_redis_backed() reflects REDIS_URL.
  - No Redis client is required at import time.
"""
from __future__ import annotations

import importlib

import pytest


def test_rate_limit_module_imports_without_redis(monkeypatch: pytest.MonkeyPatch) -> None:
    """Module must import even if REDIS_URL is unset (no connection attempt)."""
    monkeypatch.delenv("REDIS_URL", raising=False)
    # Force fresh import to assert no eager connection.
    import core.rate_limit as rl

    importlib.reload(rl)
    assert rl is not None
    assert rl.limiter is not None


def test_is_redis_backed_false_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("REDIS_URL", raising=False)
    import core.rate_limit as rl

    importlib.reload(rl)
    assert rl.is_redis_backed() is False


def test_is_redis_backed_true_with_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    import core.rate_limit as rl

    importlib.reload(rl)
    assert rl.is_redis_backed() is True
    # Cleanup: drop env again so later tests see the default.
    monkeypatch.delenv("REDIS_URL", raising=False)
    importlib.reload(rl)
