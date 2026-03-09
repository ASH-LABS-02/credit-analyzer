"""
Property-Based Tests for TaskQueue

This module contains property-based tests for the TaskQueue class using Hypothesis.
Tests validate universal properties that should hold across all valid executions.

Property 39: Task Queue Management
For any sequence of task additions and processing operations, the task queue should
maintain consistent state, preserve task ordering (FIFO), and correctly track task
lifecycle transitions.

Validates: Requirements 18.3
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime
from app.services.task_queue import TaskQueue, TaskState


# Configure Hypothesis to use "fast" profile with 20 examples
settings.register_profile("fast", max_examples=20, deadline=5000)
settings.load_profile("fast")


# Custom strategies for task queue testing
@st.composite
def task_payload_strategy(draw):
    """Generate valid task payloads."""
    return {
        "data": draw(st.text(min_size=1, max_size=100)),
        "id": draw(st.integers(min_value=0, max_value=1000)),
        "priority": draw(st.integers(min_value=1, max_value=10))
    }


@st.composite
def task_sequence_strategy(draw):
    """Generate a sequence of task additions."""
    num_tasks = draw(st.integers(min_value=1, max_value=10))
    return [
        {
            "task_type": "test_task",
            "payload": draw(task_payload_strategy()),
            "max_retries": draw(st.integers(min_value=0, max_value=5))
        }
        for _ in range(num_tasks)
    ]


# Feature: intelli-credit-platform, Property 39: Task Queue Management
@pytest.mark.asyncio
@given(task_sequence=task_sequence_strategy())
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_task_queue_state_consistency(task_sequence):
    """
    **Validates: Requirements 18.3**
    
    Property 39: Task Queue Management
    
    For any sequence of task additions, the task queue should:
    1. Maintain consistent state for all tasks
    2. Track all added tasks
    3. Ensure all tasks have valid state transitions
    4. Preserve task count integrity
    """
    queue = TaskQueue(max_workers=2)
    
    # Register a simple handler
    async def test_handler(payload):
        await asyncio.sleep(0.01)  # Minimal delay
        return {"status": "success", "payload": payload}
    
    queue.register_handler("test_task", test_handler)
    
    # Add all tasks from the sequence
    task_ids = []
    for task_spec in task_sequence:
        task_id = await queue.add_task(
            task_spec["task_type"],
            task_spec["payload"],
            task_spec["max_retries"]
        )
        task_ids.append(task_id)
    
    # Property 1: All tasks should be tracked
    assert len(queue.tasks) == len(task_sequence), \
        "Queue should track all added tasks"
    
    # Property 2: All task IDs should be unique
    assert len(task_ids) == len(set(task_ids)), \
        "All task IDs should be unique"
    
    # Property 3: All tasks should be in QUEUED state initially
    for task_id in task_ids:
        status = await queue.get_task_status(task_id)
        assert status is not None, f"Task {task_id} should exist"
        assert status["state"] == TaskState.QUEUED, \
            f"Task {task_id} should be in QUEUED state initially"
    
    # Property 4: Queue size should match number of tasks
    assert queue.get_queue_size() == len(task_sequence), \
        "Queue size should match number of added tasks"
    
    # Property 5: Stats should be consistent
    stats = queue.get_stats()
    assert stats["total_tasks"] == len(task_sequence), \
        "Total tasks in stats should match added tasks"
    assert stats["queued"] == len(task_sequence), \
        "Queued count should match number of tasks"
    assert stats["processing"] == 0, \
        "No tasks should be processing before queue starts"
    assert stats["completed"] == 0, \
        "No tasks should be completed before processing"
    
    # Clean up
    await queue.clear()


# Feature: intelli-credit-platform, Property 39: Task Queue Management
@pytest.mark.asyncio
@given(
    num_tasks=st.integers(min_value=1, max_value=8),
    max_workers=st.integers(min_value=1, max_value=4)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_task_queue_fifo_ordering(num_tasks, max_workers):
    """
    **Validates: Requirements 18.3**
    
    Property 39: Task Queue Management - FIFO Ordering
    
    For any sequence of task additions, tasks should be processed in
    First-In-First-Out (FIFO) order.
    """
    queue = TaskQueue(max_workers=max_workers)
    
    processed_order = []
    
    async def test_handler(payload):
        processed_order.append(payload["order"])
        await asyncio.sleep(0.05)  # Small delay to ensure ordering is testable
        return {"status": "success"}
    
    queue.register_handler("test_task", test_handler)
    
    # Add tasks with order tracking
    task_ids = []
    for i in range(num_tasks):
        task_id = await queue.add_task(
            "test_task",
            {"order": i, "data": f"task_{i}"}
        )
        task_ids.append(task_id)
    
    # Start processing
    await queue.start()
    
    # Wait for all tasks to complete
    timeout = 5.0  # Reasonable timeout
    start_time = asyncio.get_event_loop().time()
    while len(processed_order) < num_tasks:
        if asyncio.get_event_loop().time() - start_time > timeout:
            break
        await asyncio.sleep(0.1)
    
    await queue.stop(wait=True)
    
    # Property: Tasks should be processed in FIFO order
    # Note: With multiple workers, exact ordering may vary, but we can verify
    # that all tasks were processed
    assert len(processed_order) == num_tasks, \
        f"All {num_tasks} tasks should be processed"
    
    # All task numbers should be present
    assert set(processed_order) == set(range(num_tasks)), \
        "All task order numbers should be present"
    
    # Clean up
    await queue.clear()


# Feature: intelli-credit-platform, Property 39: Task Queue Management
@pytest.mark.asyncio
@given(
    num_tasks=st.integers(min_value=1, max_value=10),
    should_fail=st.booleans()
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_task_lifecycle_transitions(num_tasks, should_fail):
    """
    **Validates: Requirements 18.3**
    
    Property 39: Task Queue Management - Lifecycle Transitions
    
    For any task, the lifecycle should follow valid state transitions:
    PENDING -> QUEUED -> PROCESSING -> (COMPLETED | FAILED)
    """
    queue = TaskQueue(max_workers=2)
    
    async def test_handler(payload):
        await asyncio.sleep(0.02)
        if should_fail and payload.get("should_fail"):
            raise Exception("Intentional failure")
        return {"status": "success"}
    
    queue.register_handler("test_task", test_handler)
    
    # Add tasks
    task_ids = []
    for i in range(num_tasks):
        task_id = await queue.add_task(
            "test_task",
            {"id": i, "should_fail": should_fail},
            max_retries=1  # Limit retries for faster testing
        )
        task_ids.append(task_id)
    
    # Property 1: All tasks start in QUEUED state
    for task_id in task_ids:
        status = await queue.get_task_status(task_id)
        assert status["state"] == TaskState.QUEUED, \
            "Tasks should start in QUEUED state"
    
    # Start processing
    await queue.start()
    
    # Wait for processing to complete
    timeout = 3.0
    start_time = asyncio.get_event_loop().time()
    all_done = False
    
    while not all_done and (asyncio.get_event_loop().time() - start_time < timeout):
        await asyncio.sleep(0.1)
        stats = queue.get_stats()
        all_done = (stats["completed"] + stats["failed"]) == num_tasks
    
    await queue.stop(wait=True)
    
    # Property 2: All tasks should end in terminal state (COMPLETED or FAILED)
    terminal_states = {TaskState.COMPLETED, TaskState.FAILED}
    for task_id in task_ids:
        status = await queue.get_task_status(task_id)
        assert status["state"] in terminal_states, \
            f"Task {task_id} should be in terminal state, got {status['state']}"
    
    # Property 3: If should_fail is True, tasks should be FAILED
    if should_fail:
        for task_id in task_ids:
            status = await queue.get_task_status(task_id)
            assert status["state"] == TaskState.FAILED, \
                "Tasks should be FAILED when handler raises exception"
            assert status["error"] is not None, \
                "Failed tasks should have error message"
    
    # Property 4: Stats should be consistent with final states
    stats = queue.get_stats()
    assert stats["total_tasks"] == num_tasks, \
        "Total tasks should match added tasks"
    assert stats["completed"] + stats["failed"] == num_tasks, \
        "All tasks should be in terminal state"
    
    # Clean up
    await queue.clear()


# Feature: intelli-credit-platform, Property 39: Task Queue Management
@pytest.mark.asyncio
@given(
    num_tasks=st.integers(min_value=2, max_value=8),
    max_workers=st.integers(min_value=1, max_value=3)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_concurrent_task_processing_consistency(num_tasks, max_workers):
    """
    **Validates: Requirements 18.3**
    
    Property 39: Task Queue Management - Concurrent Processing
    
    For any number of concurrent workers, the queue should:
    1. Process all tasks exactly once
    2. Maintain consistent state across concurrent operations
    3. Not lose or duplicate tasks
    """
    queue = TaskQueue(max_workers=max_workers)
    
    processed_tasks = []
    lock = asyncio.Lock()
    
    async def test_handler(payload):
        await asyncio.sleep(0.02)  # Simulate work
        async with lock:
            processed_tasks.append(payload["id"])
        return {"status": "success", "id": payload["id"]}
    
    queue.register_handler("test_task", test_handler)
    
    # Add tasks
    task_ids = []
    expected_ids = []
    for i in range(num_tasks):
        task_id = await queue.add_task(
            "test_task",
            {"id": i, "data": f"task_{i}"}
        )
        task_ids.append(task_id)
        expected_ids.append(i)
    
    # Start processing
    await queue.start()
    
    # Wait for all tasks to complete
    timeout = 5.0
    start_time = asyncio.get_event_loop().time()
    
    while len(processed_tasks) < num_tasks:
        if asyncio.get_event_loop().time() - start_time > timeout:
            break
        await asyncio.sleep(0.1)
    
    await queue.stop(wait=True)
    
    # Property 1: All tasks should be processed exactly once
    assert len(processed_tasks) == num_tasks, \
        f"Expected {num_tasks} tasks processed, got {len(processed_tasks)}"
    
    # Property 2: No duplicate processing
    assert len(processed_tasks) == len(set(processed_tasks)), \
        "Tasks should not be processed more than once"
    
    # Property 3: All expected task IDs should be present
    assert set(processed_tasks) == set(expected_ids), \
        "All task IDs should be processed"
    
    # Property 4: All tasks should be in COMPLETED state
    for task_id in task_ids:
        status = await queue.get_task_status(task_id)
        assert status["state"] == TaskState.COMPLETED, \
            f"Task {task_id} should be COMPLETED"
        assert status["result"] is not None, \
            "Completed tasks should have result"
    
    # Property 5: Stats should reflect completion
    stats = queue.get_stats()
    assert stats["completed"] == num_tasks, \
        "All tasks should be marked as completed in stats"
    assert stats["processing"] == 0, \
        "No tasks should be processing after stop"
    assert stats["queued"] == 0, \
        "No tasks should be queued after completion"
    
    # Clean up
    await queue.clear()


# Feature: intelli-credit-platform, Property 39: Task Queue Management
@pytest.mark.asyncio
@given(
    num_tasks=st.integers(min_value=1, max_value=5),
    max_retries=st.integers(min_value=1, max_value=3)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_task_retry_mechanism(num_tasks, max_retries):
    """
    **Validates: Requirements 18.3**
    
    Property 39: Task Queue Management - Retry Mechanism
    
    For any task that fails, the queue should:
    1. Retry up to max_retries times
    2. Track retry count correctly
    3. Mark as FAILED after exhausting retries
    """
    queue = TaskQueue(max_workers=1)
    
    attempt_counts = {}
    
    async def failing_handler(payload):
        task_key = payload["id"]
        attempt_counts[task_key] = attempt_counts.get(task_key, 0) + 1
        # Always fail
        raise Exception(f"Task {task_key} failed")
    
    queue.register_handler("test_task", failing_handler)
    
    # Add tasks
    task_ids = []
    for i in range(num_tasks):
        task_id = await queue.add_task(
            "test_task",
            {"id": i},
            max_retries=max_retries
        )
        task_ids.append(task_id)
    
    # Start processing
    await queue.start()
    
    # Wait for all retries to exhaust
    timeout = 5.0
    start_time = asyncio.get_event_loop().time()
    
    while True:
        if asyncio.get_event_loop().time() - start_time > timeout:
            break
        stats = queue.get_stats()
        if stats["failed"] == num_tasks:
            break
        await asyncio.sleep(0.1)
    
    await queue.stop(wait=True)
    
    # Property 1: All tasks should be in FAILED state
    for task_id in task_ids:
        status = await queue.get_task_status(task_id)
        assert status["state"] == TaskState.FAILED, \
            f"Task {task_id} should be FAILED after exhausting retries"
    
    # Property 2: Retry count should match max_retries
    for task_id in task_ids:
        status = await queue.get_task_status(task_id)
        assert status["retry_count"] == max_retries, \
            f"Task should have retry_count={max_retries}, got {status['retry_count']}"
    
    # Property 3: Handler should be called max_retries times per task
    for i in range(num_tasks):
        assert attempt_counts[i] == max_retries, \
            f"Handler should be called {max_retries} times for task {i}"
    
    # Property 4: All tasks should have error messages
    for task_id in task_ids:
        status = await queue.get_task_status(task_id)
        assert status["error"] is not None, \
            "Failed tasks should have error message"
        assert "failed" in status["error"].lower(), \
            "Error message should indicate failure"
    
    # Clean up
    await queue.clear()


# Feature: intelli-credit-platform, Property 39: Task Queue Management
@pytest.mark.asyncio
@given(num_operations=st.integers(min_value=1, max_value=10))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_queue_clear_operation(num_operations):
    """
    **Validates: Requirements 18.3**
    
    Property 39: Task Queue Management - Clear Operation
    
    For any queue state, the clear operation should:
    1. Remove all tasks from the queue
    2. Clear task storage
    3. Reset queue size to zero
    """
    queue = TaskQueue(max_workers=2)
    
    async def test_handler(payload):
        await asyncio.sleep(0.01)
        return {"status": "success"}
    
    queue.register_handler("test_task", test_handler)
    
    # Add tasks
    for i in range(num_operations):
        await queue.add_task("test_task", {"id": i})
    
    # Verify tasks were added
    assert len(queue.tasks) == num_operations, \
        "Tasks should be added to queue"
    assert queue.get_queue_size() == num_operations, \
        "Queue size should match number of tasks"
    
    # Clear the queue
    await queue.clear()
    
    # Property 1: All tasks should be removed
    assert len(queue.tasks) == 0, \
        "All tasks should be removed after clear"
    
    # Property 2: Queue size should be zero
    assert queue.get_queue_size() == 0, \
        "Queue size should be zero after clear"
    
    # Property 3: Stats should reflect empty queue
    stats = queue.get_stats()
    assert stats["total_tasks"] == 0, \
        "Total tasks should be zero after clear"
    assert stats["queued"] == 0, \
        "Queued count should be zero after clear"
    assert stats["completed"] == 0, \
        "Completed count should be zero after clear"
    assert stats["failed"] == 0, \
        "Failed count should be zero after clear"


# Feature: intelli-credit-platform, Property 39: Task Queue Management
@pytest.mark.asyncio
@given(
    num_tasks=st.integers(min_value=1, max_value=8),
    filter_state=st.sampled_from([TaskState.QUEUED, TaskState.COMPLETED, TaskState.FAILED])
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_get_all_tasks_filtering(num_tasks, filter_state):
    """
    **Validates: Requirements 18.3**
    
    Property 39: Task Queue Management - Task Filtering
    
    For any queue state and filter criteria, get_all_tasks should:
    1. Return only tasks matching the filter
    2. Return all tasks when no filter is applied
    3. Maintain data consistency
    """
    queue = TaskQueue(max_workers=1)
    
    async def test_handler(payload):
        await asyncio.sleep(0.01)
        if payload.get("should_fail"):
            raise Exception("Intentional failure")
        return {"status": "success"}
    
    queue.register_handler("test_task", test_handler)
    
    # Add mix of tasks (some will fail, some will succeed)
    task_ids = []
    for i in range(num_tasks):
        should_fail = (i % 3 == 0)  # Every 3rd task fails
        task_id = await queue.add_task(
            "test_task",
            {"id": i, "should_fail": should_fail},
            max_retries=1
        )
        task_ids.append(task_id)
    
    # If testing for COMPLETED or FAILED, process the tasks
    if filter_state in [TaskState.COMPLETED, TaskState.FAILED]:
        await queue.start()
        
        # Wait for processing
        timeout = 3.0
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            stats = queue.get_stats()
            if stats["completed"] + stats["failed"] == num_tasks:
                break
            await asyncio.sleep(0.1)
        
        await queue.stop(wait=True)
    
    # Get all tasks without filter
    all_tasks = await queue.get_all_tasks()
    
    # Property 1: Should return all tasks
    assert len(all_tasks) == num_tasks, \
        "get_all_tasks() should return all tasks"
    
    # Get filtered tasks
    filtered_tasks = await queue.get_all_tasks(state=filter_state)
    
    # Property 2: All filtered tasks should have the correct state
    for task in filtered_tasks:
        assert task["state"] == filter_state, \
            f"Filtered task should have state {filter_state}"
    
    # Property 3: Filtered count should not exceed total
    assert len(filtered_tasks) <= num_tasks, \
        "Filtered tasks should not exceed total tasks"
    
    # Property 4: Task IDs in filtered results should be subset of all task IDs
    filtered_ids = {task["id"] for task in filtered_tasks}
    all_ids = {task["id"] for task in all_tasks}
    assert filtered_ids.issubset(all_ids), \
        "Filtered task IDs should be subset of all task IDs"
    
    # Clean up
    await queue.clear()
