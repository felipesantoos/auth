"""
Email Verification Service Implementation
Handles email verification for new users
"""
import logging
from typing import Optional
from datetime import datetime

from core.domain.auth.app_user import AppUser
from core.interfaces.secondary.app_user_repository_interface import IAppUserRepository
from core.interfaces.secondary.email_service_interface import IEmailService
from core.interfaces.secondary.settings_provider_interface import ISettingsProvider
from core.exceptions import (
    BusinessRuleException,
    InvalidTokenException,
    TokenExpiredException,
    UserNotFoundException,
)

logger = logging.getLogger(__name__)


class EmailVerificationService:
    """
    Service for email verification functionality.
    
    Features:
    - Send verification email with token
    - Verify email with token
    - Resend verification email
    """
    
    def __init__(
        self,
        user_repository: IAppUserRepository,
        email_service: IEmailService,
        settings_provider: ISettingsProvider,
    ):
        self.user_repository = user_repository
        self.email_service = email_service
        self.settings = settings_provider.get_settings()
    
    def _generate_verification_email_html(
        self,
        user_name: str,
        verification_link: str
    ) -> str:
        """
        Generate HTML email template for verification.
        
        Args:
            user_name: User's name
            verification_link: Complete verification link
            
        Returns:
            HTML email content
        """
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Verify Your Email</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #4a5568;">Welcome to {self.settings.app_name}!</h2>
                
                <p>Hi {user_name},</p>
                
                <p>Thank you for signing up! Please verify your email address to activate your account.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_link}" 
                       style="background-color: #4299e1; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Verify Email Address
                    </a>
                </div>
                
                <p style="color: #718096; font-size: 14px;">
                    Or copy and paste this link in your browser:<br>
                    <a href="{verification_link}" style="color: #4299e1;">{verification_link}</a>
                </p>
                
                <p style="color: #718096; font-size: 14px; margin-top: 30px;">
                    This link will expire in {self.settings.email_verification_expire_hours} hours.
                </p>
                
                <p style="color: #718096; font-size: 14px;">
                    If you didn't create this account, please ignore this email.
                </p>
                
                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">
                
                <p style="color: #a0aec0; font-size: 12px; text-align: center;">
                    © {datetime.utcnow().year} {self.settings.app_name}. All rights reserved.
                </p>
            </div>
        </body>
        </html>
        """
    
    async def send_verification_email(
        self,
        user_id: str,
        client_id: str
    ) -> bool:
        """
        Send email verification link to user.
        
        Args:
            user_id: User ID
            client_id: Client ID
            
        Returns:
            True if email sent successfully
            
        Raises:
            UserNotFoundException: If user not found
            BusinessRuleException: If email already verified
        """
        try:
            user = await self.user_repository.find_by_id(user_id, client_id=client_id)
            if not user:
                raise UserNotFoundException(user_id=user_id)
            
            if user.is_email_verified():
                raise BusinessRuleException(
                    "Email is already verified",
                    "EMAIL_ALREADY_VERIFIED"
                )
            
            # Generate verification token
            token = user.generate_email_verification_token()
            user.updated_at = datetime.utcnow()
            await self.user_repository.save(user)
            
            # Create verification link
            verification_link = f"{self.settings.frontend_url}/verify-email?token={token}&user_id={user_id}"
            
            # Generate email HTML
            html_content = self._generate_verification_email_html(
                user_name=user.name,
                verification_link=verification_link
            )
            
            # Send email
            await self.email_service.send_email(
                to_email=user.email,
                subject=f"Verify your email - {self.settings.app_name}",
                html_content=html_content
            )
            
            logger.info(f"Verification email sent to user {user_id}")
            return True
            
        except (UserNotFoundException, BusinessRuleException):
            raise
        except Exception as e:
            logger.error(f"Error sending verification email: {e}", exc_info=True)
            return False
    
    async def verify_email(
        self,
        user_id: str,
        token: str,
        client_id: str
    ) -> bool:
        """
        Verify user's email with token.
        
        Args:
            user_id: User ID
            token: Verification token
            client_id: Client ID
            
        Returns:
            True if email verified successfully
            
        Raises:
            UserNotFoundException: If user not found
            InvalidTokenException: If token is invalid
            TokenExpiredException: If token has expired
        """
        try:
            user = await self.user_repository.find_by_id(user_id, client_id=client_id)
            if not user:
                raise UserNotFoundException(user_id=user_id)
            
            if user.is_email_verified():
                # Already verified - consider this a success
                logger.info(f"Email already verified for user {user_id}")
                return True
            
            # Verify token (this will raise exception if invalid/expired)
            user.verify_email_token(
                token=token,
                expire_hours=self.settings.email_verification_expire_hours
            )
            
            # Mark email as verified
            user.mark_email_verified()
            user.updated_at = datetime.utcnow()
            await self.user_repository.save(user)
            
            logger.info(f"Email verified for user {user_id}")
            return True
            
        except (UserNotFoundException, InvalidTokenException, TokenExpiredException):
            raise
        except Exception as e:
            logger.error(f"Error verifying email: {e}", exc_info=True)
            raise BusinessRuleException(
                "Failed to verify email",
                "EMAIL_VERIFICATION_FAILED"
            )
    
    async def resend_verification_email(
        self,
        user_id: str,
        client_id: str
    ) -> bool:
        """
        Resend verification email to user.
        
        This regenerates the token and sends a new email.
        
        Args:
            user_id: User ID
            client_id: Client ID
            
        Returns:
            True if email resent successfully
        """
        # Same as send_verification_email, but allows resending
        return await self.send_verification_email(user_id, client_id)
    
    async def check_email_verified(
        self,
        user_id: str,
        client_id: str
    ) -> bool:
        """
        Check if user's email is verified.
        
        Args:
            user_id: User ID
            client_id: Client ID
            
        Returns:
            True if email is verified
        """
        try:
            user = await self.user_repository.find_by_id(user_id, client_id=client_id)
            if not user:
                return False
            
            return user.is_email_verified()
        except Exception as e:
            logger.error(f"Error checking email verification: {e}", exc_info=True)
            return False

