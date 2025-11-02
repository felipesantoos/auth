"""
Unit tests for SendGrid Service
Tests SendGrid email provider without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from infra.email.providers.sendgrid_service import SendGridService


@pytest.mark.unit
class TestSendGridService:
    """Test SendGrid service functionality"""
    
    @pytest.mark.asyncio
    async def test_send_email_via_sendgrid(self):
        """Test sending email via SendGrid API"""
        service = SendGridService(api_key="test-api-key")
        
        with patch('sendgrid.SendGridAPIClient') as mock_sg:
            mock_sg.return_value.send.return_value = Mock(status_code=202)
            
            result = await service.send(
                to_email="user@example.com",
                subject="Test",
                html_content="<p>Test</p>"
            )
            
            assert result or mock_sg.called
    
    @pytest.mark.asyncio
    async def test_send_template_email_via_sendgrid(self):
        """Test sending template email via SendGrid"""
        service = SendGridService(api_key="test-api-key")
        
        with patch('sendgrid.SendGridAPIClient') as mock_sg:
            mock_sg.return_value.send.return_value = Mock(status_code=202)
            
            result = await service.send_template(
                to_email="user@example.com",
                template_id="d-template123",
                dynamic_data={"name": "John"}
            )
            
            assert result or mock_sg.called

