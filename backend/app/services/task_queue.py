"""
Task Queue for Batch Processing

This module implements a task queue system for handling batch processing
of credit analysis requests. It manages task lifecycle, state transitions,
and concurrent task processing.

Requirements: 18.3 - Batch Processing and Scalability
"""

import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


class TaskState(str, Enum):
    """Task lifecycle states."""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """Represents a task in the queue."""
    id: str
    task_type: str
    payload: Dict[str, Any]
    state: TaskState = TaskState.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[Any] = None
    retry_count: int = 0
    max_retries: int = 3


class TaskQueue:
    """
    Task queue for batch processing of credit analysis requests.
    
    Features:
    - Task state management (pending, queued, processing, completed, failed)
    - Concurrent task processing with configurable workers
    - Task status tracking and retrieval
    - Automatic retry on failure
    - FIFO queue ordering
    
    Example:
        queue = TaskQueue(max_workers=5)
        
        # Register task handler
        async def process_analysis(payload):
            # Process the analysis
            return {"status": "success"}
        
        queue.register_handler("analysis", process_analysis)
        
        # Add task to queue
        task_id = await queue.add_task("analysis", {"app_id": "123"})
        
        # Start processing
        await queue.start()
        
        # Check task status
        status = await queue.get_task_status(task_id)
    """
    
    def __init__(self, max_workers: int = 5):
        """
        Initialize the task queue.
        
        Args:
            max_workers: Maximum number of concurrent workers
        """
        self.max_workers = max_workers
        self.tasks: Dict[str, Task] = {}
        self.queue: asyncio.Queue = asyncio.Queue()
        self.handlers: Dict[str, Callable] = {}
        self.workers: List[asyncio.Task] = []
        self.running = False
        self._lock = asyncio.Lock()
        
        logger.info(f"TaskQueue initialized with {max_workers} workers")
    
    def register_handler(self, task_type: str, handler: Callable) -> None:
        """
        Register a handler function for a specific task type.
        
        Args:
            task_type: Type of task (e.g., "analysis", "document_processing")
            handler: Async function to handle the task
        """
        self.handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")
    
    async def add_task(
        self,
        task_type: str,
        payload: Dict[str, Any],
        max_retries: int = 3
    ) -> str:
        """
        Add a task to the queue.
        
        Args:
            task_type: Type of task
            payload: Task data/parameters
            max_retries: Maximum number of retry attempts
        
        Returns:
            Task ID
        
        Raises:
            ValueError: If task_type has no registered handler
        """
        if task_type not in self.handlers:
            raise ValueError(f"No handler registered for task type: {task_type}")
        
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            task_type=task_type,
            payload=payload,
            state=TaskState.PENDING,
            max_retries=max_retries
        )
        
        async with self._lock:
            self.tasks[task_id] = task
            task.state = TaskState.QUEUED
            await self.queue.put(task_id)
        
        logger.info(f"Task {task_id} added to queue (type: {task_type})")
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a task.
        
        Args:
            task_id: Task identifier
        
        Returns:
            Task status dictionary or None if task not found
        """
        async with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return None
            
            return {
                "id": task.id,
                "task_type": task.task_type,
                "state": task.state,
                "created_at": task.created_at.isoformat(),
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "error": task.error,
                "result": task.result,
                "retry_count": task.retry_count
            }
    
    async def get_all_tasks(
        self,
        state: Optional[TaskState] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all tasks, optionally filtered by state.
        
        Args:
            state: Optional state filter
        
        Returns:
            List of task status dictionaries
        """
        async with self._lock:
            tasks = self.tasks.values()
            if state:
                tasks = [t for t in tasks if t.state == state]
            
            return [
                {
                    "id": task.id,
                    "task_type": task.task_type,
                    "state": task.state,
                    "created_at": task.created_at.isoformat(),
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "error": task.error,
                    "retry_count": task.retry_count
                }
                for task in tasks
            ]
    
    async def _process_task(self, task: Task) -> None:
        """
        Process a single task.
        
        Args:
            task: Task to process
        """
        try:
            # Update state to processing
            async with self._lock:
                task.state = TaskState.PROCESSING
                task.started_at = datetime.utcnow()
            
            logger.info(f"Processing task {task.id} (type: {task.task_type})")
            
            # Get handler and execute
            handler = self.handlers[task.task_type]
            result = await handler(task.payload)
            
            # Mark as completed
            async with self._lock:
                task.state = TaskState.COMPLETED
                task.completed_at = datetime.utcnow()
                task.result = result
            
            logger.info(f"Task {task.id} completed successfully")
            
        except Exception as e:
            logger.error(f"Task {task.id} failed: {str(e)}", exc_info=True)
            
            async with self._lock:
                task.retry_count += 1
                
                if task.retry_count < task.max_retries:
                    # Retry the task
                    task.state = TaskState.QUEUED
                    await self.queue.put(task.id)
                    logger.info(f"Task {task.id} queued for retry ({task.retry_count}/{task.max_retries})")
                else:
                    # Mark as failed
                    task.state = TaskState.FAILED
                    task.completed_at = datetime.utcnow()
                    task.error = str(e)
                    logger.error(f"Task {task.id} failed after {task.retry_count} retries")
    
    async def _worker(self, worker_id: int) -> None:
        """
        Worker coroutine that processes tasks from the queue.
        
        Args:
            worker_id: Worker identifier for logging
        """
        logger.info(f"Worker {worker_id} started")
        
        while self.running:
            try:
                # Get task from queue with timeout
                task_id = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=1.0
                )
                
                async with self._lock:
                    task = self.tasks.get(task_id)
                
                if task:
                    await self._process_task(task)
                
                self.queue.task_done()
                
            except asyncio.TimeoutError:
                # No tasks available, continue waiting
                continue
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {str(e)}", exc_info=True)
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def start(self) -> None:
        """
        Start the task queue workers.
        """
        if self.running:
            logger.warning("TaskQueue is already running")
            return
        
        self.running = True
        
        # Start worker coroutines
        self.workers = [
            asyncio.create_task(self._worker(i))
            for i in range(self.max_workers)
        ]
        
        logger.info(f"TaskQueue started with {self.max_workers} workers")
    
    async def stop(self, wait: bool = True) -> None:
        """
        Stop the task queue workers.
        
        Args:
            wait: If True, wait for all queued tasks to complete
        """
        if not self.running:
            logger.warning("TaskQueue is not running")
            return
        
        logger.info("Stopping TaskQueue...")
        
        if wait:
            # Wait for all tasks in queue to complete
            await self.queue.join()
        
        # Stop workers
        self.running = False
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers = []
        
        logger.info("TaskQueue stopped")
    
    async def clear(self) -> None:
        """
        Clear all tasks from the queue and task storage.
        """
        async with self._lock:
            # Clear queue
            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                    self.queue.task_done()
                except asyncio.QueueEmpty:
                    break
            
            # Clear tasks
            self.tasks.clear()
        
        logger.info("TaskQueue cleared")
    
    def get_queue_size(self) -> int:
        """
        Get the current number of tasks in the queue.
        
        Returns:
            Number of queued tasks
        """
        return self.queue.qsize()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics.
        
        Returns:
            Dictionary with queue statistics
        """
        stats = {
            "total_tasks": len(self.tasks),
            "queued": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0,
            "queue_size": self.queue.qsize(),
            "workers": self.max_workers,
            "running": self.running
        }
        
        for task in self.tasks.values():
            if task.state == TaskState.QUEUED:
                stats["queued"] += 1
            elif task.state == TaskState.PROCESSING:
                stats["processing"] += 1
            elif task.state == TaskState.COMPLETED:
                stats["completed"] += 1
            elif task.state == TaskState.FAILED:
                stats["failed"] += 1
        
        return stats
