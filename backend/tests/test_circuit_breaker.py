"""
Unit tests for Circuit Breaker Pattern

Tests the circuit breaker implementation including state transitions,
failure tracking, and recovery behavior.

Requirements: 15.2
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, Mock

from app.core.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerError,
    with_circuit_breaker
)


class TestCircuitBreakerInitialization:
    """Test circuit breaker initialization and configuration."""
    
    def test_default_initialization(self):
        """Test circuit breaker with default parameters."""
        breaker = CircuitBreaker()
        
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.success_count == 0
        assert breaker.failure_threshold == 5
        assert breaker.timeout == 60.0
    
    def test_custom_initialization(self):
        """Test circuit breaker with custom parameters."""
        breaker = CircuitBreaker(
            failure_threshold=3,
            timeout=30.0,
            success_threshold=2,
            name="TestBreaker"
        )
        
        assert breaker.failure_threshold == 3
        assert breaker.timeout == 30.0
        assert breaker.success_threshold == 2
        assert breaker.name == "TestBreaker"
    
    def test_invalid_failure_threshold(self):
        """Test that invalid failure threshold raises error."""
        with pytest.raises(ValueError, match="failure_threshold must be positive"):
            CircuitBreaker(failure_threshold=0)
        
        with pytest.raises(ValueError, match="failure_threshold must be positive"):
            CircuitBreaker(failure_threshold=-1)
    
    def test_invalid_timeout(self):
        """Test that invalid timeout raises error."""
        with pytest.raises(ValueError, match="timeout must be positive"):
            CircuitBreaker(timeout=0)
        
        with pytest.raises(ValueError, match="timeout must be positive"):
            CircuitBreaker(timeout=-1)
    
    def test_invalid_success_threshold(self):
        """Test that invalid success threshold raises error."""
        with pytest.raises(ValueError, match="success_threshold must be positive"):
            CircuitBreaker(success_threshold=0)


class TestCircuitBreakerClosedState:
    """Test circuit breaker behavior in CLOSED state."""
    
    @pytest.mark.asyncio
    async def test_successful_call_in_closed_state(self):
        """Test that successful calls pass through in CLOSED state."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        async def successful_func():
            return "success"
        
        result = await breaker.call(successful_func)
        
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_single_failure_in_closed_state(self):
        """Test that single failure doesn't open circuit."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        async def failing_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            await breaker.call(failing_func)
        
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 1
    
    @pytest.mark.asyncio
    async def test_multiple_failures_open_circuit(self):
        """Test that reaching failure threshold opens circuit."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        async def failing_func():
            raise ValueError("Test error")
        
        # First two failures should keep circuit closed
        for i in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)
            assert breaker.state == CircuitState.CLOSED
            assert breaker.failure_count == i + 1
        
        # Third failure should open circuit
        with pytest.raises(ValueError):
            await breaker.call(failing_func)
        
        assert breaker.state == CircuitState.OPEN
        assert breaker.failure_count == 3
    
    @pytest.mark.asyncio
    async def test_success_resets_failure_count(self):
        """Test that success resets failure count in CLOSED state."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        async def failing_func():
            raise ValueError("Test error")
        
        async def successful_func():
            return "success"
        
        # Accumulate some failures
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)
        
        assert breaker.failure_count == 2
        
        # Success should reset failure count
        await breaker.call(successful_func)
        
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0


class TestCircuitBreakerOpenState:
    """Test circuit breaker behavior in OPEN state."""
    
    @pytest.mark.asyncio
    async def test_calls_fail_immediately_in_open_state(self):
        """Test that calls fail immediately when circuit is open."""
        breaker = CircuitBreaker(failure_threshold=2, timeout=10.0)
        
        async def failing_func():
            raise ValueError("Test error")
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)
        
        assert breaker.state == CircuitState.OPEN
        
        # Next call should fail immediately with CircuitBreakerError
        async def any_func():
            return "should not execute"
        
        with pytest.raises(CircuitBreakerError, match="Circuit breaker is OPEN"):
            await breaker.call(any_func)
    
    @pytest.mark.asyncio
    async def test_transition_to_half_open_after_timeout(self):
        """Test that circuit transitions to HALF_OPEN after timeout."""
        breaker = CircuitBreaker(failure_threshold=2, timeout=0.1)  # 100ms timeout
        
        async def failing_func():
            raise ValueError("Test error")
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)
        
        assert breaker.state == CircuitState.OPEN
        
        # Wait for timeout
        await asyncio.sleep(0.15)
        
        # Next call should transition to HALF_OPEN
        async def successful_func():
            return "success"
        
        result = await breaker.call(successful_func)
        
        assert result == "success"
        # After one success with success_threshold=1, should be CLOSED
        assert breaker.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_error_message(self):
        """Test that CircuitBreakerError contains helpful message."""
        breaker = CircuitBreaker(failure_threshold=1, timeout=10.0, name="TestService")
        
        async def failing_func():
            raise ValueError("Test error")
        
        # Open the circuit
        with pytest.raises(ValueError):
            await breaker.call(failing_func)
        
        # Try to call again
        async def any_func():
            return "test"
        
        with pytest.raises(CircuitBreakerError) as exc_info:
            await breaker.call(any_func)
        
        error_message = str(exc_info.value)
        assert "TestService" in error_message
        assert "Circuit breaker is OPEN" in error_message
        assert "Try again in" in error_message


class TestCircuitBreakerHalfOpenState:
    """Test circuit breaker behavior in HALF_OPEN state."""
    
    @pytest.mark.asyncio
    async def test_success_in_half_open_closes_circuit(self):
        """Test that success in HALF_OPEN closes the circuit."""
        breaker = CircuitBreaker(
            failure_threshold=2,
            timeout=0.1,
            success_threshold=1
        )
        
        async def failing_func():
            raise ValueError("Test error")
        
        async def successful_func():
            return "success"
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)
        
        assert breaker.state == CircuitState.OPEN
        
        # Wait for timeout
        await asyncio.sleep(0.15)
        
        # Successful call should close circuit
        result = await breaker.call(successful_func)
        
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_failure_in_half_open_reopens_circuit(self):
        """Test that failure in HALF_OPEN reopens the circuit."""
        breaker = CircuitBreaker(failure_threshold=2, timeout=0.1)
        
        async def failing_func():
            raise ValueError("Test error")
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)
        
        assert breaker.state == CircuitState.OPEN
        
        # Wait for timeout
        await asyncio.sleep(0.15)
        
        # Failure should reopen circuit
        with pytest.raises(ValueError):
            await breaker.call(failing_func)
        
        assert breaker.state == CircuitState.OPEN
    
    @pytest.mark.asyncio
    async def test_multiple_successes_required(self):
        """Test that multiple successes are required when success_threshold > 1."""
        breaker = CircuitBreaker(
            failure_threshold=2,
            timeout=0.1,
            success_threshold=3
        )
        
        async def failing_func():
            raise ValueError("Test error")
        
        async def successful_func():
            return "success"
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)
        
        # Wait for timeout
        await asyncio.sleep(0.15)
        
        # First two successes should keep circuit in HALF_OPEN
        for i in range(2):
            result = await breaker.call(successful_func)
            assert result == "success"
            assert breaker.state == CircuitState.HALF_OPEN
            assert breaker.success_count == i + 1
        
        # Third success should close circuit
        result = await breaker.call(successful_func)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED


class TestCircuitBreakerSynchronous:
    """Test synchronous circuit breaker functionality."""
    
    def test_sync_successful_call(self):
        """Test synchronous successful call."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        def successful_func():
            return "success"
        
        result = breaker.call_sync(successful_func)
        
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
    
    def test_sync_failure_opens_circuit(self):
        """Test that synchronous failures open circuit."""
        breaker = CircuitBreaker(failure_threshold=2)
        
        def failing_func():
            raise ValueError("Test error")
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call_sync(failing_func)
        
        assert breaker.state == CircuitState.OPEN
    
    def test_sync_circuit_breaker_error(self):
        """Test that sync calls fail when circuit is open."""
        breaker = CircuitBreaker(failure_threshold=1, timeout=10.0)
        
        def failing_func():
            raise ValueError("Test error")
        
        # Open the circuit
        with pytest.raises(ValueError):
            breaker.call_sync(failing_func)
        
        # Next call should fail with CircuitBreakerError
        def any_func():
            return "test"
        
        with pytest.raises(CircuitBreakerError):
            breaker.call_sync(any_func)


class TestCircuitBreakerReset:
    """Test manual circuit breaker reset."""
    
    def test_manual_reset(self):
        """Test that manual reset closes the circuit."""
        breaker = CircuitBreaker(failure_threshold=1)
        
        def failing_func():
            raise ValueError("Test error")
        
        # Open the circuit
        with pytest.raises(ValueError):
            breaker.call_sync(failing_func)
        
        assert breaker.state == CircuitState.OPEN
        assert breaker.failure_count == 1
        
        # Manual reset
        breaker.reset()
        
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.success_count == 0


class TestCircuitBreakerDecorator:
    """Test circuit breaker decorator."""
    
    @pytest.mark.asyncio
    async def test_decorator_successful_call(self):
        """Test decorator with successful call."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        @with_circuit_breaker(breaker)
        async def decorated_func():
            return "success"
        
        result = await decorated_func()
        
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_decorator_opens_circuit(self):
        """Test that decorator opens circuit on failures."""
        breaker = CircuitBreaker(failure_threshold=2)
        
        @with_circuit_breaker(breaker)
        async def decorated_func():
            raise ValueError("Test error")
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await decorated_func()
        
        assert breaker.state == CircuitState.OPEN
        
        # Next call should fail with CircuitBreakerError
        with pytest.raises(CircuitBreakerError):
            await decorated_func()


class TestCircuitBreakerConcurrency:
    """Test circuit breaker with concurrent calls."""
    
    @pytest.mark.asyncio
    async def test_concurrent_calls(self):
        """Test that circuit breaker handles concurrent calls correctly."""
        breaker = CircuitBreaker(failure_threshold=5)
        call_count = 0
        
        async def counting_func():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return call_count
        
        # Execute multiple concurrent calls
        results = await asyncio.gather(
            *[breaker.call(counting_func) for _ in range(10)]
        )
        
        assert len(results) == 10
        assert breaker.state == CircuitState.CLOSED
        assert call_count == 10
    
    @pytest.mark.asyncio
    async def test_concurrent_failures(self):
        """Test circuit breaker with concurrent failures."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        async def failing_func():
            await asyncio.sleep(0.01)
            raise ValueError("Test error")
        
        # Execute concurrent failing calls
        results = await asyncio.gather(
            *[breaker.call(failing_func) for _ in range(5)],
            return_exceptions=True
        )
        
        # All should fail
        assert all(isinstance(r, (ValueError, CircuitBreakerError)) for r in results)
        
        # Circuit should be open
        assert breaker.state == CircuitState.OPEN
