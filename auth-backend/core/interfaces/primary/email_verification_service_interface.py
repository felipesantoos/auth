"""
Email Verification Service Interface
Port for email verification operations
"""
from abc import ABC, abstractmethod


class IEmailVerificationService(ABC):
    """Interface for email verification service operations"""
    
    @abstractmethod
    async def send_verification_email(self, user_id: str, client_id: str) -> bool:
        """Send verification email"""
        pass
    
    @abstractmethod
    async def verify_email(self, user_id: str, token: str, client_id: str) -> bool:
        """Verify email with token"""
        pass
    
    @abstractmethod
    async def resend_verification_email(self, user_id: str, client_id: str) -> bool:
        """Resend verification email"""
        pass
    
    @abstractmethod
    async def check_email_verified(self, user_id: str, client_id: str) -> bool:
        """Check if email is verified"""
        pass

