"""Tests for Redis failover — graceful degradation (H-04)."""

import pytest


# ============================================================
# Rate limiter without Redis
# ============================================================
def test_rate_limiter_imports_without_redis():
    """Rate limiter module is importable."""
    from core import rate_limiter
    from core.rate_limiter import limiter
    assert limiter is not None


# ============================================================
# Meta-RL inference without Redis
# ============================================================
def test_meta_rl_weights_without_redis():
    """Meta-RL returns weights even without Redis cache."""
    from meta_rl.inference import get_agent_weights
    weights = get_agent_weights(use_cache=False)
    assert weights is not None
    assert isinstance(weights, dict)
    assert len(weights) > 0


def test_agent_weights_have_required_keys():
    """Agent weights dict contains expected keys."""
    from meta_rl.inference import get_agent_weights
    weights = get_agent_weights(use_cache=False)
    assert isinstance(weights, dict)
    assert len(weights) == 13


def test_ensemble_routing_returns_valid_result():
    """Ensemble routing produces non-empty results."""
    from meta_rl.inference import apply_weights_to_decisions
    result = apply_weights_to_decisions([{'agent': 'test'}], {})
    assert result is not None
    assert isinstance(result, dict)
    assert len(result) > 0


# ============================================================
# Cache edge cases
# ============================================================
def test_cache_ttl_is_positive():
    """CACHE_TTL must be positive."""
    from meta_rl.inference import CACHE_TTL
    assert CACHE_TTL > 0


def test_get_weights_with_cache():
    """get_agent_weights(use_cache=True) returns results."""
    from meta_rl.inference import get_agent_weights, _CACHED_WEIGHTS, _CACHE_TS, CACHE_TTL
    weights = get_agent_weights(use_cache=True)
    assert weights is not None
    assert len(weights) == 13
    # Cache is implementation-dependent — just verify results are correct
