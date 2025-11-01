"""Pending Upload Repository"""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from infra.database.models.pending_upload import DBPendingUpload


class PendingUploadRepository:
    """Repository for pending upload operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, upload_data: dict) -> DBPendingUpload:
        """Create pending upload record."""
        upload = DBPendingUpload(**upload_data)
        self.session.add(upload)
        await self.session.commit()
        await self.session.refresh(upload)
        return upload
    
    async def get(self, upload_id: str) -> Optional[DBPendingUpload]:
        """Get pending upload by ID."""
        result = await self.session.execute(
            select(DBPendingUpload).where(DBPendingUpload.upload_id == upload_id)
        )
        return result.scalar_one_or_none()
    
    async def delete(self, upload_id: str) -> bool:
        """Delete pending upload."""
        upload = await self.get(upload_id)
        if upload:
            await self.session.delete(upload)
            await self.session.commit()
            return True
        return False

