"""
Email Webhook Service
Business logic for handling email provider webhooks
"""
import logging
from typing import Optional, Dict
from datetime import datetime

from core.interfaces.primary.email_webhook_service_interface import IEmailWebhookService
from infra.database.repositories.email_tracking_repository import EmailTrackingRepository
from infra.database.repositories.email_subscription_repository import EmailSubscriptionRepository

logger = logging.getLogger(__name__)


class EmailWebhookService(IEmailWebhookService):
    """
    Service for handling email provider webhooks.
    
    Processes events from email providers (SendGrid, AWS SES, Mailgun)
    and updates tracking and subscription data.
    """
    
    def __init__(
        self,
        tracking_repository: EmailTrackingRepository,
        subscription_repository: EmailSubscriptionRepository
    ):
        """
        Initialize email webhook service.
        
        Args:
            tracking_repository: Repository for email tracking
            subscription_repository: Repository for email subscriptions
        """
        self.tracking_repo = tracking_repository
        self.subscription_repo = subscription_repository
    
    async def handle_bounce(
        self,
        email: str,
        message_id: Optional[str] = None,
        bounce_type: str = "hard",
        bounce_reason: Optional[str] = None
    ) -> bool:
        """Handle email bounce event."""
        try:
            # Update tracking if message_id provided
            if message_id:
                await self.tracking_repo.mark_bounced(
                    message_id=message_id,
                    bounce_type=bounce_type,
                    bounce_reason=bounce_reason or f"{bounce_type.capitalize()} bounce"
                )
            
            # For hard bounces, consider adding to blacklist
            if bounce_type == "hard":
                logger.warning(f"Hard bounce: {email}")
                # Could add to blacklist here in future
            else:
                logger.info(f"Soft bounce: {email}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error handling bounce: {e}", exc_info=True)
            return False
    
    async def handle_spam_complaint(
        self,
        email: str,
        message_id: Optional[str] = None
    ) -> bool:
        """Handle spam complaint - unsubscribe immediately."""
        try:
            # Mark as spam in tracking
            if message_id:
                await self.tracking_repo.mark_spam_complaint(message_id)
            
            # Unsubscribe user from all emails
            subscription = await self.subscription_repo.get_by_email(email)
            
            if subscription:
                subscription.marketing_emails = False
                subscription.notification_emails = False
                subscription.product_updates = False
                subscription.newsletter = False
                subscription.unsubscribed_at = datetime.utcnow()
                subscription.unsubscribe_reason = "spam_complaint"
                await self.subscription_repo.update(subscription)
            else:
                # Create subscription with unsubscribed status
                await self.subscription_repo.create({
                    "email": email,
                    "marketing_emails": False,
                    "notification_emails": False,
                    "product_updates": False,
                    "newsletter": False,
                    "unsubscribed_at": datetime.utcnow(),
                    "unsubscribe_reason": "spam_complaint"
                })
            
            logger.warning(f"Spam complaint handled: {email}")
            return True
        
        except Exception as e:
            logger.error(f"Error handling spam complaint: {e}", exc_info=True)
            return False
    
    async def handle_delivery(self, message_id: str) -> bool:
        """Handle successful delivery event."""
        try:
            await self.tracking_repo.mark_delivered(message_id)
            logger.info(f"Email delivered: {message_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error handling delivery: {e}", exc_info=True)
            return False
    
    async def handle_unsubscribe(
        self,
        email: str,
        reason: str = "provider_unsubscribe"
    ) -> bool:
        """Handle unsubscribe event from provider."""
        try:
            subscription = await self.subscription_repo.get_by_email(email)
            
            if subscription:
                subscription.marketing_emails = False
                subscription.unsubscribed_at = datetime.utcnow()
                subscription.unsubscribe_reason = reason
                await self.subscription_repo.update(subscription)
            else:
                # Create subscription with unsubscribed status
                await self.subscription_repo.create({
                    "email": email,
                    "marketing_emails": False,
                    "notification_emails": True,  # Keep transactional
                    "unsubscribed_at": datetime.utcnow(),
                    "unsubscribe_reason": reason
                })
            
            logger.info(f"User unsubscribed via provider: {email}")
            return True
        
        except Exception as e:
            logger.error(f"Error handling unsubscribe: {e}", exc_info=True)
            return False
    
    async def handle_open(self, message_id: str) -> bool:
        """Handle email open event from provider webhook."""
        try:
            await self.tracking_repo.increment_open_count(message_id)
            logger.debug(f"Email opened (webhook): {message_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error handling open: {e}", exc_info=True)
            return False
    
    async def handle_click(
        self,
        message_id: str,
        url: Optional[str] = None
    ) -> bool:
        """Handle email click event from provider webhook."""
        try:
            await self.tracking_repo.increment_click_count(message_id)
            logger.debug(f"Email clicked (webhook): {message_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error handling click: {e}", exc_info=True)
            return False
    
    async def process_sendgrid_event(self, event: Dict) -> bool:
        """
        Process SendGrid-specific webhook event.
        
        SendGrid event format:
        {
            "event": "bounce|spamreport|delivered|open|click",
            "email": "user@example.com",
            "sg_message_id": "...",
            "type": "bounced|blocked",
            "reason": "...",
            ...
        }
        """
        try:
            event_type = event.get("event")
            email = event.get("email")
            message_id = event.get("sg_message_id")
            
            if not email or not event_type:
                logger.warning("Invalid SendGrid event: missing email or event type")
                return False
            
            # Route to appropriate handler
            if event_type == "bounce":
                bounce_type = "hard" if event.get("type") == "blocked" else "soft"
                return await self.handle_bounce(
                    email=email,
                    message_id=message_id,
                    bounce_type=bounce_type,
                    bounce_reason=event.get("reason", "")
                )
            
            elif event_type == "spamreport":
                return await self.handle_spam_complaint(
                    email=email,
                    message_id=message_id
                )
            
            elif event_type == "delivered":
                if message_id:
                    return await self.handle_delivery(message_id)
            
            elif event_type == "open":
                if message_id:
                    return await self.handle_open(message_id)
            
            elif event_type == "click":
                if message_id:
                    return await self.handle_click(
                        message_id=message_id,
                        url=event.get("url")
                    )
            
            return True
        
        except Exception as e:
            logger.error(f"Error processing SendGrid event: {e}", exc_info=True)
            return False
    
    async def process_ses_event(self, message: Dict) -> bool:
        """
        Process AWS SES SNS notification event.
        
        SES event format (SNS notification):
        {
            "notificationType": "Bounce|Complaint|Delivery",
            "mail": {"messageId": "..."},
            "bounce": {"bounceType": "Permanent|Transient", ...},
            "complaint": {"complainedRecipients": [...]}
        }
        """
        try:
            notification_type = message.get("notificationType")
            mail = message.get("mail", {})
            message_id = mail.get("messageId")
            
            if not notification_type:
                logger.warning("Invalid SES event: missing notificationType")
                return False
            
            # Route to appropriate handler
            if notification_type == "Bounce":
                bounce = message.get("bounce", {})
                bounce_type_ses = bounce.get("bounceType", "").lower()
                bounce_type = "hard" if bounce_type_ses == "permanent" else "soft"
                
                for recipient in bounce.get("bouncedRecipients", []):
                    email = recipient.get("emailAddress")
                    if email:
                        await self.handle_bounce(
                            email=email,
                            message_id=message_id,
                            bounce_type=bounce_type,
                            bounce_reason=recipient.get("diagnosticCode", "")
                        )
                
                return True
            
            elif notification_type == "Complaint":
                for recipient in message.get("complaint", {}).get("complainedRecipients", []):
                    email = recipient.get("emailAddress")
                    if email:
                        await self.handle_spam_complaint(
                            email=email,
                            message_id=message_id
                        )
                
                return True
            
            elif notification_type == "Delivery":
                if message_id:
                    return await self.handle_delivery(message_id)
            
            return True
        
        except Exception as e:
            logger.error(f"Error processing SES event: {e}", exc_info=True)
            return False

