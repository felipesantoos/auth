"""
Unit tests for Unsubscribe Service
Tests email unsubscribe logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock
from core.services.email.unsubscribe_service import UnsubscribeService


@pytest.mark.unit
class TestUnsubscribe:
    """Test email unsubscribe functionality"""
    
    @pytest.mark.asyncio
    async def test_unsubscribe_user_from_all_emails(self):
        """Test unsubscribing user from all marketing emails"""
        subscription_repo_mock = AsyncMock()
        subscription_repo_mock.get_or_create = AsyncMock(return_value=Mock(
            id="sub-123",
            unsubscribed_all=False
        ))
        subscription_repo_mock.update = AsyncMock()
        
        service = UnsubscribeService(subscription_repo_mock)
        
        await service.unsubscribe_all("user@example.com")
        
        subscription_repo_mock.update.assert_called()
    
    @pytest.mark.asyncio
    async def test_unsubscribe_from_specific_category(self):
        """Test unsubscribing from specific email category"""
        subscription_repo_mock = AsyncMock()
        subscription_repo_mock.get_or_create = AsyncMock(return_value=Mock(
            id="sub-123",
            categories_unsubscribed=[]
        ))
        subscription_repo_mock.update = AsyncMock()
        
        service = UnsubscribeService(subscription_repo_mock)
        
        await service.unsubscribe_category("user@example.com", "marketing")
        
        subscription_repo_mock.update.assert_called()
    
    @pytest.mark.asyncio
    async def test_resubscribe_user(self):
        """Test resubscribing user to emails"""
        subscription_repo_mock = AsyncMock()
        subscription_repo_mock.get_by_email = AsyncMock(return_value=Mock(
            id="sub-123",
            unsubscribed_all=True
        ))
        subscription_repo_mock.update = AsyncMock()
        
        service = UnsubscribeService(subscription_repo_mock)
        
        await service.resubscribe("user@example.com")
        
        subscription_repo_mock.update.assert_called()
    
    @pytest.mark.asyncio
    async def test_check_if_email_allowed(self):
        """Test checking if email is allowed for user"""
        subscription_repo_mock = AsyncMock()
        subscription_repo_mock.get_by_email = AsyncMock(return_value=Mock(
            unsubscribed_all=False,
            categories_unsubscribed=["marketing"]
        ))
        
        service = UnsubscribeService(subscription_repo_mock)
        
        # Should allow transactional
        is_allowed = await service.is_email_allowed("user@example.com", "transactional")
        assert is_allowed is True
        
        # Should not allow marketing
        is_allowed = await service.is_email_allowed("user@example.com", "marketing")
        assert is_allowed is False

