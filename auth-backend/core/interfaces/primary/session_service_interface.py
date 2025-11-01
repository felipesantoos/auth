"""
Session Service Interface
Port for session service operations
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from core.domain.auth.user_session import UserSession


class ISessionService(ABC):
    """Interface for session service operations"""
    
    @abstractmethod
    async def create_session(
        self,
        user_id: str,
        client_id: str,
        refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        location: Optional[str] = None
    ) -> UserSession:
        """Create a new session"""
        pass
    
    @abstractmethod
    async def get_active_sessions(
        self, user_id: str, client_id: str
    ) -> List[Dict[str, Any]]:
        """Get active sessions for user"""
        pass
    
    @abstractmethod
    async def revoke_session(
        self, session_id: str, user_id: str, client_id: str
    ) -> bool:
        """Revoke specific session"""
        pass
    
    @abstractmethod
    async def revoke_all_sessions(
        self, user_id: str, client_id: str, except_current: Optional[str] = None
    ) -> int:
        """Revoke all sessions"""
        pass
    
    @abstractmethod
    async def update_session_activity(
        self, session_id: str, ip_address: Optional[str] = None
    ) -> bool:
        """Update session activity"""
        pass

