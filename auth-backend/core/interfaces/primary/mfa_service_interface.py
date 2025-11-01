"""
MFA Service Interface
Port for MFA service operations
"""
from abc import ABC, abstractmethod
from typing import List, Tuple


class IMFAService(ABC):
    """Interface for MFA service operations"""
    
    @abstractmethod
    async def setup_mfa(self, user_id: str, client_id: str) -> Tuple[str, str, List[str]]:
        """Setup MFA - returns (secret, qr_code, backup_codes)"""
        pass
    
    @abstractmethod
    async def enable_mfa(
        self, user_id: str, client_id: str, secret: str, totp_code: str, backup_codes: List[str]
    ) -> bool:
        """Enable MFA after verification"""
        pass
    
    @abstractmethod
    async def disable_mfa(self, user_id: str, client_id: str) -> bool:
        """Disable MFA"""
        pass
    
    @abstractmethod
    def verify_totp(self, secret: str, totp_code: str) -> bool:
        """Verify TOTP code"""
        pass
    
    @abstractmethod
    async def verify_backup_code_for_user(
        self, user_id: str, client_id: str, backup_code: str
    ) -> bool:
        """Verify and consume backup code"""
        pass
    
    @abstractmethod
    async def regenerate_backup_codes(self, user_id: str, client_id: str) -> List[str]:
        """Regenerate backup codes"""
        pass
    
    @abstractmethod
    async def get_remaining_backup_codes_count(self, user_id: str, client_id: str) -> int:
        """Get count of remaining backup codes"""
        pass

