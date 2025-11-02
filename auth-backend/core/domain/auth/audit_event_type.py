"""
Audit Event Types
Comprehensive enumeration of all security and audit events tracked in the system
"""
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.domain.audit.audit_event_category import AuditEventCategory


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
    
    # ===== Data Access Events =====
    ENTITY_VIEWED = "entity.viewed"
    REPORT_VIEWED = "report.viewed"
    FILE_DOWNLOADED = "file.downloaded"
    DATA_EXPORTED = "data.exported"
    SENSITIVE_DATA_ACCESSED = "sensitive_data.accessed"
    
    # ===== Data Modification Events =====
    ENTITY_CREATED = "entity.created"
    ENTITY_UPDATED = "entity.updated"
    ENTITY_DELETED = "entity.deleted"
    ENTITY_RESTORED = "entity.restored"
    BULK_UPDATE = "entity.bulk_updated"
    BULK_DELETE = "entity.bulk_deleted"
    
    # ===== Business Logic Events =====
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_GRANTED = "approval.granted"
    APPROVAL_REJECTED = "approval.rejected"
    TASK_CREATED = "task.created"
    TASK_COMPLETED = "task.completed"
    DOCUMENT_PUBLISHED = "document.published"
    DOCUMENT_ARCHIVED = "document.archived"
    NOTIFICATION_SENT = "notification.sent"
    
    # ===== Administrative Events =====
    SETTINGS_CHANGED = "admin.settings.changed"
    FEATURE_ENABLED = "admin.feature.enabled"
    FEATURE_DISABLED = "admin.feature.disabled"
    MAINTENANCE_MODE_ENABLED = "admin.maintenance.enabled"
    MAINTENANCE_MODE_DISABLED = "admin.maintenance.disabled"
    
    # ===== System Events =====
    DATABASE_BACKUP = "system.database.backup"
    DATABASE_RESTORE = "system.database.restore"
    MIGRATION_EXECUTED = "system.migration.executed"
    CACHE_CLEARED = "system.cache.cleared"
    ERROR_OCCURRED = "system.error"
    
    def get_category(self) -> "AuditEventCategory":
        """
        Get category for this event type.
        
        Returns:
            AuditEventCategory enum value
        """
        from core.domain.audit.audit_event_category import AuditEventCategory
        
        # Authentication events
        if self.value in [
            "login_success", "login_failed", "login_failed_invalid_credentials",
            "login_failed_account_locked", "login_failed_email_not_verified",
            "logout", "logout_all_sessions", "session_revoked",
            "token_refresh_success", "token_refresh_failed", "token_revoked",
            "user_registered", "registration_failed",
            "email_verification_sent", "email_verified", "email_verification_failed",
            "password_changed", "password_change_failed",
            "password_reset_requested", "password_reset_completed", "password_reset_failed",
            "mfa_enabled", "mfa_disabled", "mfa_verification_success", "mfa_verification_failed",
            "mfa_backup_code_used", "mfa_backup_code_regenerated",
            "magic_link_sent", "magic_link_login_success", "magic_link_login_failed",
            "webauthn_credential_registered", "webauthn_login_success", "webauthn_login_failed",
            "webauthn_credential_revoked",
            "oauth_login_success", "oauth_login_failed", "oauth_account_linked", "oauth_account_unlinked",
            "sso_login_success", "sso_login_failed",
            "saml_login_success", "saml_login_failed",
            "oidc_login_success", "oidc_login_failed",
            "ldap_login_success", "ldap_login_failed",
        ]:
            return AuditEventCategory.AUTHENTICATION
        
        # Authorization events
        elif self.value in [
            "user_role_changed",
            "user_activated", "user_deactivated",
            "account_locked", "account_unlocked",
        ] or self.value.startswith(("role.", "permission.", "access.")):
            return AuditEventCategory.AUTHORIZATION
        
        # Data access events
        elif self.value in [
            "entity.viewed", "report.viewed", "file.downloaded",
            "data.exported", "sensitive_data.accessed"
        ] or "viewed" in self.value or "downloaded" in self.value or "accessed" in self.value:
            return AuditEventCategory.DATA_ACCESS
        
        # Data modification events
        elif self.value.startswith("entity.") or "bulk_" in self.value:
            return AuditEventCategory.DATA_MODIFICATION
        
        # Business logic events
        elif self.value.startswith(("workflow.", "approval.", "task.", "document.", "notification.")):
            return AuditEventCategory.BUSINESS_LOGIC
        
        # Administrative events
        elif self.value.startswith("admin.") or self.value in [
            "user_created_by_admin", "user_updated_by_admin", "user_deleted_by_admin",
            "settings_changed", "feature_enabled", "feature_disabled",
            "maintenance_mode_enabled", "maintenance_mode_disabled"
        ]:
            return AuditEventCategory.ADMINISTRATIVE
        
        # System events
        elif self.value.startswith("system.") or self.value in [
            "database_backup", "database_restore", "migration_executed",
            "cache_cleared", "error_occurred"
        ]:
            return AuditEventCategory.SYSTEM
        
        # Default to SYSTEM for unclassified events
        return AuditEventCategory.SYSTEM
    
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
            self.SENSITIVE_DATA_ACCESSED,
            self.BULK_DELETE,
            self.MAINTENANCE_MODE_ENABLED,
        }
        return self in critical_events

