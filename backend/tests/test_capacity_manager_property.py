"""
Property-Based Tests for Capacity Management

This module contains property-based tests for the CapacityManager class using Hypothesis.
Tests validate universal properties that should hold across all valid executions.

Property 40: Capacity Management and Notification
For any situation where processing capacity is reached, the system should queue
additional requests and notify users of expected wait times.

Validates: Requirements 18.4
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime, timedelta
from app.services.capacity_manager import CapacityManager, CapacityMetrics, WaitTimeEstimate


# Configure Hypothesis to use "fast" profile with 20 examples
settings.register_profile("fast", max_examples=20, deadline=5000)
settings.load_profile("fast")


# Custom strategies for capacity management testing
@st.composite
def capacity_config_strategy(draw):
    """Generate valid capacity manager configurations."""
    return {
        "max_concurrent_tasks": draw(st.integers(min_value=1, max_value=20)),
        "default_processing_time": draw(st.floats(min_value=1.0, max_value=600.0))
    }


@st.composite
def request_sequence_strategy(draw):
    """Generate a sequence of request IDs."""
    num_requests = draw(st.integers(min_value=1, max_value=30))
    return [f"request_{i}" for i in range(num_requests)]


# Feature: intelli-credit-platform, Property 40: Capacity Management and Notification
@pytest.mark.asyncio
@given(config=capacity_config_strategy(), num_requests=st.integers(min_value=1, max_value=25))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_capacity_reached_queues_requests(config, num_requests):
    """
    **Validates: Requirements 18.4**
    
    Property 40: Capacity Management and Notification
    
    For any situation where processing capacity is reached, the system should
    queue additional requests that exceed capacity.
    """
    manager = CapacityManager(
        max_concurrent_tasks=config["max_concurrent_tasks"],
        default_processing_time=config["default_processing_time"]
    )
    
    # Start processing up to capacity
    started_requests = []
    for i in range(min(num_requests, config["max_concurrent_tasks"])):
        request_id = f"request_{i}"
        await manager.start_processing(request_id)
        started_requests.append(request_id)
    
    # Property 1: System should be at capacity
    if num_requests >= config["max_concurrent_tasks"]:
        is_at_capacity = await manager.is_at_capacity()
        assert is_at_capacity, \
            "System should be at capacity when max_concurrent_tasks are processing"
    
    # Try to add more requests beyond capacity
    queued_requests = []
    for i in range(config["max_concurrent_tasks"], num_requests):
        request_id = f"request_{i}"
        
        # Should not be able to start processing
        can_accept = await manager.can_accept_request()
        if not can_accept:
            # Should queue the request
            position = await manager.queue_request(request_id)
            queued_requests.append(request_id)
            
            # Property 2: Queued request should have valid position
            assert position >= 0, \
                "Queue position should be non-negative"
            assert position == len(queued_requests) - 1, \
                "Queue position should match order of queueing"
    
    # Property 3: Number of processing + queued should equal total requests
    metrics = await manager.get_capacity_metrics()
    total_tracked = metrics.current_processing + metrics.queued_tasks
    assert total_tracked == num_requests, \
        f"Total tracked requests ({total_tracked}) should equal submitted requests ({num_requests})"
    
    # Property 4: Processing count should not exceed max capacity
    assert metrics.current_processing <= config["max_concurrent_tasks"], \
        "Processing count should never exceed max_concurrent_tasks"


# Feature: intelli-credit-platform, Property 40: Capacity Management and Notification
@pytest.mark.asyncio
@given(
    max_concurrent=st.integers(min_value=1, max_value=10),
    num_requests=st.integers(min_value=1, max_value=20)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_wait_time_notification_provided(max_concurrent, num_requests):
    """
    **Validates: Requirements 18.4**
    
    Property 40: Capacity Management and Notification
    
    For any queued request, the system should provide wait time estimates
    with position in queue and user-friendly messages.
    """
    manager = CapacityManager(
        max_concurrent_tasks=max_concurrent,
        default_processing_time=300.0  # 5 minutes
    )
    
    # Fill capacity
    for i in range(min(num_requests, max_concurrent)):
        await manager.start_processing(f"request_{i}")
    
    # Queue additional requests
    queued_ids = []
    for i in range(max_concurrent, num_requests):
        request_id = f"request_{i}"
        await manager.queue_request(request_id)
        queued_ids.append(request_id)
    
    # Property 1: Wait time estimate should be provided for each queued request
    for request_id in queued_ids:
        estimate = await manager.estimate_wait_time(request_id)
        
        # Property 2: Estimate should have all required fields
        assert isinstance(estimate, WaitTimeEstimate), \
            "Should return WaitTimeEstimate object"
        assert estimate.estimated_wait_seconds >= 0, \
            "Estimated wait time should be non-negative"
        assert estimate.position_in_queue >= 0, \
            "Queue position should be non-negative"
        assert estimate.current_queue_size >= 0, \
            "Queue size should be non-negative"
        assert len(estimate.message) > 0, \
            "Should provide user-friendly message"
        assert isinstance(estimate.timestamp, datetime), \
            "Should have timestamp"
        
        # Property 3: Message should contain key information
        assert "position" in estimate.message.lower() or str(estimate.position_in_queue + 1) in estimate.message, \
            "Message should mention queue position"
        assert "wait" in estimate.message.lower() or "time" in estimate.message.lower(), \
            "Message should mention wait time"


# Feature: intelli-credit-platform, Property 40: Capacity Management and Notification
@pytest.mark.asyncio
@given(
    max_concurrent=st.integers(min_value=2, max_value=10),
    num_to_queue=st.integers(min_value=1, max_value=15)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_queue_position_accuracy(max_concurrent, num_to_queue):
    """
    **Validates: Requirements 18.4**
    
    Property 40: Capacity Management and Notification
    
    For any queued request, the system should accurately track and report
    its position in the queue (FIFO ordering).
    """
    manager = CapacityManager(max_concurrent_tasks=max_concurrent)
    
    # Fill capacity
    for i in range(max_concurrent):
        await manager.start_processing(f"processing_{i}")
    
    # Queue requests
    queued_ids = []
    for i in range(num_to_queue):
        request_id = f"queued_{i}"
        position = await manager.queue_request(request_id)
        queued_ids.append(request_id)
        
        # Property 1: Position should match order of queueing
        assert position == i, \
            f"Request {i} should be at position {i}, got {position}"
    
    # Property 2: Verify all positions are correct
    for i, request_id in enumerate(queued_ids):
        position = await manager.get_queue_position(request_id)
        assert position == i, \
            f"Request {request_id} should be at position {i}, got {position}"
    
    # Property 3: Wait time should increase with queue position
    wait_times = []
    for request_id in queued_ids:
        estimate = await manager.estimate_wait_time(request_id)
        wait_times.append(estimate.estimated_wait_seconds)
    
    # Later positions should have equal or longer wait times
    for i in range(len(wait_times) - 1):
        assert wait_times[i] <= wait_times[i + 1], \
            f"Wait time should increase with position: {wait_times[i]} > {wait_times[i + 1]}"


# Feature: intelli-credit-platform, Property 40: Capacity Management and Notification
@pytest.mark.asyncio
@given(
    max_concurrent=st.integers(min_value=1, max_value=8),
    num_requests=st.integers(min_value=2, max_value=20),
    processing_time=st.floats(min_value=0.01, max_value=2.0)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_capacity_release_processes_queued(max_concurrent, num_requests, processing_time):
    """
    **Validates: Requirements 18.4**
    
    Property 40: Capacity Management and Notification
    
    When processing capacity is released (task completes), the system should
    be able to process queued requests.
    """
    assume(num_requests > max_concurrent)  # Ensure we have queued requests
    
    manager = CapacityManager(
        max_concurrent_tasks=max_concurrent,
        default_processing_time=processing_time
    )
    
    # Fill capacity
    processing_ids = []
    for i in range(max_concurrent):
        request_id = f"request_{i}"
        await manager.start_processing(request_id)
        processing_ids.append(request_id)
    
    # Queue additional requests
    queued_ids = []
    for i in range(max_concurrent, num_requests):
        request_id = f"request_{i}"
        await manager.queue_request(request_id)
        queued_ids.append(request_id)
    
    # Property 1: System should be at capacity
    assert await manager.is_at_capacity(), \
        "System should be at capacity"
    
    # Complete one processing task
    completed_id = processing_ids[0]
    await manager.complete_processing(completed_id, processing_time)
    
    # Property 2: Capacity should be available after completion
    can_accept = await manager.can_accept_request()
    assert can_accept, \
        "Should be able to accept new request after completion"
    
    # Property 3: Should be able to start processing a queued request
    next_request = await manager.get_next_queued_request()
    assert next_request is not None, \
        "Should have queued request available"
    assert next_request == queued_ids[0], \
        "Should get first queued request (FIFO)"
    
    # Start processing the queued request
    await manager.start_processing(next_request)
    
    # Property 4: Request should be removed from queue
    position = await manager.get_queue_position(next_request)
    assert position is None, \
        "Request should be removed from queue after starting processing"
    
    # Property 5: Queue size should decrease
    metrics = await manager.get_capacity_metrics()
    assert metrics.queued_tasks == len(queued_ids) - 1, \
        "Queue size should decrease after processing queued request"


# Feature: intelli-credit-platform, Property 40: Capacity Management and Notification
@pytest.mark.asyncio
@given(
    max_concurrent=st.integers(min_value=1, max_value=10),
    num_completions=st.integers(min_value=1, max_value=20),
    processing_times=st.lists(
        st.floats(min_value=1.0, max_value=600.0),
        min_size=1,
        max_size=20
    )
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_wait_time_estimation_accuracy(max_concurrent, num_completions, processing_times):
    """
    **Validates: Requirements 18.4**
    
    Property 40: Capacity Management and Notification
    
    Wait time estimates should be based on historical processing times
    and queue position, providing reasonable estimates.
    """
    assume(len(processing_times) >= num_completions)
    
    manager = CapacityManager(
        max_concurrent_tasks=max_concurrent,
        default_processing_time=300.0
    )
    
    # Simulate completed tasks to build processing time history
    for i in range(num_completions):
        request_id = f"completed_{i}"
        await manager.start_processing(request_id)
        await manager.complete_processing(request_id, processing_times[i])
    
    # Fill capacity again
    for i in range(max_concurrent):
        await manager.start_processing(f"current_{i}")
    
    # Queue a request
    queued_id = "queued_request"
    await manager.queue_request(queued_id)
    
    # Get wait time estimate
    estimate = await manager.estimate_wait_time(queued_id)
    
    # Property 1: Estimate should be positive
    assert estimate.estimated_wait_seconds > 0, \
        "Wait time should be positive when at capacity"
    
    # Property 2: Estimate should be reasonable based on processing times
    avg_processing_time = sum(processing_times[:num_completions]) / num_completions
    # Wait time should be related to average processing time
    # (allowing for some calculation overhead)
    assert estimate.estimated_wait_seconds <= avg_processing_time * 10, \
        "Wait time estimate should be reasonable relative to average processing time"
    
    # Property 3: Position should be 0 for first queued request
    assert estimate.position_in_queue == 0, \
        "First queued request should be at position 0"
    
    # Queue more requests and verify estimates increase
    previous_estimate = estimate.estimated_wait_seconds
    for i in range(3):
        new_id = f"queued_{i}"
        await manager.queue_request(new_id)
        new_estimate = await manager.estimate_wait_time(new_id)
        
        # Property 4: Later requests should have longer or equal wait times
        assert new_estimate.estimated_wait_seconds >= previous_estimate, \
            "Later queued requests should have longer wait times"
        previous_estimate = new_estimate.estimated_wait_seconds


# Feature: intelli-credit-platform, Property 40: Capacity Management and Notification
@pytest.mark.asyncio
@given(
    max_concurrent=st.integers(min_value=1, max_value=10),
    num_requests=st.integers(min_value=1, max_value=20)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_capacity_metrics_consistency(max_concurrent, num_requests):
    """
    **Validates: Requirements 18.4**
    
    Property 40: Capacity Management and Notification
    
    Capacity metrics should accurately reflect system state at all times.
    """
    manager = CapacityManager(max_concurrent_tasks=max_concurrent)
    
    # Start processing up to capacity
    processing_count = min(num_requests, max_concurrent)
    for i in range(processing_count):
        await manager.start_processing(f"request_{i}")
    
    # Queue remaining requests
    queued_count = max(0, num_requests - max_concurrent)
    for i in range(processing_count, num_requests):
        await manager.queue_request(f"request_{i}")
    
    # Get metrics
    metrics = await manager.get_capacity_metrics()
    
    # Property 1: Metrics should be of correct type
    assert isinstance(metrics, CapacityMetrics), \
        "Should return CapacityMetrics object"
    
    # Property 2: Max concurrent should match configuration
    assert metrics.max_concurrent_tasks == max_concurrent, \
        "Max concurrent tasks should match configuration"
    
    # Property 3: Current processing should match actual count
    assert metrics.current_processing == processing_count, \
        f"Current processing ({metrics.current_processing}) should match actual ({processing_count})"
    
    # Property 4: Queued tasks should match actual count
    assert metrics.queued_tasks == queued_count, \
        f"Queued tasks ({metrics.queued_tasks}) should match actual ({queued_count})"
    
    # Property 5: At capacity flag should be correct
    expected_at_capacity = (processing_count >= max_concurrent)
    assert metrics.is_at_capacity == expected_at_capacity, \
        f"is_at_capacity should be {expected_at_capacity}"
    
    # Property 6: Utilization percentage should be correct
    expected_utilization = (processing_count / max_concurrent) * 100
    assert abs(metrics.utilization_percentage - expected_utilization) < 0.01, \
        f"Utilization should be {expected_utilization}%, got {metrics.utilization_percentage}%"
    
    # Property 7: Timestamp should be recent
    assert isinstance(metrics.timestamp, datetime), \
        "Metrics should have timestamp"
    time_diff = (datetime.utcnow() - metrics.timestamp).total_seconds()
    assert time_diff < 5.0, \
        "Metrics timestamp should be recent"


# Feature: intelli-credit-platform, Property 40: Capacity Management and Notification
@pytest.mark.asyncio
@given(
    max_concurrent=st.integers(min_value=2, max_value=10),
    num_to_queue=st.integers(min_value=2, max_value=15)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_fifo_queue_ordering(max_concurrent, num_to_queue):
    """
    **Validates: Requirements 18.4**
    
    Property 40: Capacity Management and Notification
    
    Queued requests should be processed in FIFO (First-In-First-Out) order.
    """
    manager = CapacityManager(max_concurrent_tasks=max_concurrent)
    
    # Fill capacity with tracking
    processing_ids = []
    for i in range(max_concurrent):
        request_id = f"processing_{i}"
        await manager.start_processing(request_id)
        processing_ids.append(request_id)
    
    # Queue requests in order
    queued_order = []
    for i in range(num_to_queue):
        request_id = f"queued_{i}"
        await manager.queue_request(request_id)
        queued_order.append(request_id)
    
    # Property 1: Get next queued request should return first queued
    next_request = await manager.get_next_queued_request()
    assert next_request == queued_order[0], \
        "Should return first queued request (FIFO)"
    
    # Property 2: Process requests in order
    processed_order = []
    for i in range(min(num_to_queue, max_concurrent)):
        # Complete a processing task to free capacity
        # Use the actual processing IDs we started
        await manager.complete_processing(processing_ids[i])
        
        # Get next queued request
        next_request = await manager.get_next_queued_request()
        if next_request:
            processed_order.append(next_request)
            await manager.start_processing(next_request)
    
    # Property 3: Processed order should match queued order (for the ones we processed)
    expected_order = queued_order[:len(processed_order)]
    assert processed_order == expected_order, \
        f"Requests should be processed in FIFO order: expected {expected_order}, got {processed_order}"


# Feature: intelli-credit-platform, Property 40: Capacity Management and Notification
@pytest.mark.asyncio
@given(
    max_concurrent=st.integers(min_value=1, max_value=10),
    num_requests=st.integers(min_value=1, max_value=20)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_cannot_exceed_capacity(max_concurrent, num_requests):
    """
    **Validates: Requirements 18.4**
    
    Property 40: Capacity Management and Notification
    
    The system should never allow more than max_concurrent_tasks to process
    simultaneously, regardless of how many requests are submitted.
    """
    manager = CapacityManager(max_concurrent_tasks=max_concurrent)
    
    # Try to start processing all requests
    started_count = 0
    for i in range(num_requests):
        request_id = f"request_{i}"
        
        if await manager.can_accept_request():
            await manager.start_processing(request_id)
            started_count += 1
        else:
            # Should queue instead
            await manager.queue_request(request_id)
    
    # Property 1: Started count should not exceed max_concurrent
    assert started_count <= max_concurrent, \
        f"Started {started_count} tasks, but max is {max_concurrent}"
    
    # Property 2: Metrics should confirm capacity limit
    metrics = await manager.get_capacity_metrics()
    assert metrics.current_processing <= max_concurrent, \
        "Current processing should never exceed max_concurrent_tasks"
    
    # Property 3: If we had more requests than capacity, some should be queued
    if num_requests > max_concurrent:
        assert metrics.queued_tasks > 0, \
            "Excess requests should be queued"
        assert metrics.queued_tasks == num_requests - max_concurrent, \
            "Queue should contain all excess requests"


# Feature: intelli-credit-platform, Property 40: Capacity Management and Notification
@pytest.mark.asyncio
@given(
    max_concurrent=st.integers(min_value=1, max_value=10),
    num_to_queue=st.integers(min_value=1, max_value=15),
    num_to_remove=st.integers(min_value=1, max_value=10)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_queue_removal(max_concurrent, num_to_queue, num_to_remove):
    """
    **Validates: Requirements 18.4**
    
    Property 40: Capacity Management and Notification
    
    The system should support removing requests from the queue and
    maintain queue consistency after removal.
    """
    assume(num_to_remove <= num_to_queue)
    
    manager = CapacityManager(max_concurrent_tasks=max_concurrent)
    
    # Fill capacity
    for i in range(max_concurrent):
        await manager.start_processing(f"processing_{i}")
    
    # Queue requests
    queued_ids = []
    for i in range(num_to_queue):
        request_id = f"queued_{i}"
        await manager.queue_request(request_id)
        queued_ids.append(request_id)
    
    # Remove some requests
    removed_ids = queued_ids[:num_to_remove]
    for request_id in removed_ids:
        result = await manager.remove_from_queue(request_id)
        
        # Property 1: Should successfully remove
        assert result is True, \
            f"Should successfully remove {request_id} from queue"
        
        # Property 2: Should not be in queue anymore
        position = await manager.get_queue_position(request_id)
        assert position is None, \
            f"Removed request {request_id} should not have queue position"
    
    # Property 3: Queue size should decrease
    metrics = await manager.get_capacity_metrics()
    expected_queue_size = num_to_queue - num_to_remove
    assert metrics.queued_tasks == expected_queue_size, \
        f"Queue size should be {expected_queue_size}, got {metrics.queued_tasks}"
    
    # Property 4: Remaining requests should have updated positions
    remaining_ids = queued_ids[num_to_remove:]
    for i, request_id in enumerate(remaining_ids):
        position = await manager.get_queue_position(request_id)
        assert position == i, \
            f"Request {request_id} should be at position {i} after removals"


# Feature: intelli-credit-platform, Property 40: Capacity Management and Notification
@pytest.mark.asyncio
@given(max_concurrent=st.integers(min_value=1, max_value=10))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_wait_time_for_new_request(max_concurrent):
    """
    **Validates: Requirements 18.4**
    
    Property 40: Capacity Management and Notification
    
    The system should provide wait time estimates for new requests
    even before they are queued.
    """
    manager = CapacityManager(
        max_concurrent_tasks=max_concurrent,
        default_processing_time=300.0
    )
    
    # Fill capacity
    for i in range(max_concurrent):
        await manager.start_processing(f"request_{i}")
    
    # Queue some requests
    for i in range(5):
        await manager.queue_request(f"queued_{i}")
    
    # Get estimate for a new request (not yet queued)
    estimate = await manager.estimate_wait_time()
    
    # Property 1: Should provide estimate even for non-queued request
    assert isinstance(estimate, WaitTimeEstimate), \
        "Should provide estimate for new request"
    
    # Property 2: Position should be at end of current queue
    metrics = await manager.get_capacity_metrics()
    assert estimate.position_in_queue == metrics.queued_tasks, \
        "New request position should be at end of queue"
    
    # Property 3: Estimate should be positive when at capacity
    assert estimate.estimated_wait_seconds > 0, \
        "Wait time should be positive when system is at capacity"
    
    # Property 4: Message should be provided
    assert len(estimate.message) > 0, \
        "Should provide user-friendly message"
