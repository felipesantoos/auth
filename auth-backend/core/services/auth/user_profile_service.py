"""
User Profile Service
Self-service profile management
"""
import logging
from typing import Optional
import bcrypt
from core.interfaces.secondary.app_user_repository_interface import IAppUserRepository
from core.domain.auth.app_user import AppUser
from infra.email.email_service import EmailService
from core.interfaces.secondary.settings_provider_interface import ISettingsProvider

logger = logging.getLogger(__name__)


class UserProfileService:
    """Service for user profile self-service management"""
    
    def __init__(
        self,
        user_repository: IAppUserRepository,
        email_service: EmailService,
        settings_provider: ISettingsProvider
    ):
        self.user_repository = user_repository
        self.email_service = email_service
        self.settings = settings_provider.get_settings()
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    
    async def update_profile(
        self,
        user_id: str,
        client_id: str,
        name: Optional[str] = None,
        username: Optional[str] = None
    ) -> AppUser:
        """
        Update user profile (name, username).
        
        Args:
            user_id: User ID
            client_id: Client ID (for multi-tenancy)
            name: New name (optional)
            username: New username (optional)
            
        Returns:
            Updated user
            
        Raises:
            ValueError: If username is taken or validation fails
        """
        user = await self.user_repository.find_by_id(user_id)
        if not user or user.client_id != client_id:
            raise ValueError("User not found")
        
        # Update name
        if name:
            user.name = name
        
        # Update username (check uniqueness)
        if username:
            existing = await self.user_repository.find_by_username(username, client_id)
            if existing and existing.id != user_id:
                raise ValueError("Username already taken")
            user.username = username
        
        # Validate
        user.validate()
        
        # Save
        updated = await self.user_repository.save(user)
        logger.info(f"Profile updated for user {user_id}")
        
        return updated
    
    async def request_email_change(
        self,
        user_id: str,
        new_email: str,
        password: str
    ) -> str:
        """
        Request email change (sends verification to new email).
        
        Args:
            user_id: User ID
            new_email: New email address
            password: Current password for confirmation
            
        Returns:
            Confirmation message
            
        Raises:
            ValueError: If password incorrect or email taken
        """
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Verify password
        if not self._verify_password(password, user.password_hash):
            raise ValueError("Incorrect password")
        
        # Check if email is taken
        existing = await self.user_repository.find_by_email(new_email)
        if existing:
            raise ValueError("Email already in use")
        
        # TODO: Implement proper email change verification flow
        # For now, we'll just send a notification
        try:
            await self.email_service.send_email(
                to_email=new_email,
                subject="Email Change Request",
                html_content=f"""
                <html>
                <body>
                    <h1>Email Change Request</h1>
                    <p>A request was made to change your email address to {new_email}.</p>
                    <p>Email verification flow will be implemented in a future update.</p>
                </body>
                </html>
                """
            )
        except Exception as e:
            logger.error(f"Failed to send email change notification: {e}")
        
        logger.info(f"Email change requested for user {user_id} to {new_email}")
        
        return "Email change request received. Verification flow will be implemented soon."
    
    async def delete_account(
        self,
        user_id: str,
        password: str
    ) -> bool:
        """
        Delete account (soft delete - deactivate).
        
        Requires password confirmation for security.
        
        Args:
            user_id: User ID
            password: Current password for confirmation
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If password incorrect
        """
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Verify password
        if not self._verify_password(password, user.password_hash):
            raise ValueError("Incorrect password")
        
        # Soft delete (deactivate)
        user.deactivate()
        await self.user_repository.save(user)
        
        # TODO: Revoke all tokens, sessions, API keys
        # This should be implemented in a future update
        
        logger.info(f"Account deleted (deactivated) for user {user_id}")
        return True

