"""
Email Celery Tasks
Background tasks for async email sending
"""
import logging
from typing import List, Dict
from datetime import datetime
from celery import Task

from infra.celery.celery_app import celery_app
from infra.email.email_service import EmailService
from core.interfaces.secondary.email_service_interface import EmailMessage, EmailAttachment

logger = logging.getLogger(__name__)


class EmailTask(Task):
    """Base task for email operations with error handling."""
    
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 60}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True


@celery_app.task(base=EmailTask, bind=True)
def send_email_task(
    self,
    to: List[str],
    subject: str,
    html_content: str = None,
    text_content: str = None,
    **kwargs
):
    """
    Send single email in background.
    
    Args:
        to: Recipient email addresses
        subject: Email subject
        html_content: HTML content
        text_content: Plain text content
        **kwargs: Additional EmailMessage fields
        
    Returns:
        Result dict with status
    """
    try:
        logger.info(f"[Celery] Sending email to {to}: {subject}")
        
        # Create email service (synchronous context in Celery)
        email_service = EmailService()
        
        # Create message
        message = EmailMessage(
            to=to,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            **kwargs
        )
        
        # Send email (need to run async in sync context)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(email_service.send_email(message))
        loop.close()
        
        logger.info(f"[Celery] Email sent successfully: {result.get('message_id')}")
        return result
    
    except Exception as e:
        logger.error(f"[Celery] Failed to send email: {e}", exc_info=True)
        raise self.retry(exc=e)


@celery_app.task(base=EmailTask, bind=True)
def send_template_email_task(
    self,
    to: List[str],
    subject: str,
    template_name: str,
    context: dict,
    **kwargs
):
    """
    Send template email in background.
    
    Args:
        to: Recipient email addresses
        subject: Email subject
        template_name: Template name (without .html)
        context: Template variables
        **kwargs: Additional EmailMessage fields
        
    Returns:
        Result dict with status
    """
    try:
        logger.info(f"[Celery] Sending template email '{template_name}' to {to}")
        
        email_service = EmailService()
        
        # Send template email
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            email_service.send_template_email(
                to=to,
                subject=subject,
                template_name=template_name,
                context=context,
                **kwargs
            )
        )
        loop.close()
        
        logger.info(f"[Celery] Template email sent: {result.get('message_id')}")
        return result
    
    except Exception as e:
        logger.error(f"[Celery] Failed to send template email: {e}", exc_info=True)
        raise self.retry(exc=e)


@celery_app.task(base=EmailTask, bind=True)
def send_bulk_email_task(
    self,
    messages_data: List[Dict],
    batch_size: int = 100
):
    """
    Send bulk emails in background.
    
    Args:
        messages_data: List of message data dicts
        batch_size: Batch size for sending
        
    Returns:
        List of results
    """
    try:
        logger.info(f"[Celery] Sending {len(messages_data)} emails in bulk")
        
        email_service = EmailService()
        
        # Convert dicts to EmailMessage objects
        messages = []
        for msg_data in messages_data:
            messages.append(EmailMessage(**msg_data))
        
        # Send bulk
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(
            email_service.send_bulk_email(messages, batch_size=batch_size)
        )
        loop.close()
        
        success_count = sum(1 for r in results if r.get('success'))
        logger.info(f"[Celery] Bulk email completed: {success_count}/{len(messages)} successful")
        
        return results
    
    except Exception as e:
        logger.error(f"[Celery] Failed to send bulk email: {e}", exc_info=True)
        raise self.retry(exc=e)


@celery_app.task(base=EmailTask)
def send_scheduled_email_task(
    to: List[str],
    subject: str,
    html_content: str = None,
    text_content: str = None,
    **kwargs
):
    """
    Send scheduled email (executed at specific time via countdown/eta).
    
    This task is scheduled with .apply_async(countdown=seconds) or .apply_async(eta=datetime).
    
    Args:
        to: Recipient email addresses
        subject: Email subject
        html_content: HTML content
        text_content: Plain text content
        **kwargs: Additional EmailMessage fields
        
    Returns:
        Result dict with status
    """
    logger.info(f"[Celery] Sending scheduled email to {to}: {subject}")
    
    # Reuse send_email_task logic
    return send_email_task(
        to=to,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
        **kwargs
    )

