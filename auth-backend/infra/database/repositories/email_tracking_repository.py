"""
Email Tracking Repository
Data access layer for email tracking operations
"""
from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from infra.database.models.email_tracking import DBEmailTracking


class EmailTrackingRepository:
    """Repository for email tracking database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, tracking_data: dict) -> DBEmailTracking:
        """
        Create new email tracking record.
        
        Args:
            tracking_data: Email tracking data
            
        Returns:
            Created email tracking record
        """
        tracking = DBEmailTracking(**tracking_data)
        self.session.add(tracking)
        await self.session.flush()
        return tracking
    
    async def get_by_id(self, tracking_id: str) -> Optional[DBEmailTracking]:
        """Get email tracking by ID."""
        result = await self.session.execute(
            select(DBEmailTracking).where(DBEmailTracking.id == tracking_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_message_id(self, message_id: str) -> Optional[DBEmailTracking]:
        """Get email tracking by message ID."""
        result = await self.session.execute(
            select(DBEmailTracking).where(DBEmailTracking.message_id == message_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(
        self,
        email: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[DBEmailTracking]:
        """Get email tracking records for a specific email address."""
        result = await self.session.execute(
            select(DBEmailTracking)
            .where(DBEmailTracking.email == email)
            .order_by(DBEmailTracking.sent_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
    
    async def get_by_user_id(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[DBEmailTracking]:
        """Get email tracking records for a specific user."""
        result = await self.session.execute(
            select(DBEmailTracking)
            .where(DBEmailTracking.user_id == user_id)
            .order_by(DBEmailTracking.sent_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
    
    async def update(self, tracking: DBEmailTracking) -> DBEmailTracking:
        """Update email tracking record."""
        self.session.add(tracking)
        await self.session.flush()
        return tracking
    
    async def increment_open_count(self, message_id: str) -> bool:
        """
        Increment open count for an email.
        
        Args:
            message_id: Email message ID
            
        Returns:
            True if updated successfully
        """
        tracking = await self.get_by_message_id(message_id)
        if not tracking:
            return False
        
        # Set opened_at if first open
        if not tracking.opened_at:
            tracking.opened_at = datetime.utcnow()
        
        tracking.open_count += 1
        await self.update(tracking)
        return True
    
    async def increment_click_count(self, message_id: str) -> bool:
        """
        Increment click count for an email.
        
        Args:
            message_id: Email message ID
            
        Returns:
            True if updated successfully
        """
        tracking = await self.get_by_message_id(message_id)
        if not tracking:
            return False
        
        # Set first_click_at if first click
        if not tracking.first_click_at:
            tracking.first_click_at = datetime.utcnow()
        
        tracking.click_count += 1
        await self.update(tracking)
        return True
    
    async def mark_delivered(self, message_id: str) -> bool:
        """Mark email as delivered."""
        tracking = await self.get_by_message_id(message_id)
        if not tracking:
            return False
        
        tracking.delivered_at = datetime.utcnow()
        await self.update(tracking)
        return True
    
    async def mark_bounced(
        self,
        message_id: str,
        bounce_type: str,
        bounce_reason: str
    ) -> bool:
        """Mark email as bounced."""
        tracking = await self.get_by_message_id(message_id)
        if not tracking:
            return False
        
        tracking.bounced = True
        tracking.bounce_type = bounce_type
        tracking.bounce_reason = bounce_reason
        await self.update(tracking)
        return True
    
    async def mark_spam_complaint(self, message_id: str) -> bool:
        """Mark email as spam complaint."""
        tracking = await self.get_by_message_id(message_id)
        if not tracking:
            return False
        
        tracking.spam_complaint = True
        await self.update(tracking)
        return True
    
    async def get_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        template_name: Optional[str] = None
    ) -> Dict:
        """
        Get email analytics metrics.
        
        Args:
            start_date: Filter by start date
            end_date: Filter by end date
            template_name: Filter by template
            
        Returns:
            Dict with aggregated metrics
        """
        # Build query conditions
        conditions = []
        if start_date:
            conditions.append(DBEmailTracking.sent_at >= start_date)
        if end_date:
            conditions.append(DBEmailTracking.sent_at <= end_date)
        if template_name:
            conditions.append(DBEmailTracking.template_name == template_name)
        
        # Get counts
        result = await self.session.execute(
            select(
                func.count(DBEmailTracking.id).label('total_sent'),
                func.sum(func.cast(DBEmailTracking.delivered_at.isnot(None), func.Integer())).label('delivered'),
                func.sum(func.cast(DBEmailTracking.opened_at.isnot(None), func.Integer())).label('opened'),
                func.sum(func.cast(DBEmailTracking.first_click_at.isnot(None), func.Integer())).label('clicked'),
                func.sum(func.cast(DBEmailTracking.bounced, func.Integer())).label('bounced'),
                func.sum(func.cast(DBEmailTracking.spam_complaint, func.Integer())).label('spam_complaints')
            ).where(and_(*conditions) if conditions else True)
        )
        
        row = result.first()
        
        total_sent = row.total_sent or 0
        delivered = row.delivered or 0
        opened = row.opened or 0
        clicked = row.clicked or 0
        bounced = row.bounced or 0
        spam_complaints = row.spam_complaints or 0
        
        return {
            "total_sent": total_sent,
            "delivered": delivered,
            "opened": opened,
            "clicked": clicked,
            "bounced": bounced,
            "spam_complaints": spam_complaints,
            "delivery_rate": f"{(delivered / total_sent * 100):.1f}%" if total_sent > 0 else "0%",
            "open_rate": f"{(opened / delivered * 100):.1f}%" if delivered > 0 else "0%",
            "click_rate": f"{(clicked / delivered * 100):.1f}%" if delivered > 0 else "0%",
            "bounce_rate": f"{(bounced / total_sent * 100):.1f}%" if total_sent > 0 else "0%",
        }

