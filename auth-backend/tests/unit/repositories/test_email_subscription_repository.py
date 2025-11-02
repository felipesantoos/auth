"""
Unit tests for Email Subscription Repository
"""
import pytest
from unittest.mock import AsyncMock, Mock


@pytest.mark.unit
class TestEmailSubscriptionRepository:
    """Test email subscription repository"""
    
    @pytest.mark.asyncio
    async def test_get_or_create_subscription(self):
        """Test getting or creating email subscription"""
        session_mock = AsyncMock()
        session_mock.execute = AsyncMock()
        session_mock.execute.return_value.scalar_one_or_none = Mock(return_value=None)
        session_mock.add = Mock()
        session_mock.commit = AsyncMock()
        
        from infra.database.repositories.email_subscription_repository import EmailSubscriptionRepository
        repository = EmailSubscriptionRepository(session_mock)
        
        result = await repository.get_or_create("user@example.com")
        
        session_mock.add.assert_called() or session_mock.execute.called

