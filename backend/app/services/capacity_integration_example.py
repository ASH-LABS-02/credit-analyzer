"""
Capacity Management Integration Example

This module demonstrates how to integrate the CapacityManager with
the TaskQueue and API endpoints to provide capacity management,
request queueing, and user notifications.

Requirements: 18.4 - Batch Processing and Scalability
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

from app.services.capacity_manager import CapacityManager, WaitTimeEstimate
from app.services.task_queue import TaskQueue
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class AnalysisRequestHandler:
    """
    Handles credit analysis requests with capacity management.
    
    This class demonstrates the integration pattern for:
    1. Checking capacity before accepting requests
    2. Queueing requests when at capacity
    3. Estimating wait times
    4. Notifying users
    5. Processing requests when capacity becomes available
    
    Example:
        handler = AnalysisRequestHandler(
            capacity_manager=capacity_manager,
            task_queue=task_queue,
            notification_service=notification_service
        )
        
        # Submit analysis request
        result = await handler.submit_analysis_request(
            application_id="app123",
            user_email="analyst@bank.com"
        )
        
        if result["status"] == "queued":
            # User notified with wait time estimate
            print(f"Queued: {result['wait_estimate']['message']}")
        else:
            # Processing immediately
            print(f"Processing: {result['task_id']}")
    """
    
    def __init__(
        self,
        capacity_manager: CapacityManager,
        task_queue: TaskQueue,
        notification_service: Optional[NotificationService] = None
    ):
        """
        Initialize the request handler.
        
        Args:
            capacity_manager: CapacityManager instance
            task_queue: TaskQueue instance
            notification_service: Optional notification service for user alerts
        """
        self.capacity_manager = capacity_manager
        self.task_queue = task_queue
        self.notification_service = notification_service
    
    async def submit_analysis_request(
        self,
        application_id: str,
        user_email: str,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """
        Submit a credit analysis request with capacity management.
        
        Args:
            application_id: Application identifier
            user_email: User email for notifications
            priority: Request priority (normal, high)
        
        Returns:
            Dictionary with submission result:
            - status: "processing" or "queued"
            - task_id: Task identifier (if processing)
            - request_id: Request identifier (if queued)
            - wait_estimate: Wait time estimate (if queued)
        """
        request_id = f"{application_id}_{datetime.utcnow().timestamp()}"
        
        # Check if system can accept request immediately
        can_accept = await self.capacity_manager.can_accept_request()
        
        if can_accept:
            # Process immediately
            logger.info(f"Processing request {request_id} immediately")
            
            # Mark as processing in capacity manager
            await self.capacity_manager.start_processing(request_id)
            
            # Add to task queue for actual processing
            task_id = await self.task_queue.add_task(
                task_type="credit_analysis",
                payload={
                    "application_id": application_id,
                    "request_id": request_id,
                    "user_email": user_email,
                    "priority": priority
                }
            )
            
            # Notify user that processing has started
            if self.notification_service:
                await self.notification_service.send_notification(
                    user_email=user_email,
                    notification_type="analysis_started",
                    data={
                        "application_id": application_id,
                        "task_id": task_id,
                        "message": "Your credit analysis has started processing."
                    }
                )
            
            return {
                "status": "processing",
                "task_id": task_id,
                "request_id": request_id,
                "message": "Analysis started processing immediately."
            }
        
        else:
            # System at capacity - queue the request
            logger.info(f"System at capacity, queueing request {request_id}")
            
            # Queue in capacity manager
            position = await self.capacity_manager.queue_request(request_id)
            
            # Estimate wait time
            wait_estimate = await self.capacity_manager.estimate_wait_time(request_id)
            
            # Notify user about queueing and wait time
            if self.notification_service:
                await self.notification_service.send_notification(
                    user_email=user_email,
                    notification_type="analysis_queued",
                    data={
                        "application_id": application_id,
                        "request_id": request_id,
                        "position": position + 1,  # 1-indexed for user display
                        "queue_size": wait_estimate.current_queue_size + 1,
                        "estimated_wait_seconds": wait_estimate.estimated_wait_seconds,
                        "message": wait_estimate.message
                    }
                )
            
            logger.info(
                f"Request {request_id} queued at position {position}. "
                f"Estimated wait: {wait_estimate.estimated_wait_seconds:.0f}s"
            )
            
            return {
                "status": "queued",
                "request_id": request_id,
                "position": position,
                "wait_estimate": {
                    "estimated_wait_seconds": wait_estimate.estimated_wait_seconds,
                    "position_in_queue": wait_estimate.position_in_queue,
                    "current_queue_size": wait_estimate.current_queue_size,
                    "message": wait_estimate.message
                },
                "message": wait_estimate.message
            }
    
    async def process_next_queued_request(self) -> Optional[Dict[str, Any]]:
        """
        Process the next queued request when capacity becomes available.
        
        This should be called when a task completes to process queued requests.
        
        Returns:
            Dictionary with processing result or None if queue is empty
        """
        # Check if we have capacity
        can_accept = await self.capacity_manager.can_accept_request()
        if not can_accept:
            logger.debug("No capacity available for queued requests")
            return None
        
        # Get next queued request
        request_id = await self.capacity_manager.get_next_queued_request()
        if not request_id:
            logger.debug("No queued requests to process")
            return None
        
        # Extract application_id from request_id (format: app_id_timestamp)
        application_id = request_id.rsplit("_", 1)[0]
        
        logger.info(f"Processing queued request {request_id}")
        
        # Mark as processing
        await self.capacity_manager.start_processing(request_id)
        
        # Add to task queue
        task_id = await self.task_queue.add_task(
            task_type="credit_analysis",
            payload={
                "application_id": application_id,
                "request_id": request_id
            }
        )
        
        # Notify user that their queued request is now processing
        if self.notification_service:
            # In real implementation, would retrieve user_email from request metadata
            await self.notification_service.send_notification(
                user_email="user@example.com",  # Placeholder
                notification_type="analysis_started",
                data={
                    "application_id": application_id,
                    "task_id": task_id,
                    "message": "Your queued credit analysis has started processing."
                }
            )
        
        return {
            "request_id": request_id,
            "task_id": task_id,
            "application_id": application_id
        }
    
    async def complete_analysis_request(
        self,
        request_id: str,
        processing_time: Optional[float] = None
    ) -> None:
        """
        Mark an analysis request as completed.
        
        This should be called when task processing completes.
        It updates capacity metrics and triggers processing of queued requests.
        
        Args:
            request_id: Request identifier
            processing_time: Optional processing time in seconds
        """
        # Mark as completed in capacity manager
        await self.capacity_manager.complete_processing(request_id, processing_time)
        
        logger.info(f"Request {request_id} completed")
        
        # Try to process next queued request
        await self.process_next_queued_request()
    
    async def get_capacity_status(self) -> Dict[str, Any]:
        """
        Get current capacity status for monitoring/dashboard.
        
        Returns:
            Dictionary with capacity metrics and queue information
        """
        metrics = await self.capacity_manager.get_capacity_metrics()
        
        return {
            "max_concurrent_tasks": metrics.max_concurrent_tasks,
            "current_processing": metrics.current_processing,
            "queued_tasks": metrics.queued_tasks,
            "completed_last_hour": metrics.completed_last_hour,
            "average_processing_time_seconds": metrics.average_processing_time,
            "is_at_capacity": metrics.is_at_capacity,
            "utilization_percentage": metrics.utilization_percentage,
            "timestamp": metrics.timestamp.isoformat()
        }
    
    async def get_request_status(
        self,
        request_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific request.
        
        Args:
            request_id: Request identifier
        
        Returns:
            Dictionary with request status or None if not found
        """
        # Check if processing
        metrics = await self.capacity_manager.get_capacity_metrics()
        
        # Check if queued
        position = await self.capacity_manager.get_queue_position(request_id)
        if position is not None:
            wait_estimate = await self.capacity_manager.estimate_wait_time(request_id)
            return {
                "status": "queued",
                "request_id": request_id,
                "position": position,
                "wait_estimate": {
                    "estimated_wait_seconds": wait_estimate.estimated_wait_seconds,
                    "message": wait_estimate.message
                }
            }
        
        # Check task queue for processing/completed status
        # (In real implementation, would query task queue)
        
        return None


# Example usage in API endpoint
async def example_api_endpoint_integration():
    """
    Example showing how to integrate capacity management in an API endpoint.
    """
    # Initialize services
    capacity_manager = CapacityManager(max_concurrent_tasks=10)
    task_queue = TaskQueue(max_workers=10)
    notification_service = NotificationService()
    
    handler = AnalysisRequestHandler(
        capacity_manager=capacity_manager,
        task_queue=task_queue,
        notification_service=notification_service
    )
    
    # Start task queue
    await task_queue.start()
    
    # Example: Submit analysis request
    result = await handler.submit_analysis_request(
        application_id="app_12345",
        user_email="analyst@bank.com"
    )
    
    if result["status"] == "queued":
        # Return 503 Service Unavailable with wait time
        return {
            "status_code": 503,
            "body": {
                "error": "System at capacity",
                "message": result["message"],
                "request_id": result["request_id"],
                "wait_estimate": result["wait_estimate"]
            }
        }
    else:
        # Return 202 Accepted
        return {
            "status_code": 202,
            "body": {
                "message": "Analysis started",
                "task_id": result["task_id"],
                "request_id": result["request_id"]
            }
        }
