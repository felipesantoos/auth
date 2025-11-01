"""
Login Notification Service Interface
Port for login notification operations
"""
from abc import ABC, abstractmethod
from core.domain.auth.app_user import AppUser
from core.domain.auth.user_session import UserSession
from core.services.audit.audit_service import AuditService


class ILoginNotificationService(ABC):
    """Interface for login notification operations"""
    
    @abstractmethod
    async def should_send_notification(
        self,
        user_id: str,
        client_id: str,
        current_ip: str,
        current_user_agent: str,
        audit_service: AuditService
    ) -> bool:
        """Check if login notification should be sent"""
        pass
    
    @abstractmethod
    async def send_new_login_notification(
        self,
        user: AppUser,
        session: UserSession
    ) -> None:
        """Send new login notification email"""
        pass

