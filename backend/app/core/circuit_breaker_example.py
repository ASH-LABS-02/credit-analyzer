"""
Circuit Breaker Usage Examples

This module demonstrates how to apply the circuit breaker pattern to external
service calls in the Intelli-Credit platform.

Requirements: 15.2
"""

from typing import Dict, Any
from openai import AsyncOpenAI
import httpx

from app.core.circuit_breaker import CircuitBreaker, with_circuit_breaker
from app.core.retry import retry_with_backoff, RetryConfig


# Example 1: Circuit breaker for OpenAI API calls
# ================================================

# Create a circuit breaker for OpenAI API
openai_breaker = CircuitBreaker(
    failure_threshold=5,  # Open after 5 failures
    timeout=60.0,  # Wait 60 seconds before retry
    success_threshold=2,  # Require 2 successes to close
    name="OpenAI-API"
)


async def call_openai_with_circuit_breaker(
    client: AsyncOpenAI,
    prompt: str,
    model: str = "gpt-4"
) -> str:
    """
    Call OpenAI API with circuit breaker protection.
    
    This prevents cascading failures when OpenAI API is down or rate-limited.
    """
    async def _make_call():
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    
    # Execute through circuit breaker
    return await openai_breaker.call(_make_call)


# Example 2: Circuit breaker with decorator
# ==========================================

web_search_breaker = CircuitBreaker(
    failure_threshold=3,
    timeout=30.0,
    name="Web-Search-API"
)


@with_circuit_breaker(web_search_breaker)
async def search_web(query: str) -> Dict[str, Any]:
    """
    Search the web with circuit breaker protection.
    
    The decorator automatically wraps the function with circuit breaker logic.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.example.com/search",
            params={"q": query}
        )
        response.raise_for_status()
        return response.json()


# Example 3: Combining circuit breaker with retry logic
# ======================================================

database_breaker = CircuitBreaker(
    failure_threshold=5,
    timeout=120.0,
    name="Database"
)


async def query_database_with_resilience(query: str) -> Dict[str, Any]:
    """
    Query database with both retry logic and circuit breaker.
    
    This provides two layers of resilience:
    1. Retry logic handles transient failures (network blips, timeouts)
    2. Circuit breaker prevents cascading failures when service is down
    
    The circuit breaker wraps the retry logic, so:
    - If circuit is OPEN, request fails immediately (no retries)
    - If circuit is CLOSED, retries are attempted on failure
    - If circuit is HALF_OPEN, one attempt is made to test recovery
    """
    async def _query_with_retry():
        # This function includes retry logic
        return await retry_with_backoff(
            _execute_query,
            query,
            config=RetryConfig(max_retries=3, base_delay=1.0)
        )
    
    # Wrap with circuit breaker
    return await database_breaker.call(_query_with_retry)


async def _execute_query(query: str) -> Dict[str, Any]:
    """Execute the actual database query."""
    # Simulated database call
    # In production, this would be actual database client call
    pass


# Example 4: Multiple circuit breakers for different services
# ============================================================

class ExternalServiceClient:
    """
    Client for managing multiple external services with circuit breakers.
    
    Each external service gets its own circuit breaker to isolate failures.
    """
    
    def __init__(self):
        # Separate circuit breakers for each service
        self.openai_breaker = CircuitBreaker(
            failure_threshold=5,
            timeout=60.0,
            name="OpenAI"
        )
        
        self.web_search_breaker = CircuitBreaker(
            failure_threshold=3,
            timeout=30.0,
            name="WebSearch"
        )
        
        self.credit_bureau_breaker = CircuitBreaker(
            failure_threshold=5,
            timeout=120.0,
            name="CreditBureau"
        )
        
        self.openai_client = AsyncOpenAI()
    
    async def call_openai(self, prompt: str) -> str:
        """Call OpenAI with circuit breaker."""
        async def _call():
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        
        return await self.openai_breaker.call(_call)
    
    async def search_web(self, query: str) -> Dict[str, Any]:
        """Search web with circuit breaker."""
        async def _search():
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.example.com/search",
                    params={"q": query}
                )
                response.raise_for_status()
                return response.json()
        
        return await self.web_search_breaker.call(_search)
    
    async def query_credit_bureau(self, company_id: str) -> Dict[str, Any]:
        """Query credit bureau with circuit breaker."""
        async def _query():
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.creditbureau.com/company/{company_id}"
                )
                response.raise_for_status()
                return response.json()
        
        return await self.credit_bureau_breaker.call(_query)
    
    def get_circuit_status(self) -> Dict[str, str]:
        """Get status of all circuit breakers."""
        return {
            "openai": self.openai_breaker.state.value,
            "web_search": self.web_search_breaker.state.value,
            "credit_bureau": self.credit_bureau_breaker.state.value
        }


# Example 5: Monitoring circuit breaker state
# ============================================

def log_circuit_breaker_metrics(breaker: CircuitBreaker) -> Dict[str, Any]:
    """
    Log circuit breaker metrics for monitoring.
    
    This can be integrated with monitoring systems like Prometheus,
    CloudWatch, or custom dashboards.
    """
    return {
        "name": breaker.name,
        "state": breaker.state.value,
        "failure_count": breaker.failure_count,
        "success_count": breaker.success_count,
        "failure_threshold": breaker.failure_threshold,
        "timeout": breaker.timeout
    }


# Example 6: Graceful degradation with circuit breaker
# =====================================================

async def get_company_intelligence_with_fallback(
    company_name: str,
    client: ExternalServiceClient
) -> Dict[str, Any]:
    """
    Get company intelligence with graceful degradation.
    
    If external services are unavailable (circuit open), fall back to
    cached data or limited functionality.
    """
    result = {
        "company_name": company_name,
        "web_research": None,
        "credit_score": None,
        "data_source": "unknown"
    }
    
    # Try web research
    try:
        result["web_research"] = await client.search_web(company_name)
        result["data_source"] = "live"
    except Exception as e:
        # Circuit breaker open or service failed
        result["web_research"] = _get_cached_web_research(company_name)
        result["data_source"] = "cached"
    
    # Try credit bureau
    try:
        result["credit_score"] = await client.query_credit_bureau(company_name)
    except Exception as e:
        # Circuit breaker open or service failed
        result["credit_score"] = None
        result["data_source"] = "partial"
    
    return result


def _get_cached_web_research(company_name: str) -> Dict[str, Any]:
    """Get cached web research data as fallback."""
    # In production, this would query a cache (Redis, etc.)
    return {
        "summary": "Cached data - external service unavailable",
        "cached": True
    }


# Example 7: Testing circuit breaker behavior
# ============================================

async def test_circuit_breaker_behavior():
    """
    Test circuit breaker state transitions.
    
    This demonstrates how the circuit breaker behaves under different conditions.
    """
    breaker = CircuitBreaker(
        failure_threshold=3,
        timeout=5.0,
        name="Test"
    )
    
    async def failing_service():
        raise Exception("Service unavailable")
    
    async def healthy_service():
        return "success"
    
    print(f"Initial state: {breaker.state.value}")
    
    # Cause failures to open circuit
    for i in range(3):
        try:
            await breaker.call(failing_service)
        except Exception:
            print(f"Failure {i+1}, state: {breaker.state.value}")
    
    print(f"After failures, state: {breaker.state.value}")
    
    # Try to call while circuit is open
    try:
        await breaker.call(healthy_service)
    except Exception as e:
        print(f"Circuit open, error: {e}")
    
    # Wait for timeout and test recovery
    import asyncio
    await asyncio.sleep(5.5)
    
    # Circuit should transition to HALF_OPEN and then CLOSED on success
    result = await breaker.call(healthy_service)
    print(f"After recovery, state: {breaker.state.value}, result: {result}")


# Best Practices
# ==============
"""
1. Use separate circuit breakers for different external services
   - Isolates failures to specific services
   - Allows different thresholds and timeouts per service

2. Combine with retry logic for maximum resilience
   - Circuit breaker prevents cascading failures
   - Retry logic handles transient errors

3. Implement graceful degradation
   - Fall back to cached data when circuit is open
   - Provide partial functionality rather than complete failure

4. Monitor circuit breaker state
   - Log state transitions
   - Alert when circuits open frequently
   - Track failure patterns

5. Configure thresholds appropriately
   - failure_threshold: Based on expected error rate
   - timeout: Based on service recovery time
   - success_threshold: Based on confidence needed for recovery

6. Test circuit breaker behavior
   - Verify state transitions
   - Test timeout and recovery
   - Ensure graceful degradation works
"""
