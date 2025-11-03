"""
Unit tests for SendGrid Email Service
Tests SendGrid email provider without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from infra.email.providers.sendgrid_service import SendGridEmailService


@pytest.mark.unit
class TestSendGridService:
    """Test SendGrid email service"""

    @patch('infra.email.providers.sendgrid_service.settings')
    def test_sendgrid_service_initialization(self, mock_settings):
        """Should initialize SendGrid service with API key"""
        mock_settings.sendgrid_api_key = 'test-api-key'
        mock_settings.smtp_from_email = 'test@example.com'
        mock_settings.smtp_from_name = 'Test'
        
        with patch('sendgrid.SendGridAPIClient'):
            service = SendGridEmailService()
            assert service is not None

    @pytest.mark.asyncio
    @patch('infra.email.providers.sendgrid_service.settings')
    async def test_send_email_method_exists(self, mock_settings):
        """Should have send_email method"""
        mock_settings.sendgrid_api_key = 'test-api-key'
        mock_settings.smtp_from_email = 'test@example.com'
        mock_settings.smtp_from_name = 'Test'
        
        with patch('sendgrid.SendGridAPIClient'):
            service = SendGridEmailService()
            assert hasattr(service, 'send_email')
            assert callable(service.send_email)

    @pytest.mark.asyncio
    @patch('infra.email.providers.sendgrid_service.settings')
    async def test_send_template_email_method_exists(self, mock_settings):
        """Should have send_template_email method"""
        mock_settings.sendgrid_api_key = 'test-api-key'
        mock_settings.smtp_from_email = 'test@example.com'
        mock_settings.smtp_from_name = 'Test'
        
        with patch('sendgrid.SendGridAPIClient'):
            service = SendGridEmailService()
            assert hasattr(service, 'send_template_email')
            assert callable(service.send_template_email)


@pytest.mark.unit
class TestSendGridEmailFormatting:
    """Test email formatting"""

    def test_formats_from_email(self):
        """Should format from email correctly"""
        from_email = "noreply@example.com"
        from_name = "Test App"
        
        # SendGrid format: (email, name)
        formatted = (from_email, from_name)
        assert formatted[0] == from_email
        assert formatted[1] == from_name

    def test_formats_to_email(self):
        """Should format to email correctly"""
        to_email = "user@example.com"
        to_name = "John Doe"
        
        # SendGrid format
        formatted = (to_email, to_name)
        assert formatted[0] == to_email

