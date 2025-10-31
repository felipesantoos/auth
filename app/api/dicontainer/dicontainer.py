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
from core.interfaces.primary.auth_service_interface import AuthServiceInterface

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
) -> AuthServiceInterface:
    """
    Factory for Auth service.
    
    Creates repository with session and injects into service.
    """
    repository = AppUserRepository(session)
    return AuthService(repository)


# Export all factories
__all__ = [
    "get_client_repository",
    "get_client_service",
    "get_app_user_repository",
    "get_auth_service",
]

