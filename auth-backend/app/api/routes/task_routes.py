"""
Task Management Routes
Endpoints for checking async task status (202 Accepted pattern)
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.api.dtos.response.async_response import (
    TaskStatusResponse,
    TaskListResponse,
    TaskStatusEnum
)
from app.api.middlewares.auth_middleware import get_current_user
from core.domain.auth.app_user import AppUser
from core.domain.task.async_task import TaskStatus
from core.services.task.task_service import TaskService
from core.exceptions import NotFoundException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tasks", tags=["Async Tasks"])


# Mock task service (replace with DI container later)
async def get_task_service():
    """Get task service (placeholder - implement in DI container)."""
    # TODO: Implement proper DI container integration
    from infra.database.repositories.task_repository import TaskRepository
    from infra.database.database import get_db_session
    
    session = await anext(get_db_session())
    repository = TaskRepository(session)
    return TaskService(repository)


@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: AppUser = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
):
    """
    Get async task status.
    
    **Use Case:**
    After receiving 202 Accepted response, poll this endpoint to check task progress.
    
    **Response Status Codes:**
    - `200 OK`: Task status retrieved
    - `404 Not Found`: Task doesn't exist or doesn't belong to user
    
    **Task Statuses:**
    - `pending`: Task queued, not started yet
    - `processing`: Task is being processed
    - `completed`: Task finished successfully (check `result` field)
    - `failed`: Task failed (check `error` field)
    - `cancelled`: Task was cancelled
    
    **Polling Strategy:**
    ```javascript
    async function pollTaskStatus(taskId) {
        while (true) {
            const response = await fetch(`/api/v1/tasks/${taskId}`);
            const task = await response.json();
            
            if (task.status === 'completed') {
                console.log('Success:', task.result);
                break;
            } else if (task.status === 'failed') {
                console.error('Failed:', task.error);
                break;
            } else if (task.status === 'cancelled') {
                console.log('Cancelled');
                break;
            }
            
            // Poll every 2 seconds
            await new Promise(r => setTimeout(r, 2000));
        }
    }
    ```
    
    Requires authentication.
    """
    try:
        # Get task with multi-tenant filtering
        task = await task_service.get_task(
            task_id=task_id,
            client_id=current_user.client_id
        )
        
        # Ensure user owns the task or is admin
        if task.created_by != current_user.id and current_user.role.value != "admin":
            raise NotFoundException(
                f"Task {task_id} not found",
                "TASK_NOT_FOUND"
            )
        
        # Convert to response DTO
        return TaskStatusResponse(
            task_id=task.id,
            task_type=task.task_type,
            status=TaskStatusEnum(task.status.value),
            result=task.result,
            error=task.error,
            progress_percentage=task.progress_percentage,
            progress_message=task.progress_message,
            created_by=task.created_by,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            duration_seconds=task.get_duration_seconds()
        )
    
    except NotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    except Exception as e:
        logger.error(f"Error getting task status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving task status"
        )


@router.get("", response_model=TaskListResponse)
async def list_my_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Max tasks to return"),
    current_user: AppUser = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
):
    """
    List current user's async tasks.
    
    **Query Parameters:**
    - `status`: Filter by task status (pending, processing, completed, failed, cancelled)
    - `limit`: Max number of tasks to return (default: 50, max: 100)
    
    **Returns:**
    List of tasks ordered by created_at (newest first).
    
    Requires authentication.
    """
    try:
        # Parse status filter
        status_filter = None
        if status:
            try:
                status_filter = TaskStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status}. Valid: pending, processing, completed, failed, cancelled"
                )
        
        # Get tasks
        tasks = await task_service.list_user_tasks(
            user_id=current_user.id,
            client_id=current_user.client_id,
            status=status_filter,
            limit=limit
        )
        
        # Convert to response DTOs
        task_responses = [
            TaskStatusResponse(
                task_id=task.id,
                task_type=task.task_type,
                status=TaskStatusEnum(task.status.value),
                result=task.result,
                error=task.error,
                progress_percentage=task.progress_percentage,
                progress_message=task.progress_message,
                created_by=task.created_by,
                created_at=task.created_at,
                started_at=task.started_at,
                completed_at=task.completed_at,
                duration_seconds=task.get_duration_seconds()
            )
            for task in tasks
        ]
        
        return TaskListResponse(
            tasks=task_responses,
            total=len(task_responses)
        )
    
    except Exception as e:
        logger.error(f"Error listing tasks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing tasks"
        )


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    current_user: AppUser = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)
):
    """
    Cancel a pending or processing task.
    
    **HTTP Status:**
    - `200 OK`: Task cancelled successfully
    - `400 Bad Request`: Task already completed/failed (cannot cancel)
    - `404 Not Found`: Task not found
    
    **Note:**
    Only tasks in `pending` or `processing` status can be cancelled.
    
    Requires authentication (must be task owner or admin).
    """
    try:
        # Get task
        task = await task_service.get_task(
            task_id=task_id,
            client_id=current_user.client_id
        )
        
        # Ensure user owns the task or is admin
        if task.created_by != current_user.id and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to cancel this task"
            )
        
        # Cancel task
        updated_task = await task_service.cancel_task(task_id)
        
        logger.info(
            f"Task cancelled",
            extra={
                "task_id": task_id,
                "user_id": current_user.id
            }
        )
        
        return {
            "message": "Task cancelled successfully",
            "task_id": updated_task.id,
            "status": updated_task.status.value
        }
    
    except NotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    except Exception as e:
        if "already terminal" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel task that is already completed or failed"
            )
        
        logger.error(f"Error cancelling task: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error cancelling task"
        )

