"""
Email Click Repository
Data access layer for email click tracking
"""
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from infra.database.models.email_click import DBEmailClick


class EmailClickRepository:
    """Repository for email click database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, click_data: dict) -> DBEmailClick:
        """
        Create new email click record.
        
        Args:
            click_data: Email click data
            
        Returns:
            Created email click record
        """
        click = DBEmailClick(**click_data)
        self.session.add(click)
        await self.session.flush()
        return click
    
    async def get_by_id(self, click_id: str) -> Optional[DBEmailClick]:
        """Get email click by ID."""
        result = await self.session.execute(
            select(DBEmailClick).where(DBEmailClick.id == click_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_tracking_id(
        self,
        tracking_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[DBEmailClick]:
        """Get all clicks for a specific email tracking record."""
        result = await self.session.execute(
            select(DBEmailClick)
            .where(DBEmailClick.tracking_id == tracking_id)
            .order_by(DBEmailClick.clicked_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
    
    async def count_by_tracking_id(self, tracking_id: str) -> int:
        """Count total clicks for a specific email tracking record."""
        result = await self.session.execute(
            select(DBEmailClick)
            .where(DBEmailClick.tracking_id == tracking_id)
        )
        return len(result.scalars().all())

