"""
Settings Provider Interface
Defines contract for accessing application settings (Dependency Inversion Principle)
"""
from abc import ABC, abstractmethod


class SettingsProviderInterface(ABC):
    """
    Settings provider interface - defines contract for accessing settings.
    
    Following:
    - Dependency Inversion Principle (depend on abstraction)
    - Interface Segregation Principle (focused interface)
    """
    
    @abstractmethod
    def get_jwt_secret(self) -> str:
        """Get JWT secret key"""
        pass
    
    @abstractmethod
    def get_jwt_algorithm(self) -> str:
        """Get JWT algorithm"""
        pass
    
    @abstractmethod
    def get_jwt_issuer(self) -> str:
        """Get JWT issuer"""
        pass
    
    @abstractmethod
    def get_jwt_audience(self) -> str:
        """Get JWT audience"""
        pass
    
    @abstractmethod
    def get_access_token_expire_minutes(self) -> int:
        """Get access token expiration in minutes"""
        pass
    
    @abstractmethod
    def get_refresh_token_expire_days(self) -> int:
        """Get refresh token expiration in days"""
        pass

