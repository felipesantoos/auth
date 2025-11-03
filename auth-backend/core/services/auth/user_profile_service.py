"""
User Profile Service
Self-service profile management
"""
import logging
from typing import Optional
import bcrypt
from fastapi import UploadFile
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
        settings_provider: ISettingsProvider,
        file_service=None  # Optional, injected when needed
    ):
        self.user_repository = user_repository
        self.email_service = email_service
        self.settings = settings_provider.get_settings()
        self.file_service = file_service
    
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
        if not user:
            raise ValueError("User not found")
        # REMOVED: client_id check (multi-workspace architecture)
        
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
    
    async def update_avatar(
        self,
        user_id: str,
        client_id: str,
        avatar_file: UploadFile
    ) -> str:
        """
        Upload and set user avatar.
        
        Args:
            user_id: User ID
            client_id: Client ID
            avatar_file: Avatar image file
            
        Returns:
            Avatar URL
            
        Raises:
            ValueError: If file service not available or user not found
        """
        if not self.file_service:
            raise ValueError("File service not available")
        
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        # REMOVED: client_id check (multi-workspace architecture)
        
        # Delete old avatar if exists
        if user.avatar_url:
            try:
                # Extract file_id from URL (simplified, assumes URL pattern)
                # In production, store file_id separately
                pass
            except:
                pass
        
        # Upload new avatar
        result = await self.file_service.upload_file(
            file=avatar_file,
            user_id=user_id,
            client_id=client_id,
            directory="avatars",
            is_public=True,
            tags=["avatar"]
        )
        
        # Update user
        user.update_avatar(result['url'])
        await self.user_repository.save(user)
        
        logger.info(f"Avatar updated for user {user_id}")
        return result['url']
    
    async def delete_avatar(
        self,
        user_id: str,
        client_id: str
    ) -> bool:
        """
        Delete user avatar.
        
        Args:
            user_id: User ID
            client_id: Client ID
            
        Returns:
            True if successful
        """
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        # REMOVED: client_id check (multi-workspace architecture)
        
        # Remove avatar
        user.remove_avatar()
        await self.user_repository.save(user)
        
        logger.info(f"Avatar deleted for user {user_id}")
        return True
    
    async def submit_kyc_document(
        self,
        user_id: str,
        client_id: str,
        document_file: UploadFile
    ) -> dict:
        """
        Submit KYC document for verification.
        
        Args:
            user_id: User ID
            client_id: Client ID
            document_file: Document file (ID, passport, driver's license, etc.)
            
        Returns:
            Document info with status
            
        Raises:
            ValueError: If user not found or file service unavailable
        """
        if not self.file_service:
            raise ValueError("File service not available")
        
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        # REMOVED: client_id check (multi-workspace architecture)
        
        # Upload KYC document (private, secure)
        result = await self.file_service.upload_file(
            file=document_file,
            user_id=user_id,
            client_id=client_id,
            directory="kyc_documents",
            is_public=False,  # Keep KYC documents private
            tags=["kyc", "identity"]
        )
        
        # Update user KYC status
        user.submit_kyc_document(result['id'])
        await self.user_repository.save(user)
        
        logger.info(f"KYC document submitted for user {user_id}")
        return {
            "document_id": result['id'],
            "status": "pending",
            "message": "KYC document submitted successfully. Awaiting verification."
        }
    
    async def get_kyc_status(
        self,
        user_id: str,
        client_id: str
    ) -> dict:
        """
        Get KYC verification status.
        
        Args:
            user_id: User ID
            client_id: Client ID
            
        Returns:
            KYC status info
        """
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        # REMOVED: client_id check (multi-workspace architecture)
        
        return {
            "kyc_status": user.kyc_status or "not_submitted",
            "kyc_verified": user.is_kyc_verified(),
            "kyc_pending": user.kyc_pending(),
            "kyc_verified_at": user.kyc_verified_at.isoformat() if user.kyc_verified_at else None
        }
    
    async def approve_kyc(
        self,
        user_id: str,
        admin_id: str
    ) -> bool:
        """
        Approve KYC verification (admin only).
        
        Args:
            user_id: User ID to approve
            admin_id: Admin user ID performing approval
            
        Returns:
            True if successful
            
        Note:
            This should be called only after proper admin authorization check
        """
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        user.approve_kyc()
        await self.user_repository.save(user)
        
        logger.info(f"KYC approved for user {user_id} by admin {admin_id}")
        return True
    
    async def reject_kyc(
        self,
        user_id: str,
        admin_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Reject KYC verification (admin only).
        
        Args:
            user_id: User ID to reject
            admin_id: Admin user ID performing rejection
            reason: Optional reason for rejection
            
        Returns:
            True if successful
        """
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        user.reject_kyc(reason)
        await self.user_repository.save(user)
        
        logger.info(f"KYC rejected for user {user_id} by admin {admin_id}. Reason: {reason}")
        return True

