"""
WebAuthn Credential Repository Implementation
Handles persistence of WebAuthn credentials
"""
import logging
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.auth.webauthn_credential import WebAuthnCredential
from infra.database.models.webauthn_credential import DBWebAuthnCredential
from infra.database.mappers.webauthn_credential_mapper import WebAuthnCredentialMapper

logger = logging.getLogger(__name__)


class WebAuthnCredentialRepository:
    """Repository for WebAuthn credential operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.mapper = WebAuthnCredentialMapper
    
    async def save(self, credential: WebAuthnCredential) -> WebAuthnCredential:
        """Save WebAuthn credential"""
        try:
            db_cred = self.mapper.to_database(credential)
            self.session.add(db_cred)
            await self.session.flush()
            await self.session.refresh(db_cred)
            
            return self.mapper.to_domain(db_cred)
        except Exception as e:
            logger.error(f"Error saving WebAuthn credential: {e}", exc_info=True)
            await self.session.rollback()
            raise
    
    async def find_by_id(self, credential_id: str) -> Optional[WebAuthnCredential]:
        """Find credential by ID"""
        try:
            query = select(DBWebAuthnCredential).where(
                DBWebAuthnCredential.id == credential_id
            )
            result = await self.session.execute(query)
            db_cred = result.scalar_one_or_none()
            
            if db_cred:
                return self.mapper.to_domain(db_cred)
            return None
        except Exception as e:
            logger.error(f"Error finding WebAuthn credential: {e}", exc_info=True)
            return None
    
    async def find_by_credential_id(self, credential_id: str) -> Optional[WebAuthnCredential]:
        """Find credential by WebAuthn credential ID"""
        try:
            query = select(DBWebAuthnCredential).where(
                DBWebAuthnCredential.credential_id == credential_id
            )
            result = await self.session.execute(query)
            db_cred = result.scalar_one_or_none()
            
            if db_cred:
                return self.mapper.to_domain(db_cred)
            return None
        except Exception as e:
            logger.error(f"Error finding WebAuthn credential by credential_id: {e}", exc_info=True)
            return None
    
    async def find_by_user(self, user_id: str, client_id: str) -> List[WebAuthnCredential]:
        """Find all credentials for a user"""
        try:
            query = select(DBWebAuthnCredential).where(
                and_(
                    DBWebAuthnCredential.user_id == user_id,
                    DBWebAuthnCredential.client_id == client_id
                )
            )
            
            result = await self.session.execute(query)
            db_creds = result.scalars().all()
            
            return [self.mapper.to_domain(db_cred) for db_cred in db_creds]
        except Exception as e:
            logger.error(f"Error finding WebAuthn credentials: {e}", exc_info=True)
            return []
    
    async def find_active_by_user(self, user_id: str, client_id: str) -> List[WebAuthnCredential]:
        """Find active (non-revoked) credentials for a user"""
        try:
            query = select(DBWebAuthnCredential).where(
                and_(
                    DBWebAuthnCredential.user_id == user_id,
                    DBWebAuthnCredential.client_id == client_id,
                    DBWebAuthnCredential.revoked_at.is_(None)
                )
            )
            
            result = await self.session.execute(query)
            db_creds = result.scalars().all()
            
            return [self.mapper.to_domain(db_cred) for db_cred in db_creds]
        except Exception as e:
            logger.error(f"Error finding active WebAuthn credentials: {e}", exc_info=True)
            return []

