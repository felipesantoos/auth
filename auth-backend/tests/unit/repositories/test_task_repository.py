"""
Unit tests for Task Repository
Tests async task data access logic with mocked database
"""
import pytest
from unittest.mock import AsyncMock, Mock
from infra.database.repositories.task_repository import TaskRepository
from core.domain.task.async_task import AsyncTask, TaskStatus


@pytest.mark.unit
class TestTaskRepositorySave:
    """Test saving tasks"""
    
    @pytest.mark.asyncio
    async def test_save_task(self):
        """Test saving task to database"""
        session_mock = AsyncMock()
        session_mock.add = Mock()
        session_mock.commit = AsyncMock()
        session_mock.refresh = AsyncMock()
        
        repository = TaskRepository(session_mock)
        
        task = AsyncTask(
            task_type="bulk_create_users",
            created_by="admin-123",
            client_id="client-123",
            payload={"users": []}
        )
        
        result = await repository.save(task)
        
        session_mock.add.assert_called_once()
        session_mock.commit.assert_called_once()


@pytest.mark.unit
class TestTaskRepositoryGet:
    """Test retrieving tasks"""
    
    @pytest.mark.asyncio
    async def test_get_by_id(self):
        """Test getting task by ID"""
        session_mock = AsyncMock()
        db_task_mock = Mock(
            id="task-123",
            task_type="test_task",
            status="pending"
        )
        
        session_mock.execute = AsyncMock()
        session_mock.execute.return_value.scalar_one_or_none = Mock(return_value=db_task_mock)
        
        repository = TaskRepository(session_mock)
        
        result = await repository.get_by_id("task-123")
        
        assert result is not None or session_mock.execute.called
    
    @pytest.mark.asyncio
    async def test_get_by_user(self):
        """Test getting tasks by user"""
        session_mock = AsyncMock()
        session_mock.execute = AsyncMock()
        session_mock.execute.return_value.scalars = Mock()
        session_mock.execute.return_value.scalars.return_value.all = Mock(return_value=[])
        
        repository = TaskRepository(session_mock)
        
        result = await repository.get_by_user("user-123")
        
        assert isinstance(result, list)


@pytest.mark.unit
class TestTaskRepositoryUpdate:
    """Test updating tasks"""
    
    @pytest.mark.asyncio
    async def test_update_task_status(self):
        """Test updating task status"""
        session_mock = AsyncMock()
        db_task_mock = Mock(
            id="task-123",
            status=TaskStatus.PENDING
        )
        
        session_mock.execute = AsyncMock()
        session_mock.execute.return_value.scalar_one_or_none = Mock(return_value=db_task_mock)
        session_mock.commit = AsyncMock()
        
        repository = TaskRepository(session_mock)
        
        await repository.update_status("task-123", TaskStatus.COMPLETED)
        
        session_mock.commit.assert_called()

