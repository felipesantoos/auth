"""
Email Webhooks
Webhooks for handling email provider callbacks (bounces, spam complaints, etc)

Following Hexagonal Architecture:
- Routes depend only on PRIMARY PORTS (interfaces)
- No direct dependency on infrastructure layer
- Services injected via DI container
"""
import logging
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Header, Depends
from pydantic import BaseModel

from core.interfaces.primary.email_webhook_service_interface import IEmailWebhookService
from app.api.dicontainer.dicontainer import get_email_webhook_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/webhooks/email", tags=["webhooks"])


class EmailWebhookEvent(BaseModel):
    """Email webhook event model (generic)."""
    event: str  # bounce, spam_complaint, unsubscribe, delivered
    email: str
    message_id: Optional[str] = None
    bounce_type: Optional[str] = None  # hard, soft
    bounce_reason: Optional[str] = None


@router.post("/bounce")
async def handle_email_bounce(
    request: Request,
    signature: Optional[str] = Header(None, alias="X-Webhook-Signature"),
    webhook_service: IEmailWebhookService = Depends(get_email_webhook_service)
):
    """
    Handle generic email bounce webhook.
    
    Bounce types:
    - Hard bounce: Invalid/non-existent email (block permanently)
    - Soft bounce: Temporary issue (retry later)
    - Complaint: User marked as spam (unsubscribe immediately)
    
    Args:
        request: HTTP request
        signature: Webhook signature for verification
        webhook_service: Injected email webhook service
        
    Returns:
        Status response
    """
    try:
        webhook_data = await request.json()
        
        # Note: Signature verification would be implemented here in production
        # if signature:
        #     verify_signature(await request.body(), signature)
        
        event_type = webhook_data.get("event")
        email = webhook_data.get("email")
        message_id = webhook_data.get("message_id")
        
        if not email or not event_type:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Route to appropriate handler
        if event_type == "hard_bounce":
            await webhook_service.handle_bounce(
                email=email,
                message_id=message_id,
                bounce_type="hard",
                bounce_reason=webhook_data.get("bounce_reason", "Hard bounce")
            )
        
        elif event_type == "soft_bounce":
            await webhook_service.handle_bounce(
                email=email,
                message_id=message_id,
                bounce_type="soft",
                bounce_reason=webhook_data.get("bounce_reason", "Soft bounce")
            )
        
        elif event_type == "spam_complaint":
            await webhook_service.handle_spam_complaint(
                email=email,
                message_id=message_id
            )
        
        elif event_type == "delivered":
            if message_id:
                await webhook_service.handle_delivery(message_id)
        
        elif event_type == "unsubscribe":
            await webhook_service.handle_unsubscribe(email)
        
        return {"status": "processed", "event": event_type}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing email webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process webhook")


@router.post("/sendgrid")
async def handle_sendgrid_webhook(
    request: Request,
    webhook_service: IEmailWebhookService = Depends(get_email_webhook_service)
):
    """
    Handle SendGrid-specific webhook events.
    
    SendGrid sends events as JSON array:
    [
        {
            "event": "bounce",
            "email": "user@example.com",
            "sg_message_id": "...",
            "type": "bounced",
            "reason": "...",
            ...
        }
    ]
    
    Args:
        request: HTTP request
        webhook_service: Injected email webhook service
        
    Returns:
        Status response
    """
    try:
        events = await request.json()
        
        if not isinstance(events, list):
            events = [events]
        
        processed_count = 0
        
        for event in events:
            success = await webhook_service.process_sendgrid_event(event)
            if success:
                processed_count += 1
        
        return {"status": "processed", "count": processed_count}
    
    except Exception as e:
        logger.error(f"Error processing SendGrid webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process webhook")


@router.post("/ses")
async def handle_ses_webhook(
    request: Request,
    webhook_service: IEmailWebhookService = Depends(get_email_webhook_service)
):
    """
    Handle AWS SES SNS notifications.
    
    AWS SES sends notifications via SNS in JSON format.
    
    Args:
        request: HTTP request
        webhook_service: Injected email webhook service
        
    Returns:
        Status response
    """
    try:
        data = await request.json()
        
        # Handle SNS subscription confirmation
        if data.get("Type") == "SubscriptionConfirmation":
            logger.info(f"SNS subscription confirmation: {data.get('SubscribeURL')}")
            return {"status": "confirmation_received"}
        
        # Handle notification
        if data.get("Type") == "Notification":
            message = data.get("Message")
            
            # Parse message if it's a string
            if isinstance(message, str):
                import json
                message = json.loads(message)
            
            # Process through service
            success = await webhook_service.process_ses_event(message)
            
            return {"status": "processed" if success else "failed"}
        
        return {"status": "unknown_type"}
    
    except Exception as e:
        logger.error(f"Error processing SES webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process webhook")
