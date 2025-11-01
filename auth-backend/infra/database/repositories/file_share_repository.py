"""File Share Repository"""
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from infra.database.models.file_share import DBFileShare
from datetime import datetime


class FileShareRepository:
    """Repository for file share operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, share_data: dict) -> DBFileShare:
        """Create file share."""
        share = DBFileShare(**share_data)
        self.session.add(share)
        await self.session.commit()
        await self.session.refresh(share)
        return share
    
    async def has_access(self, file_id: str, user_id: str) -> bool:
        """Check if user has access to file."""
        result = await self.session.execute(
            select(DBFileShare).where(
                and_(
                    DBFileShare.file_id == file_id,
                    DBFileShare.shared_with == user_id,
                    or_(
                        DBFileShare.expires_at.is_(None),
                        DBFileShare.expires_at > datetime.utcnow()
                    )
                )
            )
        )
        return result.scalar_one_or_none() is not None

