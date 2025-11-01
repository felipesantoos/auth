"""
Email Webhooks
Webhooks for handling email provider callbacks (bounces, spam complaints, etc)
"""
import logging
import hashlib
import hmac
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, Header, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from infra.database.database import get_db
from infra.database.repositories.email_tracking_repository import EmailTrackingRepository
from infra.database.repositories.email_subscription_repository import EmailSubscriptionRepository
from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/email", tags=["webhooks"])


class EmailWebhookEvent(BaseModel):
    """Email webhook event model."""
    event: str  # bounce, spam_complaint, unsubscribe, delivered
    email: str
    message_id: Optional[str] = None
    bounce_type: Optional[str] = None  # hard, soft
    bounce_reason: Optional[str] = None
    timestamp: Optional[datetime] = None


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify webhook signature for security.
    
    Args:
        payload: Raw request payload
        signature: Signature from provider
        secret: Webhook secret
        
    Returns:
        True if signature is valid
    """
    if not secret or not signature:
        return False
    
    # Calculate expected signature
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)


@router.post("/bounce")
async def handle_email_bounce(
    request: Request,
    signature: Optional[str] = Header(None, alias="X-Webhook-Signature"),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle email bounce webhook from email provider.
    
    Bounce types:
    - Hard bounce: Invalid/non-existent email (block permanently)
    - Soft bounce: Temporary issue (retry later)
    - Complaint: User marked as spam (unsubscribe immediately)
    
    Args:
        request: HTTP request
        signature: Webhook signature for verification
        db: Database session
        
    Returns:
        Status response
    """
    try:
        # Get raw payload for signature verification
        payload = await request.body()
        webhook_data = await request.json()
        
        # Verify signature if configured
        # Note: This is a simplified example. In production, use provider-specific verification
        # if settings.email_webhook_secret:
        #     if not verify_webhook_signature(payload, signature, settings.email_webhook_secret):
        #         raise HTTPException(status_code=401, detail="Invalid signature")
        
        event_type = webhook_data.get("event")
        email = webhook_data.get("email")
        message_id = webhook_data.get("message_id")
        
        if not email or not event_type:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        tracking_repo = EmailTrackingRepository(db)
        subscription_repo = EmailSubscriptionRepository(db)
        
        if event_type == "hard_bounce":
            # Mark email as hard bounced - don't send again
            if message_id:
                await tracking_repo.mark_bounced(
                    message_id=message_id,
                    bounce_type="hard",
                    bounce_reason=webhook_data.get("bounce_reason", "Hard bounce")
                )
            
            # Could also add to blacklist here
            logger.warning(f"Hard bounce: {email}")
        
        elif event_type == "soft_bounce":
            # Track soft bounce, retry later
            if message_id:
                await tracking_repo.mark_bounced(
                    message_id=message_id,
                    bounce_type="soft",
                    bounce_reason=webhook_data.get("bounce_reason", "Soft bounce")
                )
            
            # If too many soft bounces (>5), treat as hard bounce
            # This would require counting soft bounces per email
            logger.info(f"Soft bounce: {email}")
        
        elif event_type == "spam_complaint":
            # User marked as spam - unsubscribe immediately
            if message_id:
                await tracking_repo.mark_spam_complaint(message_id)
            
            # Unsubscribe from all emails
            subscription = await subscription_repo.get_by_email(email)
            if subscription:
                subscription.marketing_emails = False
                subscription.notification_emails = False
                subscription.product_updates = False
                subscription.newsletter = False
                subscription.unsubscribed_at = datetime.utcnow()
                subscription.unsubscribe_reason = "spam_complaint"
                await subscription_repo.update(subscription)
            
            logger.warning(f"Spam complaint: {email}")
        
        elif event_type == "delivered":
            # Mark email as delivered
            if message_id:
                await tracking_repo.mark_delivered(message_id)
            
            logger.info(f"Email delivered: {email}")
        
        elif event_type == "unsubscribe":
            # User unsubscribed via provider interface
            subscription = await subscription_repo.get_by_email(email)
            if subscription:
                subscription.marketing_emails = False
                subscription.unsubscribed_at = datetime.utcnow()
                subscription.unsubscribe_reason = "provider_unsubscribe"
                await subscription_repo.update(subscription)
            
            logger.info(f"User unsubscribed via provider: {email}")
        
        await db.commit()
        
        return {"status": "processed", "event": event_type}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing email webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process webhook")


@router.post("/sendgrid")
async def handle_sendgrid_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
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
        db: Database session
        
    Returns:
        Status response
    """
    try:
        events = await request.json()
        
        if not isinstance(events, list):
            events = [events]
        
        tracking_repo = EmailTrackingRepository(db)
        subscription_repo = EmailSubscriptionRepository(db)
        
        for event in events:
            event_type = event.get("event")
            email = event.get("email")
            message_id = event.get("sg_message_id")
            
            if not email or not event_type:
                continue
            
            # Map SendGrid events to our event types
            if event_type == "bounce":
                bounce_type = "hard" if event.get("type") == "blocked" else "soft"
                if message_id:
                    await tracking_repo.mark_bounced(
                        message_id=message_id,
                        bounce_type=bounce_type,
                        bounce_reason=event.get("reason", "")
                    )
            
            elif event_type == "spamreport":
                if message_id:
                    await tracking_repo.mark_spam_complaint(message_id)
                
                # Unsubscribe
                subscription = await subscription_repo.get_by_email(email)
                if subscription:
                    subscription.marketing_emails = False
                    subscription.notification_emails = False
                    subscription.product_updates = False
                    subscription.newsletter = False
                    subscription.unsubscribed_at = datetime.utcnow()
                    subscription.unsubscribe_reason = "spam_complaint"
                    await subscription_repo.update(subscription)
            
            elif event_type == "delivered":
                if message_id:
                    await tracking_repo.mark_delivered(message_id)
            
            elif event_type == "open":
                if message_id:
                    await tracking_repo.increment_open_count(message_id)
            
            elif event_type == "click":
                if message_id:
                    await tracking_repo.increment_click_count(message_id)
        
        await db.commit()
        
        return {"status": "processed", "count": len(events)}
    
    except Exception as e:
        logger.error(f"Error processing SendGrid webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process webhook")


@router.post("/ses")
async def handle_ses_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle AWS SES SNS notifications.
    
    AWS SES sends notifications via SNS in JSON format.
    
    Args:
        request: HTTP request
        db: Database session
        
    Returns:
        Status response
    """
    try:
        data = await request.json()
        
        # Handle SNS subscription confirmation
        if data.get("Type") == "SubscriptionConfirmation":
            # In production, you would visit the SubscribeURL to confirm
            logger.info(f"SNS subscription confirmation: {data.get('SubscribeURL')}")
            return {"status": "confirmation_received"}
        
        # Handle notification
        if data.get("Type") == "Notification":
            message = data.get("Message")
            if isinstance(message, str):
                import json
                message = json.loads(message)
            
            notification_type = message.get("notificationType")
            mail = message.get("mail", {})
            message_id = mail.get("messageId")
            
            tracking_repo = EmailTrackingRepository(db)
            subscription_repo = EmailSubscriptionRepository(db)
            
            if notification_type == "Bounce":
                bounce = message.get("bounce", {})
                bounce_type = bounce.get("bounceType", "").lower()  # "Permanent" or "Transient"
                
                for recipient in bounce.get("bouncedRecipients", []):
                    email = recipient.get("emailAddress")
                    if message_id and email:
                        await tracking_repo.mark_bounced(
                            message_id=message_id,
                            bounce_type="hard" if bounce_type == "permanent" else "soft",
                            bounce_reason=recipient.get("diagnosticCode", "")
                        )
            
            elif notification_type == "Complaint":
                for recipient in message.get("complaint", {}).get("complainedRecipients", []):
                    email = recipient.get("emailAddress")
                    if message_id:
                        await tracking_repo.mark_spam_complaint(message_id)
                    
                    if email:
                        # Unsubscribe
                        subscription = await subscription_repo.get_by_email(email)
                        if subscription:
                            subscription.marketing_emails = False
                            subscription.notification_emails = False
                            subscription.product_updates = False
                            subscription.newsletter = False
                            subscription.unsubscribed_at = datetime.utcnow()
                            subscription.unsubscribe_reason = "spam_complaint"
                            await subscription_repo.update(subscription)
            
            elif notification_type == "Delivery":
                if message_id:
                    await tracking_repo.mark_delivered(message_id)
            
            await db.commit()
        
        return {"status": "processed"}
    
    except Exception as e:
        logger.error(f"Error processing SES webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process webhook")

