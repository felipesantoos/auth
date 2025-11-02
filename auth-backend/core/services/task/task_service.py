"""
Task Service
Manages async tasks (202 Accepted pattern)
"""
import logging
from typing import Optional, List
from datetime import datetime
from core.domain.task.async_task import AsyncTask, TaskStatus
from core.exceptions import NotFoundException, ValidationException

logger = logging.getLogger(__name__)


class TaskService:
    """
    Service for managing async tasks.
    
    Supports:
    - Create task (returns task_id)
    - Get task status
    - Update task progress/status
    - List user's tasks
    - Cancel task
    """
    
    def __init__(self, repository):
        """
        Initialize TaskService.
        
        Args:
            repository: Task repository for database operations
        """
        self.repository = repository
    
    async def create_task(
        self,
        task_type: str,
        payload: dict,
        created_by: str,
        client_id: str
    ) -> AsyncTask:
        """
        Create a new async task.
        
        Args:
            task_type: Type of task (e.g., "bulk_create_users")
            payload: Input data for the task
            created_by: User ID who created the task
            client_id: Client (tenant) ID
        
        Returns:
            Created AsyncTask
        
        Example:
            >>> task = await task_service.create_task(
            ...     task_type="bulk_create_users",
            ...     payload={"users": [...]},
            ...     created_by="admin_123",
            ...     client_id="client_123"
            ... )
            >>> print(task.id)  # "abc-123-def-456"
        """
        # Validate task type
        valid_types = [
            "bulk_create_users",
            "bulk_update_users",
            "bulk_delete_users",
            "export_user_data",
            "import_user_data"
        ]
        
        if task_type not in valid_types:
            raise ValidationException(
                f"Invalid task type: {task_type}",
                "INVALID_TASK_TYPE"
            )
        
        # Create task domain object
        task = AsyncTask(
            task_type=task_type,
            payload=payload,
            created_by=created_by,
            client_id=client_id,
            status=TaskStatus.PENDING
        )
        
        # Save to database
        saved_task = await self.repository.save(task)
        
        logger.info(
            f"Async task created",
            extra={
                "task_id": saved_task.id,
                "task_type": task_type,
                "created_by": created_by,
                "client_id": client_id
            }
        )
        
        return saved_task
    
    async def get_task(
        self,
        task_id: str,
        client_id: Optional[str] = None
    ) -> AsyncTask:
        """
        Get task by ID with optional multi-tenant filtering.
        
        Args:
            task_id: Task ID
            client_id: Optional client ID for isolation
        
        Returns:
            AsyncTask
        
        Raises:
            NotFoundException: If task not found or doesn't belong to client
        """
        task = await self.repository.find_by_id(task_id)
        
        if not task:
            raise NotFoundException(
                f"Task {task_id} not found",
                "TASK_NOT_FOUND"
            )
        
        # Multi-tenant: Ensure task belongs to client
        if client_id and task.client_id != client_id:
            raise NotFoundException(
                f"Task {task_id} not found",
                "TASK_NOT_FOUND"
            )
        
        return task
    
    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[dict] = None,
        error: Optional[str] = None
    ) -> AsyncTask:
        """
        Update task status and result/error.
        
        Args:
            task_id: Task ID
            status: New status
            result: Result data if completed
            error: Error message if failed
        
        Returns:
            Updated AsyncTask
        """
        task = await self.get_task(task_id)
        
        task.status = status
        
        if status == TaskStatus.PROCESSING:
            task.start_processing()
        elif status == TaskStatus.COMPLETED:
            task.complete(result or {})
        elif status == TaskStatus.FAILED:
            task.fail(error or "Unknown error")
        elif status == TaskStatus.CANCELLED:
            task.cancel()
        
        updated_task = await self.repository.save(task)
        
        logger.info(
            f"Task status updated",
            extra={
                "task_id": task_id,
                "status": status.value
            }
        )
        
        return updated_task
    
    async def update_task_progress(
        self,
        task_id: str,
        percentage: int,
        message: Optional[str] = None
    ) -> AsyncTask:
        """
        Update task progress.
        
        Args:
            task_id: Task ID
            percentage: Progress percentage (0-100)
            message: Optional progress message
        
        Returns:
            Updated AsyncTask
        """
        task = await self.get_task(task_id)
        task.update_progress(percentage, message)
        
        updated_task = await self.repository.save(task)
        
        logger.debug(
            f"Task progress updated",
            extra={
                "task_id": task_id,
                "progress": percentage,
                "message": message
            }
        )
        
        return updated_task
    
    async def list_user_tasks(
        self,
        user_id: str,
        client_id: str,
        status: Optional[TaskStatus] = None,
        limit: int = 50
    ) -> List[AsyncTask]:
        """
        List tasks created by a user.
        
        Args:
            user_id: User ID
            client_id: Client ID
            status: Optional status filter
            limit: Max number of tasks to return
        
        Returns:
            List of AsyncTask objects
        """
        tasks = await self.repository.find_by_user(
            user_id=user_id,
            client_id=client_id,
            status=status,
            limit=limit
        )
        
        return tasks
    
    async def cancel_task(self, task_id: str) -> AsyncTask:
        """
        Cancel a task (if not already terminal).
        
        Args:
            task_id: Task ID
        
        Returns:
            Updated AsyncTask
        """
        task = await self.get_task(task_id)
        
        if task.status.is_terminal():
            raise ValidationException(
                f"Cannot cancel task in {task.status.value} status",
                "TASK_ALREADY_TERMINAL"
            )
        
        task.cancel()
        updated_task = await self.repository.save(task)
        
        logger.info(f"Task cancelled", extra={"task_id": task_id})
        
        return updated_task
    
    async def cleanup_old_tasks(self, days_old: int = 30) -> int:
        """
        Cleanup completed/failed tasks older than N days.
        
        Args:
            days_old: Delete tasks older than this many days
        
        Returns:
            Number of tasks deleted
        """
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        count = await self.repository.delete_old_tasks(cutoff_date)
        
        logger.info(
            f"Cleaned up {count} old tasks",
            extra={"days_old": days_old, "cutoff_date": cutoff_date.isoformat()}
        )
        
        return count

