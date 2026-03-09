"""
Unit tests for TaskQueue class.

Tests task queue functionality including:
- Task addition and state management
- Task processing and completion
- Error handling and retries
- Worker management
- Queue statistics
"""

import pytest
import asyncio
from datetime import datetime
from app.services.task_queue import TaskQueue, TaskState, Task


@pytest.mark.asyncio
async def test_task_queue_initialization():
    """Test TaskQueue initialization with default and custom workers."""
    # Default workers
    queue = TaskQueue()
    assert queue.max_workers == 5
    assert not queue.running
    assert len(queue.tasks) == 0
    assert queue.queue.qsize() == 0
    
    # Custom workers
    queue = TaskQueue(max_workers=10)
    assert queue.max_workers == 10


@pytest.mark.asyncio
async def test_register_handler():
    """Test registering task handlers."""
    queue = TaskQueue()
    
    async def test_handler(payload):
        return {"result": "success"}
    
    queue.register_handler("test_task", test_handler)
    assert "test_task" in queue.handlers
    assert queue.handlers["test_task"] == test_handler


@pytest.mark.asyncio
async def test_add_task():
    """Test adding tasks to the queue."""
    queue = TaskQueue()
    
    async def test_handler(payload):
        return {"result": "success"}
    
    queue.register_handler("test_task", test_handler)
    
    # Add task
    task_id = await queue.add_task("test_task", {"data": "test"})
    
    assert task_id is not None
    assert task_id in queue.tasks
    assert queue.tasks[task_id].state == TaskState.QUEUED
    assert queue.queue.qsize() == 1


@pytest.mark.asyncio
async def test_add_task_without_handler():
    """Test adding task without registered handler raises error."""
    queue = TaskQueue()
    
    with pytest.raises(ValueError, match="No handler registered"):
        await queue.add_task("unknown_task", {"data": "test"})


@pytest.mark.asyncio
async def test_get_task_status():
    """Test retrieving task status."""
    queue = TaskQueue()
    
    async def test_handler(payload):
        return {"result": "success"}
    
    queue.register_handler("test_task", test_handler)
    
    # Add task
    task_id = await queue.add_task("test_task", {"data": "test"})
    
    # Get status
    status = await queue.get_task_status(task_id)
    
    assert status is not None
    assert status["id"] == task_id
    assert status["task_type"] == "test_task"
    assert status["state"] == TaskState.QUEUED
    assert status["created_at"] is not None
    assert status["started_at"] is None
    assert status["completed_at"] is None
    assert status["error"] is None
    assert status["retry_count"] == 0


@pytest.mark.asyncio
async def test_get_task_status_not_found():
    """Test getting status for non-existent task."""
    queue = TaskQueue()
    status = await queue.get_task_status("non_existent_id")
    assert status is None


@pytest.mark.asyncio
async def test_get_all_tasks():
    """Test retrieving all tasks."""
    queue = TaskQueue()
    
    async def test_handler(payload):
        return {"result": "success"}
    
    queue.register_handler("test_task", test_handler)
    
    # Add multiple tasks
    task_id1 = await queue.add_task("test_task", {"data": "test1"})
    task_id2 = await queue.add_task("test_task", {"data": "test2"})
    
    # Get all tasks
    all_tasks = await queue.get_all_tasks()
    
    assert len(all_tasks) == 2
    assert any(t["id"] == task_id1 for t in all_tasks)
    assert any(t["id"] == task_id2 for t in all_tasks)


@pytest.mark.asyncio
async def test_get_all_tasks_filtered_by_state():
    """Test retrieving tasks filtered by state."""
    queue = TaskQueue()
    
    async def test_handler(payload):
        return {"result": "success"}
    
    queue.register_handler("test_task", test_handler)
    
    # Add tasks
    task_id1 = await queue.add_task("test_task", {"data": "test1"})
    task_id2 = await queue.add_task("test_task", {"data": "test2"})
    
    # Manually change one task state for testing
    async with queue._lock:
        queue.tasks[task_id1].state = TaskState.COMPLETED
    
    # Get queued tasks only
    queued_tasks = await queue.get_all_tasks(state=TaskState.QUEUED)
    assert len(queued_tasks) == 1
    assert queued_tasks[0]["id"] == task_id2
    
    # Get completed tasks only
    completed_tasks = await queue.get_all_tasks(state=TaskState.COMPLETED)
    assert len(completed_tasks) == 1
    assert completed_tasks[0]["id"] == task_id1


@pytest.mark.asyncio
async def test_task_processing_success():
    """Test successful task processing."""
    queue = TaskQueue(max_workers=1)
    
    processed_data = []
    
    async def test_handler(payload):
        processed_data.append(payload)
        return {"result": "success", "data": payload["data"]}
    
    queue.register_handler("test_task", test_handler)
    
    # Add task
    task_id = await queue.add_task("test_task", {"data": "test"})
    
    # Start queue
    await queue.start()
    
    # Wait for task to complete
    await asyncio.sleep(0.5)
    
    # Check task status
    status = await queue.get_task_status(task_id)
    
    assert status["state"] == TaskState.COMPLETED
    assert status["result"] == {"result": "success", "data": "test"}
    assert status["error"] is None
    assert len(processed_data) == 1
    assert processed_data[0] == {"data": "test"}
    
    # Stop queue
    await queue.stop(wait=False)


@pytest.mark.asyncio
async def test_task_processing_failure_with_retry():
    """Test task processing failure with automatic retry."""
    queue = TaskQueue(max_workers=1)
    
    call_count = [0]
    
    async def failing_handler(payload):
        call_count[0] += 1
        if call_count[0] < 3:
            raise Exception("Temporary failure")
        return {"result": "success"}
    
    queue.register_handler("test_task", failing_handler)
    
    # Add task with max_retries=3
    task_id = await queue.add_task("test_task", {"data": "test"}, max_retries=3)
    
    # Start queue
    await queue.start()
    
    # Wait for retries to complete
    await asyncio.sleep(1.5)
    
    # Check task status
    status = await queue.get_task_status(task_id)
    
    assert status["state"] == TaskState.COMPLETED
    assert status["retry_count"] == 2  # Failed twice, succeeded on third attempt
    assert call_count[0] == 3
    
    # Stop queue
    await queue.stop(wait=False)


@pytest.mark.asyncio
async def test_task_processing_failure_max_retries():
    """Test task processing failure after max retries."""
    queue = TaskQueue(max_workers=1)
    
    async def failing_handler(payload):
        raise Exception("Permanent failure")
    
    queue.register_handler("test_task", failing_handler)
    
    # Add task with max_retries=2
    task_id = await queue.add_task("test_task", {"data": "test"}, max_retries=2)
    
    # Start queue
    await queue.start()
    
    # Wait for retries to exhaust
    await asyncio.sleep(1.0)
    
    # Check task status
    status = await queue.get_task_status(task_id)
    
    assert status["state"] == TaskState.FAILED
    assert status["retry_count"] == 2
    assert status["error"] == "Permanent failure"
    
    # Stop queue
    await queue.stop(wait=False)


@pytest.mark.asyncio
async def test_concurrent_task_processing():
    """Test concurrent processing of multiple tasks."""
    queue = TaskQueue(max_workers=3)
    
    processed_tasks = []
    
    async def test_handler(payload):
        await asyncio.sleep(0.1)  # Simulate work
        processed_tasks.append(payload["id"])
        return {"result": "success"}
    
    queue.register_handler("test_task", test_handler)
    
    # Add multiple tasks
    task_ids = []
    for i in range(5):
        task_id = await queue.add_task("test_task", {"id": i})
        task_ids.append(task_id)
    
    # Start queue
    await queue.start()
    
    # Wait for all tasks to complete
    await asyncio.sleep(1.0)
    
    # Check all tasks completed
    for task_id in task_ids:
        status = await queue.get_task_status(task_id)
        assert status["state"] == TaskState.COMPLETED
    
    assert len(processed_tasks) == 5
    
    # Stop queue
    await queue.stop(wait=False)


@pytest.mark.asyncio
async def test_start_stop_queue():
    """Test starting and stopping the queue."""
    queue = TaskQueue(max_workers=2)
    
    assert not queue.running
    assert len(queue.workers) == 0
    
    # Start queue
    await queue.start()
    
    assert queue.running
    assert len(queue.workers) == 2
    
    # Try starting again (should log warning)
    await queue.start()
    assert queue.running
    
    # Stop queue
    await queue.stop(wait=False)
    
    assert not queue.running
    assert len(queue.workers) == 0
    
    # Try stopping again (should log warning)
    await queue.stop(wait=False)
    assert not queue.running


@pytest.mark.asyncio
async def test_stop_queue_with_wait():
    """Test stopping queue with wait for completion."""
    queue = TaskQueue(max_workers=1)
    
    async def slow_handler(payload):
        await asyncio.sleep(0.3)
        return {"result": "success"}
    
    queue.register_handler("test_task", slow_handler)
    
    # Add task
    task_id = await queue.add_task("test_task", {"data": "test"})
    
    # Start queue
    await queue.start()
    
    # Wait a bit then stop with wait=True
    await asyncio.sleep(0.1)
    await queue.stop(wait=True)
    
    # Task should be completed
    status = await queue.get_task_status(task_id)
    assert status["state"] == TaskState.COMPLETED


@pytest.mark.asyncio
async def test_clear_queue():
    """Test clearing the queue."""
    queue = TaskQueue()
    
    async def test_handler(payload):
        return {"result": "success"}
    
    queue.register_handler("test_task", test_handler)
    
    # Add tasks
    await queue.add_task("test_task", {"data": "test1"})
    await queue.add_task("test_task", {"data": "test2"})
    
    assert len(queue.tasks) == 2
    assert queue.queue.qsize() == 2
    
    # Clear queue
    await queue.clear()
    
    assert len(queue.tasks) == 0
    assert queue.queue.qsize() == 0


@pytest.mark.asyncio
async def test_get_queue_size():
    """Test getting queue size."""
    queue = TaskQueue()
    
    async def test_handler(payload):
        return {"result": "success"}
    
    queue.register_handler("test_task", test_handler)
    
    assert queue.get_queue_size() == 0
    
    # Add tasks
    await queue.add_task("test_task", {"data": "test1"})
    await queue.add_task("test_task", {"data": "test2"})
    
    assert queue.get_queue_size() == 2


@pytest.mark.asyncio
async def test_get_stats():
    """Test getting queue statistics."""
    queue = TaskQueue(max_workers=3)
    
    async def test_handler(payload):
        await asyncio.sleep(0.5)
        return {"result": "success"}
    
    queue.register_handler("test_task", test_handler)
    
    # Initial stats
    stats = queue.get_stats()
    assert stats["total_tasks"] == 0
    assert stats["queued"] == 0
    assert stats["processing"] == 0
    assert stats["completed"] == 0
    assert stats["failed"] == 0
    assert stats["workers"] == 3
    assert not stats["running"]
    
    # Add tasks
    await queue.add_task("test_task", {"data": "test1"})
    await queue.add_task("test_task", {"data": "test2"})
    
    stats = queue.get_stats()
    assert stats["total_tasks"] == 2
    assert stats["queued"] == 2
    assert stats["queue_size"] == 2
    
    # Start processing
    await queue.start()
    await asyncio.sleep(0.1)
    
    stats = queue.get_stats()
    assert stats["running"]
    
    # Wait for completion
    await asyncio.sleep(1.0)
    
    stats = queue.get_stats()
    assert stats["completed"] == 2
    assert stats["queued"] == 0
    assert stats["processing"] == 0
    
    # Stop queue
    await queue.stop(wait=False)


@pytest.mark.asyncio
async def test_task_state_transitions():
    """Test task state transitions through lifecycle."""
    queue = TaskQueue(max_workers=1)
    
    async def test_handler(payload):
        return {"result": "success"}
    
    queue.register_handler("test_task", test_handler)
    
    # Add task - should be QUEUED
    task_id = await queue.add_task("test_task", {"data": "test"})
    status = await queue.get_task_status(task_id)
    assert status["state"] == TaskState.QUEUED
    
    # Start processing
    await queue.start()
    
    # Wait a bit - should be PROCESSING or COMPLETED
    await asyncio.sleep(0.2)
    status = await queue.get_task_status(task_id)
    assert status["state"] in [TaskState.PROCESSING, TaskState.COMPLETED]
    
    # Wait for completion - should be COMPLETED
    await asyncio.sleep(0.5)
    status = await queue.get_task_status(task_id)
    assert status["state"] == TaskState.COMPLETED
    assert status["started_at"] is not None
    assert status["completed_at"] is not None
    
    # Stop queue
    await queue.stop(wait=False)


@pytest.mark.asyncio
async def test_multiple_task_types():
    """Test handling multiple task types."""
    queue = TaskQueue(max_workers=2)
    
    results = {"type1": [], "type2": []}
    
    async def handler1(payload):
        results["type1"].append(payload)
        return {"type": "type1"}
    
    async def handler2(payload):
        results["type2"].append(payload)
        return {"type": "type2"}
    
    queue.register_handler("type1", handler1)
    queue.register_handler("type2", handler2)
    
    # Add tasks of different types
    task_id1 = await queue.add_task("type1", {"data": "test1"})
    task_id2 = await queue.add_task("type2", {"data": "test2"})
    task_id3 = await queue.add_task("type1", {"data": "test3"})
    
    # Start processing
    await queue.start()
    await asyncio.sleep(0.5)
    
    # Check results
    assert len(results["type1"]) == 2
    assert len(results["type2"]) == 1
    
    status1 = await queue.get_task_status(task_id1)
    status2 = await queue.get_task_status(task_id2)
    status3 = await queue.get_task_status(task_id3)
    
    assert status1["state"] == TaskState.COMPLETED
    assert status2["state"] == TaskState.COMPLETED
    assert status3["state"] == TaskState.COMPLETED
    
    # Stop queue
    await queue.stop(wait=False)
