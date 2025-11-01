"""Response DTOs package"""
from .auth_response import TokenResponse, UserResponse, MessageResponse
from .client_response import ClientResponse
from .paginated_response import PaginatedResponse
from .mfa_response import (
    SetupMFAResponse,
    EnableMFAResponse,
    MFAStatusResponse,
    RegenerateBackupCodesResponse,
)
from .mfa_login_response import MFARequiredResponse
from .session_response import (
    SessionInfoResponse,
    ActiveSessionsResponse,
    RevokeSessionResponse,
    RevokeAllSessionsResponse,
)
from .email_verification_response import (
    VerifyEmailResponse,
    ResendVerificationResponse,
    EmailVerificationStatusResponse,
)
from .api_key_response import (
    ApiKeyResponse,
    CreateApiKeyResponse,
    ListApiKeysResponse,
    RevokeApiKeyResponse,
)
from .passwordless_response import (
    SendMagicLinkResponse,
    VerifyMagicLinkResponse,
)
from .audit_response import (
    AuditLogResponse,
    AuditLogsResponse,
    SecurityEventsResponse,
)
from .email_tracking_response import (
    EmailAnalyticsResponse,
    EmailAnalyticsMetrics,
    EmailAnalyticsFilters,
    EmailPreferencesResponse,
    EmailPreferences,
    UnsubscribeResponse,
    UpdatePreferencesResponse,
)
from .file_response import (
    FileUploadResponse,
    FileInfoResponse,
    FileListResponse,
    FileListItemResponse,
    PaginationResponse,
    PresignedUrlResponse,
    FileShareResponse,
)

__all__ = [
    # Auth
    "TokenResponse",
    "UserResponse",
    "MessageResponse",
    # Client
    "ClientResponse",
    # Pagination
    "PaginatedResponse",
    # MFA
    "SetupMFAResponse",
    "EnableMFAResponse",
    "MFAStatusResponse",
    "RegenerateBackupCodesResponse",
    "MFARequiredResponse",
    # Sessions
    "SessionInfoResponse",
    "ActiveSessionsResponse",
    "RevokeSessionResponse",
    "RevokeAllSessionsResponse",
    # Email Verification
    "VerifyEmailResponse",
    "ResendVerificationResponse",
    "EmailVerificationStatusResponse",
    # API Keys
    "ApiKeyResponse",
    "CreateApiKeyResponse",
    "ListApiKeysResponse",
    "RevokeApiKeyResponse",
    # Passwordless
    "SendMagicLinkResponse",
    "VerifyMagicLinkResponse",
    # Audit
    "AuditLogResponse",
    "AuditLogsResponse",
    "SecurityEventsResponse",
    # Email Tracking
    "EmailAnalyticsResponse",
    "EmailAnalyticsMetrics",
    "EmailAnalyticsFilters",
    "EmailPreferencesResponse",
    "EmailPreferences",
    "UnsubscribeResponse",
    "UpdatePreferencesResponse",
    # File Upload
    "FileUploadResponse",
    "FileInfoResponse",
    "FileListResponse",
    "FileListItemResponse",
    "PaginationResponse",
    "PresignedUrlResponse",
    "FileShareResponse",
]

