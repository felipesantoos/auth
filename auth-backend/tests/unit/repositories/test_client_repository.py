"""
Unit tests for ClientRepository (mocking SQLAlchemy session)
Tests repository logic without real database
"""
import pytest
from unittest.mock import Mock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from infra.database.repositories.client_repository import ClientRepository
from infra.database.models.client import DBClient
from tests.factories import ClientFactory


@pytest.mark.unit
class TestClientRepositoryFind:
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
        return ClientRepository(mock_session)
    
    @pytest.mark.asyncio
    async def test_find_by_id_executes_query(self, repository, mock_session):
        """Test find_by_id executes query"""
        # Arrange
        db_client = DBClient(
            id="client-123",
            name="Test Company",
            subdomain="test-company",
            api_key="api_key_value",
            active=True
        )
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = Mock(return_value=db_client)
        mock_session.execute.return_value = mock_result
        
        # Act
        client = await repository.find_by_id("client-123")
        
        # Assert
        assert client is not None
        assert client.id == "client-123"
        assert client.subdomain == "test-company"
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_find_by_subdomain_executes_query(self, repository, mock_session):
        """Test find_by_subdomain executes query"""
        # Arrange
        db_client = DBClient(
            id="client-123",
            name="Test Company",
            subdomain="test-subdomain",
            api_key="api_key",
            active=True
        )
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = Mock(return_value=db_client)
        mock_session.execute.return_value = mock_result
        
        # Act
        client = await repository.find_by_subdomain("test-subdomain")
        
        # Assert
        assert client is not None
        assert client.subdomain == "test-subdomain"
        mock_session.execute.assert_called_once()


@pytest.mark.unit
class TestClientRepositorySave:
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
        return ClientRepository(mock_session)
    
    @pytest.mark.asyncio
    async def test_save_calls_add_and_flush(self, repository, mock_session):
        """Test save calls session.add() and flush()"""
        # Arrange
        client = ClientFactory.build()
        
        # Act
        await repository.save(client)
        
        # Assert
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()


@pytest.mark.unit
class TestClientRepositoryDelete:
    """Test delete operations with mocked session"""
    
    @pytest.fixture
    def mock_session(self):
        session = Mock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        return session
    
    @pytest.fixture
    def repository(self, mock_session):
        return ClientRepository(mock_session)
    
    @pytest.mark.asyncio
    async def test_delete_calls_execute(self, repository, mock_session):
        """Test delete executes delete query"""
        # Arrange
        mock_result = AsyncMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result
        
        # Act
        result = await repository.delete("client-123")
        
        # Assert
        assert result is True
        mock_session.execute.assert_called_once()

