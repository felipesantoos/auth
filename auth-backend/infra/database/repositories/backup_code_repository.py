"""
Backup Code Repository Implementation
Handles persistence of MFA backup codes
"""
import logging
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.auth.backup_code import BackupCode
from infra.database.models.backup_code import DBBackupCode
from infra.database.mappers.backup_code_mapper import BackupCodeMapper

logger = logging.getLogger(__name__)


class BackupCodeRepository:
    """Repository for backup code operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.mapper = BackupCodeMapper
    
    async def save(self, backup_code: BackupCode) -> BackupCode:
        """Save backup code"""
        try:
            db_code = self.mapper.to_database(backup_code)
            self.session.add(db_code)
            await self.session.flush()
            await self.session.refresh(db_code)
            
            return self.mapper.to_domain(db_code)
        except Exception as e:
            logger.error(f"Error saving backup code: {e}", exc_info=True)
            await self.session.rollback()
            raise
    
    async def find_by_user(self, user_id: str, client_id: str) -> List[BackupCode]:
        """Find all backup codes for a user"""
        try:
            query = select(DBBackupCode).where(
                and_(
                    DBBackupCode.user_id == user_id,
                    DBBackupCode.client_id == client_id
                )
            )
            
            result = await self.session.execute(query)
            db_codes = result.scalars().all()
            
            return [self.mapper.to_domain(db_code) for db_code in db_codes]
        except Exception as e:
            logger.error(f"Error finding backup codes: {e}", exc_info=True)
            return []
    
    async def find_unused_by_user(self, user_id: str, client_id: str) -> List[BackupCode]:
        """Find unused backup codes for a user"""
        try:
            query = select(DBBackupCode).where(
                and_(
                    DBBackupCode.user_id == user_id,
                    DBBackupCode.client_id == client_id,
                    DBBackupCode.used == False
                )
            )
            
            result = await self.session.execute(query)
            db_codes = result.scalars().all()
            
            return [self.mapper.to_domain(db_code) for db_code in db_codes]
        except Exception as e:
            logger.error(f"Error finding unused backup codes: {e}", exc_info=True)
            return []
    
    async def delete_by_user(self, user_id: str, client_id: str) -> bool:
        """Delete all backup codes for a user (when regenerating)"""
        try:
            query = select(DBBackupCode).where(
                and_(
                    DBBackupCode.user_id == user_id,
                    DBBackupCode.client_id == client_id
                )
            )
            
            result = await self.session.execute(query)
            db_codes = result.scalars().all()
            
            for db_code in db_codes:
                await self.session.delete(db_code)
            
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error deleting backup codes: {e}", exc_info=True)
            await self.session.rollback()
            return False

