"""
Retry Logic with Exponential Backoff

This module provides utilities for retrying failed operations with exponential backoff.
It's designed to handle transient failures in external API calls (OpenAI, web search, etc.)
with configurable retry parameters.

Requirements: 15.2
"""

import asyncio
import logging
from typing import Callable, TypeVar, Any, Optional, Type, Tuple
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryConfig:
    """
    Configuration for retry behavior.
    
    Attributes:
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay in seconds before first retry (default: 1.0)
        max_delay: Maximum delay in seconds between retries (default: 60.0)
        exponential_base: Base for exponential backoff calculation (default: 2)
        jitter: Whether to add random jitter to delays (default: True)
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay in seconds before first retry
            max_delay: Maximum delay in seconds between retries
            exponential_base: Base for exponential backoff calculation
            jitter: Whether to add random jitter to delays
        """
        if max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if base_delay <= 0:
            raise ValueError("base_delay must be positive")
        if max_delay < base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if exponential_base <= 1:
            raise ValueError("exponential_base must be > 1")
        
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


async def retry_with_backoff(
    func: Callable[..., T],
    *args: Any,
    config: Optional[RetryConfig] = None,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    **kwargs: Any
) -> T:
    """
    Retry an async function with exponential backoff.
    
    This function implements exponential backoff retry logic for handling transient
    failures in external API calls. The delay between retries increases exponentially
    with each attempt, up to a maximum delay.
    
    Args:
        func: Async function to retry
        *args: Positional arguments to pass to func
        config: Retry configuration (uses defaults if None)
        retryable_exceptions: Tuple of exception types to retry on (retries all if None)
        **kwargs: Keyword arguments to pass to func
    
    Returns:
        The result of the successful function call
    
    Raises:
        The last exception encountered if all retries are exhausted
    
    Requirements: 15.2
    
    Example:
        >>> async def api_call():
        ...     return await client.get_data()
        >>> result = await retry_with_backoff(api_call, config=RetryConfig(max_retries=5))
    """
    if config is None:
        config = RetryConfig()
    
    last_exception = None
    
    for attempt in range(config.max_retries + 1):  # +1 for initial attempt
        try:
            # Attempt the function call
            result = await func(*args, **kwargs)
            
            # Log success if this was a retry
            if attempt > 0:
                logger.info(
                    f"Function {func.__name__} succeeded on attempt {attempt + 1}"
                )
            
            return result
        
        except Exception as e:
            last_exception = e
            
            # Check if this exception type should be retried
            if retryable_exceptions and not isinstance(e, retryable_exceptions):
                logger.warning(
                    f"Non-retryable exception in {func.__name__}: {type(e).__name__}: {str(e)}"
                )
                raise
            
            # If this was the last attempt, raise the exception
            if attempt == config.max_retries:
                logger.error(
                    f"Function {func.__name__} failed after {config.max_retries + 1} attempts. "
                    f"Last error: {type(e).__name__}: {str(e)}"
                )
                raise
            
            # Calculate delay for next retry
            delay = _calculate_delay(attempt, config)
            
            logger.warning(
                f"Function {func.__name__} failed on attempt {attempt + 1}/{config.max_retries + 1}. "
                f"Error: {type(e).__name__}: {str(e)}. "
                f"Retrying in {delay:.2f} seconds..."
            )
            
            # Wait before retrying
            await asyncio.sleep(delay)
    
    # This should never be reached, but just in case
    if last_exception:
        raise last_exception
    raise RuntimeError("Unexpected retry loop exit")


def _calculate_delay(attempt: int, config: RetryConfig) -> float:
    """
    Calculate the delay before the next retry attempt.
    
    Uses exponential backoff: delay = base_delay * (exponential_base ^ attempt)
    Optionally adds jitter to prevent thundering herd problem.
    
    Args:
        attempt: Current attempt number (0-indexed)
        config: Retry configuration
    
    Returns:
        Delay in seconds before next retry
    """
    import random
    
    # Calculate exponential delay
    delay = config.base_delay * (config.exponential_base ** attempt)
    
    # Cap at max_delay
    delay = min(delay, config.max_delay)
    
    # Add jitter if enabled (random value between 0 and delay)
    if config.jitter:
        delay = delay * (0.5 + random.random() * 0.5)  # 50-100% of calculated delay
    
    return delay


def with_retry(
    config: Optional[RetryConfig] = None,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None
):
    """
    Decorator for adding retry logic with exponential backoff to async functions.
    
    This decorator wraps an async function with retry logic, making it easier to
    apply retry behavior to multiple functions without repeating code.
    
    Args:
        config: Retry configuration (uses defaults if None)
        retryable_exceptions: Tuple of exception types to retry on (retries all if None)
    
    Returns:
        Decorated function with retry logic
    
    Requirements: 15.2
    
    Example:
        >>> @with_retry(config=RetryConfig(max_retries=5))
        ... async def fetch_data():
        ...     return await api.get_data()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await retry_with_backoff(
                func,
                *args,
                config=config,
                retryable_exceptions=retryable_exceptions,
                **kwargs
            )
        return wrapper
    return decorator


# Synchronous version for non-async functions
def retry_with_backoff_sync(
    func: Callable[..., T],
    *args: Any,
    config: Optional[RetryConfig] = None,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    **kwargs: Any
) -> T:
    """
    Retry a synchronous function with exponential backoff.
    
    This is the synchronous version of retry_with_backoff for use with
    non-async functions.
    
    Args:
        func: Synchronous function to retry
        *args: Positional arguments to pass to func
        config: Retry configuration (uses defaults if None)
        retryable_exceptions: Tuple of exception types to retry on (retries all if None)
        **kwargs: Keyword arguments to pass to func
    
    Returns:
        The result of the successful function call
    
    Raises:
        The last exception encountered if all retries are exhausted
    
    Requirements: 15.2
    """
    import time
    import random
    
    if config is None:
        config = RetryConfig()
    
    last_exception = None
    func_name = getattr(func, '__name__', 'unknown_function')
    
    for attempt in range(config.max_retries + 1):
        try:
            result = func(*args, **kwargs)
            
            if attempt > 0:
                logger.info(
                    f"Function {func_name} succeeded on attempt {attempt + 1}"
                )
            
            return result
        
        except Exception as e:
            last_exception = e
            
            if retryable_exceptions and not isinstance(e, retryable_exceptions):
                logger.warning(
                    f"Non-retryable exception in {func_name}: {type(e).__name__}: {str(e)}"
                )
                raise
            
            if attempt == config.max_retries:
                logger.error(
                    f"Function {func_name} failed after {config.max_retries + 1} attempts. "
                    f"Last error: {type(e).__name__}: {str(e)}"
                )
                raise
            
            # Calculate delay
            delay = config.base_delay * (config.exponential_base ** attempt)
            delay = min(delay, config.max_delay)
            
            if config.jitter:
                delay = delay * (0.5 + random.random() * 0.5)
            
            logger.warning(
                f"Function {func_name} failed on attempt {attempt + 1}/{config.max_retries + 1}. "
                f"Error: {type(e).__name__}: {str(e)}. "
                f"Retrying in {delay:.2f} seconds..."
            )
            
            time.sleep(delay)
    
    if last_exception:
        raise last_exception
    raise RuntimeError("Unexpected retry loop exit")
