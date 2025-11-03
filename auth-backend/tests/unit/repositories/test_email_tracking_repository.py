"""
Unit tests for Email Tracking Repository
Tests email tracking data access logic with mocked database
"""
import pytest
from unittest.mock import AsyncMock, Mock


@pytest.mark.unit
class TestEmailTrackingRepository:
    """Test email tracking repository"""
    
    @pytest.mark.asyncio
    async def test_save_tracking_record(self):
        """Test saving email tracking record"""
        session_mock = AsyncMock()
        session_mock.add = Mock()
        session_mock.commit = AsyncMock()
        
        from infra.database.repositories.email_tracking_repository import EmailTrackingRepository
        repository = EmailTrackingRepository(session_mock)
        
        tracking_data = Mock(
            id=None,
            user_id="user-123",
            email="user@example.com",
            template="welcome"
        )
        
        await repository.save(tracking_data)
        
        session_mock.add.assert_called_once()
        # Commit is not automatic in repositories
    
    @pytest.mark.asyncio
    async def test_get_by_template(self):
        """Test getting tracking records by template"""
        session_mock = AsyncMock()
        session_mock.execute = AsyncMock()
        session_mock.execute.return_value.scalars = Mock()
        session_mock.execute.return_value.scalars.return_value.all = Mock(return_value=[])
        
        from infra.database.repositories.email_tracking_repository import EmailTrackingRepository
        repository = EmailTrackingRepository(session_mock)
        
        result = await repository.find_by_template("welcome")
        
        assert isinstance(result, list)

