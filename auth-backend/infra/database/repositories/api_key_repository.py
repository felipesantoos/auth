"""
API Key Repository Implementation
Handles persistence of API keys
"""
import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.auth.api_key import ApiKey
from infra.database.models.api_key import DBApiKey
from infra.database.mappers.api_key_mapper import ApiKeyMapper

logger = logging.getLogger(__name__)


class ApiKeyRepository:
    """Repository for API key operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.mapper = ApiKeyMapper
    
    async def save(self, api_key: ApiKey) -> ApiKey:
        """Save API key"""
        try:
            db_key = self.mapper.to_database(api_key)
            self.session.add(db_key)
            await self.session.flush()
            await self.session.refresh(db_key)
            
            return self.mapper.to_domain(db_key)
        except Exception as e:
            logger.error(f"Error saving API key: {e}", exc_info=True)
            await self.session.rollback()
            raise
    
    async def find_by_id(self, key_id: str) -> Optional[ApiKey]:
        """Find API key by ID"""
        try:
            query = select(DBApiKey).where(DBApiKey.id == key_id)
            result = await self.session.execute(query)
            db_key = result.scalar_one_or_none()
            
            if db_key:
                return self.mapper.to_domain(db_key)
            return None
        except Exception as e:
            logger.error(f"Error finding API key by ID: {e}", exc_info=True)
            return None
    
    async def find_by_key_hash(self, key_hash: str) -> Optional[ApiKey]:
        """Find API key by hash"""
        try:
            query = select(DBApiKey).where(DBApiKey.key_hash == key_hash)
            result = await self.session.execute(query)
            db_key = result.scalar_one_or_none()
            
            if db_key:
                return self.mapper.to_domain(db_key)
            return None
        except Exception as e:
            logger.error(f"Error finding API key by hash: {e}", exc_info=True)
            return None
    
    async def find_by_user(self, user_id: str, client_id: str) -> List[ApiKey]:
        """Find all API keys for a user"""
        try:
            query = select(DBApiKey).where(
                and_(
                    DBApiKey.user_id == user_id,
                    DBApiKey.client_id == client_id
                )
            )
            
            result = await self.session.execute(query)
            db_keys = result.scalars().all()
            
            return [self.mapper.to_domain(db_key) for db_key in db_keys]
        except Exception as e:
            logger.error(f"Error finding API keys: {e}", exc_info=True)
            return []
    
    async def find_active_by_user(self, user_id: str, client_id: str) -> List[ApiKey]:
        """Find active (non-revoked, non-expired) API keys for a user"""
        try:
            now = datetime.utcnow()
            query = select(DBApiKey).where(
                and_(
                    DBApiKey.user_id == user_id,
                    DBApiKey.client_id == client_id,
                    DBApiKey.revoked_at.is_(None),
                    or_(
                        DBApiKey.expires_at.is_(None),
                        DBApiKey.expires_at > now
                    )
                )
            )
            
            result = await self.session.execute(query)
            db_keys = result.scalars().all()
            
            return [self.mapper.to_domain(db_key) for db_key in db_keys]
        except Exception as e:
            logger.error(f"Error finding active API keys: {e}", exc_info=True)
            return []
    
    async def count_by_user(self, user_id: str, client_id: str) -> int:
        """Count API keys for a user"""
        try:
            query = select(DBApiKey).where(
                and_(
                    DBApiKey.user_id == user_id,
                    DBApiKey.client_id == client_id,
                    DBApiKey.revoked_at.is_(None)
                )
            )
            
            result = await self.session.execute(query)
            keys = result.scalars().all()
            
            return len(keys)
        except Exception as e:
            logger.error(f"Error counting API keys: {e}", exc_info=True)
            return 0

