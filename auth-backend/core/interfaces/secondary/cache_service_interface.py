"""
Cache Service Interface
Defines contract for caching operations (Dependency Inversion Principle)
"""
from abc import ABC, abstractmethod
from typing import Optional, Any


class CacheServiceInterface(ABC):
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

