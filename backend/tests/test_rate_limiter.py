"""
Unit Tests for Rate Limiter

Tests the RateLimiter class functionality including:
- Request tracking per client
- Throttling logic
- Rate limit headers
- Client identification
- Cleanup of old entries

Requirements: 14.5
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from app.api.rate_limiter import RateLimiter


class MockRequest:
    """Mock request object for testing"""
    
    def __init__(self, client_host: str = "127.0.0.1", user_id: str = None, forwarded_for: str = None):
        self.client = Mock()
        self.client.host = client_host
        self.state = Mock()
        self.state.user_id = user_id
        self.headers = {}
        if forwarded_for:
            self.headers["X-Forwarded-For"] = forwarded_for


@pytest.fixture
def rate_limiter():
    """Create a rate limiter with small limits for testing"""
    return RateLimiter(max_requests=5, time_window=2)


@pytest.fixture
def mock_call_next():
    """Create a mock call_next function"""
    async def call_next(request):
        return Response(content="OK", status_code=200)
    return call_next


@pytest.mark.asyncio
async def test_rate_limiter_allows_requests_within_limit(rate_limiter, mock_call_next):
    """Test that requests within the limit are allowed"""
    request = MockRequest(client_host="192.168.1.1")
    
    # Make requests within the limit
    for i in range(5):
        response = await rate_limiter(request, mock_call_next)
        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert response.headers["X-RateLimit-Limit"] == "5"
        assert int(response.headers["X-RateLimit-Remaining"]) == 4 - i


@pytest.mark.asyncio
async def test_rate_limiter_blocks_requests_exceeding_limit(rate_limiter, mock_call_next):
    """Test that requests exceeding the limit are blocked with 429"""
    request = MockRequest(client_host="192.168.1.2")
    
    # Make requests up to the limit
    for _ in range(5):
        response = await rate_limiter(request, mock_call_next)
        assert response.status_code == 200
    
    # Next request should be blocked
    response = await rate_limiter(request, mock_call_next)
    assert response.status_code == 429
    
    # Check response content
    assert isinstance(response, JSONResponse)
    # Parse the response body
    import json
    body = json.loads(response.body.decode())
    assert body["error"] == "rate_limit_exceeded"
    assert "retry_after" in body
    
    # Check headers
    assert response.headers["X-RateLimit-Limit"] == "5"
    assert response.headers["X-RateLimit-Remaining"] == "0"
    assert "Retry-After" in response.headers


@pytest.mark.asyncio
async def test_rate_limiter_resets_after_time_window(rate_limiter, mock_call_next):
    """Test that rate limit resets after the time window expires"""
    request = MockRequest(client_host="192.168.1.3")
    
    # Make requests up to the limit
    for _ in range(5):
        response = await rate_limiter(request, mock_call_next)
        assert response.status_code == 200
    
    # Next request should be blocked
    response = await rate_limiter(request, mock_call_next)
    assert response.status_code == 429
    
    # Wait for time window to expire
    await asyncio.sleep(2.1)
    
    # Should be able to make requests again
    response = await rate_limiter(request, mock_call_next)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_rate_limiter_tracks_clients_separately(rate_limiter, mock_call_next):
    """Test that different clients are tracked separately"""
    request1 = MockRequest(client_host="192.168.1.4")
    request2 = MockRequest(client_host="192.168.1.5")
    
    # Client 1 makes requests up to limit
    for _ in range(5):
        response = await rate_limiter(request1, mock_call_next)
        assert response.status_code == 200
    
    # Client 1 is blocked
    response = await rate_limiter(request1, mock_call_next)
    assert response.status_code == 429
    
    # Client 2 should still be able to make requests
    response = await rate_limiter(request2, mock_call_next)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_rate_limiter_uses_user_id_over_ip(rate_limiter, mock_call_next):
    """Test that authenticated user ID is preferred over IP address"""
    # Two requests from same IP but different users
    request1 = MockRequest(client_host="192.168.1.6", user_id="user123")
    request2 = MockRequest(client_host="192.168.1.6", user_id="user456")
    
    # User 1 makes requests up to limit
    for _ in range(5):
        response = await rate_limiter(request1, mock_call_next)
        assert response.status_code == 200
    
    # User 1 is blocked
    response = await rate_limiter(request1, mock_call_next)
    assert response.status_code == 429
    
    # User 2 (different user, same IP) should still be able to make requests
    response = await rate_limiter(request2, mock_call_next)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_rate_limiter_handles_forwarded_for_header(rate_limiter, mock_call_next):
    """Test that X-Forwarded-For header is used when present"""
    request = MockRequest(
        client_host="10.0.0.1",  # Internal proxy IP
        forwarded_for="203.0.113.1, 198.51.100.1"  # Client IP chain
    )
    
    # Make requests
    response = await rate_limiter(request, mock_call_next)
    assert response.status_code == 200
    
    # Verify the client is tracked by the forwarded IP
    client_id = "ip:203.0.113.1"  # First IP in the chain
    status = await rate_limiter.get_client_status(client_id)
    assert status["requests_made"] == 1


@pytest.mark.asyncio
async def test_rate_limiter_get_client_status():
    """Test getting client status information"""
    limiter = RateLimiter(max_requests=10, time_window=60)
    client_id = "user:test123"
    
    # Initially no requests
    status = await limiter.get_client_status(client_id)
    assert status["requests_made"] == 0
    assert status["requests_remaining"] == 10
    assert status["limit"] == 10
    
    # Simulate some requests
    limiter.request_counts[client_id] = [time.time() for _ in range(3)]
    
    status = await limiter.get_client_status(client_id)
    assert status["requests_made"] == 3
    assert status["requests_remaining"] == 7


@pytest.mark.asyncio
async def test_rate_limiter_reset_client():
    """Test resetting rate limit for a specific client"""
    limiter = RateLimiter(max_requests=5, time_window=60)
    client_id = "user:test456"
    
    # Simulate requests
    limiter.request_counts[client_id] = [time.time() for _ in range(5)]
    
    status = await limiter.get_client_status(client_id)
    assert status["requests_made"] == 5
    
    # Reset the client
    await limiter.reset_client(client_id)
    
    status = await limiter.get_client_status(client_id)
    assert status["requests_made"] == 0


@pytest.mark.asyncio
async def test_rate_limiter_cleanup_old_entries():
    """Test that old entries are cleaned up"""
    limiter = RateLimiter(max_requests=10, time_window=1, cleanup_interval=1)
    
    # Add some old entries
    old_time = time.time() - 5
    limiter.request_counts["client1"] = [old_time]
    limiter.request_counts["client2"] = [old_time]
    limiter.request_counts["client3"] = [time.time()]  # Recent entry
    
    # Trigger cleanup
    window_start = time.time() - limiter.time_window
    await limiter._cleanup_old_entries(window_start)
    
    # Old entries should be removed
    assert "client1" not in limiter.request_counts
    assert "client2" not in limiter.request_counts
    # Recent entry should remain
    assert "client3" in limiter.request_counts


@pytest.mark.asyncio
async def test_rate_limiter_sliding_window():
    """Test that the sliding window works correctly"""
    limiter = RateLimiter(max_requests=3, time_window=2)
    request = MockRequest(client_host="192.168.1.7")
    
    async def call_next(req):
        return Response(content="OK", status_code=200)
    
    # Make 3 requests at t=0
    for _ in range(3):
        response = await limiter(request, call_next)
        assert response.status_code == 200
    
    # 4th request should be blocked
    response = await limiter(request, call_next)
    assert response.status_code == 429
    
    # Wait 1 second (still within window)
    await asyncio.sleep(1)
    
    # Should still be blocked
    response = await limiter(request, call_next)
    assert response.status_code == 429
    
    # Wait another 1.1 seconds (total 2.1 seconds, outside window)
    await asyncio.sleep(1.1)
    
    # Should be allowed again
    response = await limiter(request, call_next)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_rate_limiter_concurrent_requests():
    """Test that rate limiter handles concurrent requests correctly"""
    limiter = RateLimiter(max_requests=10, time_window=60)
    request = MockRequest(client_host="192.168.1.8")
    
    async def call_next(req):
        # Simulate some processing time
        await asyncio.sleep(0.01)
        return Response(content="OK", status_code=200)
    
    # Make 10 concurrent requests
    tasks = [limiter(request, call_next) for _ in range(10)]
    responses = await asyncio.gather(*tasks)
    
    # All should succeed
    success_count = sum(1 for r in responses if r.status_code == 200)
    assert success_count == 10
    
    # 11th request should be blocked
    response = await limiter(request, call_next)
    assert response.status_code == 429


@pytest.mark.asyncio
async def test_rate_limiter_headers_format():
    """Test that rate limit headers are in the correct format"""
    limiter = RateLimiter(max_requests=5, time_window=60)
    request = MockRequest(client_host="192.168.1.9")
    
    async def call_next(req):
        return Response(content="OK", status_code=200)
    
    response = await limiter(request, call_next)
    
    # Check header presence and format
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers
    
    # Check values are numeric strings
    assert response.headers["X-RateLimit-Limit"].isdigit()
    assert response.headers["X-RateLimit-Remaining"].isdigit()
    assert response.headers["X-RateLimit-Reset"].isdigit()
    
    # Check values are reasonable
    assert int(response.headers["X-RateLimit-Limit"]) == 5
    assert 0 <= int(response.headers["X-RateLimit-Remaining"]) <= 5
    assert int(response.headers["X-RateLimit-Reset"]) > time.time()
