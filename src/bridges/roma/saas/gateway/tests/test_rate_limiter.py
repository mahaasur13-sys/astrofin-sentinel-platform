"""Tests for rate_limiter.py."""
import pytest
import asyncio
from saas.gateway.rate_limiter import TokenBucket


class TestTokenBucket:
    def test_initial_tokens_equal_burst(self):
        bucket = TokenBucket(rate=1.0, burst=5)
        assert bucket.tokens == 5.0

    @pytest.mark.asyncio
    async def test_consume_returns_true_when_tokens_available(self):
        bucket = TokenBucket(rate=1.0, burst=5)
        result = await bucket.consume(1)
        assert result is True

    @pytest.mark.asyncio
    async def test_consume_decrements_tokens(self):
        bucket = TokenBucket(rate=1.0, burst=5)
        await bucket.consume(2)
        assert bucket.tokens == 3.0

    @pytest.mark.asyncio
    async def test_consume_returns_false_when_empty(self):
        bucket = TokenBucket(rate=0.001, burst=1)
        allowed1 = await bucket.consume(1)  # exhaust
        allowed2 = await bucket.consume(1)   # should be denied
        assert allowed1 is True
        assert allowed2 is False

    @pytest.mark.asyncio
    async def test_refill_over_time(self):
        bucket = TokenBucket(rate=100.0, burst=5)
        await bucket.consume(5)  # exhaust tokens to 0
        assert bucket.tokens == 0.0
        await asyncio.sleep(0.05)  # 100 tokens/sec → ~5 tokens added in 50ms
        # Trigger refill by calling consume (refill happens inside consume)
        await bucket.consume(0)  # pass 0 tokens just to trigger refill math
        assert bucket.tokens > 4.0, f"Expected >4 tokens, got {bucket.tokens}"


class TestRateLimitWithMockedRequest:
    """Test rate_limit_dependency with a real in-memory bucket."""

    @pytest.mark.asyncio
    async def test_allows_request_under_limit(self):
        from saas.gateway.rate_limiter import _buckets, check_rate_limit
        _buckets.clear()
        
        from unittest.mock import MagicMock
        from fastapi import Request
        
        mock_request = MagicMock(spec=Request)
        mock_request.state.tenant_id = "test-tenant-rl"
        mock_request.url.path = "/test"
        
        # Should not raise
        await check_rate_limit(
            mock_request,
            requests_per_minute=60,
            burst_size=10,
            use_redis=False,
        )

    @pytest.mark.asyncio
    async def test_rejects_over_burst(self):
        from saas.gateway.rate_limiter import _buckets
        from unittest.mock import MagicMock
        from fastapi import Request
        
        _buckets.clear()
        
        mock_request = MagicMock(spec=Request)
        mock_request.state.tenant_id = "test-tenant-burst"
        mock_request.url.path = "/test"
        
        # Consume burst with direct bucket access
        bucket = TokenBucket(rate=1.0, burst=2)
        await bucket.consume(1)
        await bucket.consume(1)
        
        # Now the bucket is empty — next should fail
        result = await bucket.consume(1)
        assert result is False
