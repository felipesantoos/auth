"""
Unit tests for Celery Email Tasks
Tests background email task execution
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from infra.celery.tasks.email_tasks import (
    send_email_task,
    send_template_email_task,
    send_bulk_email_task,
    send_scheduled_email_task
)


@pytest.mark.asyncio
async def test_send_email_task():
    """Test Celery email task."""
    with patch('infra.celery.tasks.email_tasks.EmailService') as MockEmailService:
        mock_service = MockEmailService.return_value
        mock_service.send_email = AsyncMock(return_value={"success": True, "message_id": "123"})
        
        # Call task directly (not via delay)
        result = send_email_task(
            to=["test@example.com"],
            subject="Test Email",
            html_content="<p>Test</p>"
        )
        
        assert result["success"] is True


@pytest.mark.asyncio
async def test_send_template_email_task():
    """Test Celery template email task."""
    with patch('infra.celery.tasks.email_tasks.EmailService') as MockEmailService:
        mock_service = MockEmailService.return_value
        mock_service.send_template_email = AsyncMock(return_value={"success": True, "message_id": "456"})
        
        result = send_template_email_task(
            to=["test@example.com"],
            subject="Test",
            template_name="welcome",
            context={"user_name": "John"}
        )
        
        assert result["success"] is True


@pytest.mark.asyncio
async def test_send_bulk_email_task():
    """Test Celery bulk email task."""
    with patch('infra.celery.tasks.email_tasks.EmailService') as MockEmailService:
        mock_service = MockEmailService.return_value
        mock_service.send_bulk_email = AsyncMock(return_value=[
            {"success": True},
            {"success": True}
        ])
        
        messages_data = [
            {"to": ["user1@example.com"], "subject": "Test 1", "html_content": "<p>1</p>"},
            {"to": ["user2@example.com"], "subject": "Test 2", "html_content": "<p>2</p>"}
        ]
        
        results = send_bulk_email_task(messages_data=messages_data)
        
        assert len(results) == 2


@pytest.mark.asyncio
async def test_send_scheduled_email_task():
    """Test Celery scheduled email task."""
    with patch('infra.celery.tasks.email_tasks.send_email_task') as mock_send:
        mock_send.return_value = {"success": True}
        
        result = send_scheduled_email_task(
            to=["test@example.com"],
            subject="Scheduled Email",
            html_content="<p>Scheduled</p>"
        )
        
        assert result["success"] is True


def test_email_task_retry_on_failure():
    """Test that email task retries on failure."""
    # Verify task has retry configuration
    assert send_email_task.autoretry_for == (Exception,)
    assert send_email_task.retry_kwargs['max_retries'] == 3
    assert send_email_task.retry_backoff is True

