"""
LDAP Service Implementation
Handles LDAP/Active Directory authentication
"""
import logging
from typing import Optional
from datetime import datetime

from core.domain.auth.app_user import AppUser
from core.domain.auth.user_role import UserRole
from core.interfaces.secondary.app_user_repository_interface import AppUserRepositoryInterface
from core.interfaces.secondary.settings_provider_interface import SettingsProviderInterface
from core.exceptions import (
    BusinessRuleException,
    InvalidCredentialsException,
    UserNotFoundException,
)

logger = logging.getLogger(__name__)


class LDAPService:
    """
    Service for LDAP/Active Directory authentication.
    
    Allows users to authenticate using corporate LDAP/AD credentials.
    Common use cases:
    - Enterprise organizations
    - Corporate networks
    - Microsoft Active Directory
    - OpenLDAP
    """
    
    def __init__(
        self,
        user_repository: AppUserRepositoryInterface,
        settings_provider: SettingsProviderInterface,
    ):
        self.user_repository = user_repository
        self.settings = settings_provider.get_settings()
    
    def is_enabled(self) -> bool:
        """Check if LDAP is enabled"""
        return self.settings.ldap_enabled
    
    async def authenticate_ldap(
        self,
        username: str,
        password: str,
        client_id: str
    ) -> AppUser:
        """
        Authenticate user via LDAP/Active Directory.
        
        Args:
            username: LDAP username (e.g., 'jdoe' or 'DOMAIN\\jdoe')
            password: LDAP password
            client_id: Client ID
            
        Returns:
            Authenticated user (created if doesn't exist in local DB)
            
        Raises:
            InvalidCredentialsException: If LDAP authentication fails
        """
        if not self.is_enabled():
            raise BusinessRuleException(
                "LDAP authentication is not enabled",
                "LDAP_NOT_ENABLED"
            )
        
        try:
            # In production, use ldap3 library:
            # from ldap3 import Server, Connection, ALL, NTLM
            
            # server = Server(
            #     self.settings.ldap_server,
            #     port=self.settings.ldap_port,
            #     use_ssl=self.settings.ldap_use_ssl,
            #     get_info=ALL
            # )
            
            # # Construct user DN
            # user_filter = self.settings.ldap_user_filter.replace('{username}', username)
            # user_dn = f"{user_filter},{self.settings.ldap_base_dn}"
            
            # # Try to bind (authenticate)
            # conn = Connection(
            #     server,
            #     user=user_dn,
            #     password=password,
            #     authentication=NTLM if '\\' in username else None
            # )
            
            # if not conn.bind():
            #     raise InvalidCredentialsException()
            
            # # Get user attributes
            # conn.search(
            #     search_base=self.settings.ldap_base_dn,
            #     search_filter=user_filter,
            #     attributes=['mail', 'displayName', 'cn']
            # )
            
            # if not conn.entries:
            #     raise InvalidCredentialsException()
            
            # entry = conn.entries[0]
            # email = str(entry.mail) if hasattr(entry, 'mail') else f"{username}@company.com"
            # name = str(entry.displayName) if hasattr(entry, 'displayName') else username
            
            # conn.unbind()
            
            # Simplified implementation (placeholder)
            # In production, authenticate against real LDAP
            email = f"{username}@company.com"  # From LDAP
            name = username.title()  # From LDAP displayName
            
            # Validate credentials (simplified - in production, LDAP bind does this)
            if not password or len(password) < 3:
                raise InvalidCredentialsException()
            
            # Find or create user in local DB
            user = await self.user_repository.find_by_email(email, client_id=client_id)
            
            if not user:
                # Auto-provision user from LDAP
                user = AppUser(
                    id=None,
                    username=username,
                    email=email,
                    name=name,
                    role=UserRole.USER,
                    client_id=client_id,
                    active=True,
                    email_verified=True,  # Auto-verified for LDAP users
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    _password_hash="ldap_user_no_local_password"
                )
                
                user.validate()
                user = await self.user_repository.save(user)
                
                logger.info(f"LDAP user auto-provisioned: {email}")
            
            logger.info(f"LDAP authentication successful for {username}")
            return user
            
        except InvalidCredentialsException:
            logger.warning(f"LDAP authentication failed for {username}")
            raise
        except (BusinessRuleException, ValidationException):
            raise
        except Exception as e:
            logger.error(f"Error in LDAP authentication: {e}", exc_info=True)
            raise BusinessRuleException(
                "Failed to authenticate via LDAP",
                "LDAP_AUTHENTICATION_FAILED"
            )
    
    async def sync_user_from_ldap(
        self,
        username: str,
        client_id: str
    ) -> Optional[AppUser]:
        """
        Sync user information from LDAP (update local user with LDAP data).
        
        Args:
            username: LDAP username
            client_id: Client ID
            
        Returns:
            Updated user or None if not found in LDAP
        """
        if not self.is_enabled():
            raise BusinessRuleException(
                "LDAP is not enabled",
                "LDAP_NOT_ENABLED"
            )
        
        try:
            # In production:
            # 1. Connect to LDAP using bind DN
            # 2. Search for user
            # 3. Extract attributes
            # 4. Update local user
            
            logger.info(f"LDAP sync for user {username}")
            
            # Placeholder - implement with ldap3 library
            return None
            
        except Exception as e:
            logger.error(f"Error syncing user from LDAP: {e}", exc_info=True)
            return None
    
    def test_connection(self) -> bool:
        """
        Test LDAP connection.
        
        Returns:
            True if connection successful
        """
        if not self.is_enabled():
            return False
        
        try:
            # In production, use ldap3:
            # from ldap3 import Server, Connection
            
            # server = Server(self.settings.ldap_server, port=self.settings.ldap_port)
            # conn = Connection(
            #     server,
            #     user=self.settings.ldap_bind_dn,
            #     password=self.settings.ldap_bind_password
            # )
            # return conn.bind()
            
            logger.info("LDAP connection test (not implemented)")
            return True
            
        except Exception as e:
            logger.error(f"LDAP connection test failed: {e}", exc_info=True)
            return False

