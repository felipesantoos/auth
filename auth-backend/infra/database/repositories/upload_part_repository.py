"""Upload Part Repository"""
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from infra.database.models.upload_part import DBUploadPart


class UploadPartRepository:
    """Repository for upload part operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, part_data: dict) -> DBUploadPart:
        """Create upload part record."""
        part = DBUploadPart(**part_data)
        self.session.add(part)
        await self.session.commit()
        await self.session.refresh(part)
        return part
    
    async def list_by_upload(self, upload_id: str) -> List[DBUploadPart]:
        """List all parts for a multipart upload."""
        result = await self.session.execute(
            select(DBUploadPart)
            .where(DBUploadPart.upload_id == upload_id)
            .order_by(DBUploadPart.part_number)
        )
        return result.scalars().all()

