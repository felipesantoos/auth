"""
Account Lockout Service Interface
Primary port for account lockout and brute-force protection
"""
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from datetime import datetime


class IAccountLockoutService(ABC):
    """
    Interface for account lockout protection service.
    
    Provides methods to:
    - Check if account or IP is locked out
    - Record failed login attempts
    - Determine if account should be locked
    """
    
    @abstractmethod
    async def check_lockout(
        self,
        email: str,
        ip_address: str,
        client_id: str
    ) -> Tuple[bool, Optional[datetime]]:
        """
        Check if account or IP is locked out.
        
        Args:
            email: User email
            ip_address: Client IP address
            client_id: Client ID
            
        Returns:
            Tuple of (is_locked, unlock_time)
            - is_locked: True if locked
            - unlock_time: When the lockout will expire (None if not locked)
        """
        pass
    
    @abstractmethod
    async def record_failed_attempt(
        self,
        email: str,
        ip_address: str,
        user_agent: str,
        client_id: str
    ) -> bool:
        """
        Record failed login attempt and potentially lock account.
        
        Args:
            email: User email
            ip_address: Client IP
            user_agent: User agent string
            client_id: Client ID
            
        Returns:
            True if account/IP is now locked
        """
        pass
    
    @abstractmethod
    async def should_lock_account(
        self,
        user_id: str,
        email: str,
        ip_address: str,
        client_id: str
    ) -> bool:
        """
        Check if account should be locked based on failed attempts.
        
        Args:
            user_id: User ID
            email: User email
            ip_address: Client IP
            client_id: Client ID
            
        Returns:
            True if account should be locked
        """
        pass

