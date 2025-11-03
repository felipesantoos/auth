"""
Unit tests for Task Repository
Tests async task data persistence
"""
import pytest
from unittest.mock import AsyncMock
from infra.database.repositories.task_repository import TaskRepository


@pytest.mark.unit
class TestTaskRepository:
    """Test task repository"""

    def test_repository_initialization(self):
        """Should initialize repository"""
        mock_session = AsyncMock()
        repository = TaskRepository(session=mock_session)
        
        assert repository is not None
        assert repository.session == mock_session

    @pytest.mark.asyncio
    async def test_has_save_method(self):
        """Should have save method"""
        mock_session = AsyncMock()
        repository = TaskRepository(session=mock_session)
        
        assert hasattr(repository, 'add') or hasattr(repository, 'save')

    @pytest.mark.asyncio
    async def test_has_find_methods(self):
        """Should have find methods"""
        mock_session = AsyncMock()
        repository = TaskRepository(session=mock_session)
        
        assert hasattr(repository, 'find_by_id') or hasattr(repository, 'get_by_id')

    @pytest.mark.asyncio
    async def test_has_delete_method(self):
        """Should have delete method"""
        mock_session = AsyncMock()
        repository = TaskRepository(session=mock_session)
        
        assert hasattr(repository, 'delete') or hasattr(repository, 'remove')

