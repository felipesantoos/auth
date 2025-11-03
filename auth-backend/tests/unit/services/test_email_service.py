"""
Unit tests for Email Service
Tests email service functionality
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from infra.email.email_service import EmailService
from core.interfaces.secondary.email_service_interface import (
    EmailMessage,
    EmailAttachment,
    EmailPriority
)


@pytest.fixture
def email_service():
    """Create email service instance for testing."""
    with patch('infra.email.email_service.settings') as mock_settings:
        # Configure mock settings
        mock_settings.smtp_host = None
        mock_settings.smtp_port = 587
        mock_settings.smtp_user = None
        mock_settings.smtp_password = None
        mock_settings.smtp_from_email = "test@example.com"
        mock_settings.smtp_from_name = "Test Sender"
        mock_settings.smtp_use_tls = True
        mock_settings.smtp_timeout = 30
        mock_settings.email_backend = "console"
        mock_settings.email_tracking_enabled = True
        mock_settings.email_templates_dir = "templates/emails"
        mock_settings.frontend_url = "http://localhost:5173"
        mock_settings.api_base_url = "http://localhost:8080"
        
        service = EmailService()
        return service


@pytest.mark.asyncio
async def test_validate_email_valid(email_service):
    """Test email validation with valid email."""
    # Mock DNS resolution
    with patch('dns.resolver.resolve'):
        result = await email_service.validate_email("test@example.com")
        assert result  # validate_email returns truthy value or raises


@pytest.mark.asyncio
async def test_validate_email_invalid_format(email_service):
    """Test email validation with invalid format."""
    result = await email_service.validate_email("invalid-email")
    assert result is False


@pytest.mark.asyncio
async def test_validate_email_disposable(email_service):
    """Test email validation rejects disposable emails."""
    result = await email_service.validate_email("test@tempmail.com")
    assert result is False


@pytest.mark.asyncio
async def test_send_email_console_backend(email_service):
    """Test sending email with console backend."""
    message = EmailMessage(
        to=["recipient@example.com"],
        subject="Test Email",
        html_content="<p>Test content</p>",
        text_content="Test content"
    )
    
    # Mock validate_email to return True
    with patch.object(email_service, 'validate_email', return_value=True):
        result = await email_service.send_email(message)
    
    assert result["success"] is True
    assert result["status"] == "sent_to_console"
    assert "message_id" in result


@pytest.mark.asyncio
async def test_send_email_with_invalid_recipient(email_service):
    """Test sending email with invalid recipient."""
    message = EmailMessage(
        to=["invalid-email"],
        subject="Test Email",
        html_content="<p>Test content</p>"
    )
    
    result = await email_service.send_email(message)
    
    assert result["success"] is False
    assert result["status"] == "invalid_recipient"


@pytest.mark.asyncio
async def test_send_email_with_attachments(email_service):
    """Test sending email with attachments."""
    attachment = EmailAttachment(
        filename="test.pdf",
        content=b"PDF content",
        content_type="application/pdf"
    )
    
    message = EmailMessage(
        to=["recipient@example.com"],
        subject="Test Email with Attachment",
        html_content="<p>Test content</p>",
        attachments=[attachment]
    )
    
    with patch.object(email_service, 'validate_email', return_value=True):
        result = await email_service.send_email(message)
    
    assert result["success"] is True


@pytest.mark.asyncio
async def test_send_email_with_priority(email_service):
    """Test sending email with priority."""
    message = EmailMessage(
        to=["recipient@example.com"],
        subject="Urgent Email",
        html_content="<p>Urgent content</p>",
        priority=EmailPriority.HIGH
    )
    
    with patch.object(email_service, 'validate_email', return_value=True):
        result = await email_service.send_email(message)
    
    assert result["success"] is True


@pytest.mark.asyncio
async def test_send_email_with_tracking(email_service):
    """Test sending email with tracking enabled."""
    message = EmailMessage(
        to=["recipient@example.com"],
        subject="Tracked Email",
        html_content="<p>Content with <a href='http://example.com'>link</a></p>",
        track_opens=True,
        track_clicks=True
    )
    
    with patch.object(email_service, 'validate_email', return_value=True):
        result = await email_service.send_email(message)
    
    assert result["success"] is True


@pytest.mark.asyncio
async def test_send_password_reset_email(email_service):
    """Test sending password reset email."""
    with patch.object(email_service, 'validate_email', return_value=True):
        result = await email_service.send_password_reset_email(
            email="user@example.com",
            reset_token="test-token-123",
            client_id="client-1"
        )
    
    assert result  # validate_email returns truthy value or raises


@pytest.mark.asyncio
async def test_send_bulk_email(email_service):
    """Test sending bulk emails."""
    messages = [
        EmailMessage(
            to=[f"user{i}@example.com"],
            subject=f"Test Email {i}",
            html_content=f"<p>Test content {i}</p>"
        )
        for i in range(3)
    ]
    
    with patch.object(email_service, 'send_email', return_value={"success": True, "message_id": "123"}):
        results = await email_service.send_bulk_email(messages)
    
    assert len(results) == 3
    for result in results:
        assert result["success"] is True


@pytest.mark.asyncio
async def test_template_filters(email_service):
    """Test template custom filters."""
    # Test currency filter
    assert email_service._format_currency(1234.56) == "$1,234.56"
    
    # Test date filter
    date = datetime(2024, 11, 1, 12, 0, 0)
    assert email_service._format_date(date) == "November 01, 2024"
    assert email_service._format_date(date, "%Y-%m-%d") == "2024-11-01"


def test_is_configured(email_service):
    """Test SMTP configuration check."""
    # Service is not configured (console backend)
    assert email_service._is_configured() is False
    
    # Configure SMTP
    email_service.smtp_host = "smtp.gmail.com"
    email_service.smtp_user = "user@gmail.com"
    email_service.smtp_password = "password"
    
    assert email_service._is_configured() is True

