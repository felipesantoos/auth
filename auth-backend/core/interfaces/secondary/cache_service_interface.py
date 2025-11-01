"""
Cache Service Interface
Defines contract for caching operations (Dependency Inversion Principle)
"""
from abc import ABC, abstractmethod
from typing import Optional, Any


class ICacheService(ABC):
    """
    Cache service interface - defines caching contract.
    
    Following:
    - Dependency Inversion Principle (depend on abstraction)
    - Interface Segregation Principle (focused interface)
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.
        
        Args:
            pattern: Pattern to match (e.g., "prefix:*")
            
        Returns:
            Number of keys deleted
        """
        pass
    
    @abstractmethod
    async def clear_all(self) -> bool:
        """
        Clear all cache (use with caution!).
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def store_challenge(self, key: str, challenge: str, ttl: int = 300) -> bool:
        """
        Store a challenge (for WebAuthn, OIDC, etc.) with TTL.
        
        Args:
            key: Challenge key (e.g., "webauthn:reg:{user_id}")
            challenge: Challenge value (base64 string)
            ttl: Time to live in seconds (default: 300 = 5 minutes)
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_challenge(self, key: str) -> Optional[str]:
        """
        Get a challenge from cache.
        
        Args:
            key: Challenge key
            
        Returns:
            Challenge value if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def verify_and_delete_challenge(self, key: str, expected_challenge: str) -> bool:
        """
        Verify a challenge matches and delete it (single-use).
        
        Args:
            key: Challenge key
            expected_challenge: Expected challenge value
            
        Returns:
            True if challenge matches and was deleted, False otherwise
        """
        pass
    
    @abstractmethod
    async def store_state(self, key: str, state: dict, ttl: int = 600) -> bool:
        """
        Store state data (for OIDC, SAML, etc.) with TTL.
        
        Args:
            key: State key (e.g., "oidc:state:{state_id}")
            state: State data (will be JSON serialized)
            ttl: Time to live in seconds (default: 600 = 10 minutes)
            
        Returns:
            True if successful, False otherwise
        """
        pass

