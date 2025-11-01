"""
Unit tests for AppUserRepository (mocking SQLAlchemy session)
Tests repository logic without real database
"""
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from infra.database.repositories.app_user_repository import AppUserRepository
from infra.database.models.app_user import DBAppUser
from core.services.filters.user_filter import UserFilter
from tests.factories import UserFactory


@pytest.mark.unit
class TestAppUserRepositoryFind:
    """Test find operations with mocked session"""
    
    @pytest.fixture
    def mock_session(self):
        """Create mock database session"""
        session = Mock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session
    
    @pytest.fixture
    def repository(self, mock_session):
        """Create repository with mocked session"""
        return AppUserRepository(mock_session)
    
    @pytest.mark.asyncio
    async def test_find_by_id_calls_execute(self, repository, mock_session):
        """Test find_by_id executes query"""
        # Arrange
        db_user = DBAppUser(
            id="user-123",
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
            role="user",
            client_id="client-456",
            is_active=True
        )
        
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=db_user)
        mock_session.execute.return_value = mock_result
        
        # Act
        user = await repository.find_by_id("user-123", "client-456")
        
        # Assert
        assert user is not None
        assert user.id == "user-123"
        assert user.username == "testuser"
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_by_id_returns_none_when_not_found(self, repository, mock_session):
        """Test find_by_id returns None for non-existent user"""
        # Arrange
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute.return_value = mock_result
        
        # Act
        user = await repository.find_by_id("nonexistent", "client-456")
        
        # Assert
        assert user is None
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_by_email_executes_query(self, repository, mock_session):
        """Test find_by_email executes correct query"""
        # Arrange
        db_user = DBAppUser(
            id="user-123",
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            full_name="Test User",
            role="user",
            client_id="client-456",
            is_active=True
        )
        
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=db_user)
        mock_session.execute.return_value = mock_result
        
        # Act
        user = await repository.find_by_email("test@example.com", "client-456")
        
        # Assert
        assert user is not None
        assert user.email == "test@example.com"
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_all_with_filter_builds_query(self, repository, mock_session):
        """Test find_all builds query with filter"""
        # Arrange
        db_users = [
            DBAppUser(
                id=f"user-{i}",
                username=f"user{i}",
                email=f"user{i}@example.com",
                hashed_password="hashed",
                full_name=f"User {i}",
                role="user",
                client_id="client-456",
                is_active=True
            )
            for i in range(3)
        ]
        
        mock_result = Mock()
        mock_result.scalars = Mock(return_value=Mock(all=Mock(return_value=db_users)))
        mock_session.execute.return_value = mock_result
        
        filter_obj = UserFilter(client_id="client-456", active=True)
        
        # Act
        users = await repository.find_all(filter_obj)
        
        # Assert
        assert len(users) == 3
        mock_session.execute.assert_called_once()


@pytest.mark.unit
class TestAppUserRepositorySave:
    """Test save operations with mocked session"""
    
    @pytest.fixture
    def mock_session(self):
        session = Mock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.add = Mock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        session.commit = AsyncMock()
        return session
    
    @pytest.fixture
    def repository(self, mock_session):
        return AppUserRepository(mock_session)
    
    @pytest.mark.asyncio
    async def test_save_new_user_calls_add(self, repository, mock_session):
        """Test saving new user calls session.add()"""
        # Arrange
        user = UserFactory.build(id=None)
        
        # Mock to return no existing user
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=None)
        mock_session.execute.return_value = mock_result
        
        # Act
        await repository.save(user)
        
        # Assert
        # Should add new user to session
        assert mock_session.add.called
        mock_session.flush.assert_called()
    
    @pytest.mark.asyncio
    async def test_save_existing_user_updates_fields(self, repository, mock_session):
        """Test saving existing user updates fields"""
        # Arrange
        user = UserFactory.build(id="user-123", name="Updated Name")
        
        db_user = DBAppUser(
            id="user-123",
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            full_name="Old Name",
            role="user",
            client_id="client-456",
            is_active=True
        )
        
        mock_result = Mock()
        mock_result.scalar_one_or_none = Mock(return_value=db_user)
        mock_session.execute.return_value = mock_result
        
        # Act
        await repository.save(user)
        
        # Assert
        # Should NOT call add (already exists)
        assert not mock_session.add.called
        # Should update fields
        assert db_user.full_name == "Updated Name"
        mock_session.flush.assert_called()


@pytest.mark.unit
class TestAppUserRepositoryDelete:
    """Test delete operations with mocked session"""
    
    @pytest.fixture
    def mock_session(self):
        session = Mock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        return session
    
    @pytest.fixture
    def repository(self, mock_session):
        return AppUserRepository(mock_session)
    
    @pytest.mark.asyncio
    async def test_delete_success_returns_true(self, repository, mock_session):
        """Test successful deletion returns True"""
        # Arrange
        mock_result = Mock()
        mock_result.rowcount = 1  # One row deleted
        mock_session.execute.return_value = mock_result
        
        # Act
        result = await repository.delete("user-123", "client-456")
        
        # Assert
        assert result is True
        mock_session.execute.assert_called_once()
        mock_session.flush.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_not_found_returns_false(self, repository, mock_session):
        """Test deleting non-existent user returns False"""
        # Arrange
        mock_result = Mock()
        mock_result.rowcount = 0  # No rows deleted
        mock_session.execute.return_value = mock_result
        
        # Act
        result = await repository.delete("nonexistent", "client-456")
        
        # Assert
        assert result is False
        mock_session.execute.assert_called_once()


@pytest.mark.unit
class TestAppUserRepositoryCount:
    """Test count operations with mocked session"""
    
    @pytest.fixture
    def mock_session(self):
        session = Mock(spec=AsyncSession)
        session.execute = AsyncMock()
        return session
    
    @pytest.fixture
    def repository(self, mock_session):
        return AppUserRepository(mock_session)
    
    @pytest.mark.asyncio
    async def test_count_returns_number(self, repository, mock_session):
        """Test count returns correct number"""
        # Arrange
        mock_result = Mock()
        mock_result.scalar = Mock(return_value=42)
        mock_session.execute.return_value = mock_result
        
        filter_obj = UserFilter(client_id="client-456")
        
        # Act
        count = await repository.count(filter_obj)
        
        # Assert
        assert count == 42
        mock_session.execute.assert_called_once()

