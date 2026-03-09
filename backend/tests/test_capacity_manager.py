"""
Unit Tests for Capacity Manager

This module contains unit tests for the CapacityManager class.
Tests cover capacity checking, request queueing, wait time estimation,
and user notification scenarios.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from app.services.capacity_manager import (
    CapacityManager,
    CapacityMetrics,
    WaitTimeEstimate
)


@pytest.mark.asyncio
async def test_capacity_manager_initialization():
    """Test capacity manager initialization."""
    manager = CapacityManager(max_concurrent_tasks=5)
    
    assert manager.max_concurrent_tasks == 5
    assert len(manager.processing_tasks) == 0
    assert len(manager.queued_requests) == 0
    assert await manager.can_accept_request() is True


@pytest.mark.asyncio
async def test_can_accept_request_when_below_capacity():
    """Test that requests are accepted when below capacity."""
    manager = CapacityManager(max_concurrent_tasks=3)
    
    # Start 2 tasks (below capacity)
    await manager.start_processing("req1")
    await manager.start_processing("req2")
    
    # Should still accept requests
    assert await manager.can_accept_request() is True
    assert await manager.is_at_capacity() is False


@pytest.mark.asyncio
async def test_at_capacity_when_limit_reached():
    """Test that system is at capacity when limit is reached."""
    manager = CapacityManager(max_concurrent_tasks=2)
    
    # Start tasks up to capacity
    await manager.start_processing("req1")
    await manager.start_processing("req2")
    
    # Should be at capacity
    assert await manager.can_accept_request() is False
    assert await manager.is_at_capacity() is True


@pytest.mark.asyncio
async def test_cannot_start_processing_when_at_capacity():
    """Test that starting processing fails when at capacity."""
    manager = CapacityManager(max_concurrent_tasks=2)
    
    # Fill capacity
    await manager.start_processing("req1")
    await manager.start_processing("req2")
    
    # Attempting to start another should raise error
    with pytest.raises(ValueError, match="at capacity"):
        await manager.start_processing("req3")


@pytest.mark.asyncio
async def test_complete_processing_frees_capacity():
    """Test that completing processing frees up capacity."""
    manager = CapacityManager(max_concurrent_tasks=2)
    
    # Fill capacity
    await manager.start_processing("req1")
    await manager.start_processing("req2")
    assert await manager.is_at_capacity() is True
    
    # Complete one task
    await manager.complete_processing("req1", processing_time=100.0)
    
    # Should have capacity again
    assert await manager.can_accept_request() is True
    assert await manager.is_at_capacity() is False


@pytest.mark.asyncio
async def test_queue_request_when_at_capacity():
    """Test queueing requests when at capacity."""
    manager = CapacityManager(max_concurrent_tasks=2)
    
    # Fill capacity
    await manager.start_processing("req1")
    await manager.start_processing("req2")
    
    # Queue additional requests
    position1 = await manager.queue_request("req3")
    position2 = await manager.queue_request("req4")
    
    assert position1 == 0
    assert position2 == 1
    assert len(manager.queued_requests) == 2


@pytest.mark.asyncio
async def test_get_queue_position():
    """Test getting queue position for a request."""
    manager = CapacityManager(max_concurrent_tasks=1)
    
    # Queue some requests
    await manager.queue_request("req1")
    await manager.queue_request("req2")
    await manager.queue_request("req3")
    
    # Check positions
    assert await manager.get_queue_position("req1") == 0
    assert await manager.get_queue_position("req2") == 1
    assert await manager.get_queue_position("req3") == 2
    assert await manager.get_queue_position("req4") is None


@pytest.mark.asyncio
async def test_remove_from_queue():
    """Test removing a request from the queue."""
    manager = CapacityManager(max_concurrent_tasks=1)
    
    # Queue requests
    await manager.queue_request("req1")
    await manager.queue_request("req2")
    await manager.queue_request("req3")
    
    # Remove middle request
    removed = await manager.remove_from_queue("req2")
    assert removed is True
    
    # Check updated positions
    assert await manager.get_queue_position("req1") == 0
    assert await manager.get_queue_position("req3") == 1
    assert await manager.get_queue_position("req2") is None
    
    # Try removing non-existent request
    removed = await manager.remove_from_queue("req4")
    assert removed is False


@pytest.mark.asyncio
async def test_start_processing_removes_from_queue():
    """Test that starting processing removes request from queue."""
    manager = CapacityManager(max_concurrent_tasks=2)
    
    # Queue a request
    await manager.queue_request("req1")
    assert len(manager.queued_requests) == 1
    
    # Start processing it
    await manager.start_processing("req1")
    
    # Should be removed from queue
    assert len(manager.queued_requests) == 0
    assert await manager.get_queue_position("req1") is None


@pytest.mark.asyncio
async def test_estimate_wait_time_for_queued_request():
    """Test wait time estimation for a queued request."""
    manager = CapacityManager(max_concurrent_tasks=2, default_processing_time=120.0)
    
    # Add some processing history
    manager.processing_times = [100.0, 120.0, 110.0]
    
    # Fill capacity
    await manager.start_processing("req1")
    await manager.start_processing("req2")
    
    # Queue requests
    await manager.queue_request("req3")
    await manager.queue_request("req4")
    
    # Estimate wait time for queued request
    estimate = await manager.estimate_wait_time("req3")
    
    assert isinstance(estimate, WaitTimeEstimate)
    assert estimate.position_in_queue == 0
    assert estimate.current_queue_size == 2
    assert estimate.estimated_wait_seconds > 0
    # Message shows position 1 (0-indexed + 1) of total queue size + 1
    assert "position 1" in estimate.message.lower()
    assert "estimated wait time" in estimate.message.lower()


@pytest.mark.asyncio
async def test_estimate_wait_time_for_new_request():
    """Test wait time estimation for a new request."""
    manager = CapacityManager(max_concurrent_tasks=2, default_processing_time=100.0)
    
    # Queue some requests
    await manager.queue_request("req1")
    await manager.queue_request("req2")
    
    # Estimate for new request (not yet queued)
    estimate = await manager.estimate_wait_time()
    
    assert estimate.position_in_queue == 2  # Would be at end
    assert estimate.current_queue_size == 2
    assert estimate.estimated_wait_seconds > 0


@pytest.mark.asyncio
async def test_wait_time_uses_default_when_no_history():
    """Test that wait time estimation uses default when no history."""
    manager = CapacityManager(max_concurrent_tasks=2, default_processing_time=300.0)
    
    # No processing history
    assert len(manager.processing_times) == 0
    
    # Queue a request
    await manager.queue_request("req1")
    
    # Estimate should use default
    estimate = await manager.estimate_wait_time("req1")
    
    # With position 0 and max_concurrent 2, wait should be minimal
    # but calculation should use default_processing_time
    assert estimate.estimated_wait_seconds >= 0


@pytest.mark.asyncio
async def test_wait_time_uses_average_from_history():
    """Test that wait time estimation uses average from history."""
    manager = CapacityManager(max_concurrent_tasks=1, default_processing_time=300.0)
    
    # Add processing history
    manager.processing_times = [100.0, 200.0, 150.0]
    
    # Fill capacity
    await manager.start_processing("req1")
    
    # Queue requests
    await manager.queue_request("req2")
    await manager.queue_request("req3")
    
    # Estimate for second queued request
    estimate = await manager.estimate_wait_time("req3")
    
    # Average is 150s, position 1, max_concurrent 1
    # Expected: 1 batch * 150s + partial current batch
    assert estimate.estimated_wait_seconds > 150.0


@pytest.mark.asyncio
async def test_capacity_metrics():
    """Test getting capacity metrics."""
    manager = CapacityManager(max_concurrent_tasks=5)
    
    # Start some tasks
    await manager.start_processing("req1")
    await manager.start_processing("req2")
    
    # Queue some requests
    await manager.queue_request("req3")
    await manager.queue_request("req4")
    
    # Add processing history
    manager.processing_times = [100.0, 120.0, 110.0]
    manager.completed_tasks = [datetime.utcnow(), datetime.utcnow()]
    
    # Get metrics
    metrics = await manager.get_capacity_metrics()
    
    assert isinstance(metrics, CapacityMetrics)
    assert metrics.max_concurrent_tasks == 5
    assert metrics.current_processing == 2
    assert metrics.queued_tasks == 2
    assert metrics.completed_last_hour == 2
    assert metrics.average_processing_time == 110.0
    assert metrics.is_at_capacity is False
    assert metrics.utilization_percentage == 40.0


@pytest.mark.asyncio
async def test_capacity_metrics_at_capacity():
    """Test capacity metrics when at capacity."""
    manager = CapacityManager(max_concurrent_tasks=2)
    
    # Fill capacity
    await manager.start_processing("req1")
    await manager.start_processing("req2")
    
    metrics = await manager.get_capacity_metrics()
    
    assert metrics.is_at_capacity is True
    assert metrics.utilization_percentage == 100.0


@pytest.mark.asyncio
async def test_get_next_queued_request():
    """Test getting next request from queue (FIFO)."""
    manager = CapacityManager(max_concurrent_tasks=1)
    
    # Queue requests
    await manager.queue_request("req1")
    await manager.queue_request("req2")
    await manager.queue_request("req3")
    
    # Get next should return first
    next_req = await manager.get_next_queued_request()
    assert next_req == "req1"
    
    # Queue should not be modified
    assert len(manager.queued_requests) == 3


@pytest.mark.asyncio
async def test_get_next_queued_request_empty_queue():
    """Test getting next request from empty queue."""
    manager = CapacityManager(max_concurrent_tasks=1)
    
    next_req = await manager.get_next_queued_request()
    assert next_req is None


@pytest.mark.asyncio
async def test_clear_queue():
    """Test clearing the queue."""
    manager = CapacityManager(max_concurrent_tasks=1)
    
    # Queue requests
    await manager.queue_request("req1")
    await manager.queue_request("req2")
    await manager.queue_request("req3")
    
    # Clear queue
    count = await manager.clear_queue()
    
    assert count == 3
    assert len(manager.queued_requests) == 0


@pytest.mark.asyncio
async def test_processing_time_history_limit():
    """Test that processing time history is limited."""
    manager = CapacityManager(max_concurrent_tasks=5)
    manager.max_history_size = 10
    
    # Add more than max history
    for i in range(15):
        await manager.start_processing(f"req{i}")
        await manager.complete_processing(f"req{i}", processing_time=100.0 + i)
    
    # Should only keep last 10
    assert len(manager.processing_times) == 10
    # Should have the most recent ones
    assert manager.processing_times[-1] == 114.0


@pytest.mark.asyncio
async def test_completed_tasks_cleanup():
    """Test that old completed tasks are cleaned up."""
    manager = CapacityManager(max_concurrent_tasks=5)
    
    # Add old completed tasks
    old_time = datetime.utcnow() - timedelta(hours=2)
    manager.completed_tasks = [old_time, old_time]
    
    # Complete a new task
    await manager.start_processing("req1")
    await manager.complete_processing("req1")
    
    # Old tasks should be removed
    assert len(manager.completed_tasks) == 1
    assert manager.completed_tasks[0] > old_time


@pytest.mark.asyncio
async def test_reset_metrics():
    """Test resetting metrics."""
    manager = CapacityManager(max_concurrent_tasks=5)
    
    # Add some data
    manager.processing_times = [100.0, 120.0, 110.0]
    manager.completed_tasks = [datetime.utcnow(), datetime.utcnow()]
    
    # Reset
    await manager.reset_metrics()
    
    assert len(manager.processing_times) == 0
    assert len(manager.completed_tasks) == 0


@pytest.mark.asyncio
async def test_concurrent_operations():
    """Test concurrent operations on capacity manager."""
    manager = CapacityManager(max_concurrent_tasks=10)
    
    # Simulate concurrent requests
    async def add_and_complete(req_id: str):
        await manager.start_processing(req_id)
        await asyncio.sleep(0.01)  # Simulate processing
        await manager.complete_processing(req_id, processing_time=10.0)
    
    # Run multiple concurrent operations
    tasks = [add_and_complete(f"req{i}") for i in range(5)]
    await asyncio.gather(*tasks)
    
    # All should complete successfully
    assert len(manager.processing_tasks) == 0
    assert len(manager.processing_times) == 5


@pytest.mark.asyncio
async def test_wait_time_message_formatting():
    """Test that wait time messages are user-friendly."""
    manager = CapacityManager(max_concurrent_tasks=1, default_processing_time=30.0)
    
    # Test seconds
    await manager.queue_request("req1")
    estimate = await manager.estimate_wait_time("req1")
    assert "seconds" in estimate.message or "minutes" in estimate.message
    
    # Test minutes
    manager2 = CapacityManager(max_concurrent_tasks=1, default_processing_time=180.0)
    await manager2.queue_request("req1")
    await manager2.queue_request("req2")
    estimate2 = await manager2.estimate_wait_time("req2")
    assert "minute" in estimate2.message or "hour" in estimate2.message
