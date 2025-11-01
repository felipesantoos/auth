"""
Backup Code Repository Interface
Port for backup code persistence
"""
from abc import ABC, abstractmethod
from typing import List
from core.domain.auth.backup_code import BackupCode


class IBackupCodeRepository(ABC):
    """Interface for backup code repository operations"""
    
    @abstractmethod
    async def save(self, backup_code: BackupCode) -> BackupCode:
        """Save backup code"""
        pass
    
    @abstractmethod
    async def find_by_user(self, user_id: str, client_id: str) -> List[BackupCode]:
        """Find all backup codes for a user"""
        pass
    
    @abstractmethod
    async def find_unused_by_user(self, user_id: str, client_id: str) -> List[BackupCode]:
        """Find unused backup codes for a user"""
        pass
    
    @abstractmethod
    async def delete_by_user(self, user_id: str, client_id: str) -> bool:
        """Delete all backup codes for a user"""
        pass

