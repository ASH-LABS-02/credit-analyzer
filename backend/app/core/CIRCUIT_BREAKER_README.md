# Circuit Breaker Pattern Implementation

## Overview

The circuit breaker pattern prevents cascading failures when external services are down. It monitors failures and "opens the circuit" when a threshold is reached, preventing further calls until the service recovers.

**Requirements:** 15.2

## How It Works

The circuit breaker has three states:

### 1. CLOSED (Normal Operation)
- All requests pass through to the external service
- Failures are counted
- When failure count reaches `failure_threshold`, circuit opens

### 2. OPEN (Service Down)
- All requests fail immediately with `CircuitBreakerError`
- No calls are made to the external service
- After `timeout` period, circuit transitions to HALF_OPEN

### 3. HALF_OPEN (Testing Recovery)
- Limited requests are allowed to test if service recovered
- If request succeeds, increment success count
- When success count reaches `success_threshold`, circuit closes
- If request fails, circuit immediately reopens

## State Transitions

```
CLOSED --[failures >= threshold]--> OPEN
OPEN --[timeout elapsed]--> HALF_OPEN
HALF_OPEN --[success]--> CLOSED
HALF_OPEN --[failure]--> OPEN
```

## Usage

### Basic Usage

```python
from app.core.circuit_breaker import CircuitBreaker

# Create circuit breaker
breaker = CircuitBreaker(
    failure_threshold=5,  # Open after 5 failures
    timeout=60.0,         # Wait 60 seconds before retry
    success_threshold=2,  # Require 2 successes to close
    name="MyService"      # Name for logging
)

# Use with async function
async def call_external_service():
    return await breaker.call(my_async_function, arg1, arg2)

# Use with sync function
def call_external_service_sync():
    return breaker.call_sync(my_sync_function, arg1, arg2)
```

### Decorator Usage

```python
from app.core.circuit_breaker import with_circuit_breaker

breaker = CircuitBreaker(failure_threshold=3, timeout=30.0)

@with_circuit_breaker(breaker)
async def fetch_data():
    # Your external service call
    return await api.get_data()
```

### Combining with Retry Logic

```python
from app.core.circuit_breaker import CircuitBreaker
from app.core.retry import retry_with_backoff, RetryConfig

breaker = CircuitBreaker(failure_threshold=5, timeout=60.0)

async def resilient_call():
    async def _call_with_retry():
        return await retry_with_backoff(
            external_service_call,
            config=RetryConfig(max_retries=3)
        )
    
    # Circuit breaker wraps retry logic
    return await breaker.call(_call_with_retry)
```

## Configuration Parameters

### `failure_threshold` (int)
- Number of consecutive failures before opening circuit
- Default: 5
- Recommendation: Set based on expected error rate
  - High-reliability services: 3-5
  - Less critical services: 5-10

### `timeout` (float)
- Seconds to wait before attempting recovery (OPEN → HALF_OPEN)
- Default: 60.0
- Recommendation: Set based on service recovery time
  - Fast-recovering services: 30-60 seconds
  - Slow-recovering services: 120-300 seconds

### `success_threshold` (int)
- Number of successes required in HALF_OPEN to close circuit
- Default: 1
- Recommendation:
  - Critical services: 2-3 (more confidence needed)
  - Less critical services: 1 (faster recovery)

### `name` (str)
- Optional name for logging and monitoring
- Default: "CircuitBreaker"
- Recommendation: Use descriptive names like "OpenAI-API", "Database", "WebSearch"

## Best Practices

### 1. Use Separate Circuit Breakers per Service

```python
# Good: Separate breakers isolate failures
openai_breaker = CircuitBreaker(name="OpenAI")
database_breaker = CircuitBreaker(name="Database")
web_search_breaker = CircuitBreaker(name="WebSearch")

# Bad: Single breaker affects all services
shared_breaker = CircuitBreaker(name="AllServices")
```

### 2. Implement Graceful Degradation

```python
async def get_data_with_fallback():
    try:
        return await breaker.call(fetch_live_data)
    except CircuitBreakerError:
        # Circuit is open, use cached data
        return get_cached_data()
```

### 3. Monitor Circuit Breaker State

```python
def log_circuit_metrics(breaker: CircuitBreaker):
    logger.info(
        f"Circuit {breaker.name}: "
        f"state={breaker.state.value}, "
        f"failures={breaker.failure_count}, "
        f"successes={breaker.success_count}"
    )
```

### 4. Configure Appropriately for Each Service

```python
# Fast, reliable service
fast_breaker = CircuitBreaker(
    failure_threshold=3,
    timeout=30.0,
    success_threshold=1
)

# Slow, less reliable service
slow_breaker = CircuitBreaker(
    failure_threshold=10,
    timeout=120.0,
    success_threshold=3
)
```

### 5. Combine with Retry Logic

```python
# Circuit breaker prevents cascading failures
# Retry logic handles transient errors
async def resilient_call():
    async def _with_retry():
        return await retry_with_backoff(service_call)
    return await breaker.call(_with_retry)
```

## Error Handling

### CircuitBreakerError

Raised when circuit is OPEN and a call is attempted:

```python
from app.core.circuit_breaker import CircuitBreakerError

try:
    result = await breaker.call(service_call)
except CircuitBreakerError as e:
    # Circuit is open, service unavailable
    logger.warning(f"Circuit breaker open: {e}")
    # Fall back to cached data or alternative
    result = get_fallback_data()
```

### Service Exceptions

Service exceptions are propagated normally:

```python
try:
    result = await breaker.call(service_call)
except CircuitBreakerError:
    # Circuit is open
    pass
except ValueError:
    # Service raised ValueError (circuit still tracks this failure)
    pass
```

## Testing

### Unit Tests

See `tests/test_circuit_breaker.py` for comprehensive unit tests covering:
- State transitions
- Failure tracking
- Timeout behavior
- Concurrent calls
- Decorator usage

### Property-Based Tests

See `tests/test_circuit_breaker_property.py` for property-based tests covering:
- Initialization with various parameters
- State invariants
- Threshold behavior
- Recovery logic

Run tests:
```bash
pytest tests/test_circuit_breaker*.py -v
```

## Examples

See `app/core/circuit_breaker_example.py` for detailed examples including:
- OpenAI API integration
- Web search integration
- Database queries
- Multiple service management
- Monitoring and metrics
- Graceful degradation

## Integration with Intelli-Credit Platform

The circuit breaker is used throughout the platform to protect against failures in:

1. **OpenAI API calls** (all AI agents)
   - Document intelligence
   - Financial analysis
   - Risk scoring
   - CAM generation

2. **Web search APIs** (Web Research Agent)
   - Company news gathering
   - Market intelligence

3. **External data sources**
   - Credit bureaus
   - Financial data providers
   - Industry databases

4. **Database operations**
   - Firestore queries
   - Firebase Storage

## Monitoring and Alerting

Monitor circuit breaker state in production:

```python
# Log state changes
logger.info(f"Circuit {breaker.name} opened after {breaker.failure_count} failures")

# Alert on frequent openings
if breaker.state == CircuitState.OPEN:
    alert_ops_team(f"Circuit {breaker.name} is open")

# Track metrics
metrics.gauge(f"circuit.{breaker.name}.state", breaker.state.value)
metrics.gauge(f"circuit.{breaker.name}.failures", breaker.failure_count)
```

## Manual Reset

For administrative purposes, circuits can be manually reset:

```python
# Reset circuit to CLOSED state
breaker.reset()

# Use with caution - only for testing or emergency recovery
```

## Performance Considerations

- Circuit breaker adds minimal overhead (< 1ms per call)
- State checks are fast (no I/O operations)
- Thread-safe for concurrent calls (uses asyncio.Lock)
- Memory footprint is negligible (< 1KB per breaker)

## References

- Design Document: `.kiro/specs/intelli-credit-platform/design.md`
- Requirements: Requirement 15.2 (Error Handling and Resilience)
- Related: `app/core/retry.py` (Retry logic with exponential backoff)
