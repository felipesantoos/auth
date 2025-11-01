"""
Passwordless Authentication Service Implementation
Handles magic link authentication (passwordless login via email)
"""
import logging
from typing import Tuple
from datetime import datetime

from core.domain.auth.app_user import AppUser
from core.interfaces.secondary.app_user_repository_interface import AppUserRepositoryInterface
from core.interfaces.secondary.email_service_interface import EmailServiceInterface
from core.interfaces.secondary.settings_provider_interface import SettingsProviderInterface
from core.exceptions import (
    BusinessRuleException,
    InvalidTokenException,
    TokenExpiredException,
    UserNotFoundException,
)

logger = logging.getLogger(__name__)


class PasswordlessService:
    """
    Service for passwordless authentication via magic links.
    
    Features:
    - Send magic link via email
    - Login with magic link token
    - Rate limiting on magic link requests
    """
    
    def __init__(
        self,
        user_repository: AppUserRepositoryInterface,
        email_service: EmailServiceInterface,
        settings_provider: SettingsProviderInterface,
    ):
        self.user_repository = user_repository
        self.email_service = email_service
        self.settings = settings_provider.get_settings()
    
    def _generate_magic_link_email_html(
        self,
        user_name: str,
        magic_link: str
    ) -> str:
        """Generate HTML email template for magic link"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Your Login Link</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #4a5568;">Sign in to {self.settings.app_name}</h2>
                
                <p>Hi {user_name},</p>
                
                <p>Click the button below to sign in to your account. No password needed!</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{magic_link}" 
                       style="background-color: #48bb78; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Sign In
                    </a>
                </div>
                
                <p style="color: #718096; font-size: 14px;">
                    Or copy and paste this link in your browser:<br>
                    <a href="{magic_link}" style="color: #4299e1;">{magic_link}</a>
                </p>
                
                <p style="color: #e53e3e; font-size: 14px; margin-top: 30px;">
                    ⚠️ This link will expire in {self.settings.magic_link_expire_minutes} minutes.
                </p>
                
                <p style="color: #718096; font-size: 14px;">
                    If you didn't request this link, please ignore this email. Your account is secure.
                </p>
                
                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">
                
                <p style="color: #a0aec0; font-size: 12px; text-align: center;">
                    © {datetime.utcnow().year} {self.settings.app_name}. All rights reserved.
                </p>
            </div>
        </body>
        </html>
        """
    
    async def send_magic_link(
        self,
        email: str,
        client_id: str
    ) -> bool:
        """
        Send magic link to user's email.
        
        Args:
            email: User's email
            client_id: Client ID
            
        Returns:
            True if magic link sent successfully
            
        Raises:
            UserNotFoundException: If user not found
        """
        try:
            user = await self.user_repository.find_by_email(email, client_id=client_id)
            if not user:
                raise UserNotFoundException(email=email)
            
            if not user.active:
                raise BusinessRuleException(
                    "Account is not active",
                    "ACCOUNT_NOT_ACTIVE"
                )
            
            # Generate magic link token
            token = user.generate_magic_link_token()
            user.updated_at = datetime.utcnow()
            await self.user_repository.save(user)
            
            # Create magic link
            magic_link = f"{self.settings.frontend_url}/auth/magic-link?token={token}&user_id={user.id}"
            
            # Generate email HTML
            html_content = self._generate_magic_link_email_html(
                user_name=user.name,
                magic_link=magic_link
            )
            
            # Send email
            await self.email_service.send_email(
                to_email=user.email,
                subject=f"Sign in to {self.settings.app_name}",
                html_content=html_content
            )
            
            logger.info(f"Magic link sent to {email}")
            return True
            
        except (UserNotFoundException, BusinessRuleException):
            raise
        except Exception as e:
            logger.error(f"Error sending magic link: {e}", exc_info=True)
            return False
    
    async def verify_magic_link(
        self,
        user_id: str,
        token: str,
        client_id: str
    ) -> AppUser:
        """
        Verify magic link token and return user.
        
        Args:
            user_id: User ID
            token: Magic link token
            client_id: Client ID
            
        Returns:
            Authenticated user
            
        Raises:
            UserNotFoundException: If user not found
            InvalidTokenException: If token is invalid
            TokenExpiredException: If token has expired
        """
        try:
            user = await self.user_repository.find_by_id(user_id, client_id=client_id)
            if not user:
                raise UserNotFoundException(user_id=user_id)
            
            if not user.active:
                raise BusinessRuleException(
                    "Account is not active",
                    "ACCOUNT_NOT_ACTIVE"
                )
            
            # Verify token (this will raise exception if invalid/expired)
            user.verify_magic_link_token(
                token=token,
                expire_minutes=self.settings.magic_link_expire_minutes
            )
            
            # Clear the token (single use)
            user.clear_magic_link_token()
            user.updated_at = datetime.utcnow()
            await self.user_repository.save(user)
            
            logger.info(f"Magic link verified for user {user_id}")
            return user
            
        except (UserNotFoundException, InvalidTokenException, TokenExpiredException, BusinessRuleException):
            raise
        except Exception as e:
            logger.error(f"Error verifying magic link: {e}", exc_info=True)
            raise BusinessRuleException(
                "Failed to verify magic link",
                "MAGIC_LINK_VERIFICATION_FAILED"
            )

