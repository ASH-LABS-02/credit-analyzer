"""
Unit Tests for Retry Logic with Exponential Backoff

Tests the retry utility functions for handling transient failures in external API calls.

Requirements: 15.2
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from typing import Any

from app.core.retry import (
    retry_with_backoff,
    retry_with_backoff_sync,
    with_retry,
    RetryConfig,
    _calculate_delay
)


class TestRetryConfig:
    """Test RetryConfig validation and initialization."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = RetryConfig(
            max_retries=5,
            base_delay=2.0,
            max_delay=120.0,
            exponential_base=3.0,
            jitter=False
        )
        assert config.max_retries == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 120.0
        assert config.exponential_base == 3.0
        assert config.jitter is False
    
    def test_invalid_max_retries(self):
        """Test that negative max_retries raises ValueError."""
        with pytest.raises(ValueError, match="max_retries must be non-negative"):
            RetryConfig(max_retries=-1)
    
    def test_invalid_base_delay(self):
        """Test that non-positive base_delay raises ValueError."""
        with pytest.raises(ValueError, match="base_delay must be positive"):
            RetryConfig(base_delay=0)
        
        with pytest.raises(ValueError, match="base_delay must be positive"):
            RetryConfig(base_delay=-1.0)
    
    def test_invalid_max_delay(self):
        """Test that max_delay < base_delay raises ValueError."""
        with pytest.raises(ValueError, match="max_delay must be >= base_delay"):
            RetryConfig(base_delay=10.0, max_delay=5.0)
    
    def test_invalid_exponential_base(self):
        """Test that exponential_base <= 1 raises ValueError."""
        with pytest.raises(ValueError, match="exponential_base must be > 1"):
            RetryConfig(exponential_base=1.0)
        
        with pytest.raises(ValueError, match="exponential_base must be > 1"):
            RetryConfig(exponential_base=0.5)


class TestCalculateDelay:
    """Test delay calculation for exponential backoff."""
    
    def test_exponential_growth(self):
        """Test that delay grows exponentially."""
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, jitter=False)
        
        delay_0 = _calculate_delay(0, config)
        delay_1 = _calculate_delay(1, config)
        delay_2 = _calculate_delay(2, config)
        
        assert delay_0 == 1.0  # 1.0 * 2^0 = 1.0
        assert delay_1 == 2.0  # 1.0 * 2^1 = 2.0
        assert delay_2 == 4.0  # 1.0 * 2^2 = 4.0
    
    def test_max_delay_cap(self):
        """Test that delay is capped at max_delay."""
        config = RetryConfig(base_delay=1.0, max_delay=5.0, exponential_base=2.0, jitter=False)
        
        delay_10 = _calculate_delay(10, config)  # Would be 1024 without cap
        assert delay_10 == 5.0
    
    def test_jitter_range(self):
        """Test that jitter produces delays in expected range."""
        config = RetryConfig(base_delay=10.0, exponential_base=2.0, jitter=True)
        
        # Run multiple times to test randomness
        delays = [_calculate_delay(0, config) for _ in range(100)]
        
        # With jitter, delays should be between 50% and 100% of base delay
        assert all(5.0 <= d <= 10.0 for d in delays)
        
        # Should have some variation (not all the same)
        assert len(set(delays)) > 1
    
    def test_no_jitter(self):
        """Test that delays are deterministic without jitter."""
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, jitter=False)
        
        delays = [_calculate_delay(0, config) for _ in range(10)]
        
        # All delays should be identical
        assert all(d == 1.0 for d in delays)


@pytest.mark.asyncio
class TestRetryWithBackoff:
    """Test async retry_with_backoff function."""
    
    async def test_success_on_first_attempt(self):
        """Test that successful function returns immediately."""
        mock_func = AsyncMock(return_value="success")
        
        result = await retry_with_backoff(mock_func)
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    async def test_success_after_retries(self):
        """Test that function succeeds after some failures."""
        mock_func = AsyncMock(side_effect=[
            Exception("Failure 1"),
            Exception("Failure 2"),
            "success"
        ])
        
        config = RetryConfig(max_retries=3, base_delay=0.01)  # Fast retries for testing
        result = await retry_with_backoff(mock_func, config=config)
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    async def test_exhausted_retries(self):
        """Test that exception is raised after max retries."""
        mock_func = AsyncMock(side_effect=Exception("Persistent failure"))
        
        config = RetryConfig(max_retries=2, base_delay=0.01)
        
        with pytest.raises(Exception, match="Persistent failure"):
            await retry_with_backoff(mock_func, config=config)
        
        assert mock_func.call_count == 3  # Initial + 2 retries
    
    async def test_with_args_and_kwargs(self):
        """Test that args and kwargs are passed correctly."""
        mock_func = AsyncMock(return_value="success")
        
        result = await retry_with_backoff(
            mock_func,
            "arg1",
            "arg2",
            kwarg1="value1",
            kwarg2="value2"
        )
        
        assert result == "success"
        mock_func.assert_called_once_with("arg1", "arg2", kwarg1="value1", kwarg2="value2")
    
    async def test_retryable_exceptions_filter(self):
        """Test that only specified exceptions are retried."""
        class RetryableError(Exception):
            pass
        
        class NonRetryableError(Exception):
            pass
        
        mock_func = AsyncMock(side_effect=NonRetryableError("Should not retry"))
        
        config = RetryConfig(max_retries=3, base_delay=0.01)
        
        with pytest.raises(NonRetryableError, match="Should not retry"):
            await retry_with_backoff(
                mock_func,
                config=config,
                retryable_exceptions=(RetryableError,)
            )
        
        # Should fail immediately without retries
        assert mock_func.call_count == 1
    
    async def test_retryable_exceptions_success(self):
        """Test that specified exceptions are retried."""
        class RetryableError(Exception):
            pass
        
        mock_func = AsyncMock(side_effect=[
            RetryableError("Retry this"),
            "success"
        ])
        
        config = RetryConfig(max_retries=3, base_delay=0.01)
        
        result = await retry_with_backoff(
            mock_func,
            config=config,
            retryable_exceptions=(RetryableError,)
        )
        
        assert result == "success"
        assert mock_func.call_count == 2
    
    async def test_zero_retries(self):
        """Test behavior with max_retries=0."""
        mock_func = AsyncMock(side_effect=Exception("Failure"))
        
        config = RetryConfig(max_retries=0, base_delay=0.01)
        
        with pytest.raises(Exception, match="Failure"):
            await retry_with_backoff(mock_func, config=config)
        
        # Should only try once
        assert mock_func.call_count == 1


class TestRetryWithBackoffSync:
    """Test synchronous retry_with_backoff_sync function."""
    
    def test_success_on_first_attempt(self):
        """Test that successful function returns immediately."""
        mock_func = Mock(return_value="success")
        
        result = retry_with_backoff_sync(mock_func)
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_success_after_retries(self):
        """Test that function succeeds after some failures."""
        mock_func = Mock(side_effect=[
            Exception("Failure 1"),
            Exception("Failure 2"),
            "success"
        ])
        
        config = RetryConfig(max_retries=3, base_delay=0.01)
        result = retry_with_backoff_sync(mock_func, config=config)
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    def test_exhausted_retries(self):
        """Test that exception is raised after max retries."""
        mock_func = Mock(side_effect=Exception("Persistent failure"))
        
        config = RetryConfig(max_retries=2, base_delay=0.01)
        
        with pytest.raises(Exception, match="Persistent failure"):
            retry_with_backoff_sync(mock_func, config=config)
        
        assert mock_func.call_count == 3


@pytest.mark.asyncio
class TestWithRetryDecorator:
    """Test with_retry decorator."""
    
    async def test_decorator_success(self):
        """Test that decorator works for successful function."""
        @with_retry()
        async def test_func():
            return "success"
        
        result = await test_func()
        assert result == "success"
    
    async def test_decorator_with_retries(self):
        """Test that decorator retries on failure."""
        call_count = 0
        
        @with_retry(config=RetryConfig(max_retries=3, base_delay=0.01))
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Retry me")
            return "success"
        
        result = await test_func()
        assert result == "success"
        assert call_count == 3
    
    async def test_decorator_with_custom_config(self):
        """Test decorator with custom configuration."""
        call_count = 0
        
        @with_retry(config=RetryConfig(max_retries=5, base_delay=0.01))
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 4:
                raise Exception("Keep retrying")
            return "success"
        
        result = await test_func()
        assert result == "success"
        assert call_count == 4
    
    async def test_decorator_with_retryable_exceptions(self):
        """Test decorator with exception filtering."""
        class RetryableError(Exception):
            pass
        
        class NonRetryableError(Exception):
            pass
        
        @with_retry(
            config=RetryConfig(max_retries=3, base_delay=0.01),
            retryable_exceptions=(RetryableError,)
        )
        async def test_func():
            raise NonRetryableError("Should not retry")
        
        with pytest.raises(NonRetryableError, match="Should not retry"):
            await test_func()
    
    async def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function name and docstring."""
        @with_retry()
        async def test_func():
            """Test function docstring."""
            return "success"
        
        assert test_func.__name__ == "test_func"
        assert test_func.__doc__ == "Test function docstring."


@pytest.mark.asyncio
class TestRetryIntegration:
    """Integration tests for retry logic."""
    
    async def test_realistic_api_call_scenario(self):
        """Test retry logic with realistic API call simulation."""
        call_count = 0
        
        async def simulated_api_call():
            nonlocal call_count
            call_count += 1
            
            # Simulate transient failures
            if call_count == 1:
                raise ConnectionError("Network timeout")
            elif call_count == 2:
                raise Exception("Rate limit exceeded")
            else:
                return {"status": "success", "data": "result"}
        
        config = RetryConfig(
            max_retries=3,
            base_delay=0.01,
            exponential_base=2.0,
            jitter=True
        )
        
        result = await retry_with_backoff(simulated_api_call, config=config)
        
        assert result == {"status": "success", "data": "result"}
        assert call_count == 3
    
    async def test_concurrent_retries(self):
        """Test that multiple concurrent retry operations work correctly."""
        async def flaky_operation(operation_id: int):
            # Fail once, then succeed
            if not hasattr(flaky_operation, 'attempts'):
                flaky_operation.attempts = {}
            
            if operation_id not in flaky_operation.attempts:
                flaky_operation.attempts[operation_id] = 0
            
            flaky_operation.attempts[operation_id] += 1
            
            if flaky_operation.attempts[operation_id] == 1:
                raise Exception(f"Failure for operation {operation_id}")
            
            return f"Success {operation_id}"
        
        config = RetryConfig(max_retries=2, base_delay=0.01)
        
        # Run 5 operations concurrently
        tasks = [
            retry_with_backoff(flaky_operation, i, config=config)
            for i in range(5)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert all(f"Success {i}" in results for i in range(5))
