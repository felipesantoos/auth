"""
Dependency Injection Container
Factory functions for service and repository dependencies
"""
import logging
from infra.database.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

# Client
from infra.database.repositories.client_repository import ClientRepository
from core.services.client.client_service import ClientService
from core.interfaces.primary.client_service_interface import ClientServiceInterface

# Auth
from infra.database.repositories.app_user_repository import AppUserRepository
from core.services.auth.auth_service import AuthService
from core.interfaces.primary.auth_service_interface import IAuthService
from core.interfaces.primary.password_reset_service_interface import IPasswordResetService
from core.interfaces.primary.oauth_service_interface import IOAuthService

# Email
from infra.email.email_service import EmailService

# Cache
from infra.redis.cache_service import CacheService

# Settings
from infra.config.settings_provider import SettingsProvider

logger = logging.getLogger(__name__)


def get_client_repository(
    session: AsyncSession = Depends(get_db_session)
) -> ClientRepository:
    """Factory for Client repository"""
    return ClientRepository(session)


async def get_client_service(
    session: AsyncSession = Depends(get_db_session)
) -> ClientServiceInterface:
    """
    Factory for Client service.
    
    Creates repository with session and injects into service.
    """
    repository = ClientRepository(session)
    return ClientService(repository)


def get_app_user_repository(
    session: AsyncSession = Depends(get_db_session)
) -> AppUserRepository:
    """Factory for AppUser repository"""
    return AppUserRepository(session)


async def get_auth_service(
    session: AsyncSession = Depends(get_db_session)
) -> IAuthService:
    """
    Factory for Auth service.
    
    Creates repository with session and injects into service.
    Also injects CacheService, SettingsProvider and EmailService for password reset functionality.
    """
    repository = AppUserRepository(session)
    cache_service = CacheService()
    settings_provider = SettingsProvider()
    email_service = EmailService()
    return AuthService(
        repository,
        cache_service=cache_service,
        settings_provider=settings_provider,
        email_service=email_service
    )


# Export all factories
__all__ = [
    "get_client_repository",
    "get_client_service",
    "get_app_user_repository",
    "get_auth_service",
]

