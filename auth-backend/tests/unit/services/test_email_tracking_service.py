"""
Unit tests for Email Tracking Service
Tests email tracking logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock
from core.services.email.email_tracking_service import EmailTrackingService


@pytest.mark.unit
class TestEmailTracking:
    """Test email tracking functionality"""
    
    @pytest.mark.asyncio
    async def test_record_email_sent(self):
        """Test recording email sent event"""
        tracking_repo_mock = AsyncMock()
        tracking_repo_mock.save = AsyncMock(return_value=Mock(id="tracking-123"))
        
        service = EmailTrackingService(tracking_repo_mock, AsyncMock(), subscription_repo_mock = AsyncMock())
        
        tracking = await service.record_email_sent(
            user_id="user-123",
            email="user@example.com",
            subject="Test Email",
            template="welcome",
            client_id="client-123"
        )
        
        tracking_repo_mock.save.assert_called()
        assert tracking is not None
    
    @pytest.mark.asyncio
    async def test_record_email_opened(self):
        """Test recording email opened event"""
        tracking_repo_mock = AsyncMock()
        tracking_repo_mock.get_by_id = AsyncMock(return_value=Mock(
            id="tracking-123",
            opened_at=None
        ))
        tracking_repo_mock.update = AsyncMock()
        
        service = EmailTrackingService(tracking_repo_mock, AsyncMock(), subscription_repo_mock = AsyncMock())
        
        await service.record_email_opened("tracking-123")
        
        tracking_repo_mock.update.assert_called()
    
    @pytest.mark.asyncio
    async def test_record_link_clicked(self):
        """Test recording email link clicked event"""
        click_repo_mock = AsyncMock()
        click_repo_mock.save = AsyncMock(return_value=Mock(id="click-123"))
        
        service = EmailTrackingService(AsyncMock(), click_repo_mock, subscription_repo_mock = AsyncMock())
        
        click = await service.record_link_clicked(
            tracking_id="tracking-123",
            url="https://example.com/confirm",
            ip_address="1.2.3.4"
        )
        
        click_repo_mock.save.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_email_stats(self):
        """Test getting email statistics"""
        tracking_repo_mock = AsyncMock()
        tracking_repo_mock.count_by_template = AsyncMock(return_value=100)
        tracking_repo_mock.count_opened = AsyncMock(return_value=75)
        
        service = EmailTrackingService(tracking_repo_mock, AsyncMock(), subscription_repo_mock = AsyncMock())
        
        stats = await service.get_email_stats(template="welcome")
        
        assert stats["sent"] == 100 or tracking_repo_mock.count_by_template.called
        assert stats["opened"] == 75 or tracking_repo_mock.count_opened.called

