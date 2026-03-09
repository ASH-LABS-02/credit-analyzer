"""
Capacity Management Service

This module implements capacity management for the credit analysis platform.
It monitors system capacity, queues requests when at capacity, estimates wait times,
and notifies users.

Requirements: 18.4 - Batch Processing and Scalability
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field
import logging
from statistics import mean

logger = logging.getLogger(__name__)


@dataclass
class CapacityMetrics:
    """Metrics for capacity tracking."""
    max_concurrent_tasks: int
    current_processing: int
    queued_tasks: int
    completed_last_hour: int
    average_processing_time: float  # in seconds
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def is_at_capacity(self) -> bool:
        """Check if system is at capacity."""
        return self.current_processing >= self.max_concurrent_tasks
    
    @property
    def utilization_percentage(self) -> float:
        """Calculate current utilization percentage."""
        if self.max_concurrent_tasks == 0:
            return 0.0
        return (self.current_processing / self.max_concurrent_tasks) * 100


@dataclass
class WaitTimeEstimate:
    """Wait time estimation for queued requests."""
    estimated_wait_seconds: float
    position_in_queue: int
    current_queue_size: int
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class CapacityManager:
    """
    Manages system capacity and provides wait time estimates.
    
    Features:
    - Capacity checking based on concurrent task limits
    - Request queueing when at capacity
    - Wait time estimation based on historical processing times
    - User notification with estimated wait times
    - Capacity metrics tracking
    
    Example:
        manager = CapacityManager(max_concurrent_tasks=10)
        
        # Check if can accept new request
        if manager.can_accept_request():
            # Process immediately
            await manager.start_processing(request_id)
        else:
            # Queue and notify user
            wait_estimate = manager.estimate_wait_time()
            await manager.queue_request(request_id)
            await notify_user(wait_estimate)
    """
    
    def __init__(
        self,
        max_concurrent_tasks: int = 10,
        default_processing_time: float = 300.0  # 5 minutes default
    ):
        """
        Initialize the capacity manager.
        
        Args:
            max_concurrent_tasks: Maximum number of concurrent processing tasks
            default_processing_time: Default processing time in seconds (used when no history)
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self.default_processing_time = default_processing_time
        
        # Track currently processing tasks
        self.processing_tasks: Dict[str, datetime] = {}
        
        # Track queued requests
        self.queued_requests: List[str] = []
        
        # Track processing times for estimation
        self.processing_times: List[float] = []
        self.max_history_size = 100  # Keep last 100 processing times
        
        # Track completed tasks in last hour
        self.completed_tasks: List[datetime] = []
        
        self._lock = asyncio.Lock()
        
        logger.info(
            f"CapacityManager initialized with max_concurrent_tasks={max_concurrent_tasks}"
        )
    
    async def can_accept_request(self) -> bool:
        """
        Check if system can accept a new request for immediate processing.
        
        Returns:
            True if capacity available, False if at capacity
        """
        async with self._lock:
            return len(self.processing_tasks) < self.max_concurrent_tasks
    
    async def is_at_capacity(self) -> bool:
        """
        Check if system is at capacity.
        
        Returns:
            True if at capacity, False otherwise
        """
        async with self._lock:
            return len(self.processing_tasks) >= self.max_concurrent_tasks
    
    async def start_processing(self, request_id: str) -> None:
        """
        Mark a request as started processing.
        
        Args:
            request_id: Unique identifier for the request
        
        Raises:
            ValueError: If system is at capacity
        """
        async with self._lock:
            if len(self.processing_tasks) >= self.max_concurrent_tasks:
                raise ValueError(
                    f"Cannot start processing: at capacity "
                    f"({len(self.processing_tasks)}/{self.max_concurrent_tasks})"
                )
            
            self.processing_tasks[request_id] = datetime.utcnow()
            
            # Remove from queue if it was queued
            if request_id in self.queued_requests:
                self.queued_requests.remove(request_id)
        
        logger.info(
            f"Started processing request {request_id} "
            f"({len(self.processing_tasks)}/{self.max_concurrent_tasks} slots used)"
        )
    
    async def complete_processing(
        self,
        request_id: str,
        processing_time: Optional[float] = None
    ) -> None:
        """
        Mark a request as completed processing.
        
        Args:
            request_id: Unique identifier for the request
            processing_time: Optional processing time in seconds (calculated if not provided)
        """
        async with self._lock:
            if request_id not in self.processing_tasks:
                logger.warning(f"Request {request_id} not found in processing tasks")
                return
            
            # Calculate processing time if not provided
            if processing_time is None:
                start_time = self.processing_tasks[request_id]
                processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Record processing time for estimation
            self.processing_times.append(processing_time)
            if len(self.processing_times) > self.max_history_size:
                self.processing_times.pop(0)
            
            # Record completion
            self.completed_tasks.append(datetime.utcnow())
            
            # Clean up old completed tasks (keep last hour)
            cutoff = datetime.utcnow() - timedelta(hours=1)
            self.completed_tasks = [
                t for t in self.completed_tasks if t > cutoff
            ]
            
            # Remove from processing
            del self.processing_tasks[request_id]
        
        logger.info(
            f"Completed processing request {request_id} "
            f"in {processing_time:.2f}s "
            f"({len(self.processing_tasks)}/{self.max_concurrent_tasks} slots used)"
        )
    
    async def queue_request(self, request_id: str) -> int:
        """
        Queue a request when system is at capacity.
        
        Args:
            request_id: Unique identifier for the request
        
        Returns:
            Position in queue (0-indexed)
        """
        async with self._lock:
            if request_id not in self.queued_requests:
                self.queued_requests.append(request_id)
            
            position = self.queued_requests.index(request_id)
        
        logger.info(
            f"Queued request {request_id} at position {position} "
            f"(queue size: {len(self.queued_requests)})"
        )
        
        return position
    
    async def remove_from_queue(self, request_id: str) -> bool:
        """
        Remove a request from the queue.
        
        Args:
            request_id: Unique identifier for the request
        
        Returns:
            True if removed, False if not in queue
        """
        async with self._lock:
            if request_id in self.queued_requests:
                self.queued_requests.remove(request_id)
                logger.info(f"Removed request {request_id} from queue")
                return True
            return False
    
    async def get_queue_position(self, request_id: str) -> Optional[int]:
        """
        Get the position of a request in the queue.
        
        Args:
            request_id: Unique identifier for the request
        
        Returns:
            Position in queue (0-indexed) or None if not in queue
        """
        async with self._lock:
            if request_id in self.queued_requests:
                return self.queued_requests.index(request_id)
            return None
    
    def _get_average_processing_time(self) -> float:
        """
        Calculate average processing time from history.
        
        Returns:
            Average processing time in seconds
        """
        if not self.processing_times:
            return self.default_processing_time
        return mean(self.processing_times)
    
    async def estimate_wait_time(
        self,
        request_id: Optional[str] = None
    ) -> WaitTimeEstimate:
        """
        Estimate wait time for a request.
        
        If request_id is provided and the request is in the queue, estimates
        wait time based on its position. Otherwise, estimates wait time for
        a new request joining the queue.
        
        Args:
            request_id: Optional request identifier
        
        Returns:
            WaitTimeEstimate with estimated wait time and details
        """
        async with self._lock:
            # Get queue position
            if request_id and request_id in self.queued_requests:
                position = self.queued_requests.index(request_id)
            else:
                # New request would be added at the end
                position = len(self.queued_requests)
            
            queue_size = len(self.queued_requests)
            current_processing = len(self.processing_tasks)
            
            # Calculate average processing time
            avg_time = self._get_average_processing_time()
            
            # Estimate wait time
            # Formula: (position / max_concurrent) * avg_processing_time
            # This assumes tasks complete at a steady rate
            if self.max_concurrent_tasks > 0:
                # How many "batches" of concurrent tasks before this request?
                batches_ahead = position / self.max_concurrent_tasks
                estimated_wait = batches_ahead * avg_time
            else:
                estimated_wait = 0.0
            
            # Add time for currently processing tasks to complete
            if current_processing >= self.max_concurrent_tasks:
                # At capacity, add partial batch time
                estimated_wait += avg_time * 0.5  # Assume average halfway done
            
            # Generate user-friendly message
            if estimated_wait < 60:
                time_str = f"{int(estimated_wait)} seconds"
            elif estimated_wait < 3600:
                time_str = f"{int(estimated_wait / 60)} minutes"
            else:
                time_str = f"{estimated_wait / 3600:.1f} hours"
            
            message = (
                f"Your request is queued at position {position + 1} of {queue_size + 1}. "
                f"Estimated wait time: {time_str}. "
                f"You will be notified when processing begins."
            )
        
        estimate = WaitTimeEstimate(
            estimated_wait_seconds=estimated_wait,
            position_in_queue=position,
            current_queue_size=queue_size,
            message=message
        )
        
        logger.info(
            f"Wait time estimate for position {position}: {estimated_wait:.2f}s"
        )
        
        return estimate
    
    async def get_capacity_metrics(self) -> CapacityMetrics:
        """
        Get current capacity metrics.
        
        Returns:
            CapacityMetrics with current system state
        """
        async with self._lock:
            metrics = CapacityMetrics(
                max_concurrent_tasks=self.max_concurrent_tasks,
                current_processing=len(self.processing_tasks),
                queued_tasks=len(self.queued_requests),
                completed_last_hour=len(self.completed_tasks),
                average_processing_time=self._get_average_processing_time()
            )
        
        return metrics
    
    async def get_next_queued_request(self) -> Optional[str]:
        """
        Get the next request from the queue (FIFO).
        
        Returns:
            Request ID or None if queue is empty
        """
        async with self._lock:
            if self.queued_requests:
                return self.queued_requests[0]
            return None
    
    async def clear_queue(self) -> int:
        """
        Clear all queued requests.
        
        Returns:
            Number of requests cleared
        """
        async with self._lock:
            count = len(self.queued_requests)
            self.queued_requests.clear()
        
        logger.info(f"Cleared {count} requests from queue")
        return count
    
    async def reset_metrics(self) -> None:
        """
        Reset all metrics and history.
        """
        async with self._lock:
            self.processing_times.clear()
            self.completed_tasks.clear()
        
        logger.info("Reset capacity metrics")
