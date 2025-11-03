"""
Unit tests for Task Service
Tests async task management logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock
from core.services.task.task_service import TaskService
from core.domain.task.async_task import AsyncTask, TaskStatus


@pytest.mark.unit
class TestTaskManagement:
    """Test async task management functionality"""
    
    @pytest.mark.asyncio
    async def test_create_task(self):
        """Test creating async task"""
        task_repo_mock = AsyncMock()
        task_repo_mock.save = AsyncMock(return_value=Mock(id="task-123"))
        
        service = TaskService(task_repo_mock)
        
        task = await service.create_task(
            task_type="bulk_create_users",
            payload={"users": [{"email": "user@example.com"}]},
            created_by="admin-123",
            client_id="client-123"
        )
        
        task_repo_mock.save.assert_called()
        assert task is not None
    
    @pytest.mark.asyncio
    async def test_get_task_by_id(self):
        """Test getting task by ID"""
        task_repo_mock = AsyncMock()
        task_repo_mock.get_by_id = AsyncMock(return_value=Mock(
            id="task-123",
            status=TaskStatus.PENDING
        ))
        
        service = TaskService(task_repo_mock)
        
        task = await service.get_task("task-123")
        
        task_repo_mock.get_by_id.assert_called_with("task-123")
        assert task.status == TaskStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_update_task_progress(self):
        """Test updating task progress"""
        task_repo_mock = AsyncMock()
        task_repo_mock.get_by_id = AsyncMock(return_value=Mock(
            id="task-123",
            update_progress=Mock()
        ))
        task_repo_mock.update = AsyncMock()
        
        service = TaskService(task_repo_mock)
        
        await service.update_task_progress("task-123", 50, "Processing...")
        
        task_repo_mock.update.assert_called()
    
    @pytest.mark.asyncio
    async def test_complete_task(self):
        """Test completing task"""
        task_repo_mock = AsyncMock()
        task_repo_mock.get_by_id = AsyncMock(return_value=Mock(
            id="task-123",
            complete=Mock()
        ))
        task_repo_mock.update = AsyncMock()
        
        service = TaskService(task_repo_mock)
        
        result = {"success_count": 10}
        await service.complete("task-123", result)
        
        task_repo_mock.update.assert_called()
    
    @pytest.mark.asyncio
    async def test_fail_task(self):
        """Test failing task"""
        task_repo_mock = AsyncMock()
        task_repo_mock.get_by_id = AsyncMock(return_value=Mock(
            id="task-123",
            fail=Mock()
        ))
        task_repo_mock.update = AsyncMock()
        
        service = TaskService(task_repo_mock)
        
        await service.fail("task-123", "Error processing data")
        
        task_repo_mock.update.assert_called()
    
    @pytest.mark.asyncio
    async def test_cancel_task(self):
        """Test cancelling task"""
        task_repo_mock = AsyncMock()
        task_repo_mock.get_by_id = AsyncMock(return_value=Mock(
            id="task-123",
            status=TaskStatus.PENDING,
            cancel=Mock()
        ))
        task_repo_mock.update = AsyncMock()
        
        service = TaskService(task_repo_mock)
        
        await service.cancel_task("task-123")
        
        task_repo_mock.update.assert_called()

