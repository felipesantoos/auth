"""
Unit tests for AuditEventType domain model
Tests domain logic without external dependencies
"""
import pytest
from core.domain.auth.audit_event_type import AuditEventType
from core.domain.audit.audit_event_category import AuditEventCategory


@pytest.mark.unit
class TestAuditEventTypeCategory:
    """Test event category mapping"""
    
    def test_login_success_is_authentication_category(self):
        """Test LOGIN_SUCCESS is in authentication category"""
        event = AuditEventType.LOGIN_SUCCESS
        assert event.get_category() == AuditEventCategory.AUTHENTICATION
    
    def test_login_failed_is_authentication_category(self):
        """Test LOGIN_FAILED is in authentication category"""
        event = AuditEventType.LOGIN_FAILED
        assert event.get_category() == AuditEventCategory.AUTHENTICATION
    
    def test_password_changed_is_authentication_category(self):
        """Test PASSWORD_CHANGED is in authentication category"""
        event = AuditEventType.PASSWORD_CHANGED
        assert event.get_category() == AuditEventCategory.AUTHENTICATION
    
    def test_mfa_enabled_is_authentication_category(self):
        """Test MFA_ENABLED is in authentication category"""
        event = AuditEventType.MFA_ENABLED
        assert event.get_category() == AuditEventCategory.AUTHENTICATION
    
    def test_user_role_changed_is_authorization_category(self):
        """Test USER_ROLE_CHANGED is in authorization category"""
        event = AuditEventType.USER_ROLE_CHANGED
        assert event.get_category() == AuditEventCategory.AUTHORIZATION
    
    def test_account_locked_is_authorization_category(self):
        """Test ACCOUNT_LOCKED is in authorization category"""
        event = AuditEventType.ACCOUNT_LOCKED
        assert event.get_category() == AuditEventCategory.AUTHORIZATION
    
    def test_entity_viewed_is_data_access_category(self):
        """Test ENTITY_VIEWED is in data access category"""
        event = AuditEventType.ENTITY_VIEWED
        assert event.get_category() == AuditEventCategory.DATA_ACCESS
    
    def test_file_downloaded_is_data_access_category(self):
        """Test FILE_DOWNLOADED is in data access category"""
        event = AuditEventType.FILE_DOWNLOADED
        assert event.get_category() == AuditEventCategory.DATA_ACCESS
    
    def test_entity_created_is_data_modification_category(self):
        """Test ENTITY_CREATED is in data modification category"""
        event = AuditEventType.ENTITY_CREATED
        assert event.get_category() == AuditEventCategory.DATA_MODIFICATION
    
    def test_entity_updated_is_data_modification_category(self):
        """Test ENTITY_UPDATED is in data modification category"""
        event = AuditEventType.ENTITY_UPDATED
        assert event.get_category() == AuditEventCategory.DATA_MODIFICATION
    
    def test_entity_deleted_is_data_modification_category(self):
        """Test ENTITY_DELETED is in data modification category"""
        event = AuditEventType.ENTITY_DELETED
        assert event.get_category() == AuditEventCategory.DATA_MODIFICATION
    
    def test_bulk_update_is_data_modification_category(self):
        """Test BULK_UPDATE is in data modification category"""
        event = AuditEventType.BULK_UPDATE
        assert event.get_category() == AuditEventCategory.DATA_MODIFICATION
    
    def test_workflow_started_is_business_logic_category(self):
        """Test WORKFLOW_STARTED is in business logic category"""
        event = AuditEventType.WORKFLOW_STARTED
        assert event.get_category() == AuditEventCategory.BUSINESS_LOGIC
    
    def test_approval_requested_is_business_logic_category(self):
        """Test APPROVAL_REQUESTED is in business logic category"""
        event = AuditEventType.APPROVAL_REQUESTED
        assert event.get_category() == AuditEventCategory.BUSINESS_LOGIC
    
    def test_settings_changed_is_administrative_category(self):
        """Test SETTINGS_CHANGED is in administrative category"""
        event = AuditEventType.SETTINGS_CHANGED
        assert event.get_category() == AuditEventCategory.ADMINISTRATIVE
    
    def test_user_created_by_admin_is_administrative_category(self):
        """Test USER_CREATED_BY_ADMIN is in administrative category"""
        event = AuditEventType.USER_CREATED_BY_ADMIN
        assert event.get_category() == AuditEventCategory.ADMINISTRATIVE
    
    def test_database_backup_is_system_category(self):
        """Test DATABASE_BACKUP is in system category"""
        event = AuditEventType.DATABASE_BACKUP
        assert event.get_category() == AuditEventCategory.SYSTEM
    
    def test_cache_cleared_is_system_category(self):
        """Test CACHE_CLEARED is in system category"""
        event = AuditEventType.CACHE_CLEARED
        assert event.get_category() == AuditEventCategory.SYSTEM


@pytest.mark.unit
class TestAuditEventTypeStatus:
    """Test success/failure detection"""
    
    def test_login_success_is_success_event(self):
        """Test LOGIN_SUCCESS is success event"""
        event = AuditEventType.LOGIN_SUCCESS
        assert event.is_success_event() is True
        assert event.is_failure_event() is False
    
    def test_login_failed_is_failure_event(self):
        """Test LOGIN_FAILED is failure event"""
        event = AuditEventType.LOGIN_FAILED
        assert event.is_success_event() is False
        assert event.is_failure_event() is True
    
    def test_email_verified_is_success_event(self):
        """Test EMAIL_VERIFIED is success event"""
        event = AuditEventType.EMAIL_VERIFIED
        assert event.is_success_event() is True
    
    def test_mfa_enabled_is_success_event(self):
        """Test MFA_ENABLED is success event"""
        event = AuditEventType.MFA_ENABLED
        assert event.is_success_event() is True
    
    def test_password_reset_failed_is_failure_event(self):
        """Test PASSWORD_RESET_FAILED is failure event"""
        event = AuditEventType.PASSWORD_RESET_FAILED
        assert event.is_failure_event() is True
    
    def test_mfa_verification_failed_is_failure_event(self):
        """Test MFA_VERIFICATION_FAILED is failure event"""
        event = AuditEventType.MFA_VERIFICATION_FAILED
        assert event.is_failure_event() is True


@pytest.mark.unit
class TestAuditEventTypeSecurity:
    """Test security-critical event detection"""
    
    def test_login_failed_account_locked_is_security_critical(self):
        """Test LOGIN_FAILED_ACCOUNT_LOCKED is security critical"""
        event = AuditEventType.LOGIN_FAILED_ACCOUNT_LOCKED
        assert event.is_security_critical() is True
    
    def test_account_locked_is_security_critical(self):
        """Test ACCOUNT_LOCKED is security critical"""
        event = AuditEventType.ACCOUNT_LOCKED
        assert event.is_security_critical() is True
    
    def test_suspicious_activity_detected_is_security_critical(self):
        """Test SUSPICIOUS_ACTIVITY_DETECTED is security critical"""
        event = AuditEventType.SUSPICIOUS_ACTIVITY_DETECTED
        assert event.is_security_critical() is True
    
    def test_mfa_disabled_is_security_critical(self):
        """Test MFA_DISABLED is security critical"""
        event = AuditEventType.MFA_DISABLED
        assert event.is_security_critical() is True
    
    def test_user_deleted_by_admin_is_security_critical(self):
        """Test USER_DELETED_BY_ADMIN is security critical"""
        event = AuditEventType.USER_DELETED_BY_ADMIN
        assert event.is_security_critical() is True
    
    def test_password_reset_completed_is_security_critical(self):
        """Test PASSWORD_RESET_COMPLETED is security critical"""
        event = AuditEventType.PASSWORD_RESET_COMPLETED
        assert event.is_security_critical() is True
    
    def test_sensitive_data_accessed_is_security_critical(self):
        """Test SENSITIVE_DATA_ACCESSED is security critical"""
        event = AuditEventType.SENSITIVE_DATA_ACCESSED
        assert event.is_security_critical() is True
    
    def test_bulk_delete_is_security_critical(self):
        """Test BULK_DELETE is security critical"""
        event = AuditEventType.BULK_DELETE
        assert event.is_security_critical() is True
    
    def test_maintenance_mode_enabled_is_security_critical(self):
        """Test MAINTENANCE_MODE_ENABLED is security critical"""
        event = AuditEventType.MAINTENANCE_MODE_ENABLED
        assert event.is_security_critical() is True
    
    def test_login_success_is_not_security_critical(self):
        """Test LOGIN_SUCCESS is not security critical"""
        event = AuditEventType.LOGIN_SUCCESS
        assert event.is_security_critical() is False
    
    def test_user_registered_is_not_security_critical(self):
        """Test USER_REGISTERED is not security critical"""
        event = AuditEventType.USER_REGISTERED
        assert event.is_security_critical() is False


@pytest.mark.unit
class TestAuditEventTypeSSO:
    """Test SSO event types"""
    
    def test_oauth_login_success_is_authentication(self):
        """Test OAUTH_LOGIN_SUCCESS is authentication"""
        event = AuditEventType.OAUTH_LOGIN_SUCCESS
        assert event.get_category() == AuditEventCategory.AUTHENTICATION
    
    def test_saml_login_success_is_authentication(self):
        """Test SAML_LOGIN_SUCCESS is authentication"""
        event = AuditEventType.SAML_LOGIN_SUCCESS
        assert event.get_category() == AuditEventCategory.AUTHENTICATION
    
    def test_oidc_login_success_is_authentication(self):
        """Test OIDC_LOGIN_SUCCESS is authentication"""
        event = AuditEventType.OIDC_LOGIN_SUCCESS
        assert event.get_category() == AuditEventCategory.AUTHENTICATION
    
    def test_ldap_login_success_is_authentication(self):
        """Test LDAP_LOGIN_SUCCESS is authentication"""
        event = AuditEventType.LDAP_LOGIN_SUCCESS
        assert event.get_category() == AuditEventCategory.AUTHENTICATION


@pytest.mark.unit
class TestAuditEventTypeWebAuthn:
    """Test WebAuthn event types"""
    
    def test_webauthn_credential_registered_is_authentication(self):
        """Test WEBAUTHN_CREDENTIAL_REGISTERED is authentication"""
        event = AuditEventType.WEBAUTHN_CREDENTIAL_REGISTERED
        assert event.get_category() == AuditEventCategory.AUTHENTICATION
    
    def test_webauthn_login_success_is_authentication(self):
        """Test WEBAUTHN_LOGIN_SUCCESS is authentication"""
        event = AuditEventType.WEBAUTHN_LOGIN_SUCCESS
        assert event.get_category() == AuditEventCategory.AUTHENTICATION
        assert event.is_success_event() is True
    
    def test_webauthn_login_failed_is_authentication(self):
        """Test WEBAUTHN_LOGIN_FAILED is authentication"""
        event = AuditEventType.WEBAUTHN_LOGIN_FAILED
        assert event.get_category() == AuditEventCategory.AUTHENTICATION
        assert event.is_failure_event() is True

