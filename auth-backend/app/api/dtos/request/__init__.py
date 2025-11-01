"""Request DTOs package"""
from .auth_request import (
    LoginRequest,
    RegisterRequest,
    ChangePasswordRequest,
    RefreshTokenRequest,
    UpdateUserRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from .client_request import CreateClientRequest, UpdateClientRequest
from .mfa_request import (
    SetupMFARequest,
    EnableMFARequest,
    VerifyTOTPRequest,
    VerifyBackupCodeRequest,
    DisableMFARequest,
    RegenerateBackupCodesRequest,
)
from .mfa_login_request import MFALoginRequest
from .session_request import RevokeSessionRequest, RevokeAllSessionsRequest
from .email_verification_request import VerifyEmailRequest, ResendVerificationRequest
from .api_key_request import CreateApiKeyRequest, RevokeApiKeyRequest
from .passwordless_request import SendMagicLinkRequest, VerifyMagicLinkRequest

__all__ = [
    # Auth
    "LoginRequest",
    "RegisterRequest",
    "ChangePasswordRequest",
    "RefreshTokenRequest",
    "UpdateUserRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    # Client
    "CreateClientRequest",
    "UpdateClientRequest",
    # MFA
    "SetupMFARequest",
    "EnableMFARequest",
    "VerifyTOTPRequest",
    "VerifyBackupCodeRequest",
    "DisableMFARequest",
    "RegenerateBackupCodesRequest",
    "MFALoginRequest",
    # Sessions
    "RevokeSessionRequest",
    "RevokeAllSessionsRequest",
    # Email Verification
    "VerifyEmailRequest",
    "ResendVerificationRequest",
    # API Keys
    "CreateApiKeyRequest",
    "RevokeApiKeyRequest",
    # Passwordless
    "SendMagicLinkRequest",
    "VerifyMagicLinkRequest",
]

