"""WebAuthnCredential Mapper - Converts between DB model and domain"""
from core.domain.auth.webauthn_credential import WebAuthnCredential
from infra.database.models.webauthn_credential import DBWebAuthnCredential


class WebAuthnCredentialMapper:
    """Mapper for WebAuthnCredential entity"""
    
    @staticmethod
    def to_domain(db_cred: DBWebAuthnCredential) -> WebAuthnCredential:
        """Converts DB model to domain"""
        return WebAuthnCredential(
            id=db_cred.id,
            user_id=db_cred.user_id,
            client_id=db_cred.client_id,
            credential_id=db_cred.credential_id,
            public_key=db_cred.public_key,
            counter=db_cred.counter,
            aaguid=db_cred.aaguid,
            device_name=db_cred.device_name,
            created_at=db_cred.created_at,
            last_used_at=db_cred.last_used_at,
            revoked_at=db_cred.revoked_at,
        )
    
    @staticmethod
    def to_database(cred: WebAuthnCredential, db_cred: DBWebAuthnCredential = None) -> DBWebAuthnCredential:
        """Converts domain to DB model"""
        if db_cred is None:
            db_cred = DBWebAuthnCredential()
        
        db_cred.id = cred.id
        db_cred.user_id = cred.user_id
        db_cred.client_id = cred.client_id
        db_cred.credential_id = cred.credential_id
        db_cred.public_key = cred.public_key
        db_cred.counter = cred.counter
        db_cred.aaguid = cred.aaguid
        db_cred.device_name = cred.device_name
        db_cred.created_at = cred.created_at
        db_cred.last_used_at = cred.last_used_at
        db_cred.revoked_at = cred.revoked_at
        
        return db_cred

