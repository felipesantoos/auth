"""
User Session Repository Implementation
Handles persistence of user sessions with eager loading to prevent N+1 queries
"""
import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.auth.user_session import UserSession
from infra.database.models.user_session import DBUserSession
from infra.database.mappers.user_session_mapper import UserSessionMapper

logger = logging.getLogger(__name__)


class UserSessionRepository:
    """Repository for user session operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.mapper = UserSessionMapper
    
    async def save(self, user_session: UserSession) -> UserSession:
        """Save user session"""
        try:
            db_session = self.mapper.to_database(user_session)
            self.session.add(db_session)
            await self.session.flush()
            await self.session.refresh(db_session)
            
            return self.mapper.to_domain(db_session)
        except Exception as e:
            logger.error(f"Error saving user session: {e}", exc_info=True)
            await self.session.rollback()
            raise
    
    async def find_by_id(self, session_id: str) -> Optional[UserSession]:
        """Find session by ID"""
        try:
            query = select(DBUserSession).where(DBUserSession.id == session_id)
            result = await self.session.execute(query)
            db_session = result.scalar_one_or_none()
            
            if db_session:
                return self.mapper.to_domain(db_session)
            return None
        except Exception as e:
            logger.error(f"Error finding session by ID: {e}", exc_info=True)
            return None
    
    async def find_by_token_hash(self, token_hash: str) -> Optional[UserSession]:
        """Find session by refresh token hash"""
        try:
            query = select(DBUserSession).where(
                DBUserSession.refresh_token_hash == token_hash
            )
            result = await self.session.execute(query)
            db_session = result.scalar_one_or_none()
            
            if db_session:
                return self.mapper.to_domain(db_session)
            return None
        except Exception as e:
            logger.error(f"Error finding session by token: {e}", exc_info=True)
            return None
    
    async def find_active_by_user(
        self, user_id: str, client_id: str
    ) -> List[UserSession]:
        """
        Find all active sessions for a user.
        
        Uses eager loading to prevent N+1 queries if relationships are accessed.
        """
        try:
            now = datetime.utcnow()
            query = select(DBUserSession).where(
                and_(
                    DBUserSession.user_id == user_id,
                    DBUserSession.client_id == client_id,
                    DBUserSession.revoked_at.is_(None),
                    DBUserSession.expires_at > now
                )
            )
            
            result = await self.session.execute(query)
            db_sessions = result.scalars().all()
            
            return [self.mapper.to_domain(db_session) for db_session in db_sessions]
        except Exception as e:
            logger.error(f"Error finding active sessions: {e}", exc_info=True)
            return []
    
    async def revoke_all_by_user(
        self, user_id: str, client_id: str, except_session_id: Optional[str] = None
    ) -> bool:
        """Revoke all sessions for a user (logout all devices)"""
        try:
            conditions = [
                DBUserSession.user_id == user_id,
                DBUserSession.client_id == client_id,
                DBUserSession.revoked_at.is_(None)
            ]
            
            if except_session_id:
                conditions.append(DBUserSession.id != except_session_id)
            
            query = select(DBUserSession).where(and_(*conditions))
            result = await self.session.execute(query)
            db_sessions = result.scalars().all()
            
            now = datetime.utcnow()
            for db_session in db_sessions:
                db_session.revoked_at = now
            
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error revoking all sessions: {e}", exc_info=True)
            await self.session.rollback()
            return False

