"""
Unit tests for PermissionRepository (mocking SQLAlchemy session)
Tests repository logic without real database
"""
import pytest
from unittest.mock import Mock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from infra.database.repositories.permission_repository import PermissionRepository
from infra.database.models.permission import DBPermission
from tests.factories import PermissionFactory
from core.domain.auth.permission import PermissionAction


@pytest.mark.unit
class TestPermissionRepositoryFind:
    """Test find operations with mocked session"""
    
    @pytest.fixture
    def mock_session(self):
        """Create mock database session"""
        session = Mock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        return session
    
    @pytest.fixture
    def repository(self, mock_session):
        """Create repository with mocked session"""
        return PermissionRepository(mock_session)
    
    @pytest.mark.asyncio
    async def test_find_by_id_calls_execute(self, repository, mock_session):
        """Test find_by_id executes query"""
        # Arrange
        db_permission = DBPermission(
            id="perm-123",
            user_id="user-456",
            client_id="client-789",
            resource_type="project",
            resource_id="proj-001",
            action="read",
            granted_by="admin-123"
        )
        
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=db_permission)
        mock_session.execute.return_value = mock_result
        
        # Act
        permission = await repository.find_by_id("perm-123")
        
        # Assert
        assert permission is not None
        assert permission.id == "perm-123"
        assert permission.resource_type == "project"
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_by_user_returns_list(self, repository, mock_session):
        """Test find_by_user returns list of permissions"""
        # Arrange
        db_permissions = [
            DBPermission(
                id=f"perm-{i}",
                user_id="user-123",
                client_id="client-456",
                resource_type="project",
                action="read"
            )
            for i in range(3)
        ]
        
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=db_permissions)))
        mock_session.execute.return_value = mock_result
        
        # Act
        permissions = await repository.find_by_user("user-123", "client-456")
        
        # Assert
        assert len(permissions) == 3
        assert all(p.user_id == "user-123" for p in permissions)
        mock_session.execute.assert_called_once()


@pytest.mark.unit
class TestPermissionRepositorySave:
    """Test save operations with mocked session"""
    
    @pytest.fixture
    def mock_session(self):
        session = Mock(spec=AsyncSession)
        session.add = Mock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        return session
    
    @pytest.fixture
    def repository(self, mock_session):
        return PermissionRepository(mock_session)
    
    @pytest.mark.asyncio
    async def test_save_calls_add_and_flush(self, repository, mock_session):
        """Test save calls session.add() and flush()"""
        # Arrange
        permission = PermissionFactory.build()
        
        # Act
        await repository.save(permission)
        
        # Assert
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()


@pytest.mark.unit
class TestPermissionRepositoryDelete:
    """Test delete operations with mocked session"""
    
    @pytest.fixture
    def mock_session(self):
        session = Mock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        return session
    
    @pytest.fixture
    def repository(self, mock_session):
        return PermissionRepository(mock_session)
    
    @pytest.mark.asyncio
    async def test_delete_success(self, repository, mock_session):
        """Test successful deletion"""
        # Arrange
        mock_result = Mock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result
        
        # Act
        result = await repository.delete("perm-123")
        
        # Assert
        assert result is True
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_not_found(self, repository, mock_session):
        """Test deleting non-existent permission"""
        # Arrange
        mock_result = Mock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result
        
        # Act
        result = await repository.delete("nonexistent")
        
        # Assert
        assert result is False

