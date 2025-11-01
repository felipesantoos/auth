"""File Repository - CRUD operations for files"""
from typing import List, Optional
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from infra.database.models.file import DBFile
from datetime import datetime


class FileRepository:
    """Repository for file operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, file_data: dict) -> DBFile:
        """Create new file record."""
        db_file = DBFile(**file_data)
        self.session.add(db_file)
        await self.session.commit()
        await self.session.refresh(db_file)
        return db_file
    
    async def get(self, file_id: str) -> Optional[DBFile]:
        """Get file by ID."""
        result = await self.session.execute(
            select(DBFile).where(DBFile.id == file_id)
        )
        return result.scalar_one_or_none()
    
    async def delete(self, file_id: str) -> bool:
        """Delete file."""
        file = await self.get(file_id)
        if file:
            await self.session.delete(file)
            await self.session.commit()
            return True
        return False
    
    async def list_by_user(
        self,
        user_id: str,
        file_type: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> tuple[List[DBFile], int]:
        """List files by user with pagination."""
        query = select(DBFile).where(DBFile.user_id == user_id)
        
        if file_type:
            if file_type == 'image':
                query = query.where(DBFile.mime_type.like('image/%'))
            elif file_type == 'video':
                query = query.where(DBFile.mime_type.like('video/%'))
            elif file_type == 'audio':
                query = query.where(DBFile.mime_type.like('audio/%'))
        
        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query)
        
        # Paginate
        query = query.offset((page - 1) * per_page).limit(per_page)
        result = await self.session.execute(query)
        files = result.scalars().all()
        
        return files, total
    
    async def find_by_checksum(self, checksum: str, user_id: str) -> Optional[DBFile]:
        """Find file by checksum (detect duplicates)."""
        result = await self.session.execute(
            select(DBFile).where(
                and_(DBFile.checksum == checksum, DBFile.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()

