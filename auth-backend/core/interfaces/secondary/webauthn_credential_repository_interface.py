"""
WebAuthn Credential Repository Interface
Port for WebAuthn credential persistence
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from core.domain.auth.webauthn_credential import WebAuthnCredential


class WebAuthnCredentialRepositoryInterface(ABC):
    """Interface for WebAuthn credential repository operations"""
    
    @abstractmethod
    async def save(self, credential: WebAuthnCredential) -> WebAuthnCredential:
        """Save WebAuthn credential"""
        pass
    
    @abstractmethod
    async def find_by_id(self, credential_id: str) -> Optional[WebAuthnCredential]:
        """Find credential by ID"""
        pass
    
    @abstractmethod
    async def find_by_credential_id(self, credential_id: str) -> Optional[WebAuthnCredential]:
        """Find credential by WebAuthn credential ID"""
        pass
    
    @abstractmethod
    async def find_by_user(self, user_id: str, client_id: str) -> List[WebAuthnCredential]:
        """Find all credentials for a user"""
        pass
    
    @abstractmethod
    async def find_active_by_user(self, user_id: str, client_id: str) -> List[WebAuthnCredential]:
        """Find active credentials for a user"""
        pass

