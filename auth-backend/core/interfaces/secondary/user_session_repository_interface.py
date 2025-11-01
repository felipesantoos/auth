"""
User Session Repository Interface
Port for session persistence
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from core.domain.auth.user_session import UserSession


class UserSessionRepositoryInterface(ABC):
    """Interface for user session repository operations"""
    
    @abstractmethod
    async def save(self, user_session: UserSession) -> UserSession:
        """Save user session"""
        pass
    
    @abstractmethod
    async def find_by_id(self, session_id: str) -> Optional[UserSession]:
        """Find session by ID"""
        pass
    
    @abstractmethod
    async def find_by_token_hash(self, token_hash: str) -> Optional[UserSession]:
        """Find session by refresh token hash"""
        pass
    
    @abstractmethod
    async def find_active_by_user(self, user_id: str, client_id: str) -> List[UserSession]:
        """Find all active sessions for a user"""
        pass
    
    @abstractmethod
    async def revoke_all_by_user(
        self, user_id: str, client_id: str, except_session_id: Optional[str] = None
    ) -> bool:
        """Revoke all sessions for a user"""
        pass

