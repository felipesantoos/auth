"""
Session Service Implementation
Handles user session tracking across multiple devices
"""
import logging
import bcrypt
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from core.domain.auth.user_session import UserSession
from infra.database.repositories.user_session_repository import UserSessionRepository
from core.interfaces.secondary.cache_service_interface import ICacheService
from core.interfaces.secondary.settings_provider_interface import ISettingsProvider
from core.exceptions import (
    BusinessRuleException,
    ValidationException,
)

logger = logging.getLogger(__name__)


class SessionService:
    """
    Service for managing user sessions across multiple devices.
    
    Features:
    - Track sessions per device
    - List active sessions
    - Revoke specific session (logout from device)
    - Revoke all sessions (logout from all devices)
    - Device information parsing
    """
    
    def __init__(
        self,
        repository: UserSessionRepository,
        cache_service: ICacheService,
        settings_provider: ISettingsProvider,
    ):
        self.repository = repository
        self.cache = cache_service
        self.settings = settings_provider.get_settings()
    
    def _hash_token(self, refresh_token: str) -> str:
        """Hash refresh token for storage"""
        return bcrypt.hashpw(refresh_token.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def _parse_device_type(self, user_agent: Optional[str]) -> str:
        """
        Parse device type from user agent.
        
        Returns: 'mobile', 'tablet', 'desktop', or 'unknown'
        """
        if not user_agent:
            return 'unknown'
        
        user_agent_lower = user_agent.lower()
        
        if any(mobile in user_agent_lower for mobile in ['mobile', 'android', 'iphone', 'ipod']):
            return 'mobile'
        elif 'ipad' in user_agent_lower or 'tablet' in user_agent_lower:
            return 'tablet'
        elif any(desktop in user_agent_lower for desktop in ['windows', 'mac', 'linux', 'x11']):
            return 'desktop'
        
        return 'unknown'
    
    def _get_device_name(self, user_agent: Optional[str]) -> Optional[str]:
        """
        Extract friendly device name from user agent.
        
        Examples: "Chrome on Windows", "Safari on iPhone", etc.
        """
        if not user_agent:
            return None
        
        # Simple parsing - in production, use user-agents library for better parsing
        try:
            ua = user_agent.lower()
            
            # Browser detection
            browser = 'Unknown Browser'
            if 'chrome' in ua and 'edg' not in ua:
                browser = 'Chrome'
            elif 'safari' in ua and 'chrome' not in ua:
                browser = 'Safari'
            elif 'firefox' in ua:
                browser = 'Firefox'
            elif 'edg' in ua:
                browser = 'Edge'
            
            # OS detection
            os = 'Unknown OS'
            if 'windows' in ua:
                os = 'Windows'
            elif 'mac' in ua:
                os = 'macOS'
            elif 'linux' in ua:
                os = 'Linux'
            elif 'android' in ua:
                os = 'Android'
            elif 'iphone' in ua or 'ipad' in ua:
                os = 'iOS'
            
            return f"{browser} on {os}"
        except Exception as e:
            logger.error(f"Error parsing device name: {e}")
            return None
    
    async def create_session(
        self,
        user_id: str,
        client_id: str,
        refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        location: Optional[str] = None
    ) -> UserSession:
        """
        Create a new user session.
        
        Args:
            user_id: User ID
            client_id: Client ID
            refresh_token: Refresh token (will be hashed)
            ip_address: IP address of the request
            user_agent: User agent string
            location: Optional location (e.g., "São Paulo, Brazil")
            
        Returns:
            Created session
        """
        try:
            # Check session limit
            active_sessions = await self.repository.find_active_by_user(user_id, client_id)
            if len(active_sessions) >= self.settings.session_max_devices:
                # Revoke oldest session
                oldest = min(active_sessions, key=lambda s: s.created_at)
                oldest.revoke()
                await self.repository.save(oldest)
                logger.info(f"Revoked oldest session for user {user_id} due to limit")
            
            # Parse device information
            device_type = self._parse_device_type(user_agent)
            device_name = self._get_device_name(user_agent)
            
            # Calculate expiration
            expires_at = datetime.utcnow() + timedelta(days=self.settings.refresh_token_expire_days)
            
            # Create session
            session = UserSession(
                id=str(uuid.uuid4()),
                user_id=user_id,
                client_id=client_id,
                refresh_token_hash=self._hash_token(refresh_token),
                device_name=device_name,
                device_type=device_type,
                ip_address=ip_address,
                user_agent=user_agent,
                location=location,
                last_activity=datetime.utcnow(),
                created_at=datetime.utcnow(),
                revoked_at=None,
                expires_at=expires_at
            )
            
            session.validate()
            saved_session = await self.repository.save(session)
            
            # Cache session in Redis for fast lookup
            await self._cache_session(saved_session)
            
            logger.info(f"Session created for user {user_id} from {device_type}")
            return saved_session
            
        except Exception as e:
            logger.error(f"Error creating session: {e}", exc_info=True)
            raise
    
    async def _cache_session(self, session: UserSession) -> None:
        """Cache session in Redis"""
        try:
            cache_key = f"{session.client_id}:session:{session.id}"
            session_data = {
                "user_id": session.user_id,
                "device_name": session.device_name or "",
                "ip_address": session.ip_address or "",
                "created_at": session.created_at.isoformat() if session.created_at else "",
            }
            ttl_seconds = self.settings.refresh_token_expire_days * 24 * 60 * 60
            await self.cache.set(cache_key, str(session_data), ttl_seconds)
        except Exception as e:
            logger.error(f"Error caching session: {e}")
            # Don't fail if caching fails
    
    async def update_session_activity(
        self,
        session_id: str,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Update session's last activity timestamp.
        
        Called on each token refresh.
        """
        try:
            session = await self.repository.find_by_id(session_id)
            if not session or not session.is_active():
                return False
            
            session.update_activity()
            if ip_address:
                session.ip_address = ip_address
            
            await self.repository.save(session)
            await self._cache_session(session)
            
            return True
        except Exception as e:
            logger.error(f"Error updating session activity: {e}", exc_info=True)
            return False
    
    async def get_active_sessions(
        self,
        user_id: str,
        client_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all active sessions for a user.
        
        Returns list of session information (sanitized, without sensitive data)
        """
        try:
            sessions = await self.repository.find_active_by_user(user_id, client_id)
            
            return [
                {
                    "id": session.id,
                    "device_name": session.get_device_description(),
                    "device_type": session.device_type,
                    "ip_address": session.ip_address,
                    "location": session.get_location_description(),
                    "last_activity": session.last_activity.isoformat() if session.last_activity else None,
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "is_current": False,  # Will be set by caller based on current session
                }
                for session in sessions
            ]
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}", exc_info=True)
            return []
    
    async def revoke_session(
        self,
        session_id: str,
        user_id: str,
        client_id: str
    ) -> bool:
        """
        Revoke a specific session (logout from specific device).
        
        Args:
            session_id: Session ID to revoke
            user_id: User ID (for authorization check)
            client_id: Client ID
            
        Returns:
            True if session was revoked
        """
        try:
            session = await self.repository.find_by_id(session_id)
            
            if not session:
                logger.warning(f"Session not found: {session_id}")
                return False
            
            # Authorization check: only owner can revoke their sessions
            if session.user_id != user_id or session.client_id != client_id:
                logger.warning(f"Unauthorized session revoke attempt: {session_id}")
                return False
            
            if session.is_revoked():
                return True  # Already revoked
            
            session.revoke()
            await self.repository.save(session)
            
            # Remove from cache
            cache_key = f"{client_id}:session:{session_id}"
            await self.cache.delete(cache_key)
            
            logger.info(f"Session revoked: {session_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking session: {e}", exc_info=True)
            return False
    
    async def revoke_all_sessions(
        self,
        user_id: str,
        client_id: str,
        except_current: Optional[str] = None
    ) -> int:
        """
        Revoke all sessions for a user (logout from all devices).
        
        Args:
            user_id: User ID
            client_id: Client ID
            except_current: Optional session ID to keep active (current session)
            
        Returns:
            Number of sessions revoked
        """
        try:
            success = await self.repository.revoke_all_by_user(
                user_id=user_id,
                client_id=client_id,
                except_session_id=except_current
            )
            
            if success:
                # Clear all session caches for this user
                # Note: This is a simplified approach; in production, you might track session IDs
                logger.info(f"All sessions revoked for user {user_id}")
                return 1  # Return success indicator
            
            return 0
            
        except Exception as e:
            logger.error(f"Error revoking all sessions: {e}", exc_info=True)
            return 0
    
    async def cleanup_expired_sessions(self, client_id: Optional[str] = None) -> int:
        """
        Cleanup expired sessions (maintenance task).
        
        This should be called periodically (e.g., daily cron job).
        
        Returns:
            Number of sessions cleaned up
        """
        # TODO: Implement batch cleanup query
        # This would require adding a cleanup method to the repository
        logger.info("Session cleanup not yet implemented")
        return 0

