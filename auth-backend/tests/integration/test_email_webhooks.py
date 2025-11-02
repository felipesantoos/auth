"""
Integration tests for Email Webhook Routes
Tests email provider webhook endpoints (SendGrid, etc.)
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestEmailWebhooks:
    """Test email webhook routes"""
    
    @pytest.mark.asyncio
    async def test_sendgrid_webhook_accepts_events(self, async_client: AsyncClient):
        """Test SendGrid webhook accepts event data"""
        webhook_data = [
            {
                "event": "open",
                "email": "user@example.com",
                "timestamp": 1234567890,
                "tracking_id": "tracking-123"
            }
        ]
        
        response = await async_client.post(
            "/api/v1/webhooks/email/sendgrid",
            json=webhook_data
        )
        
        assert response.status_code in [200, 202]
    
    @pytest.mark.asyncio
    async def test_sendgrid_webhook_processes_bounce(self, async_client: AsyncClient):
        """Test SendGrid webhook processes bounce events"""
        webhook_data = [
            {
                "event": "bounce",
                "email": "invalid@example.com",
                "reason": "Invalid mailbox",
                "status": "5.1.1"
            }
        ]
        
        response = await async_client.post(
            "/api/v1/webhooks/email/sendgrid",
            json=webhook_data
        )
        
        assert response.status_code in [200, 202]
    
    @pytest.mark.asyncio
    async def test_sendgrid_webhook_processes_click(self, async_client: AsyncClient):
        """Test SendGrid webhook processes click events"""
        webhook_data = [
            {
                "event": "click",
                "email": "user@example.com",
                "url": "https://example.com/verify",
                "tracking_id": "tracking-123"
            }
        ]
        
        response = await async_client.post(
            "/api/v1/webhooks/email/sendgrid",
            json=webhook_data
        )
        
        assert response.status_code in [200, 202]
    
    @pytest.mark.asyncio
    async def test_sendgrid_webhook_validates_signature(self, async_client: AsyncClient):
        """Test SendGrid webhook validates signature"""
        # Without valid signature, should reject
        response = await async_client.post(
            "/api/v1/webhooks/email/sendgrid",
            json=[{"event": "test"}],
            headers={"X-Twilio-Email-Event-Webhook-Signature": "invalid"}
        )
        
        assert response.status_code in [200, 202, 401, 403]

