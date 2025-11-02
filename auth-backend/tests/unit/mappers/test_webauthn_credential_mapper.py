"""
Unit tests for WebAuthnCredentialMapper
Tests conversion between database model and domain model
"""
import pytest
from datetime import datetime
from infra.database.mappers.webauthn_credential_mapper import WebAuthnCredentialMapper
from core.domain.auth.webauthn_credential import WebAuthnCredential
from infra.database.models.webauthn_credential import DBWebAuthnCredential


@pytest.mark.unit
class TestWebAuthnCredentialMapperToDomain:
    """Test converting DB model to domain model"""
    
    def test_to_domain_maps_all_fields(self):
        """Test to_domain maps all fields correctly"""
        db_credential = DBWebAuthnCredential(
            id="cred-123",
            user_id="user-123",
            client_id="client-123",
            credential_id="webauthn-credential-id",
            public_key="base64_encoded_public_key",
            counter=5,
            aaguid="00000000-0000-0000-0000-000000000000",
            device_name="YubiKey 5",
            created_at=datetime(2023, 1, 1),
            last_used_at=datetime(2023, 6, 1),
            revoked_at=None
        )
        
        domain_credential = WebAuthnCredentialMapper.to_domain(db_credential)
        
        assert isinstance(domain_credential, WebAuthnCredential)
        assert domain_credential.id == "cred-123"
        assert domain_credential.user_id == "user-123"
        assert domain_credential.client_id == "client-123"
        assert domain_credential.credential_id == "webauthn-credential-id"
        assert domain_credential.public_key == "base64_encoded_public_key"
        assert domain_credential.counter == 5
        assert domain_credential.aaguid == "00000000-0000-0000-0000-000000000000"
        assert domain_credential.device_name == "YubiKey 5"
    
    def test_to_domain_with_revoked_credential(self):
        """Test converting revoked credential"""
        db_credential = DBWebAuthnCredential(
            id="cred-123",
            user_id="user-123",
            client_id="client-123",
            credential_id="cred-id",
            public_key="public-key",
            counter=10,
            revoked_at=datetime.utcnow()
        )
        
        domain_credential = WebAuthnCredentialMapper.to_domain(db_credential)
        
        assert domain_credential.revoked_at is not None
        assert domain_credential.is_revoked() is True


@pytest.mark.unit
class TestWebAuthnCredentialMapperToDatabase:
    """Test converting domain model to DB model"""
    
    def test_to_database_maps_all_fields(self):
        """Test to_database maps all fields correctly"""
        domain_credential = WebAuthnCredential(
            id="cred-123",
            user_id="user-123",
            client_id="client-123",
            credential_id="webauthn-cred-id",
            public_key="encoded_public_key",
            counter=3,
            aaguid="test-aaguid",
            device_name="Touch ID",
            created_at=datetime(2023, 1, 1),
            last_used_at=datetime(2023, 5, 1)
        )
        
        db_credential = WebAuthnCredentialMapper.to_database(domain_credential)
        
        assert isinstance(db_credential, DBWebAuthnCredential)
        assert db_credential.id == "cred-123"
        assert db_credential.user_id == "user-123"
        assert db_credential.credential_id == "webauthn-cred-id"
        assert db_credential.public_key == "encoded_public_key"
        assert db_credential.counter == 3
        assert db_credential.device_name == "Touch ID"
    
    def test_to_database_preserves_counter(self):
        """Test counter value is preserved correctly"""
        domain_credential = WebAuthnCredential(
            id="cred-123",
            user_id="user-123",
            client_id="client-123",
            credential_id="cred-id",
            public_key="key",
            counter=42  # Specific counter value
        )
        
        db_credential = WebAuthnCredentialMapper.to_database(domain_credential)
        
        assert db_credential.counter == 42

