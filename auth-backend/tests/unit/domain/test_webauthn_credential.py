"""
Unit tests for WebAuthnCredential domain model
Tests domain logic without external dependencies
"""
import pytest
from datetime import datetime
from core.domain.auth.webauthn_credential import WebAuthnCredential
from core.exceptions import MissingRequiredFieldException, BusinessRuleException


@pytest.mark.unit
class TestWebAuthnCredentialValidation:
    """Test WebAuthn credential validation"""
    
    def test_valid_credential_passes_validation(self):
        """Test that a valid credential passes validation"""
        credential = WebAuthnCredential(
            id="cred-123",
            user_id="user-123",
            client_id="client-123",
            credential_id="webauthn-cred-123",
            public_key="base64_encoded_public_key"
        )
        
        # Should not raise
        credential.validate()
    
    def test_missing_user_id_raises_exception(self):
        """Test that missing user_id raises exception"""
        credential = WebAuthnCredential(
            id="cred-123",
            user_id="",
            client_id="client-123",
            credential_id="webauthn-cred-123",
            public_key="base64_encoded_public_key"
        )
        
        with pytest.raises(MissingRequiredFieldException, match="user_id"):
            credential.validate()
    
    def test_missing_client_id_raises_exception(self):
        """Test that missing client_id raises exception"""
        credential = WebAuthnCredential(
            id="cred-123",
            user_id="user-123",
            client_id="",
            credential_id="webauthn-cred-123",
            public_key="base64_encoded_public_key"
        )
        
        with pytest.raises(MissingRequiredFieldException, match="client_id"):
            credential.validate()
    
    def test_missing_credential_id_raises_exception(self):
        """Test that missing credential_id raises exception"""
        credential = WebAuthnCredential(
            id="cred-123",
            user_id="user-123",
            client_id="client-123",
            credential_id="",
            public_key="base64_encoded_public_key"
        )
        
        with pytest.raises(MissingRequiredFieldException, match="credential_id"):
            credential.validate()
    
    def test_missing_public_key_raises_exception(self):
        """Test that missing public_key raises exception"""
        credential = WebAuthnCredential(
            id="cred-123",
            user_id="user-123",
            client_id="client-123",
            credential_id="webauthn-cred-123",
            public_key=""
        )
        
        with pytest.raises(MissingRequiredFieldException, match="public_key"):
            credential.validate()


@pytest.mark.unit
class TestWebAuthnCredentialStatus:
    """Test credential status checks"""
    
    def test_is_active_returns_true_for_active_credential(self):
        """Test is_active returns True for active credential"""
        credential = WebAuthnCredential(
            id="cred-123",
            user_id="user-123",
            client_id="client-123",
            credential_id="webauthn-cred-123",
            public_key="base64_encoded_public_key"
        )
        
        assert credential.is_active() is True
    
    def test_is_active_returns_false_for_revoked_credential(self):
        """Test is_active returns False for revoked credential"""
        credential = WebAuthnCredential(
            id="cred-123",
            user_id="user-123",
            client_id="client-123",
            credential_id="webauthn-cred-123",
            public_key="base64_encoded_public_key",
            revoked_at=datetime.utcnow()
        )
        
        assert credential.is_active() is False
    
    def test_is_revoked_returns_true_for_revoked_credential(self):
        """Test is_revoked returns True for revoked credential"""
        credential = WebAuthnCredential(
            id="cred-123",
            user_id="user-123",
            client_id="client-123",
            credential_id="webauthn-cred-123",
            public_key="base64_encoded_public_key",
            revoked_at=datetime.utcnow()
        )
        
        assert credential.is_revoked() is True
    
    def test_is_revoked_returns_false_for_active_credential(self):
        """Test is_revoked returns False for active credential"""
        credential = WebAuthnCredential(
            id="cred-123",
            user_id="user-123",
            client_id="client-123",
            credential_id="webauthn-cred-123",
            public_key="base64_encoded_public_key"
        )
        
        assert credential.is_revoked() is False


@pytest.mark.unit
class TestWebAuthnCredentialRevocation:
    """Test credential revocation"""
    
    def test_revoke_sets_revoked_at(self):
        """Test revoke sets revoked_at timestamp"""
        credential = WebAuthnCredential(
            id="cred-123",
            user_id="user-123",
            client_id="client-123",
            credential_id="webauthn-cred-123",
            public_key="base64_encoded_public_key"
        )
        
        credential.revoke()
        
        assert credential.revoked_at is not None
        assert isinstance(credential.revoked_at, datetime)
    
    def test_revoke_raises_exception_if_already_revoked(self):
        """Test revoke raises exception if credential already revoked"""
        credential = WebAuthnCredential(
            id="cred-123",
            user_id="user-123",
            client_id="client-123",
            credential_id="webauthn-cred-123",
            public_key="base64_encoded_public_key",
            revoked_at=datetime.utcnow()
        )
        
        with pytest.raises(BusinessRuleException, match="already been revoked"):
            credential.revoke()


@pytest.mark.unit
class TestWebAuthnCredentialLastUsed:
    """Test last used tracking"""
    
    def test_update_last_used_sets_timestamp(self):
        """Test update_last_used sets last_used_at timestamp"""
        credential = WebAuthnCredential(
            id="cred-123",
            user_id="user-123",
            client_id="client-123",
            credential_id="webauthn-cred-123",
            public_key="base64_encoded_public_key"
        )
        
        credential.update_last_used()
        
        assert credential.last_used_at is not None
        assert isinstance(credential.last_used_at, datetime)


@pytest.mark.unit
class TestWebAuthnCredentialCounter:
    """Test sign counter methods for replay attack prevention"""
    
    def test_increment_counter_increases_by_one(self):
        """Test increment_counter increases counter by 1"""
        credential = WebAuthnCredential(
            id="cred-123",
            user_id="user-123",
            client_id="client-123",
            credential_id="webauthn-cred-123",
            public_key="base64_encoded_public_key",
            counter=5
        )
        
        credential.increment_counter()
        
        assert credential.counter == 6
    
    def test_verify_counter_returns_true_for_greater_counter(self):
        """Test verify_counter returns True for greater counter"""
        credential = WebAuthnCredential(
            id="cred-123",
            user_id="user-123",
            client_id="client-123",
            credential_id="webauthn-cred-123",
            public_key="base64_encoded_public_key",
            counter=5
        )
        
        result = credential.verify_counter(10)
        
        assert result is True
    
    def test_verify_counter_returns_false_for_equal_counter(self):
        """Test verify_counter returns False for equal counter"""
        credential = WebAuthnCredential(
            id="cred-123",
            user_id="user-123",
            client_id="client-123",
            credential_id="webauthn-cred-123",
            public_key="base64_encoded_public_key",
            counter=5
        )
        
        result = credential.verify_counter(5)
        
        assert result is False
    
    def test_verify_counter_returns_false_for_smaller_counter(self):
        """Test verify_counter returns False for smaller counter (possible cloned authenticator)"""
        credential = WebAuthnCredential(
            id="cred-123",
            user_id="user-123",
            client_id="client-123",
            credential_id="webauthn-cred-123",
            public_key="base64_encoded_public_key",
            counter=10
        )
        
        result = credential.verify_counter(5)
        
        assert result is False
    
    def test_update_counter_succeeds_with_valid_counter(self):
        """Test update_counter succeeds with valid (greater) counter"""
        credential = WebAuthnCredential(
            id="cred-123",
            user_id="user-123",
            client_id="client-123",
            credential_id="webauthn-cred-123",
            public_key="base64_encoded_public_key",
            counter=5
        )
        
        credential.update_counter(10)
        
        assert credential.counter == 10
    
    def test_update_counter_raises_exception_with_invalid_counter(self):
        """Test update_counter raises exception with invalid (equal or smaller) counter"""
        credential = WebAuthnCredential(
            id="cred-123",
            user_id="user-123",
            client_id="client-123",
            credential_id="webauthn-cred-123",
            public_key="base64_encoded_public_key",
            counter=10
        )
        
        with pytest.raises(BusinessRuleException, match="Invalid counter value"):
            credential.update_counter(5)
    
    def test_update_counter_detects_cloned_authenticator(self):
        """Test update_counter detects possible cloned authenticator"""
        credential = WebAuthnCredential(
            id="cred-123",
            user_id="user-123",
            client_id="client-123",
            credential_id="webauthn-cred-123",
            public_key="base64_encoded_public_key",
            counter=10
        )
        
        with pytest.raises(BusinessRuleException, match="cloned authenticator"):
            credential.update_counter(10)


@pytest.mark.unit
class TestWebAuthnCredentialDeviceDescription:
    """Test device description"""
    
    def test_get_device_description_returns_device_name_if_set(self):
        """Test get_device_description returns device_name if set"""
        credential = WebAuthnCredential(
            id="cred-123",
            user_id="user-123",
            client_id="client-123",
            credential_id="webauthn-cred-123",
            public_key="base64_encoded_public_key",
            device_name="YubiKey 5"
        )
        
        description = credential.get_device_description()
        
        assert description == "YubiKey 5"
    
    def test_get_device_description_returns_security_key_if_no_name(self):
        """Test get_device_description returns Security Key if no name"""
        credential = WebAuthnCredential(
            id="cred-123",
            user_id="user-123",
            client_id="client-123",
            credential_id="webauthn-cred-123",
            public_key="base64_encoded_public_key"
        )
        
        description = credential.get_device_description()
        
        assert description == "Security Key"


@pytest.mark.unit
class TestWebAuthnCredentialOptionalFields:
    """Test optional credential fields"""
    
    def test_credential_can_have_aaguid(self):
        """Test credential can have aaguid"""
        credential = WebAuthnCredential(
            id="cred-123",
            user_id="user-123",
            client_id="client-123",
            credential_id="webauthn-cred-123",
            public_key="base64_encoded_public_key",
            aaguid="00000000-0000-0000-0000-000000000000"
        )
        
        assert credential.aaguid == "00000000-0000-0000-0000-000000000000"
    
    def test_credential_can_have_created_at(self):
        """Test credential can have created_at"""
        created = datetime.utcnow()
        credential = WebAuthnCredential(
            id="cred-123",
            user_id="user-123",
            client_id="client-123",
            credential_id="webauthn-cred-123",
            public_key="base64_encoded_public_key",
            created_at=created
        )
        
        assert credential.created_at == created
    
    def test_credential_counter_defaults_to_zero(self):
        """Test credential counter defaults to 0"""
        credential = WebAuthnCredential(
            id="cred-123",
            user_id="user-123",
            client_id="client-123",
            credential_id="webauthn-cred-123",
            public_key="base64_encoded_public_key"
        )
        
        assert credential.counter == 0

