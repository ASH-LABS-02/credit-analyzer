"""
Property-Based Tests for Circuit Breaker Pattern

Tests universal properties of the circuit breaker implementation using
hypothesis for property-based testing.

Requirements: 15.2
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings, assume
from hypothesis import HealthCheck

from app.core.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerError
)


# Feature: intelli-credit-platform, Property 31: External API Retry Logic
# (Circuit breaker complements retry logic for resilience)


@given(
    failure_threshold=st.integers(min_value=1, max_value=10),
    timeout=st.floats(min_value=0.1, max_value=10.0),
    success_threshold=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=100, deadline=None)
def test_circuit_breaker_initialization_property(
    failure_threshold, timeout, success_threshold
):
    """
    Property: Circuit breaker can be initialized with any valid parameters
    and starts in CLOSED state with zero failure count.
    
    **Validates: Requirements 15.2**
    """
    breaker = CircuitBreaker(
        failure_threshold=failure_threshold,
        timeout=timeout,
        success_threshold=success_threshold
    )
    
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0
    assert breaker.success_count == 0
    assert breaker.failure_threshold == failure_threshold
    assert breaker.timeout == timeout
    assert breaker.success_threshold == success_threshold


@given(
    failure_threshold=st.integers(min_value=1, max_value=10),
    num_successes=st.integers(min_value=1, max_value=20)
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_successful_calls_keep_circuit_closed_property(
    failure_threshold, num_successes
):
    """
    Property: Any number of successful calls should keep the circuit in CLOSED state
    and maintain zero failure count.
    
    **Validates: Requirements 15.2**
    """
    breaker = CircuitBreaker(failure_threshold=failure_threshold)
    
    async def successful_func():
        return "success"
    
    # Execute multiple successful calls
    for _ in range(num_successes):
        result = await breaker.call(successful_func)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0


@given(
    failure_threshold=st.integers(min_value=1, max_value=10),
    num_failures=st.integers(min_value=1, max_value=20)
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_failures_open_circuit_at_threshold_property(
    failure_threshold, num_failures
):
    """
    Property: Circuit should open when failure count reaches threshold,
    and remain open for additional failures.
    
    **Validates: Requirements 15.2**
    """
    breaker = CircuitBreaker(failure_threshold=failure_threshold)
    
    async def failing_func():
        raise ValueError("Test error")
    
    # Execute failures
    for i in range(num_failures):
        try:
            await breaker.call(failing_func)
        except (ValueError, CircuitBreakerError):
            pass
        
        # Check state based on failure count
        if i + 1 < failure_threshold:
            assert breaker.state == CircuitState.CLOSED
            assert breaker.failure_count == i + 1
        else:
            assert breaker.state == CircuitState.OPEN
            # Failure count may vary in OPEN state due to immediate failures


@given(
    failure_threshold=st.integers(min_value=2, max_value=10),
    failures_before_success=st.integers(min_value=1, max_value=9)
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_success_resets_failure_count_property(
    failure_threshold, failures_before_success
):
    """
    Property: A successful call in CLOSED state should reset the failure count to zero,
    preventing the circuit from opening.
    
    **Validates: Requirements 15.2**
    """
    assume(failures_before_success < failure_threshold)
    
    breaker = CircuitBreaker(failure_threshold=failure_threshold)
    
    async def failing_func():
        raise ValueError("Test error")
    
    async def successful_func():
        return "success"
    
    # Accumulate some failures (but not enough to open circuit)
    for _ in range(failures_before_success):
        try:
            await breaker.call(failing_func)
        except ValueError:
            pass
    
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == failures_before_success
    
    # Success should reset failure count
    result = await breaker.call(successful_func)
    assert result == "success"
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0


@given(
    failure_threshold=st.integers(min_value=1, max_value=5),
    timeout=st.floats(min_value=0.05, max_value=0.2)
)
@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_circuit_transitions_to_half_open_after_timeout_property(
    failure_threshold, timeout
):
    """
    Property: After timeout period, circuit should transition from OPEN to HALF_OPEN
    on the next call attempt.
    
    **Validates: Requirements 15.2**
    """
    breaker = CircuitBreaker(failure_threshold=failure_threshold, timeout=timeout)
    
    async def failing_func():
        raise ValueError("Test error")
    
    async def successful_func():
        return "success"
    
    # Open the circuit
    for _ in range(failure_threshold):
        try:
            await breaker.call(failing_func)
        except ValueError:
            pass
    
    assert breaker.state == CircuitState.OPEN
    
    # Wait for timeout
    await asyncio.sleep(timeout + 0.05)
    
    # Next successful call should transition through HALF_OPEN to CLOSED
    result = await breaker.call(successful_func)
    assert result == "success"
    assert breaker.state == CircuitState.CLOSED


@given(
    failure_threshold=st.integers(min_value=1, max_value=5),
    success_threshold=st.integers(min_value=1, max_value=5),
    num_successes=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_half_open_requires_success_threshold_property(
    failure_threshold, success_threshold, num_successes
):
    """
    Property: Circuit should close from HALF_OPEN only after success_threshold
    successful calls are made.
    
    **Validates: Requirements 15.2**
    """
    breaker = CircuitBreaker(
        failure_threshold=failure_threshold,
        timeout=0.05,
        success_threshold=success_threshold
    )
    
    async def failing_func():
        raise ValueError("Test error")
    
    async def successful_func():
        return "success"
    
    # Open the circuit
    for _ in range(failure_threshold):
        try:
            await breaker.call(failing_func)
        except ValueError:
            pass
    
    # Wait for timeout
    await asyncio.sleep(0.1)
    
    # Make successful calls
    for i in range(num_successes):
        result = await breaker.call(successful_func)
        assert result == "success"
        
        # Check state based on success count
        if i + 1 < success_threshold:
            assert breaker.state == CircuitState.HALF_OPEN
        else:
            assert breaker.state == CircuitState.CLOSED
            # Once closed, should stay closed
            break


@given(
    failure_threshold=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_failure_in_half_open_reopens_circuit_property(
    failure_threshold
):
    """
    Property: Any failure in HALF_OPEN state should immediately reopen the circuit.
    
    **Validates: Requirements 15.2**
    """
    breaker = CircuitBreaker(
        failure_threshold=failure_threshold,
        timeout=0.05
    )
    
    async def failing_func():
        raise ValueError("Test error")
    
    # Open the circuit
    for _ in range(failure_threshold):
        try:
            await breaker.call(failing_func)
        except ValueError:
            pass
    
    assert breaker.state == CircuitState.OPEN
    
    # Wait for timeout
    await asyncio.sleep(0.1)
    
    # Failure should reopen circuit
    try:
        await breaker.call(failing_func)
    except ValueError:
        pass
    
    assert breaker.state == CircuitState.OPEN


@given(
    failure_threshold=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=100, deadline=None)
def test_manual_reset_always_closes_circuit_property(failure_threshold):
    """
    Property: Manual reset should always transition circuit to CLOSED state
    and reset all counters, regardless of current state.
    
    **Validates: Requirements 15.2**
    """
    breaker = CircuitBreaker(failure_threshold=failure_threshold)
    
    def failing_func():
        raise ValueError("Test error")
    
    # Open the circuit
    for _ in range(failure_threshold):
        try:
            breaker.call_sync(failing_func)
        except ValueError:
            pass
    
    # Circuit should be open
    assert breaker.state == CircuitState.OPEN
    
    # Manual reset
    breaker.reset()
    
    # Should be closed with reset counters
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0
    assert breaker.success_count == 0


@given(
    failure_threshold=st.integers(min_value=1, max_value=10),
    timeout=st.floats(min_value=0.1, max_value=5.0)
)
@settings(max_examples=100, deadline=None)
def test_circuit_breaker_error_raised_when_open_property(
    failure_threshold, timeout
):
    """
    Property: When circuit is OPEN and timeout has not elapsed,
    all calls should fail immediately with CircuitBreakerError.
    
    **Validates: Requirements 15.2**
    """
    breaker = CircuitBreaker(
        failure_threshold=failure_threshold,
        timeout=timeout
    )
    
    def failing_func():
        raise ValueError("Test error")
    
    def any_func():
        return "should not execute"
    
    # Open the circuit
    for _ in range(failure_threshold):
        try:
            breaker.call_sync(failing_func)
        except ValueError:
            pass
    
    assert breaker.state == CircuitState.OPEN
    
    # Next call should fail with CircuitBreakerError
    with pytest.raises(CircuitBreakerError):
        breaker.call_sync(any_func)


@given(
    failure_threshold=st.integers(min_value=1, max_value=10),
    num_calls=st.integers(min_value=1, max_value=20)
)
@settings(max_examples=100, deadline=None)
def test_sync_and_async_behave_consistently_property(
    failure_threshold, num_calls
):
    """
    Property: Synchronous and asynchronous circuit breaker calls should
    behave consistently in terms of state transitions.
    
    **Validates: Requirements 15.2**
    """
    breaker_sync = CircuitBreaker(failure_threshold=failure_threshold)
    breaker_async = CircuitBreaker(failure_threshold=failure_threshold)
    
    def failing_func_sync():
        raise ValueError("Test error")
    
    async def failing_func_async():
        raise ValueError("Test error")
    
    # Execute same number of failures on both
    for i in range(min(num_calls, failure_threshold)):
        try:
            breaker_sync.call_sync(failing_func_sync)
        except ValueError:
            pass
        
        try:
            asyncio.run(breaker_async.call(failing_func_async))
        except ValueError:
            pass
    
    # Both should be in same state
    assert breaker_sync.state == breaker_async.state
    
    # If we reached threshold, both should be OPEN
    if num_calls >= failure_threshold:
        assert breaker_sync.state == CircuitState.OPEN
        assert breaker_async.state == CircuitState.OPEN


@given(
    failure_threshold=st.integers(min_value=1, max_value=10),
    timeout=st.floats(min_value=0.1, max_value=10.0),
    success_threshold=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=100, deadline=None)
def test_state_invariants_property(
    failure_threshold, timeout, success_threshold
):
    """
    Property: Circuit breaker state invariants should always hold:
    - State is always one of CLOSED, OPEN, or HALF_OPEN
    - Failure count is non-negative
    - Success count is non-negative
    - In CLOSED state, success_count is 0
    - In OPEN state, success_count is 0
    
    **Validates: Requirements 15.2**
    """
    breaker = CircuitBreaker(
        failure_threshold=failure_threshold,
        timeout=timeout,
        success_threshold=success_threshold
    )
    
    def check_invariants():
        # State is valid
        assert breaker.state in [CircuitState.CLOSED, CircuitState.OPEN, CircuitState.HALF_OPEN]
        
        # Counts are non-negative
        assert breaker.failure_count >= 0
        assert breaker.success_count >= 0
        
        # State-specific invariants
        if breaker.state == CircuitState.CLOSED:
            assert breaker.success_count == 0
        elif breaker.state == CircuitState.OPEN:
            assert breaker.success_count == 0
    
    # Check initial state
    check_invariants()
    
    def failing_func():
        raise ValueError("Test error")
    
    def successful_func():
        return "success"
    
    # Execute some operations and check invariants
    for _ in range(failure_threshold):
        try:
            breaker.call_sync(failing_func)
        except ValueError:
            pass
        check_invariants()
    
    # Reset and check
    breaker.reset()
    check_invariants()
    
    # Execute successful call
    breaker.call_sync(successful_func)
    check_invariants()
