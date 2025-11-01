"""
Email Tracking Service
Business logic for email tracking operations
"""
import logging
from typing import Optional, Dict
from datetime import datetime

from core.interfaces.primary.email_tracking_service_interface import IEmailTrackingService
from infra.database.repositories.email_tracking_repository import EmailTrackingRepository
from infra.database.repositories.email_click_repository import EmailClickRepository
from infra.database.repositories.email_subscription_repository import EmailSubscriptionRepository

logger = logging.getLogger(__name__)


class EmailTrackingService(IEmailTrackingService):
    """
    Service for email tracking operations.
    
    Implements business logic for tracking email opens, clicks,
    and managing subscription preferences.
    """
    
    def __init__(
        self,
        tracking_repository: EmailTrackingRepository,
        click_repository: EmailClickRepository,
        subscription_repository: EmailSubscriptionRepository
    ):
        """
        Initialize email tracking service.
        
        Args:
            tracking_repository: Repository for email tracking
            click_repository: Repository for email clicks
            subscription_repository: Repository for email subscriptions
        """
        self.tracking_repo = tracking_repository
        self.click_repo = click_repository
        self.subscription_repo = subscription_repository
    
    async def track_open(self, message_id: str) -> bool:
        """Track email open event."""
        try:
            success = await self.tracking_repo.increment_open_count(message_id)
            
            if success:
                logger.info(f"Email opened: {message_id}")
            
            return success
        
        except Exception as e:
            logger.error(f"Error tracking email open: {e}", exc_info=True)
            return False
    
    async def track_click(
        self,
        message_id: str,
        url: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """Track email click event."""
        try:
            # Get tracking record
            tracking = await self.tracking_repo.get_by_message_id(message_id)
            
            if not tracking:
                logger.warning(f"Tracking record not found: {message_id}")
                return False
            
            # Increment click count
            await self.tracking_repo.increment_click_count(message_id)
            
            # Record click details
            await self.click_repo.create({
                "tracking_id": tracking.id,
                "url": url,
                "clicked_at": datetime.utcnow(),
                "ip_address": ip_address,
                "user_agent": user_agent
            })
            
            logger.info(f"Email link clicked: {message_id} -> {url}")
            return True
        
        except Exception as e:
            logger.error(f"Error tracking email click: {e}", exc_info=True)
            return False
    
    async def get_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        template_name: Optional[str] = None
    ) -> Dict:
        """Get email analytics metrics."""
        try:
            analytics = await self.tracking_repo.get_analytics(
                start_date=start_date,
                end_date=end_date,
                template_name=template_name
            )
            
            return analytics
        
        except Exception as e:
            logger.error(f"Error getting email analytics: {e}", exc_info=True)
            raise
    
    async def get_preferences(self, token: str) -> Optional[Dict]:
        """Get email subscription preferences."""
        try:
            subscription = await self.subscription_repo.get_by_token(token)
            
            if not subscription:
                return None
            
            return {
                "email": subscription.email,
                "preferences": {
                    "marketing": subscription.marketing_emails,
                    "notifications": subscription.notification_emails,
                    "updates": subscription.product_updates,
                    "newsletter": subscription.newsletter
                },
                "unsubscribed_at": subscription.unsubscribed_at.isoformat() if subscription.unsubscribed_at else None
            }
        
        except Exception as e:
            logger.error(f"Error getting preferences: {e}", exc_info=True)
            raise
    
    async def update_preferences(
        self,
        token: str,
        marketing: Optional[bool] = None,
        notifications: Optional[bool] = None,
        updates: Optional[bool] = None,
        newsletter: Optional[bool] = None
    ) -> Optional[Dict]:
        """Update email subscription preferences."""
        try:
            subscription = await self.subscription_repo.get_by_token(token)
            
            if not subscription:
                return None
            
            # Update preferences
            if marketing is not None:
                subscription.marketing_emails = marketing
            if notifications is not None:
                subscription.notification_emails = notifications
            if updates is not None:
                subscription.product_updates = updates
            if newsletter is not None:
                subscription.newsletter = newsletter
            
            await self.subscription_repo.update(subscription)
            
            logger.info(f"Updated email preferences for {subscription.email}")
            
            return {
                "status": "updated",
                "preferences": {
                    "marketing": subscription.marketing_emails,
                    "notifications": subscription.notification_emails,
                    "updates": subscription.product_updates,
                    "newsletter": subscription.newsletter
                }
            }
        
        except Exception as e:
            logger.error(f"Error updating preferences: {e}", exc_info=True)
            raise
    
    async def unsubscribe(self, token: str, reason: str = "user_request") -> bool:
        """Unsubscribe user from all emails."""
        try:
            subscription = await self.subscription_repo.get_by_token(token)
            
            if not subscription:
                return False
            
            # Unsubscribe from all email types
            subscription.marketing_emails = False
            subscription.notification_emails = False
            subscription.product_updates = False
            subscription.newsletter = False
            subscription.unsubscribed_at = datetime.utcnow()
            subscription.unsubscribe_reason = reason
            
            await self.subscription_repo.update(subscription)
            
            logger.info(f"User unsubscribed: {subscription.email} (reason: {reason})")
            return True
        
        except Exception as e:
            logger.error(f"Error processing unsubscribe: {e}", exc_info=True)
            raise

