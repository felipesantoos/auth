"""
Dependency Injection Container
Factory functions for service and repository dependencies
Following hexagonal architecture patterns
"""
import logging
from infra.database.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from config.settings import settings

# Client
from infra.database.repositories.client_repository import ClientRepository
from core.services.client.client_service import ClientService
from core.interfaces.primary.client_service_interface import ClientServiceInterface

# Auth Repositories
from infra.database.repositories.app_user_repository import AppUserRepository
from core.interfaces.secondary.app_user_repository_interface import AppUserRepositoryInterface

# Auth Services
from core.services.auth.auth_service import AuthService
from core.services.auth.password_reset_service import PasswordResetService
from core.services.auth.oauth_service import OAuthService
from core.interfaces.primary.auth_service_interface import IAuthService
from core.interfaces.primary.password_reset_service_interface import IPasswordResetService
from core.interfaces.primary.oauth_service_interface import IOAuthService

# Email
from infra.email.email_service import EmailService

# Cache
from infra.redis.cache_service import CacheService

# Settings
from infra.config.settings_provider import SettingsProvider

# New Repositories
from infra.database.repositories.audit_log_repository import AuditLogRepository
from infra.database.repositories.backup_code_repository import BackupCodeRepository
from infra.database.repositories.user_session_repository import UserSessionRepository
from infra.database.repositories.api_key_repository import ApiKeyRepository

# New Services
from core.services.audit.audit_service import AuditService
from core.services.auth.mfa_service import MFAService
from core.services.auth.session_service import SessionService
from core.services.auth.email_verification_service import EmailVerificationService
from core.services.auth.passwordless_service import PasswordlessService
from core.services.auth.api_key_service import ApiKeyService
from core.services.auth.webauthn_service import WebAuthnService
from core.services.auth.saml_service import SAMLService
from core.services.auth.oidc_service import OIDCService
from core.services.auth.ldap_service import LDAPService
from core.services.auth.login_notification_service import LoginNotificationService

# New Repositories (WebAuthn)
from infra.database.repositories.webauthn_credential_repository import WebAuthnCredentialRepository

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


async def get_app_user_repository(
    session: AsyncSession = Depends(get_db_session)
) -> AppUserRepositoryInterface:
    """
    Factory for AppUser repository.
    
    Uses PostgreSQL repository for all environments.
    """
    return AppUserRepository(session)


async def get_auth_service(
    session: AsyncSession = Depends(get_db_session)
) -> IAuthService:
    """
    Factory for IAuthService interface.
    
    Returns AuthService instance (implements only IAuthService).
    """
    repository = await get_app_user_repository(session)
    cache_service = CacheService()
    settings_provider = SettingsProvider()
    return AuthService(
        repository=repository,
        cache_service=cache_service,
        settings_provider=settings_provider,
    )


async def get_password_reset_service(
    session: AsyncSession = Depends(get_db_session)
) -> IPasswordResetService:
    """
    Factory for IPasswordResetService interface.
    
    Returns PasswordResetService instance (implements only IPasswordResetService).
    """
    repository = await get_app_user_repository(session)
    cache_service = CacheService()
    settings_provider = SettingsProvider()
    email_service = EmailService()
    return PasswordResetService(
        repository=repository,
        cache_service=cache_service,
        settings_provider=settings_provider,
        email_service=email_service,
    )


async def get_oauth_service(
    session: AsyncSession = Depends(get_db_session)
) -> IOAuthService:
    """
    Factory for IOAuthService interface.
    
    Returns OAuthService instance (implements only IOAuthService).
    """
    repository = await get_app_user_repository(session)
    cache_service = CacheService()
    settings_provider = SettingsProvider()
    return OAuthService(
        repository=repository,
        cache_service=cache_service,
        settings_provider=settings_provider,
    )


async def get_audit_service(
    session: AsyncSession = Depends(get_db_session)
) -> AuditService:
    """Factory for AuditService"""
    repository = AuditLogRepository(session)
    return AuditService(repository=repository)


async def get_mfa_service(
    session: AsyncSession = Depends(get_db_session)
) -> MFAService:
    """Factory for MFAService"""
    user_repository = await get_app_user_repository(session)
    backup_code_repository = BackupCodeRepository(session)
    settings_provider = SettingsProvider()
    return MFAService(
        user_repository=user_repository,
        backup_code_repository=backup_code_repository,
        settings_provider=settings_provider,
    )


async def get_session_service(
    session: AsyncSession = Depends(get_db_session)
) -> SessionService:
    """Factory for SessionService"""
    repository = UserSessionRepository(session)
    cache_service = CacheService()
    settings_provider = SettingsProvider()
    return SessionService(
        repository=repository,
        cache_service=cache_service,
        settings_provider=settings_provider,
    )


async def get_email_verification_service(
    session: AsyncSession = Depends(get_db_session)
) -> EmailVerificationService:
    """Factory for EmailVerificationService"""
    user_repository = await get_app_user_repository(session)
    email_service = EmailService()
    settings_provider = SettingsProvider()
    return EmailVerificationService(
        user_repository=user_repository,
        email_service=email_service,
        settings_provider=settings_provider,
    )


async def get_passwordless_service(
    session: AsyncSession = Depends(get_db_session)
) -> PasswordlessService:
    """Factory for PasswordlessService"""
    user_repository = await get_app_user_repository(session)
    email_service = EmailService()
    settings_provider = SettingsProvider()
    return PasswordlessService(
        user_repository=user_repository,
        email_service=email_service,
        settings_provider=settings_provider,
    )


async def get_api_key_service(
    session: AsyncSession = Depends(get_db_session)
) -> ApiKeyService:
    """Factory for ApiKeyService"""
    repository = ApiKeyRepository(session)
    settings_provider = SettingsProvider()
    return ApiKeyService(
        repository=repository,
        settings_provider=settings_provider,
    )


async def get_webauthn_service(
    session: AsyncSession = Depends(get_db_session)
) -> WebAuthnService:
    """Factory for WebAuthnService"""
    user_repository = await get_app_user_repository(session)
    credential_repository = WebAuthnCredentialRepository(session)
    settings_provider = SettingsProvider()
    return WebAuthnService(
        user_repository=user_repository,
        credential_repository=credential_repository,
        settings_provider=settings_provider,
    )


async def get_saml_service(
    session: AsyncSession = Depends(get_db_session)
) -> SAMLService:
    """Factory for SAMLService"""
    user_repository = await get_app_user_repository(session)
    settings_provider = SettingsProvider()
    return SAMLService(
        user_repository=user_repository,
        settings_provider=settings_provider,
    )


async def get_oidc_service(
    session: AsyncSession = Depends(get_db_session)
) -> OIDCService:
    """Factory for OIDCService"""
    user_repository = await get_app_user_repository(session)
    cache_service = CacheService()
    settings_provider = SettingsProvider()
    return OIDCService(
        user_repository=user_repository,
        cache_service=cache_service,
        settings_provider=settings_provider,
    )


async def get_ldap_service(
    session: AsyncSession = Depends(get_db_session)
) -> LDAPService:
    """Factory for LDAPService"""
    user_repository = await get_app_user_repository(session)
    settings_provider = SettingsProvider()
    return LDAPService(
        user_repository=user_repository,
        settings_provider=settings_provider,
    )


def get_login_notification_service() -> LoginNotificationService:
    """Factory for LoginNotificationService"""
    email_service = EmailService()
    settings_provider = SettingsProvider()
    return LoginNotificationService(
        email_service=email_service,
        settings_provider=settings_provider
    )


# Export all factories
__all__ = [
    "get_client_repository",
    "get_client_service",
    "get_app_user_repository",
    "get_auth_service",
    "get_password_reset_service",
    "get_oauth_service",
    "get_audit_service",
    "get_mfa_service",
    "get_session_service",
    "get_email_verification_service",
    "get_passwordless_service",
    "get_api_key_service",
    "get_webauthn_service",
    "get_saml_service",
    "get_oidc_service",
    "get_ldap_service",
    "get_login_notification_service",
]

