"""
WebAuthn Service Implementation
Handles biometric authentication (Passkeys, Face ID, Touch ID, Windows Hello)
"""
import logging
import base64
import json
from typing import Optional, Tuple, Dict, Any, List
from datetime import datetime
import uuid

from core.domain.auth.webauthn_credential import WebAuthnCredential
from core.domain.auth.app_user import AppUser
from core.interfaces.secondary.app_user_repository_interface import IAppUserRepository
from infra.database.repositories.webauthn_credential_repository import WebAuthnCredentialRepository
from core.interfaces.secondary.settings_provider_interface import ISettingsProvider
from core.exceptions import (
    BusinessRuleException,
    ValidationException,
    UserNotFoundException,
)

logger = logging.getLogger(__name__)


class WebAuthnService:
    """
    Service for WebAuthn/Passkey authentication.
    
    WebAuthn enables passwordless authentication using:
    - Biometrics (Face ID, Touch ID, fingerprint)
    - Security keys (YubiKey, etc.)
    - Platform authenticators (Windows Hello, etc.)
    
    Note: This is a simplified implementation. For production, use the webauthn library.
    """
    
    def __init__(
        self,
        user_repository: IAppUserRepository,
        credential_repository: WebAuthnCredentialRepository,
        settings_provider: ISettingsProvider,
    ):
        self.user_repository = user_repository
        self.credential_repository = credential_repository
        self.settings = settings_provider.get_settings()
    
    async def register_begin(
        self,
        user_id: str,
        client_id: str
    ) -> Dict[str, Any]:
        """
        Begin WebAuthn registration (create challenge).
        
        Args:
            user_id: User ID
            client_id: Client ID
            
        Returns:
            Registration options for client (publicKey)
        """
        try:
            user = await self.user_repository.find_by_id(user_id, client_id=client_id)
            if not user:
                raise UserNotFoundException(user_id=user_id)
            
            # Generate challenge (random bytes)
            import secrets
            challenge = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')
            
            # WebAuthn registration options
            # In production, use webauthn library for proper implementation
            registration_options = {
                "challenge": challenge,
                "rp": {
                    "name": self.settings.webauthn_rp_name,
                    "id": self.settings.webauthn_rp_id,
                },
                "user": {
                    "id": base64.urlsafe_b64encode(user.id.encode()).decode('utf-8'),
                    "name": user.email,
                    "displayName": user.name,
                },
                "pubKeyCredParams": [
                    {"type": "public-key", "alg": -7},  # ES256
                    {"type": "public-key", "alg": -257},  # RS256
                ],
                "timeout": 60000,  # 60 seconds
                "attestation": "direct",
                "authenticatorSelection": {
                    "authenticatorAttachment": "platform",  # or "cross-platform"
                    "userVerification": "required",
                },
            }
            
            # Store challenge in cache for verification
            # TODO: Store challenge in Redis with TTL
            
            logger.info(f"WebAuthn registration begin for user {user_id}")
            return registration_options
            
        except UserNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error beginning WebAuthn registration: {e}", exc_info=True)
            raise BusinessRuleException(
                "Failed to begin WebAuthn registration",
                "WEBAUTHN_REGISTRATION_FAILED"
            )
    
    async def register_complete(
        self,
        user_id: str,
        client_id: str,
        credential_id: str,
        public_key: str,
        device_name: Optional[str] = None
    ) -> WebAuthnCredential:
        """
        Complete WebAuthn registration (store credential).
        
        Args:
            user_id: User ID
            client_id: Client ID
            credential_id: WebAuthn credential ID
            public_key: Public key (base64 encoded)
            device_name: Optional friendly device name
            
        Returns:
            Created WebAuthnCredential
        """
        try:
            user = await self.user_repository.find_by_id(user_id, client_id=client_id)
            if not user:
                raise UserNotFoundException(user_id=user_id)
            
            # Check if credential already exists
            existing = await self.credential_repository.find_by_credential_id(credential_id)
            if existing:
                raise BusinessRuleException(
                    "Credential already registered",
                    "WEBAUTHN_CREDENTIAL_EXISTS"
                )
            
            # Create credential
            credential = WebAuthnCredential(
                id=str(uuid.uuid4()),
                user_id=user_id,
                client_id=client_id,
                credential_id=credential_id,
                public_key=public_key,
                counter=0,
                aaguid=None,  # TODO: Extract from attestation
                device_name=device_name,
                created_at=datetime.utcnow(),
                last_used_at=None,
                revoked_at=None
            )
            
            credential.validate()
            saved_credential = await self.credential_repository.save(credential)
            
            logger.info(f"WebAuthn credential registered for user {user_id}")
            return saved_credential
            
        except (UserNotFoundException, BusinessRuleException):
            raise
        except Exception as e:
            logger.error(f"Error completing WebAuthn registration: {e}", exc_info=True)
            raise BusinessRuleException(
                "Failed to complete WebAuthn registration",
                "WEBAUTHN_REGISTRATION_FAILED"
            )
    
    async def authenticate_begin(
        self,
        user_id: str,
        client_id: str
    ) -> Dict[str, Any]:
        """
        Begin WebAuthn authentication (create challenge).
        
        Args:
            user_id: User ID
            client_id: Client ID
            
        Returns:
            Authentication options for client
        """
        try:
            user = await self.user_repository.find_by_id(user_id, client_id=client_id)
            if not user:
                raise UserNotFoundException(user_id=user_id)
            
            # Get user's credentials
            credentials = await self.credential_repository.find_active_by_user(user_id, client_id)
            if not credentials:
                raise BusinessRuleException(
                    "No WebAuthn credentials registered",
                    "NO_WEBAUTHN_CREDENTIALS"
                )
            
            # Generate challenge
            import secrets
            challenge = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')
            
            # Authentication options
            authentication_options = {
                "challenge": challenge,
                "timeout": 60000,
                "rpId": self.settings.webauthn_rp_id,
                "allowCredentials": [
                    {
                        "type": "public-key",
                        "id": cred.credential_id,
                    }
                    for cred in credentials
                ],
                "userVerification": "required",
            }
            
            # Store challenge in cache
            # TODO: Store in Redis with TTL
            
            logger.info(f"WebAuthn authentication begin for user {user_id}")
            return authentication_options
            
        except (UserNotFoundException, BusinessRuleException):
            raise
        except Exception as e:
            logger.error(f"Error beginning WebAuthn authentication: {e}", exc_info=True)
            raise BusinessRuleException(
                "Failed to begin WebAuthn authentication",
                "WEBAUTHN_AUTHENTICATION_FAILED"
            )
    
    async def authenticate_complete(
        self,
        user_id: str,
        client_id: str,
        credential_id: str,
        authenticator_data: str,
        signature: str,
        client_data_json: str
    ) -> AppUser:
        """
        Complete WebAuthn authentication (verify signature).
        
        Args:
            user_id: User ID
            client_id: Client ID
            credential_id: Credential ID used
            authenticator_data: Authenticator data (base64)
            signature: Signature (base64)
            client_data_json: Client data JSON (base64)
            
        Returns:
            Authenticated user
            
        Note: This is simplified. In production, use webauthn library for proper verification.
        """
        try:
            user = await self.user_repository.find_by_id(user_id, client_id=client_id)
            if not user:
                raise UserNotFoundException(user_id=user_id)
            
            # Get credential
            credential = await self.credential_repository.find_by_credential_id(credential_id)
            if not credential or not credential.is_active():
                raise BusinessRuleException(
                    "Credential not found or revoked",
                    "WEBAUTHN_CREDENTIAL_INVALID"
                )
            
            # Verify credential belongs to user
            if credential.user_id != user_id or credential.client_id != client_id:
                raise BusinessRuleException(
                    "Credential does not belong to user",
                    "WEBAUTHN_CREDENTIAL_MISMATCH"
                )
            
            # TODO: Verify signature using public key
            # In production, use webauthn library:
            # from webauthn import verify_authentication_response
            # verification = verify_authentication_response(...)
            
            # Update credential
            credential.update_last_used()
            # credential.increment_counter()  # Update based on authenticator data
            await self.credential_repository.save(credential)
            
            logger.info(f"WebAuthn authentication success for user {user_id}")
            return user
            
        except (UserNotFoundException, BusinessRuleException):
            raise
        except Exception as e:
            logger.error(f"Error completing WebAuthn authentication: {e}", exc_info=True)
            raise BusinessRuleException(
                "Failed to complete WebAuthn authentication",
                "WEBAUTHN_AUTHENTICATION_FAILED"
            )
    
    async def list_credentials(
        self,
        user_id: str,
        client_id: str
    ) -> List[WebAuthnCredential]:
        """List all WebAuthn credentials for user"""
        try:
            return await self.credential_repository.find_by_user(user_id, client_id)
        except Exception as e:
            logger.error(f"Error listing WebAuthn credentials: {e}", exc_info=True)
            return []
    
    async def revoke_credential(
        self,
        credential_id: str,
        user_id: str,
        client_id: str
    ) -> bool:
        """Revoke a WebAuthn credential"""
        try:
            credential = await self.credential_repository.find_by_id(credential_id)
            
            if not credential:
                return False
            
            # Authorization check
            if credential.user_id != user_id or credential.client_id != client_id:
                logger.warning(f"Unauthorized credential revoke attempt: {credential_id}")
                return False
            
            if credential.is_revoked():
                return True
            
            credential.revoke()
            await self.credential_repository.save(credential)
            
            logger.info(f"WebAuthn credential revoked: {credential_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking WebAuthn credential: {e}", exc_info=True)
            return False

