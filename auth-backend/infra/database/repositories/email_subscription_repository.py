"""
Email Subscription Repository
Data access layer for email subscription preferences
"""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from infra.database.models.email_subscription import DBEmailSubscription


class EmailSubscriptionRepository:
    """Repository for email subscription database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, subscription_data: dict) -> DBEmailSubscription:
        """
        Create new email subscription record.
        
        Args:
            subscription_data: Email subscription data
            
        Returns:
            Created email subscription record
        """
        subscription = DBEmailSubscription(**subscription_data)
        self.session.add(subscription)
        await self.session.flush()
        return subscription
    
    async def get_by_id(self, subscription_id: str) -> Optional[DBEmailSubscription]:
        """Get email subscription by ID."""
        result = await self.session.execute(
            select(DBEmailSubscription).where(DBEmailSubscription.id == subscription_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[DBEmailSubscription]:
        """Get email subscription by email address."""
        result = await self.session.execute(
            select(DBEmailSubscription).where(DBEmailSubscription.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_id(self, user_id: str) -> Optional[DBEmailSubscription]:
        """Get email subscription by user ID."""
        result = await self.session.execute(
            select(DBEmailSubscription).where(DBEmailSubscription.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_token(self, token: str) -> Optional[DBEmailSubscription]:
        """Get email subscription by unsubscribe token."""
        result = await self.session.execute(
            select(DBEmailSubscription).where(DBEmailSubscription.unsubscribe_token == token)
        )
        return result.scalar_one_or_none()
    
    async def update(self, subscription: DBEmailSubscription) -> DBEmailSubscription:
        """Update email subscription record."""
        self.session.add(subscription)
        await self.session.flush()
        return subscription
    
    async def delete(self, subscription: DBEmailSubscription) -> None:
        """Delete email subscription record."""
        await self.session.delete(subscription)
        await self.session.flush()
    
    async def get_or_create(self, email: str, user_id: Optional[str] = None) -> DBEmailSubscription:
        """
        Get existing subscription or create new one.
        
        Args:
            email: Email address
            user_id: Optional user ID
            
        Returns:
            Email subscription record
        """
        subscription = await self.get_by_email(email)
        
        if not subscription:
            subscription = await self.create({
                "email": email,
                "user_id": user_id
            })
        
        return subscription

