"""
Property-Based Tests for Retry Logic with Exponential Backoff

Tests universal properties of the retry mechanism to ensure it correctly handles
transient failures with exponential backoff across all valid inputs.

**Validates: Requirements 15.2**
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import AsyncMock
from typing import List

from app.core.retry import (
    retry_with_backoff,
    RetryConfig,
    _calculate_delay
)


# Feature: intelli-credit-platform, Property 31: External API Retry Logic
@given(
    max_retries=st.integers(min_value=0, max_value=5),
    base_delay=st.floats(min_value=0.001, max_value=0.01),
    exponential_base=st.floats(min_value=1.1, max_value=2.0),
    num_failures=st.integers(min_value=0, max_value=8)
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_retry_attempts_with_exponential_backoff(
    max_retries: int,
    base_delay: float,
    exponential_base: float,
    num_failures: int
):
    """
    **Validates: Requirements 15.2**
    
    Property 31: External API Retry Logic
    
    For any failed external API call, the system should implement retry logic
    with exponential backoff, attempting the request multiple times before
    reporting failure.
    
    This property verifies:
    1. The function is called at most (max_retries + 1) times
    2. If failures < max_retries, the function eventually succeeds
    3. If failures > max_retries, the function raises the last exception
    4. Delays between retries follow exponential backoff pattern
    """
    # Track call count and delays
    call_count = 0
    delays_observed = []
    start_times = []
    
    async def failing_api_call():
        nonlocal call_count
        start_times.append(asyncio.get_event_loop().time())
        call_count += 1
        
        if call_count <= num_failures:
            raise Exception(f"Transient failure {call_count}")
        return "success"
    
    config = RetryConfig(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=1.0,  # Keep delays short for testing
        exponential_base=exponential_base,
        jitter=False  # Disable jitter for predictable testing
    )
    
    # Test the retry logic
    if num_failures <= max_retries:
        # Should eventually succeed
        result = await retry_with_backoff(failing_api_call, config=config)
        assert result == "success"
        assert call_count == num_failures + 1
    else:
        # Should exhaust retries and raise exception
        with pytest.raises(Exception, match="Transient failure"):
            await retry_with_backoff(failing_api_call, config=config)
        assert call_count == max_retries + 1
    
    # Verify exponential backoff pattern in delays
    if len(start_times) > 1:
        actual_delays = [
            start_times[i] - start_times[i-1]
            for i in range(1, len(start_times))
        ]
        
        for i, delay in enumerate(actual_delays):
            expected_delay = _calculate_delay(i, config)
            # Allow some tolerance for timing variations (±20%)
            assert delay >= expected_delay * 0.8, \
                f"Delay {delay} is less than expected {expected_delay}"


# Feature: intelli-credit-platform, Property 31: External API Retry Logic
@given(
    max_retries=st.integers(min_value=1, max_value=5),
    base_delay=st.floats(min_value=0.001, max_value=0.1),
    max_delay=st.floats(min_value=0.5, max_value=2.0),
    exponential_base=st.floats(min_value=1.5, max_value=3.0)
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_delay_never_exceeds_max_delay(
    max_retries: int,
    base_delay: float,
    max_delay: float,
    exponential_base: float
):
    """
    **Validates: Requirements 15.2**
    
    Property 31: External API Retry Logic (Max Delay Cap)
    
    For any retry configuration, the delay between retries should never
    exceed the configured max_delay, even with exponential growth.
    """
    assume(max_delay >= base_delay)
    
    config = RetryConfig(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        jitter=False
    )
    
    # Test all retry attempts
    for attempt in range(max_retries):
        delay = _calculate_delay(attempt, config)
        assert delay <= max_delay, \
            f"Delay {delay} exceeds max_delay {max_delay} at attempt {attempt}"


# Feature: intelli-credit-platform, Property 31: External API Retry Logic
@given(
    max_retries=st.integers(min_value=1, max_value=5),
    base_delay=st.floats(min_value=0.001, max_value=0.1),
    exponential_base=st.floats(min_value=1.5, max_value=3.0)
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_exponential_growth_pattern(
    max_retries: int,
    base_delay: float,
    exponential_base: float
):
    """
    **Validates: Requirements 15.2**
    
    Property 31: External API Retry Logic (Exponential Growth)
    
    For any retry configuration, delays should grow exponentially according
    to the formula: delay = base_delay * (exponential_base ^ attempt)
    """
    config = RetryConfig(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=100.0,  # High enough to not cap
        exponential_base=exponential_base,
        jitter=False
    )
    
    # Verify exponential growth for first few attempts
    for attempt in range(min(max_retries, 3)):
        delay = _calculate_delay(attempt, config)
        expected_delay = base_delay * (exponential_base ** attempt)
        
        # Should match the exponential formula (within floating point precision)
        assert abs(delay - expected_delay) < 0.001, \
            f"Delay {delay} doesn't match expected exponential {expected_delay}"


# Feature: intelli-credit-platform, Property 31: External API Retry Logic
@given(
    max_retries=st.integers(min_value=0, max_value=5),
    success_on_attempt=st.integers(min_value=1, max_value=6)
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_success_stops_retrying(
    max_retries: int,
    success_on_attempt: int
):
    """
    **Validates: Requirements 15.2**
    
    Property 31: External API Retry Logic (Success Termination)
    
    For any retry configuration, once the function succeeds, no further
    retry attempts should be made, regardless of max_retries.
    """
    call_count = 0
    
    async def api_call_succeeds_eventually():
        nonlocal call_count
        call_count += 1
        
        if call_count < success_on_attempt:
            raise Exception(f"Failure {call_count}")
        return f"success on attempt {call_count}"
    
    config = RetryConfig(
        max_retries=max_retries,
        base_delay=0.001,  # Very short delay for testing
        jitter=False
    )
    
    if success_on_attempt <= max_retries + 1:
        # Should succeed
        result = await retry_with_backoff(api_call_succeeds_eventually, config=config)
        assert "success" in result
        assert call_count == success_on_attempt
    else:
        # Should fail after exhausting retries
        with pytest.raises(Exception):
            await retry_with_backoff(api_call_succeeds_eventually, config=config)
        assert call_count == max_retries + 1


# Feature: intelli-credit-platform, Property 31: External API Retry Logic
@given(
    max_retries=st.integers(min_value=1, max_value=5),
    args_list=st.lists(st.integers(), min_size=0, max_size=3),
    kwargs_dict=st.dictionaries(
        st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        st.integers(),
        min_size=0,
        max_size=3
    )
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_args_kwargs_preserved_across_retries(
    max_retries: int,
    args_list: List[int],
    kwargs_dict: dict
):
    """
    **Validates: Requirements 15.2**
    
    Property 31: External API Retry Logic (Argument Preservation)
    
    For any function arguments and keyword arguments, they should be
    correctly passed to the function on every retry attempt.
    """
    call_count = 0
    received_args = []
    received_kwargs = []
    
    async def api_call_with_args(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        received_args.append(args)
        received_kwargs.append(kwargs)
        
        if call_count < 2:
            raise Exception("First attempt fails")
        return "success"
    
    config = RetryConfig(
        max_retries=max_retries,
        base_delay=0.001,  # Very short delay for testing
        jitter=False
    )
    
    result = await retry_with_backoff(
        api_call_with_args,
        *args_list,
        config=config,
        **kwargs_dict
    )
    
    assert result == "success"
    assert call_count == 2
    
    # Verify args and kwargs were the same on both attempts
    assert received_args[0] == tuple(args_list)
    assert received_args[1] == tuple(args_list)
    assert received_kwargs[0] == kwargs_dict
    assert received_kwargs[1] == kwargs_dict


# Feature: intelli-credit-platform, Property 31: External API Retry Logic
@given(
    max_retries=st.integers(min_value=1, max_value=5),
    base_delay=st.floats(min_value=0.001, max_value=0.05)
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_jitter_adds_randomness(
    max_retries: int,
    base_delay: float
):
    """
    **Validates: Requirements 15.2**
    
    Property 31: External API Retry Logic (Jitter)
    
    For any retry configuration with jitter enabled, delays should have
    random variation to prevent thundering herd problem, while staying
    within the expected range (50-100% of calculated delay).
    """
    config_with_jitter = RetryConfig(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=10.0,
        exponential_base=2.0,
        jitter=True
    )
    
    config_without_jitter = RetryConfig(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=10.0,
        exponential_base=2.0,
        jitter=False
    )
    
    # Calculate delays multiple times with jitter
    delays_with_jitter = [
        _calculate_delay(0, config_with_jitter)
        for _ in range(20)
    ]
    
    # Calculate delay without jitter
    delay_without_jitter = _calculate_delay(0, config_without_jitter)
    
    # With jitter, delays should vary
    unique_delays = set(delays_with_jitter)
    assert len(unique_delays) > 1, "Jitter should produce varying delays"
    
    # All jittered delays should be in range [50%, 100%] of base delay
    for delay in delays_with_jitter:
        assert delay >= delay_without_jitter * 0.5, \
            f"Jittered delay {delay} is below 50% of base {delay_without_jitter}"
        assert delay <= delay_without_jitter, \
            f"Jittered delay {delay} exceeds base {delay_without_jitter}"


# Feature: intelli-credit-platform, Property 31: External API Retry Logic
@given(
    max_retries=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_property_last_exception_is_raised(
    max_retries: int
):
    """
    **Validates: Requirements 15.2**
    
    Property 31: External API Retry Logic (Exception Propagation)
    
    For any retry configuration, when all retries are exhausted, the last
    exception encountered should be raised to the caller.
    """
    call_count = 0
    
    async def always_failing_api_call():
        nonlocal call_count
        call_count += 1
        raise ValueError(f"Failure number {call_count}")
    
    config = RetryConfig(
        max_retries=max_retries,
        base_delay=0.001,  # Very short delay for testing
        jitter=False
    )
    
    with pytest.raises(ValueError) as exc_info:
        await retry_with_backoff(always_failing_api_call, config=config)
    
    # Should raise the last exception
    assert f"Failure number {max_retries + 1}" in str(exc_info.value)
    assert call_count == max_retries + 1
