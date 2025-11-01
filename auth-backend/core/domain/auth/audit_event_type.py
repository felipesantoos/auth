"""
Audit Event Types
Enumeration of all security and audit events tracked in the system
"""
from enum import Enum


class AuditEventType(str, Enum):
    """
    Types of events that are logged for security and audit purposes.
    
    These events help track user activities, detect suspicious behavior,
    and maintain compliance with security requirements.
    """
    # Authentication Events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGIN_FAILED_INVALID_CREDENTIALS = "login_failed_invalid_credentials"
    LOGIN_FAILED_ACCOUNT_LOCKED = "login_failed_account_locked"
    LOGIN_FAILED_EMAIL_NOT_VERIFIED = "login_failed_email_not_verified"
    LOGOUT = "logout"
    LOGOUT_ALL_SESSIONS = "logout_all_sessions"
    SESSION_REVOKED = "session_revoked"
    
    # Token Events
    TOKEN_REFRESH_SUCCESS = "token_refresh_success"
    TOKEN_REFRESH_FAILED = "token_refresh_failed"
    TOKEN_REVOKED = "token_revoked"
    
    # Registration Events
    USER_REGISTERED = "user_registered"
    REGISTRATION_FAILED = "registration_failed"
    
    # Email Verification Events
    EMAIL_VERIFICATION_SENT = "email_verification_sent"
    EMAIL_VERIFIED = "email_verified"
    EMAIL_VERIFICATION_FAILED = "email_verification_failed"
    
    # Password Events
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_CHANGE_FAILED = "password_change_failed"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_RESET_COMPLETED = "password_reset_completed"
    PASSWORD_RESET_FAILED = "password_reset_failed"
    
    # MFA/2FA Events
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    MFA_VERIFICATION_SUCCESS = "mfa_verification_success"
    MFA_VERIFICATION_FAILED = "mfa_verification_failed"
    MFA_BACKUP_CODE_USED = "mfa_backup_code_used"
    MFA_BACKUP_CODE_REGENERATED = "mfa_backup_code_regenerated"
    
    # Account Security Events
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    SUSPICIOUS_ACTIVITY_DETECTED = "suspicious_activity_detected"
    
    # User Management Events (Admin)
    USER_CREATED_BY_ADMIN = "user_created_by_admin"
    USER_UPDATED_BY_ADMIN = "user_updated_by_admin"
    USER_DELETED_BY_ADMIN = "user_deleted_by_admin"
    USER_ACTIVATED = "user_activated"
    USER_DEACTIVATED = "user_deactivated"
    
    # Role Management Events
    USER_ROLE_CHANGED = "user_role_changed"
    
    # API Key Events
    API_KEY_CREATED = "api_key_created"
    API_KEY_USED = "api_key_used"
    API_KEY_REVOKED = "api_key_revoked"
    API_KEY_EXPIRED = "api_key_expired"
    
    # Passwordless Auth Events
    MAGIC_LINK_SENT = "magic_link_sent"
    MAGIC_LINK_LOGIN_SUCCESS = "magic_link_login_success"
    MAGIC_LINK_LOGIN_FAILED = "magic_link_login_failed"
    
    # WebAuthn Events
    WEBAUTHN_CREDENTIAL_REGISTERED = "webauthn_credential_registered"
    WEBAUTHN_LOGIN_SUCCESS = "webauthn_login_success"
    WEBAUTHN_LOGIN_FAILED = "webauthn_login_failed"
    WEBAUTHN_CREDENTIAL_REVOKED = "webauthn_credential_revoked"
    
    # OAuth Events
    OAUTH_LOGIN_SUCCESS = "oauth_login_success"
    OAUTH_LOGIN_FAILED = "oauth_login_failed"
    OAUTH_ACCOUNT_LINKED = "oauth_account_linked"
    OAUTH_ACCOUNT_UNLINKED = "oauth_account_unlinked"
    
    # SSO Events
    SSO_LOGIN_SUCCESS = "sso_login_success"
    SSO_LOGIN_FAILED = "sso_login_failed"
    SAML_LOGIN_SUCCESS = "saml_login_success"
    SAML_LOGIN_FAILED = "saml_login_failed"
    OIDC_LOGIN_SUCCESS = "oidc_login_success"
    OIDC_LOGIN_FAILED = "oidc_login_failed"
    LDAP_LOGIN_SUCCESS = "ldap_login_success"
    LDAP_LOGIN_FAILED = "ldap_login_failed"
    
    def is_success_event(self) -> bool:
        """Check if this is a successful operation event"""
        return "success" in self.value or "verified" in self.value or "enabled" in self.value
    
    def is_failure_event(self) -> bool:
        """Check if this is a failed operation event"""
        return "failed" in self.value
    
    def is_security_critical(self) -> bool:
        """Check if this is a security-critical event (requires immediate attention)"""
        critical_events = {
            self.LOGIN_FAILED_ACCOUNT_LOCKED,
            self.ACCOUNT_LOCKED,
            self.SUSPICIOUS_ACTIVITY_DETECTED,
            self.MFA_DISABLED,
            self.USER_DELETED_BY_ADMIN,
            self.PASSWORD_RESET_COMPLETED,
        }
        return self in critical_events

