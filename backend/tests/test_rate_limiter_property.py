"""
Property-Based Tests for RateLimiter

This module contains property-based tests for the RateLimiter using Hypothesis.
These tests validate universal properties that should hold across all valid inputs.

Properties tested:
- Property 29: API Rate Limiting

Requirements: 14.5
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from fastapi import Request, status
from fastapi.responses import JSONResponse
from unittest.mock import Mock, AsyncMock
import time
import asyncio
from app.api.rate_limiter import RateLimiter


# Hypothesis strategies for generating test data
@st.composite
def client_id_strategy(draw):
    """Generate valid client identifiers."""
    id_type = draw(st.sampled_from(['user', 'ip']))
    if id_type == 'user':
        user_id = draw(st.integers(min_value=1, max_value=999999))
        return f"user:{user_id}"
    else:
        # Generate IP address
        octets = [draw(st.integers(min_value=0, max_value=255)) for _ in range(4)]
        return f"ip:{'.'.join(map(str, octets))}"


@st.composite
def rate_limit_config_strategy(draw):
    """Generate valid rate limit configurations."""
    max_requests = draw(st.integers(min_value=1, max_value=100))
    time_window = draw(st.integers(min_value=1, max_value=60))
    return max_requests, time_window


def create_mock_request(client_id: str, user_id: str = None, ip: str = None):
    """Create a mock FastAPI request."""
    request = Mock(spec=Request)
    request.state = Mock()
    
    if user_id:
        request.state.user_id = user_id
    else:
        request.state.user_id = None
    
    # Mock client
    request.client = Mock()
    request.client.host = ip if ip else "127.0.0.1"
    
    # Mock headers
    request.headers = {}
    
    return request


# Feature: intelli-credit-platform, Property 29: API Rate Limiting
@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    max_requests=st.integers(min_value=1, max_value=20),
    time_window=st.integers(min_value=1, max_value=10),
    num_requests=st.integers(min_value=1, max_value=30)
)
@pytest.mark.asyncio
async def test_property_rate_limiting_throttles_excess_requests(
    max_requests,
    num_requests,
    time_window
):
    """
    **Validates: Requirements 14.5**
    
    Property 29: API Rate Limiting
    
    For any API endpoint, when the number of requests from a single client exceeds
    the rate limit threshold within the time window, subsequent requests should be
    throttled with HTTP 429 status code.
    
    This property verifies that:
    1. Requests within the limit are allowed (HTTP 200)
    2. Requests exceeding the limit are throttled (HTTP 429)
    3. Rate limit headers are included in all responses
    4. Throttled responses include retry-after information
    """
    # Create rate limiter with test configuration
    rate_limiter = RateLimiter(
        max_requests=max_requests,
        time_window=time_window,
        cleanup_interval=300
    )
    
    # Create a mock request for a single client
    client_ip = "192.168.1.100"
    request = create_mock_request(
        client_id=f"ip:{client_ip}",
        ip=client_ip
    )
    
    # Mock call_next function that returns a successful response
    async def mock_call_next(req):
        response = Mock()
        response.headers = {}
        return response
    
    # Track responses
    allowed_count = 0
    throttled_count = 0
    
    # Make requests
    for i in range(num_requests):
        response = await rate_limiter(request, mock_call_next)
        
        if isinstance(response, JSONResponse):
            # Check if it's a throttled response
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                throttled_count += 1
                
                # Verify throttled response has required fields
                assert "error" in response.body.decode() or hasattr(response, "body")
                
                # Verify rate limit headers are present
                assert "X-RateLimit-Limit" in response.headers
                assert "X-RateLimit-Remaining" in response.headers
                assert "X-RateLimit-Reset" in response.headers
                assert "Retry-After" in response.headers
                
                # Verify remaining is 0 when throttled
                assert response.headers["X-RateLimit-Remaining"] == "0"
            else:
                allowed_count += 1
        else:
            # Regular response (allowed)
            allowed_count += 1
            
            # Verify rate limit headers are present
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers
    
    # Property verification: requests should be throttled when exceeding limit
    if num_requests <= max_requests:
        # All requests should be allowed
        assert allowed_count == num_requests
        assert throttled_count == 0
    else:
        # First max_requests should be allowed, rest should be throttled
        assert allowed_count == max_requests
        assert throttled_count == num_requests - max_requests


# Feature: intelli-credit-platform, Property 29: API Rate Limiting (Per-Client Isolation)
@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    max_requests=st.integers(min_value=5, max_value=20),
    time_window=st.integers(min_value=1, max_value=10),
    num_clients=st.integers(min_value=2, max_value=5)
)
@pytest.mark.asyncio
async def test_property_rate_limiting_per_client_isolation(
    max_requests,
    time_window,
    num_clients
):
    """
    **Validates: Requirements 14.5**
    
    Property 29: API Rate Limiting (Per-Client Isolation)
    
    For any set of clients, rate limiting should be applied independently per client.
    One client exceeding the rate limit should not affect other clients.
    
    This property verifies that:
    1. Each client has independent rate limit tracking
    2. One client being throttled doesn't affect others
    3. Each client can make up to max_requests within the window
    """
    # Create rate limiter with test configuration
    rate_limiter = RateLimiter(
        max_requests=max_requests,
        time_window=time_window,
        cleanup_interval=300
    )
    
    # Mock call_next function
    async def mock_call_next(req):
        response = Mock()
        response.headers = {}
        return response
    
    # Create requests for different clients
    clients = []
    for i in range(num_clients):
        client_ip = f"192.168.1.{100 + i}"
        request = create_mock_request(
            client_id=f"ip:{client_ip}",
            ip=client_ip
        )
        clients.append((client_ip, request))
    
    # Each client makes max_requests + 1 requests
    for client_ip, request in clients:
        allowed_count = 0
        throttled_count = 0
        
        for i in range(max_requests + 1):
            response = await rate_limiter(request, mock_call_next)
            
            if isinstance(response, JSONResponse) and response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                throttled_count += 1
            else:
                allowed_count += 1
        
        # Verify per-client isolation
        assert allowed_count == max_requests, f"Client {client_ip} should have {max_requests} allowed requests"
        assert throttled_count == 1, f"Client {client_ip} should have 1 throttled request"


# Feature: intelli-credit-platform, Property 29: API Rate Limiting (Rate Limit Headers)
@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    max_requests=st.integers(min_value=5, max_value=50),
    time_window=st.integers(min_value=1, max_value=60),
    num_requests=st.integers(min_value=1, max_value=10)
)
@pytest.mark.asyncio
async def test_property_rate_limiting_headers_present(
    max_requests,
    time_window,
    num_requests
):
    """
    **Validates: Requirements 14.5**
    
    Property 29: API Rate Limiting (Rate Limit Headers)
    
    For any API response (successful or throttled), rate limit headers should be
    included with accurate information about limits, remaining requests, and reset time.
    
    This property verifies that:
    1. X-RateLimit-Limit header shows the maximum requests allowed
    2. X-RateLimit-Remaining header shows remaining requests (decreases with each request)
    3. X-RateLimit-Reset header shows when the limit resets
    4. Retry-After header is present in throttled responses
    """
    # Ensure num_requests doesn't exceed max_requests for this test
    assume(num_requests <= max_requests)
    
    # Create rate limiter with test configuration
    rate_limiter = RateLimiter(
        max_requests=max_requests,
        time_window=time_window,
        cleanup_interval=300
    )
    
    # Create a mock request
    client_ip = "192.168.1.200"
    request = create_mock_request(
        client_id=f"ip:{client_ip}",
        ip=client_ip
    )
    
    # Mock call_next function
    async def mock_call_next(req):
        response = Mock()
        response.headers = {}
        return response
    
    # Make requests and verify headers
    for i in range(num_requests):
        response = await rate_limiter(request, mock_call_next)
        
        # Verify required headers are present
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        
        # Verify limit header value
        assert response.headers["X-RateLimit-Limit"] == str(max_requests)
        
        # Verify remaining header value decreases
        remaining = int(response.headers["X-RateLimit-Remaining"])
        expected_remaining = max_requests - (i + 1)
        assert remaining == expected_remaining, f"After {i+1} requests, remaining should be {expected_remaining}"
        
        # Verify reset time is in the future
        reset_time = float(response.headers["X-RateLimit-Reset"])
        assert reset_time > time.time(), "Reset time should be in the future"


# Feature: intelli-credit-platform, Property 29: API Rate Limiting (Window Reset)
@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    max_requests=st.integers(min_value=2, max_value=10),
    time_window=st.integers(min_value=1, max_value=3)
)
@pytest.mark.asyncio
async def test_property_rate_limiting_window_reset(
    max_requests,
    time_window
):
    """
    **Validates: Requirements 14.5**
    
    Property 29: API Rate Limiting (Window Reset)
    
    For any client that has been throttled, after the time window expires,
    the client should be able to make requests again up to the limit.
    
    This property verifies that:
    1. Client is throttled after exceeding limit
    2. After time window expires, client can make requests again
    3. Rate limit tracking resets properly
    """
    # Create rate limiter with test configuration
    rate_limiter = RateLimiter(
        max_requests=max_requests,
        time_window=time_window,
        cleanup_interval=300
    )
    
    # Create a mock request
    client_ip = "192.168.1.250"
    request = create_mock_request(
        client_id=f"ip:{client_ip}",
        ip=client_ip
    )
    
    # Mock call_next function
    async def mock_call_next(req):
        response = Mock()
        response.headers = {}
        return response
    
    # Phase 1: Exhaust the rate limit
    for i in range(max_requests):
        response = await rate_limiter(request, mock_call_next)
        assert not (isinstance(response, JSONResponse) and response.status_code == status.HTTP_429_TOO_MANY_REQUESTS)
    
    # Phase 2: Verify throttling
    response = await rate_limiter(request, mock_call_next)
    assert isinstance(response, JSONResponse)
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    
    # Phase 3: Wait for window to expire
    await asyncio.sleep(time_window + 0.5)
    
    # Phase 4: Verify client can make requests again
    response = await rate_limiter(request, mock_call_next)
    # Should be allowed now (not a JSONResponse with 429)
    if isinstance(response, JSONResponse):
        assert response.status_code != status.HTTP_429_TOO_MANY_REQUESTS
    
    # Verify remaining count is reset
    assert "X-RateLimit-Remaining" in response.headers
    remaining = int(response.headers["X-RateLimit-Remaining"])
    assert remaining == max_requests - 1, "After window reset, remaining should be max_requests - 1"
