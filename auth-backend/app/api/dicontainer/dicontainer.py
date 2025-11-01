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
from core.interfaces.primary.client_service_interface import IClientService

# Auth Repositories
from infra.database.repositories.app_user_repository import AppUserRepository
from core.interfaces.secondary.app_user_repository_interface import IAppUserRepository

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
from infra.database.repositories.permission_repository import PermissionRepository

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
from core.services.auth.permission_service import PermissionService
from core.services.auth.user_profile_service import UserProfileService

# New Repositories (WebAuthn)
from infra.database.repositories.webauthn_credential_repository import WebAuthnCredentialRepository

# Email Tracking
from infra.database.repositories.email_tracking_repository import EmailTrackingRepository
from infra.database.repositories.email_click_repository import EmailClickRepository
from infra.database.repositories.email_subscription_repository import EmailSubscriptionRepository
from infra.database.repositories.email_ab_test_repository import EmailABTestRepository
from core.services.email.email_tracking_service import EmailTrackingService
from core.services.email.email_webhook_service import EmailWebhookService
from core.services.email.unsubscribe_service import UnsubscribeService
from core.services.email.email_ab_test_service import EmailABTestService
from core.interfaces.primary.email_tracking_service_interface import IEmailTrackingService
from core.interfaces.primary.email_webhook_service_interface import IEmailWebhookService
from core.interfaces.primary.unsubscribe_service_interface import IUnsubscribeService
from core.interfaces.primary.email_ab_test_service_interface import IEmailABTestService

# File Upload
from infra.database.repositories.file_repository import FileRepository
from infra.database.repositories.pending_upload_repository import PendingUploadRepository
from infra.database.repositories.file_share_repository import FileShareRepository
from infra.database.repositories.multipart_upload_repository import MultipartUploadRepository
from infra.database.repositories.upload_part_repository import UploadPartRepository
from core.services.files.file_service import FileService
from core.services.files.chunked_upload_manager import ChunkedUploadManager
from core.interfaces.primary.file_service_interface import IFileService
from infra.storage.storage_factory import StorageFactory
from core.interfaces.secondary import IFileStorage
from app.api.utils.file_validator import FileValidator

logger = logging.getLogger(__name__)


def get_client_repository(
    session: AsyncSession = Depends(get_db_session)
) -> ClientRepository:
    """Factory for Client repository"""
    return ClientRepository(session)


async def get_client_service(
    session: AsyncSession = Depends(get_db_session)
) -> IClientService:
    """
    Factory for Client service.
    
    Creates repository with session and injects into service.
    """
    repository = ClientRepository(session)
    return ClientService(repository)


async def get_app_user_repository(
    session: AsyncSession = Depends(get_db_session)
) -> IAppUserRepository:
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


async def get_permission_service(
    session: AsyncSession = Depends(get_db_session)
) -> PermissionService:
    """Factory for PermissionService"""
    repository = PermissionRepository(session)
    return PermissionService(repository=repository)


async def get_user_profile_service(
    session: AsyncSession = Depends(get_db_session)
) -> UserProfileService:
    """Factory for UserProfileService"""
    user_repository = await get_app_user_repository(session)
    email_service = EmailService()
    settings_provider = SettingsProvider()
    return UserProfileService(
        user_repository=user_repository,
        email_service=email_service,
        settings_provider=settings_provider
    )


async def get_email_tracking_service(
    session: AsyncSession = Depends(get_db_session)
) -> IEmailTrackingService:
    """
    Factory for IEmailTrackingService interface.
    
    Returns EmailTrackingService instance following hexagonal architecture.
    """
    tracking_repository = EmailTrackingRepository(session)
    click_repository = EmailClickRepository(session)
    subscription_repository = EmailSubscriptionRepository(session)
    
    return EmailTrackingService(
        tracking_repository=tracking_repository,
        click_repository=click_repository,
        subscription_repository=subscription_repository
    )


async def get_email_webhook_service(
    session: AsyncSession = Depends(get_db_session)
) -> IEmailWebhookService:
    """
    Factory for IEmailWebhookService interface.
    
    Returns EmailWebhookService instance following hexagonal architecture.
    """
    tracking_repository = EmailTrackingRepository(session)
    subscription_repository = EmailSubscriptionRepository(session)
    
    return EmailWebhookService(
        tracking_repository=tracking_repository,
        subscription_repository=subscription_repository
    )


async def get_unsubscribe_service(
    session: AsyncSession = Depends(get_db_session)
) -> IUnsubscribeService:
    """
    Factory for IUnsubscribeService interface.
    
    Returns UnsubscribeService instance following hexagonal architecture.
    """
    subscription_repository = EmailSubscriptionRepository(session)
    
    return UnsubscribeService(
        email_subscription_repository=subscription_repository
    )


async def get_email_ab_test_service(
    session: AsyncSession = Depends(get_db_session)
) -> IEmailABTestService:
    """
    Factory for IEmailABTestService interface.
    
    Returns EmailABTestService instance following hexagonal architecture.
    """
    ab_test_repository = EmailABTestRepository(session)
    email_service = EmailService()
    
    return EmailABTestService(
        ab_test_repository=ab_test_repository,
        email_service=email_service
    )


# ===========================================
# File Upload Factories
# ===========================================

def get_file_storage() -> IFileStorage:
    """
    Factory for file storage provider.
    
    Returns appropriate storage implementation based on settings.
    """
    return StorageFactory.get_default_storage()


def get_file_repository(
    session: AsyncSession = Depends(get_db_session)
) -> FileRepository:
    """Factory for FileRepository."""
    return FileRepository(session)


def get_pending_upload_repository(
    session: AsyncSession = Depends(get_db_session)
) -> PendingUploadRepository:
    """Factory for PendingUploadRepository."""
    return PendingUploadRepository(session)


def get_file_share_repository(
    session: AsyncSession = Depends(get_db_session)
) -> FileShareRepository:
    """Factory for FileShareRepository."""
    return FileShareRepository(session)


def get_file_validator() -> FileValidator:
    """Factory for FileValidator."""
    return FileValidator()


async def get_file_service(
    session: AsyncSession = Depends(get_db_session),
    storage: IFileStorage = Depends(get_file_storage),
    validator: FileValidator = Depends(get_file_validator)
) -> IFileService:
    """
    Factory for IFileService interface.
    
    Returns FileService instance following hexagonal architecture.
    """
    file_repository = FileRepository(session)
    pending_upload_repository = PendingUploadRepository(session)
    file_share_repository = FileShareRepository(session)
    
    return FileService(
        storage=storage,
        file_repository=file_repository,
        pending_upload_repository=pending_upload_repository,
        file_share_repository=file_share_repository,
        validator=validator
    )


async def get_chunked_upload_manager(
    session: AsyncSession = Depends(get_db_session)
) -> ChunkedUploadManager:
    """
    Factory for ChunkedUploadManager.
    
    Manages multipart uploads for large files.
    """
    multipart_upload_repository = MultipartUploadRepository(session)
    upload_part_repository = UploadPartRepository(session)
    
    return ChunkedUploadManager(
        multipart_upload_repository=multipart_upload_repository,
        upload_part_repository=upload_part_repository
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
    "get_permission_service",
    "get_user_profile_service",
    "get_email_tracking_service",
    "get_email_webhook_service",
    "get_unsubscribe_service",
    "get_email_ab_test_service",
    # File Upload
    "get_file_storage",
    "get_file_repository",
    "get_pending_upload_repository",
    "get_file_share_repository",
    "get_file_validator",
    "get_file_service",
    "get_chunked_upload_manager",
]

