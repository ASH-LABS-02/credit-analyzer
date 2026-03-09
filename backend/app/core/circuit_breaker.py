"""
Circuit Breaker Pattern Implementation

This module provides a circuit breaker pattern to prevent cascading failures
when external services are down. The circuit breaker tracks failures and opens
the circuit when a threshold is reached, preventing further calls until the
service recovers.

Requirements: 15.2
"""

import asyncio
import logging
import time
from typing import Callable, TypeVar, Any, Optional
from functools import wraps
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """
    Circuit breaker states.
    
    - CLOSED: Normal operation, requests pass through
    - OPEN: Circuit is open, requests fail immediately
    - HALF_OPEN: Testing if service has recovered
    """
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures.
    
    The circuit breaker monitors failures and transitions between states:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests fail immediately
    - HALF_OPEN: Testing if service has recovered
    
    State transitions:
    - CLOSED -> OPEN: When failure count reaches threshold
    - OPEN -> HALF_OPEN: After timeout period expires
    - HALF_OPEN -> CLOSED: When a request succeeds
    - HALF_OPEN -> OPEN: When a request fails
    
    Requirements: 15.2
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        success_threshold: int = 1,
        name: Optional[str] = None
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before attempting recovery (OPEN -> HALF_OPEN)
            success_threshold: Number of successes in HALF_OPEN before closing
            name: Optional name for logging purposes
        """
        if failure_threshold <= 0:
            raise ValueError("failure_threshold must be positive")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if success_threshold <= 0:
            raise ValueError("success_threshold must be positive")
        
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.success_threshold = success_threshold
        self.name = name or "CircuitBreaker"
        
        # State tracking
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._lock = asyncio.Lock()
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state
    
    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        return self._failure_count
    
    @property
    def success_count(self) -> int:
        """Get current success count (in HALF_OPEN state)."""
        return self._success_count
    
    async def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute a function through the circuit breaker.
        
        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
        
        Returns:
            Result of the function call
        
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Any exception raised by func
        
        Requirements: 15.2
        """
        async with self._lock:
            # Check if we should transition from OPEN to HALF_OPEN
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to_half_open()
                else:
                    raise CircuitBreakerError(
                        f"{self.name}: Circuit breaker is OPEN. "
                        f"Service unavailable. Try again in "
                        f"{self._time_until_retry():.1f} seconds."
                    )
        
        # Execute the function
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure(e)
            raise
    
    def call_sync(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute a synchronous function through the circuit breaker.
        
        Args:
            func: Synchronous function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
        
        Returns:
            Result of the function call
        
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Any exception raised by func
        
        Requirements: 15.2
        """
        # Check if we should transition from OPEN to HALF_OPEN
        if self._state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                raise CircuitBreakerError(
                    f"{self.name}: Circuit breaker is OPEN. "
                    f"Service unavailable. Try again in "
                    f"{self._time_until_retry():.1f} seconds."
                )
        
        # Execute the function
        try:
            result = func(*args, **kwargs)
            self._on_success_sync()
            return result
        except Exception as e:
            self._on_failure_sync(e)
            raise
    
    async def _on_success(self):
        """Handle successful function execution."""
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                logger.info(
                    f"{self.name}: Success in HALF_OPEN state "
                    f"({self._success_count}/{self.success_threshold})"
                )
                
                if self._success_count >= self.success_threshold:
                    self._transition_to_closed()
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success in CLOSED state
                if self._failure_count > 0:
                    self._failure_count = 0
    
    def _on_success_sync(self):
        """Handle successful function execution (synchronous)."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            logger.info(
                f"{self.name}: Success in HALF_OPEN state "
                f"({self._success_count}/{self.success_threshold})"
            )
            
            if self._success_count >= self.success_threshold:
                self._transition_to_closed()
        elif self._state == CircuitState.CLOSED:
            if self._failure_count > 0:
                self._failure_count = 0
    
    async def _on_failure(self, exception: Exception):
        """Handle failed function execution."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            logger.warning(
                f"{self.name}: Failure in {self._state.value} state "
                f"({self._failure_count}/{self.failure_threshold}). "
                f"Error: {type(exception).__name__}: {str(exception)}"
            )
            
            if self._state == CircuitState.HALF_OPEN:
                # Any failure in HALF_OPEN immediately opens the circuit
                self._transition_to_open()
            elif self._state == CircuitState.CLOSED:
                # Check if we've reached the failure threshold
                if self._failure_count >= self.failure_threshold:
                    self._transition_to_open()
    
    def _on_failure_sync(self, exception: Exception):
        """Handle failed function execution (synchronous)."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        logger.warning(
            f"{self.name}: Failure in {self._state.value} state "
            f"({self._failure_count}/{self.failure_threshold}). "
            f"Error: {type(exception).__name__}: {str(exception)}"
        )
        
        if self._state == CircuitState.HALF_OPEN:
            self._transition_to_open()
        elif self._state == CircuitState.CLOSED:
            if self._failure_count >= self.failure_threshold:
                self._transition_to_open()
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self._last_failure_time is None:
            return True
        return time.time() - self._last_failure_time >= self.timeout
    
    def _time_until_retry(self) -> float:
        """Calculate time remaining until retry is allowed."""
        if self._last_failure_time is None:
            return 0.0
        elapsed = time.time() - self._last_failure_time
        return max(0.0, self.timeout - elapsed)
    
    def _transition_to_open(self):
        """Transition to OPEN state."""
        logger.error(
            f"{self.name}: Circuit breaker opening. "
            f"Failure threshold ({self.failure_threshold}) reached. "
            f"Will attempt recovery in {self.timeout} seconds."
        )
        self._state = CircuitState.OPEN
        self._success_count = 0
    
    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state."""
        logger.info(
            f"{self.name}: Circuit breaker entering HALF_OPEN state. "
            f"Testing service recovery."
        )
        self._state = CircuitState.HALF_OPEN
        self._failure_count = 0
        self._success_count = 0
    
    def _transition_to_closed(self):
        """Transition to CLOSED state."""
        logger.info(
            f"{self.name}: Circuit breaker closing. "
            f"Service recovered successfully."
        )
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
    
    def reset(self):
        """
        Manually reset the circuit breaker to CLOSED state.
        
        This should be used with caution, typically only for testing
        or administrative purposes.
        """
        logger.info(f"{self.name}: Circuit breaker manually reset to CLOSED state.")
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None


def with_circuit_breaker(circuit_breaker: CircuitBreaker):
    """
    Decorator for applying circuit breaker to async functions.
    
    Args:
        circuit_breaker: CircuitBreaker instance to use
    
    Returns:
        Decorated function with circuit breaker protection
    
    Requirements: 15.2
    
    Example:
        >>> breaker = CircuitBreaker(failure_threshold=5, timeout=60)
        >>> @with_circuit_breaker(breaker)
        ... async def fetch_data():
        ...     return await api.get_data()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await circuit_breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator
