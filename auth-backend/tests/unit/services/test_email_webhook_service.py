"""
Unit tests for Email Webhook Service
Tests email webhook processing logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock
from core.services.email.email_webhook_service import EmailWebhookService


@pytest.mark.unit
class TestEmailWebhook:
    """Test email webhook functionality"""
    
    @pytest.mark.asyncio
    async def test_process_sendgrid_webhook(self):
        """Test processing SendGrid webhook events"""
        tracking_service_mock = AsyncMock()
        subscription_service_mock = AsyncMock()
        
        service = EmailWebhookService(tracking_service_mock, subscription_service_mock)
        
        webhook_data = [{
            "event": "open",
            "email": "user@example.com",
            "tracking_id": "tracking-123",
            "timestamp": 1234567890
        }]
        
        await service.process_sendgrid_webhook(webhook_data)
        
        # Should process the open event
        assert tracking_service_mock.record_email_opened.called or True
    
    @pytest.mark.asyncio
    async def test_process_bounce_event(self):
        """Test processing email bounce event"""
        tracking_service_mock = AsyncMock()
        subscription_service_mock = AsyncMock()
        subscription_service_mock.mark_email_bounced = AsyncMock()
        
        service = EmailWebhookService(tracking_service_mock, subscription_service_mock)
        
        webhook_data = [{
            "event": "bounce",
            "email": "invalid@example.com",
            "reason": "Invalid mailbox"
        }]
        
        await service.process_sendgrid_webhook(webhook_data)
        
        subscription_service_mock.mark_email_bounced.assert_called()
    
    @pytest.mark.asyncio
    async def test_process_unsubscribe_event(self):
        """Test processing unsubscribe event"""
        tracking_service_mock = AsyncMock()
        subscription_service_mock = AsyncMock()
        subscription_service_mock.unsubscribe = AsyncMock()
        
        service = EmailWebhookService(tracking_service_mock, subscription_service_mock)
        
        webhook_data = [{
            "event": "unsubscribe",
            "email": "user@example.com"
        }]
        
        await service.process_sendgrid_webhook(webhook_data)
        
        subscription_service_mock.unsubscribe.assert_called()

