"""
Unit tests for Email Service (Infrastructure)
Tests email service implementation without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from infra.email.email_service import EmailService


@pytest.mark.unit
class TestEmailService:
    """Test email service functionality"""
    
    @pytest.mark.asyncio
    async def test_send_email(self):
        """Test sending email"""
        provider_mock = AsyncMock()
        provider_mock.send = AsyncMock(return_value={"message_id": "msg-123"})
        
        service = EmailService(provider=provider_mock)
        
        result = await service.send_email(
            to="user@example.com",
            subject="Test Email",
            body="Test content"
        )
        
        provider_mock.send.assert_called_once()
        assert result["message_id"] == "msg-123"
    
    @pytest.mark.asyncio
    async def test_send_template_email(self):
        """Test sending templated email"""
        provider_mock = AsyncMock()
        provider_mock.send_template = AsyncMock(return_value={"message_id": "msg-123"})
        
        service = EmailService(provider=provider_mock)
        
        result = await service.send_template(
            to="user@example.com",
            template="welcome",
            context={"name": "John"}
        )
        
        provider_mock.send_template.assert_called_once()

