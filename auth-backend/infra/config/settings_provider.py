"""
Settings Provider Implementation
Provides access to application settings via interface
"""
from core.interfaces.secondary.settings_provider_interface import ISettingsProvider
from config.settings import settings


class SettingsProvider(ISettingsProvider):
    """
    Implementation of SettingsProviderInterface.
    
    Wraps the global settings object to provide dependency injection.
    """
    
    def get_jwt_secret(self) -> str:
        """Get JWT secret key"""
        return settings.jwt_secret
    
    def get_jwt_algorithm(self) -> str:
        """Get JWT algorithm"""
        return settings.jwt_algorithm
    
    def get_jwt_issuer(self) -> str:
        """Get JWT issuer"""
        return settings.jwt_issuer
    
    def get_jwt_audience(self) -> str:
        """Get JWT audience"""
        return settings.jwt_audience
    
    def get_access_token_expire_minutes(self) -> int:
        """Get access token expiration in minutes"""
        return settings.access_token_expire_minutes
    
    def get_refresh_token_expire_days(self) -> int:
        """Get refresh token expiration in days"""
        return settings.refresh_token_expire_days

