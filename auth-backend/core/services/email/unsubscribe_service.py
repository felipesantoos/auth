"""
Unsubscribe Service
Business logic for managing email subscription preferences and unsubscribe
"""
import hashlib
import logging
from typing import Optional
from datetime import datetime

from config.settings import settings
from core.interfaces.primary.unsubscribe_service_interface import IUnsubscribeService

logger = logging.getLogger(__name__)


class UnsubscribeService(IUnsubscribeService):
    """
    Service for managing email subscriptions and unsubscribe functionality.
    
    Features:
    - Create secure unsubscribe tokens
    - Unsubscribe users from emails
    - Manage granular email preferences
    - Check if emails can be sent to users
    """
    
    def __init__(self, email_subscription_repository):
        """
        Initialize unsubscribe service.
        
        Args:
            email_subscription_repository: Repository for email subscriptions
        """
        self.subscription_repo = email_subscription_repository
    
    def create_unsubscribe_token(self, email: str) -> str:
        """
        Generate secure unsubscribe token.
        
        Args:
            email: Email address
            
        Returns:
            Secure token
        """
        token = hashlib.sha256(
            f"{email}:{settings.jwt_secret}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()
        
        return token
    
    async def create_subscription(
        self,
        email: str,
        user_id: Optional[str] = None
    ) -> dict:
        """
        Create email subscription with unsubscribe token.
        
        Args:
            email: Email address
            user_id: Optional user ID
            
        Returns:
            Subscription data
        """
        # Check if subscription already exists
        existing = await self.subscription_repo.get_by_email(email)
        if existing:
            return {
                "exists": True,
                "subscription_id": existing.id,
                "unsubscribe_token": existing.unsubscribe_token
            }
        
        # Generate token
        token = self.create_unsubscribe_token(email)
        
        # Create subscription
        subscription = await self.subscription_repo.create({
            "email": email,
            "user_id": user_id,
            "unsubscribe_token": token,
            "marketing_emails": True,
            "notification_emails": True,
            "product_updates": True,
            "newsletter": True
        })
        
        logger.info(f"Created email subscription for {email}")
        
        return {
            "exists": False,
            "subscription_id": subscription.id,
            "unsubscribe_token": subscription.unsubscribe_token
        }
    
    async def unsubscribe(
        self,
        email: Optional[str] = None,
        token: Optional[str] = None,
        reason: Optional[str] = None
    ) -> bool:
        """
        Unsubscribe user from all emails.
        
        Args:
            email: Email address (if known)
            token: Unsubscribe token
            reason: Reason for unsubscribing
            
        Returns:
            True if unsubscribed successfully
        """
        # Get subscription
        if token:
            subscription = await self.subscription_repo.get_by_token(token)
        elif email:
            subscription = await self.subscription_repo.get_by_email(email)
        else:
            return False
        
        if not subscription:
            logger.warning(f"Subscription not found for unsubscribe request")
            return False
        
        # Update subscription - unsubscribe from all
        subscription.marketing_emails = False
        subscription.notification_emails = False
        subscription.product_updates = False
        subscription.newsletter = False
        subscription.unsubscribed_at = datetime.utcnow()
        subscription.unsubscribe_reason = reason
        
        await self.subscription_repo.update(subscription)
        
        logger.info(f"User unsubscribed: {subscription.email} (reason: {reason})")
        
        return True
    
    async def update_preferences(
        self,
        email: str,
        marketing_emails: Optional[bool] = None,
        notification_emails: Optional[bool] = None,
        product_updates: Optional[bool] = None,
        newsletter: Optional[bool] = None
    ) -> bool:
        """
        Update granular email preferences.
        
        Args:
            email: Email address
            marketing_emails: Receive marketing emails
            notification_emails: Receive notification emails
            product_updates: Receive product updates
            newsletter: Receive newsletter
            
        Returns:
            True if updated successfully
        """
        subscription = await self.subscription_repo.get_by_email(email)
        
        if not subscription:
            # Create if doesn't exist
            subscription = await self.subscription_repo.create({"email": email})
        
        # Update preferences
        if marketing_emails is not None:
            subscription.marketing_emails = marketing_emails
        if notification_emails is not None:
            subscription.notification_emails = notification_emails
        if product_updates is not None:
            subscription.product_updates = product_updates
        if newsletter is not None:
            subscription.newsletter = newsletter
        
        await self.subscription_repo.update(subscription)
        
        logger.info(f"Updated email preferences for {email}")
        
        return True
    
    async def can_send_email(self, email: str, email_type: str) -> bool:
        """
        Check if user can receive this type of email.
        
        Args:
            email: Email address
            email_type: Type of email (transactional, marketing, notification, product_update, newsletter)
            
        Returns:
            True if email can be sent
        """
        subscription = await self.subscription_repo.get_by_email(email)
        
        # No preference set - allow all emails
        if not subscription:
            return True
        
        # Transactional emails always allowed (password reset, verification, etc)
        if email_type == "transactional":
            return True
        
        # Check preferences
        if email_type == "marketing" and not subscription.marketing_emails:
            return False
        if email_type == "notification" and not subscription.notification_emails:
            return False
        if email_type == "product_update" and not subscription.product_updates:
            return False
        if email_type == "newsletter" and not subscription.newsletter:
            return False
        
        return True
    
    async def get_preferences(self, email: str) -> Optional[dict]:
        """
        Get email preferences for a user.
        
        Args:
            email: Email address
            
        Returns:
            Dict with preferences or None
        """
        subscription = await self.subscription_repo.get_by_email(email)
        
        if not subscription:
            return None
        
        return {
            "email": subscription.email,
            "marketing_emails": subscription.marketing_emails,
            "notification_emails": subscription.notification_emails,
            "product_updates": subscription.product_updates,
            "newsletter": subscription.newsletter,
            "unsubscribed_at": subscription.unsubscribed_at.isoformat() if subscription.unsubscribed_at else None,
            "unsubscribe_reason": subscription.unsubscribe_reason
        }

