"""
Unit tests for AppUser domain model
Tests domain logic without external dependencies
"""
import pytest
from datetime import datetime, timedelta
from core.domain.auth.app_user import AppUser
from core.domain.auth.user_role import UserRole
from core.exceptions import (
    MissingRequiredFieldException,
    InvalidEmailException,
    InvalidValueException,
    InvalidTokenException,
    TokenExpiredException,
    BusinessRuleException,
)
from tests.factories import UserFactory


@pytest.mark.unit
class TestAppUserValidation:
    """Test AppUser validation rules"""
    
    def test_valid_user_passes_validation(self):
        """Test that a valid user passes validation"""
        user = UserFactory.build()
        # Should not raise
        user.validate()
    
    def test_invalid_email_format_raises_exception(self):
        """Test that invalid email format raises exception"""
        user = UserFactory.build(email="not-an-email")
        
        with pytest.raises(InvalidEmailException):
            user.validate()
    
    def test_username_too_short_raises_exception(self):
        """Test that username shorter than 3 chars raises exception"""
        user = UserFactory.build(username="ab")
        
        with pytest.raises(InvalidValueException, match="at least 3 characters"):
            user.validate()
    
    def test_username_too_long_raises_exception(self):
        """Test that username longer than 255 chars raises exception"""
        user = UserFactory.build(username="a" * 256)
        
        with pytest.raises(InvalidValueException, match="not exceed 255 characters"):
            user.validate()
    
    def test_name_too_short_raises_exception(self):
        """Test that name shorter than 2 chars raises exception"""
        user = UserFactory.build(name="a")
        
        with pytest.raises(InvalidValueException, match="at least 2 characters"):
            user.validate()
    
    def test_name_too_long_raises_exception(self):
        """Test that name longer than 255 chars raises exception"""
        user = UserFactory.build(name="a" * 256)
        
        with pytest.raises(InvalidValueException, match="not exceed 255 characters"):
            user.validate()
    
    def test_missing_client_id_raises_exception(self):
        """Test that missing client_id raises exception"""
        user = UserFactory.build(client_id=None)
        
        with pytest.raises(MissingRequiredFieldException, match="client_id"):
            user.validate()


@pytest.mark.unit
class TestAppUserRoles:
    """Test user role methods"""
    
    def test_is_admin_returns_true_for_admin(self):
        """Test is_admin returns True for admin users"""
        user = UserFactory.create_admin()
        assert user.is_admin() is True
    
    def test_is_admin_returns_false_for_regular_user(self):
        """Test is_admin returns False for regular users"""
        user = UserFactory.build(role=UserRole.USER)
        assert user.is_admin() is False
    
    def test_is_manager_returns_true_for_manager(self):
        """Test is_manager returns True for manager users"""
        user = UserFactory.create_manager()
        assert user.is_manager() is True
    
    def test_is_manager_returns_false_for_regular_user(self):
        """Test is_manager returns False for regular users"""
        user = UserFactory.build(role=UserRole.USER)
        assert user.is_manager() is False
    
    def test_can_manage_users_for_admin(self):
        """Test admins can manage users"""
        user = UserFactory.create_admin()
        assert user.can_manage_users() is True
    
    def test_can_manage_users_for_manager(self):
        """Test managers can manage users"""
        user = UserFactory.create_manager()
        assert user.can_manage_users() is True
    
    def test_can_manage_users_for_regular_user(self):
        """Test regular users cannot manage users"""
        user = UserFactory.build(role=UserRole.USER)
        assert user.can_manage_users() is False


@pytest.mark.unit
class TestAppUserActivation:
    """Test user activation/deactivation"""
    
    def test_activate_sets_active_to_true(self):
        """Test activate() sets active to True"""
        user = UserFactory.build(active=False)
        user.activate()
        assert user.active is True
    
    def test_deactivate_sets_active_to_false(self):
        """Test deactivate() sets active to False"""
        user = UserFactory.build(active=True)
        user.deactivate()
        assert user.active is False


@pytest.mark.unit
class TestAppUserMultiTenant:
    """Test multi-tenant functionality"""
    
    def test_belongs_to_client_returns_true_for_matching_client(self):
        """Test belongs_to_client returns True for matching client"""
        user = UserFactory.build(client_id="client-123")
        assert user.belongs_to_client("client-123") is True
    
    def test_belongs_to_client_returns_false_for_different_client(self):
        """Test belongs_to_client returns False for different client"""
        user = UserFactory.build(client_id="client-123")
        assert user.belongs_to_client("client-456") is False


@pytest.mark.unit
class TestEmailVerification:
    """Test email verification functionality"""
    
    def test_generate_email_verification_token_creates_token(self):
        """Test generating email verification token"""
        user = UserFactory.build()
        
        token = user.generate_email_verification_token()
        
        assert token is not None
        assert len(token) > 20  # URL-safe tokens are typically longer
        assert user.email_verification_token == token
        assert user.email_verification_sent_at is not None
    
    def test_verify_email_token_succeeds_with_valid_token(self):
        """Test verifying valid email token"""
        user = UserFactory.build()
        token = user.generate_email_verification_token()
        
        # Should not raise
        result = user.verify_email_token(token)
        assert result is True
    
    def test_verify_email_token_fails_with_invalid_token(self):
        """Test verifying invalid email token raises exception"""
        user = UserFactory.build()
        user.generate_email_verification_token()
        
        with pytest.raises(InvalidTokenException, match="Invalid email verification token"):
            user.verify_email_token("wrong-token")
    
    def test_verify_email_token_fails_with_expired_token(self):
        """Test verifying expired email token raises exception"""
        user = UserFactory.build()
        token = user.generate_email_verification_token()
        
        # Manually set sent_at to 25 hours ago (expired)
        user.email_verification_sent_at = datetime.utcnow() - timedelta(hours=25)
        
        with pytest.raises(TokenExpiredException, match="Email verification token has expired"):
            user.verify_email_token(token, expire_hours=24)
    
    def test_verify_email_token_fails_when_no_token_exists(self):
        """Test verifying when no token exists raises exception"""
        user = UserFactory.build()
        
        with pytest.raises(InvalidTokenException):
            user.verify_email_token("any-token")
    
    def test_mark_email_verified_sets_verified_and_clears_token(self):
        """Test marking email as verified"""
        user = UserFactory.build()
        user.generate_email_verification_token()
        
        user.mark_email_verified()
        
        assert user.email_verified is True
        assert user.email_verification_token is None
        assert user.email_verification_sent_at is None
    
    def test_is_email_verified_returns_verification_status(self):
        """Test checking email verification status"""
        user = UserFactory.build(email_verified=False)
        assert user.is_email_verified() is False
        
        user.mark_email_verified()
        assert user.is_email_verified() is True


@pytest.mark.unit
class TestMFAFunctionality:
    """Test MFA/2FA functionality"""
    
    def test_enable_mfa_sets_enabled_and_secret(self):
        """Test enabling MFA"""
        user = UserFactory.build()
        secret = "JBSWY3DPEHPK3PXP"
        
        user.enable_mfa(secret)
        
        assert user.mfa_enabled is True
        assert user.mfa_secret == secret
    
    def test_disable_mfa_clears_enabled_and_secret(self):
        """Test disabling MFA"""
        user = UserFactory.create_with_mfa()
        
        user.disable_mfa()
        
        assert user.mfa_enabled is False
        assert user.mfa_secret is None
    
    def test_has_mfa_enabled_returns_mfa_status(self):
        """Test checking MFA status"""
        user_without_mfa = UserFactory.build()
        user_with_mfa = UserFactory.create_with_mfa()
        
        assert user_without_mfa.has_mfa_enabled() is False
        assert user_with_mfa.has_mfa_enabled() is True


@pytest.mark.unit
class TestAccountLocking:
    """Test account locking functionality"""
    
    def test_is_locked_returns_false_when_not_locked(self):
        """Test is_locked returns False when account is not locked"""
        user = UserFactory.build()
        assert user.is_locked() is False
    
    def test_is_locked_returns_true_when_locked(self):
        """Test is_locked returns True when account is locked"""
        user = UserFactory.create_locked()
        assert user.is_locked() is True
    
    def test_is_locked_returns_false_when_lock_expired(self):
        """Test is_locked returns False when lock has expired"""
        user = UserFactory.build()
        # Set lock to 1 hour ago (expired)
        user.locked_until = datetime.utcnow() - timedelta(hours=1)
        assert user.is_locked() is False
    
    def test_increment_failed_login_increases_counter(self):
        """Test incrementing failed login attempts"""
        user = UserFactory.build()
        assert user.failed_login_attempts == 0
        
        user.increment_failed_login()
        assert user.failed_login_attempts == 1
        
        user.increment_failed_login()
        assert user.failed_login_attempts == 2
    
    def test_lock_account_sets_locked_until(self):
        """Test locking account"""
        user = UserFactory.build()
        
        user.lock_account(duration_minutes=30)
        
        assert user.locked_until is not None
        # Check that locked_until is approximately 30 minutes from now
        expected_unlock = datetime.utcnow() + timedelta(minutes=30)
        time_diff = abs((user.locked_until - expected_unlock).total_seconds())
        assert time_diff < 5  # Within 5 seconds tolerance
    
    def test_reset_failed_login_attempts_clears_counter_and_lock(self):
        """Test resetting failed login attempts"""
        user = UserFactory.create_locked()
        
        user.reset_failed_login_attempts()
        
        assert user.failed_login_attempts == 0
        assert user.locked_until is None


@pytest.mark.unit
class TestMagicLinkAuth:
    """Test passwordless/magic link authentication"""
    
    def test_generate_magic_link_token_creates_token(self):
        """Test generating magic link token"""
        user = UserFactory.build()
        
        token = user.generate_magic_link_token()
        
        assert token is not None
        assert len(token) > 20
        assert user.magic_link_token == token
        assert user.magic_link_sent_at is not None
    
    def test_verify_magic_link_token_succeeds_with_valid_token(self):
        """Test verifying valid magic link token"""
        user = UserFactory.build()
        token = user.generate_magic_link_token()
        
        # Should not raise
        result = user.verify_magic_link_token(token, expire_minutes=15)
        assert result is True
    
    def test_verify_magic_link_token_fails_with_invalid_token(self):
        """Test verifying invalid magic link token raises exception"""
        user = UserFactory.build()
        user.generate_magic_link_token()
        
        with pytest.raises(InvalidTokenException, match="Invalid magic link token"):
            user.verify_magic_link_token("wrong-token")
    
    def test_verify_magic_link_token_fails_with_expired_token(self):
        """Test verifying expired magic link token raises exception"""
        user = UserFactory.build()
        token = user.generate_magic_link_token()
        
        # Manually set sent_at to 20 minutes ago (expired)
        user.magic_link_sent_at = datetime.utcnow() - timedelta(minutes=20)
        
        with pytest.raises(TokenExpiredException, match="Magic link has expired"):
            user.verify_magic_link_token(token, expire_minutes=15)
    
    def test_verify_magic_link_token_fails_when_no_token_exists(self):
        """Test verifying when no token exists raises exception"""
        user = UserFactory.build()
        
        with pytest.raises(InvalidTokenException):
            user.verify_magic_link_token("any-token")
    
    def test_clear_magic_link_token_removes_token(self):
        """Test clearing magic link token"""
        user = UserFactory.build()
        user.generate_magic_link_token()
        
        user.clear_magic_link_token()
        
        assert user.magic_link_token is None
        assert user.magic_link_sent_at is None


@pytest.mark.unit
class TestPasswordEncapsulation:
    """Test password hash encapsulation"""
    
    def test_password_hash_property_is_readonly(self):
        """Test password_hash property returns value"""
        user = UserFactory.build()
        assert user.password_hash is not None
        assert len(user.password_hash) > 0
    
    def test_change_password_hash_updates_hash(self):
        """Test changing password hash"""
        user = UserFactory.build()
        old_hash = user.password_hash
        
        new_hash = "new_hashed_password_value"
        user.change_password_hash(new_hash)
        
        assert user.password_hash == new_hash
        assert user.password_hash != old_hash
    
    def test_change_password_hash_with_empty_string_raises_exception(self):
        """Test changing password hash to empty string raises exception"""
        user = UserFactory.build()
        
        with pytest.raises(MissingRequiredFieldException, match="password_hash"):
            user.change_password_hash("")

