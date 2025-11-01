"""Multipart Upload Repository"""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from infra.database.models.multipart_upload import DBMultipartUpload


class MultipartUploadRepository:
    """Repository for multipart upload operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, upload_data: dict) -> DBMultipartUpload:
        """Create multipart upload record."""
        upload = DBMultipartUpload(**upload_data)
        self.session.add(upload)
        await self.session.commit()
        await self.session.refresh(upload)
        return upload
    
    async def get(self, upload_id: str) -> Optional[DBMultipartUpload]:
        """Get multipart upload by ID."""
        result = await self.session.execute(
            select(DBMultipartUpload).where(DBMultipartUpload.upload_id == upload_id)
        )
        return result.scalar_one_or_none()
    
    async def save(self, upload: DBMultipartUpload) -> DBMultipartUpload:
        """Save multipart upload changes."""
        await self.session.commit()
        await self.session.refresh(upload)
        return upload

