"""
Rate Limiting Middleware for API Endpoints

This module provides rate limiting functionality to prevent API abuse by
tracking and throttling requests on a per-client basis.

Requirements: 14.5
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from typing import Callable, Dict, Optional
from datetime import datetime, timedelta
import time
import asyncio
from collections import defaultdict


class RateLimiter:
    """
    Rate limiter that tracks requests per client and enforces throttling.
    
    This class implements a sliding window rate limiting algorithm:
    - Tracks requests per client (identified by IP or user ID)
    - Enforces configurable rate limits (requests per time window)
    - Returns HTTP 429 when limits are exceeded
    - Adds rate limit headers to all responses
    
    Attributes:
        max_requests: Maximum number of requests allowed per time window
        time_window: Time window in seconds for rate limiting
        request_counts: Dictionary tracking request timestamps per client
    """
    
    def __init__(
        self,
        max_requests: int = 100,
        time_window: int = 60,
        cleanup_interval: int = 300
    ):
        """
        Initialize the rate limiter.
        
        Args:
            max_requests: Maximum requests allowed per time window (default: 100)
            time_window: Time window in seconds (default: 60 seconds)
            cleanup_interval: Interval in seconds to clean up old entries (default: 300)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.cleanup_interval = cleanup_interval
        
        # Store request timestamps per client
        # Format: {client_id: [timestamp1, timestamp2, ...]}
        self.request_counts: Dict[str, list] = defaultdict(list)
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
        
        # Last cleanup time
        self._last_cleanup = time.time()
    
    async def __call__(self, request: Request, call_next: Callable):
        """
        Process the request through the rate limiting middleware.
        
        Args:
            request: The incoming request
            call_next: The next middleware or route handler
            
        Returns:
            Response with rate limit headers or 429 error if limit exceeded
        """
        # Get client identifier (user ID if authenticated, otherwise IP address)
        client_id = self._get_client_id(request)
        
        # Check rate limit
        is_allowed, remaining, reset_time = await self._check_rate_limit(client_id)
        
        if not is_allowed:
            # Rate limit exceeded
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded. Maximum {self.max_requests} requests per {self.time_window} seconds.",
                    "retry_after": int(reset_time - time.time())
                },
                headers={
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_time)),
                    "Retry-After": str(int(reset_time - time.time()))
                }
            )
        
        # Process the request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(reset_time))
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """
        Get a unique identifier for the client.
        
        Priority:
        1. User ID from authenticated session (if available)
        2. IP address from request
        
        Args:
            request: The incoming request
            
        Returns:
            Client identifier string
        """
        # Try to get user ID from authenticated session
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        # Check for forwarded IP (behind proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            ip = forwarded_for.split(",")[0].strip()
        else:
            # Use direct client IP
            ip = request.client.host if request.client else "unknown"
        
        return f"ip:{ip}"
    
    async def _check_rate_limit(self, client_id: str) -> tuple[bool, int, float]:
        """
        Check if the client has exceeded the rate limit.
        
        This method:
        1. Removes expired timestamps from the client's request history
        2. Checks if the number of requests exceeds the limit
        3. Adds the current timestamp if allowed
        4. Calculates remaining requests and reset time
        
        Args:
            client_id: Unique identifier for the client
            
        Returns:
            Tuple of (is_allowed, remaining_requests, reset_timestamp)
        """
        async with self._lock:
            current_time = time.time()
            window_start = current_time - self.time_window
            
            # Get client's request history
            request_times = self.request_counts[client_id]
            
            # Remove timestamps outside the current window
            request_times = [t for t in request_times if t > window_start]
            
            # Update the stored timestamps
            self.request_counts[client_id] = request_times
            
            # Check if limit is exceeded
            if len(request_times) >= self.max_requests:
                # Calculate when the oldest request will expire
                oldest_request = min(request_times)
                reset_time = oldest_request + self.time_window
                return False, 0, reset_time
            
            # Add current request timestamp
            request_times.append(current_time)
            
            # Calculate remaining requests
            remaining = self.max_requests - len(request_times)
            
            # Calculate reset time (when the oldest request expires)
            if request_times:
                oldest_request = min(request_times)
                reset_time = oldest_request + self.time_window
            else:
                reset_time = current_time + self.time_window
            
            # Periodic cleanup of old entries
            if current_time - self._last_cleanup > self.cleanup_interval:
                await self._cleanup_old_entries(window_start)
                self._last_cleanup = current_time
            
            return True, remaining, reset_time
    
    async def _cleanup_old_entries(self, window_start: float):
        """
        Clean up old entries to prevent memory growth.
        
        Removes clients that have no requests in the current window.
        
        Args:
            window_start: Start of the current time window
        """
        clients_to_remove = []
        
        for client_id, request_times in self.request_counts.items():
            # Remove timestamps outside the window
            active_requests = [t for t in request_times if t > window_start]
            
            if not active_requests:
                # No active requests, mark for removal
                clients_to_remove.append(client_id)
            else:
                # Update with only active requests
                self.request_counts[client_id] = active_requests
        
        # Remove inactive clients
        for client_id in clients_to_remove:
            del self.request_counts[client_id]
    
    async def reset_client(self, client_id: str):
        """
        Reset rate limit for a specific client.
        
        This is useful for testing or administrative purposes.
        
        Args:
            client_id: Client identifier to reset
        """
        async with self._lock:
            if client_id in self.request_counts:
                del self.request_counts[client_id]
    
    async def get_client_status(self, client_id: str) -> Dict:
        """
        Get the current rate limit status for a client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Dictionary with current status information
        """
        async with self._lock:
            current_time = time.time()
            window_start = current_time - self.time_window
            
            request_times = self.request_counts.get(client_id, [])
            active_requests = [t for t in request_times if t > window_start]
            
            remaining = self.max_requests - len(active_requests)
            
            if active_requests:
                oldest_request = min(active_requests)
                reset_time = oldest_request + self.time_window
            else:
                reset_time = current_time + self.time_window
            
            return {
                "client_id": client_id,
                "requests_made": len(active_requests),
                "requests_remaining": max(0, remaining),
                "limit": self.max_requests,
                "window_seconds": self.time_window,
                "reset_time": reset_time,
                "reset_in_seconds": max(0, int(reset_time - current_time))
            }
