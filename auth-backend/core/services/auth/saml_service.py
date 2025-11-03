"""
SAML Service Implementation
Handles SAML 2.0 Single Sign-On integration
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from core.domain.auth.app_user import AppUser
# REMOVED: from core.domain.auth.user_role import UserRole (roles now in WorkspaceMember)
from core.interfaces.secondary.app_user_repository_interface import IAppUserRepository
from core.interfaces.secondary.settings_provider_interface import ISettingsProvider
from core.exceptions import (
    BusinessRuleException,
    ValidationException,
    UserNotFoundException,
)

logger = logging.getLogger(__name__)


class SAMLService:
    """
    Service for SAML 2.0 Single Sign-On (multi-workspace architecture).
    
    Allows users to authenticate using enterprise identity providers (IdP)
    such as Okta, Azure AD, Google Workspace, etc.
    
    Note: This is a simplified implementation. For production,
    use python3-saml library with proper configuration.
    """
    
    def __init__(
        self,
        user_repository: IAppUserRepository,
        settings_provider: ISettingsProvider,
        workspace_service=None,
        workspace_member_service=None,
    ):
        self.user_repository = user_repository
        self.settings = settings_provider.get_settings()
        self.workspace_service = workspace_service
        self.workspace_member_service = workspace_member_service
    
    def is_enabled(self) -> bool:
        """Check if SAML is enabled"""
        return self.settings.saml_enabled
    
    def get_login_url(self, client_id: str, relay_state: Optional[str] = None) -> str:
        """
        Get SAML login URL (redirect to IdP).
        
        Args:
            client_id: Client ID
            relay_state: Optional relay state (return URL)
            
        Returns:
            IdP login URL
        """
        if not self.is_enabled():
            raise BusinessRuleException(
                "SAML SSO is not enabled",
                "SAML_NOT_ENABLED"
            )
        
        try:
            # In production, use OneLogin SAML library:
            # from onelogin.saml2.auth import OneLogin_Saml2_Auth
            # from onelogin.saml2.utils import OneLogin_Saml2_Utils
            
            # auth = OneLogin_Saml2_Auth(request_data, saml_settings)
            # return auth.login(return_to=relay_state)
            
            # Simplified implementation
            idp_url = self.settings.saml_idp_metadata_url or "https://idp.example.com/saml/login"
            sp_acs_url = f"{self.settings.api_base_url}/auth/saml/acs"
            
            # Construct SAML request
            login_url = f"{idp_url}?SAMLRequest=...&RelayState={relay_state or ''}"
            
            logger.info(f"SAML login initiated for client {client_id}")
            return login_url
            
        except Exception as e:
            logger.error(f"Error getting SAML login URL: {e}", exc_info=True)
            raise BusinessRuleException(
                "Failed to initiate SAML login",
                "SAML_LOGIN_FAILED"
            )
    
    async def process_saml_response(
        self,
        saml_response: str,
        client_id: str
    ) -> AppUser:
        """
        Process SAML response from IdP (Assertion Consumer Service).
        
        Args:
            saml_response: SAML response (base64 encoded)
            client_id: Client ID
            
        Returns:
            Authenticated user (created if doesn't exist)
        """
        if not self.is_enabled():
            raise BusinessRuleException(
                "SAML SSO is not enabled",
                "SAML_NOT_ENABLED"
            )
        
        try:
            # In production, use OneLogin SAML library:
            # from onelogin.saml2.auth import OneLogin_Saml2_Auth
            
            # auth = OneLogin_Saml2_Auth(request_data, saml_settings)
            # auth.process_response()
            # errors = auth.get_errors()
            # if errors:
            #     raise ValidationException(f"SAML errors: {errors}")
            
            # attributes = auth.get_attributes()
            # email = attributes.get('email')[0]
            # name = attributes.get('name')[0]
            # username = attributes.get('username')[0] or email.split('@')[0]
            
            # Simplified implementation (placeholder)
            # In production, extract from SAML assertion
            email = "user@company.com"  # Extract from SAML
            name = "SAML User"  # Extract from SAML
            username = email.split('@')[0]
            
            # Find or create user
            user = await self.user_repository.find_by_email(email, client_id=client_id)
            
            if not user:
                # Auto-provision user from SAML attributes
                # Note: SAML users don't use local passwords - they authenticate via IdP
                # We create a random password hash to satisfy the domain model
                import secrets
                import bcrypt
                
                random_password = secrets.token_urlsafe(32)
                password_hash = bcrypt.hashpw(
                    random_password.encode('utf-8'),
                    bcrypt.gensalt(rounds=12)
                ).decode('utf-8')
                
                user = AppUser(
                    id=None,
                    username=username,
                    email=email,
                    name=name,
                    role=UserRole.USER,
                    client_id=client_id,
                    active=True,
                    email_verified=True,  # Auto-verified for SAML users
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    _password_hash=password_hash
                )
                
                user.validate()
                user = await self.user_repository.save(user)
                
                logger.info(f"SAML user auto-provisioned: {email}")
            
            logger.info(f"SAML authentication successful for {email}")
            return user
            
        except (BusinessRuleException, ValidationException):
            raise
        except Exception as e:
            logger.error(f"Error processing SAML response: {e}", exc_info=True)
            raise BusinessRuleException(
                "Failed to process SAML response",
                "SAML_RESPONSE_INVALID"
            )
    
    def get_metadata(self) -> str:
        """
        Get SAML SP metadata XML.
        
        Returns:
            SP metadata XML string
        """
        if not self.is_enabled():
            raise BusinessRuleException(
                "SAML SSO is not enabled",
                "SAML_NOT_ENABLED"
            )
        
        try:
            # In production, use OneLogin SAML library:
            # from onelogin.saml2.settings import OneLogin_Saml2_Settings
            # settings = OneLogin_Saml2_Settings(saml_settings)
            # metadata = settings.get_sp_metadata()
            
            # Simplified metadata
            entity_id = self.settings.saml_entity_id or f"{self.settings.api_base_url}/saml/metadata"
            acs_url = f"{self.settings.api_base_url}/auth/saml/acs"
            
            metadata_xml = f"""<?xml version="1.0"?>
<EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata" entityID="{entity_id}">
  <SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <AssertionConsumerService 
      Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST" 
      Location="{acs_url}" 
      index="0"/>
  </SPSSODescriptor>
</EntityDescriptor>
"""
            
            logger.info("SAML metadata requested")
            return metadata_xml
            
        except Exception as e:
            logger.error(f"Error getting SAML metadata: {e}", exc_info=True)
            raise BusinessRuleException(
                "Failed to generate SAML metadata",
                "SAML_METADATA_FAILED"
            )

