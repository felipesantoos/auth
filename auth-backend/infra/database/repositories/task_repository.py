"""
Task Repository
Database operations for async tasks
"""
import logging
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from core.domain.task.async_task import AsyncTask, TaskStatus
from infra.database.models.async_task_model import DBAsyncTask

logger = logging.getLogger(__name__)


class TaskRepository:
    """Repository for async task operations."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
    
    async def save(self, task: AsyncTask) -> AsyncTask:
        """
        Save or update task.
        
        Args:
            task: AsyncTask domain object
        
        Returns:
            Saved AsyncTask
        """
        # Check if exists
        existing = await self.session.get(DBAsyncTask, task.id)
        
        if existing:
            # Update existing
            existing.task_type = task.task_type
            existing.status = task.status.value
            existing.payload = task.payload
            existing.result = task.result
            existing.error = task.error
            existing.progress_percentage = task.progress_percentage
            existing.progress_message = task.progress_message
            existing.celery_task_id = task.celery_task_id
            existing.started_at = task.started_at
            existing.completed_at = task.completed_at
        else:
            # Create new
            db_task = DBAsyncTask(
                id=task.id,
                task_type=task.task_type,
                status=task.status.value,
                payload=task.payload,
                result=task.result,
                error=task.error,
                progress_percentage=task.progress_percentage,
                progress_message=task.progress_message,
                client_id=task.client_id,
                created_by=task.created_by,
                celery_task_id=task.celery_task_id,
                created_at=task.created_at,
                started_at=task.started_at,
                completed_at=task.completed_at
            )
            self.session.add(db_task)
        
        await self.session.commit()
        
        # Refresh to get server-side defaults
        if existing:
            await self.session.refresh(existing)
            return self._to_domain(existing)
        else:
            await self.session.refresh(db_task)
            return self._to_domain(db_task)
    
    async def find_by_id(self, task_id: str) -> Optional[AsyncTask]:
        """Find task by ID."""
        db_task = await self.session.get(DBAsyncTask, task_id)
        return self._to_domain(db_task) if db_task else None
    
    async def find_by_user(
        self,
        user_id: str,
        client_id: str,
        status: Optional[TaskStatus] = None,
        limit: int = 50
    ) -> List[AsyncTask]:
        """
        Find tasks by user.
        
        Args:
            user_id: User ID
            client_id: Client ID
            status: Optional status filter
            limit: Max results
        
        Returns:
            List of AsyncTask objects
        """
        query = select(DBAsyncTask).where(
            DBAsyncTask.created_by == user_id,
            DBAsyncTask.client_id == client_id
        )
        
        if status:
            query = query.where(DBAsyncTask.status == status.value)
        
        query = query.order_by(DBAsyncTask.created_at.desc()).limit(limit)
        
        result = await self.session.execute(query)
        db_tasks = result.scalars().all()
        
        return [self._to_domain(db_task) for db_task in db_tasks]
    
    async def delete_old_tasks(self, cutoff_date: datetime) -> int:
        """
        Delete completed/failed tasks older than cutoff date.
        
        Args:
            cutoff_date: Delete tasks older than this
        
        Returns:
            Number of deleted tasks
        """
        result = await self.session.execute(
            delete(DBAsyncTask).where(
                DBAsyncTask.completed_at < cutoff_date,
                DBAsyncTask.status.in_(['completed', 'failed', 'cancelled'])
            )
        )
        await self.session.commit()
        
        return result.rowcount
    
    def _to_domain(self, db_task: DBAsyncTask) -> AsyncTask:
        """Convert DB model to domain model."""
        return AsyncTask(
            id=db_task.id,
            task_type=db_task.task_type,
            status=TaskStatus(db_task.status),
            payload=db_task.payload,
            result=db_task.result,
            error=db_task.error,
            progress_percentage=db_task.progress_percentage,
            progress_message=db_task.progress_message,
            client_id=db_task.client_id,
            created_by=db_task.created_by,
            celery_task_id=db_task.celery_task_id,
            created_at=db_task.created_at,
            started_at=db_task.started_at,
            completed_at=db_task.completed_at
        )

