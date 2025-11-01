"""
MFA (Multi-Factor Authentication) Service Implementation
Handles TOTP, QR codes, and backup codes for 2FA
"""
import logging
import pyotp
import qrcode
import bcrypt
import secrets
import io
import base64
from typing import List, Tuple, Optional
from datetime import datetime

from core.domain.auth.app_user import AppUser
from core.domain.auth.backup_code import BackupCode
from core.interfaces.secondary.app_user_repository_interface import AppUserRepositoryInterface
from infra.database.repositories.backup_code_repository import BackupCodeRepository
from core.interfaces.secondary.settings_provider_interface import SettingsProviderInterface
from core.exceptions import (
    BusinessRuleException,
    ValidationException,
    InvalidValueException,
)

logger = logging.getLogger(__name__)


class MFAService:
    """
    Service for Multi-Factor Authentication (2FA/MFA).
    
    Supports:
    - TOTP (Time-based One-Time Password) via Google Authenticator, Authy, etc.
    - Backup codes for account recovery
    - QR code generation for easy setup
    """
    
    def __init__(
        self,
        user_repository: AppUserRepositoryInterface,
        backup_code_repository: BackupCodeRepository,
        settings_provider: SettingsProviderInterface,
    ):
        self.user_repository = user_repository
        self.backup_code_repository = backup_code_repository
        self.settings = settings_provider.get_settings()
    
    def _generate_totp_secret(self) -> str:
        """Generate a new TOTP secret key"""
        return pyotp.random_base32()
    
    def _generate_totp_uri(self, secret: str, user_email: str) -> str:
        """
        Generate TOTP provisioning URI for QR code.
        
        Args:
            secret: TOTP secret key
            user_email: User's email (used as account identifier)
            
        Returns:
            otpauth:// URI
        """
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=user_email,
            issuer_name=self.settings.mfa_issuer_name
        )
    
    def _generate_qr_code(self, totp_uri: str) -> str:
        """
        Generate QR code image as base64 string.
        
        Args:
            totp_uri: TOTP provisioning URI
            
        Returns:
            Base64 encoded PNG image
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return f"data:image/png;base64,{img_base64}"
    
    def _generate_backup_code(self) -> str:
        """
        Generate a single backup code.
        
        Format: XXXX-XXXX-XXXX (12 digits, grouped for readability)
        """
        code = ''.join([str(secrets.randbelow(10)) for _ in range(12)])
        return f"{code[:4]}-{code[4:8]}-{code[8:12]}"
    
    def _hash_backup_code(self, code: str) -> str:
        """Hash backup code with bcrypt"""
        return bcrypt.hashpw(code.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def _verify_backup_code(self, code: str, code_hash: str) -> bool:
        """Verify backup code against hash"""
        try:
            return bcrypt.checkpw(code.encode('utf-8'), code_hash.encode('utf-8'))
        except Exception:
            return False
    
    async def setup_mfa(
        self,
        user_id: str,
        client_id: str
    ) -> Tuple[str, str, List[str]]:
        """
        Initialize MFA setup for a user.
        
        This generates a secret and backup codes but doesn't enable MFA yet.
        User must verify the TOTP code before MFA is enabled.
        
        Args:
            user_id: User ID
            client_id: Client ID
            
        Returns:
            Tuple of (secret, qr_code_base64, backup_codes)
            
        Raises:
            UserNotFoundException: If user not found
            BusinessRuleException: If MFA already enabled
        """
        user = await self.user_repository.find_by_id(user_id, client_id=client_id)
        if not user:
            raise BusinessRuleException("User not found", "USER_NOT_FOUND")
        
        if user.has_mfa_enabled():
            raise BusinessRuleException(
                "MFA is already enabled. Disable it first to re-configure.",
                "MFA_ALREADY_ENABLED"
            )
        
        # Generate TOTP secret
        secret = self._generate_totp_secret()
        
        # Generate QR code
        totp_uri = self._generate_totp_uri(secret, user.email)
        qr_code = self._generate_qr_code(totp_uri)
        
        # Generate backup codes
        backup_codes = [
            self._generate_backup_code()
            for _ in range(self.settings.mfa_backup_codes_count)
        ]
        
        logger.info(f"MFA setup initialized for user {user_id}")
        
        return secret, qr_code, backup_codes
    
    async def enable_mfa(
        self,
        user_id: str,
        client_id: str,
        secret: str,
        totp_code: str,
        backup_codes: List[str]
    ) -> bool:
        """
        Enable MFA for a user after verifying TOTP code.
        
        Args:
            user_id: User ID
            client_id: Client ID
            secret: TOTP secret from setup
            totp_code: TOTP code to verify
            backup_codes: Backup codes to store
            
        Returns:
            True if MFA enabled successfully
            
        Raises:
            ValidationException: If TOTP code is invalid
        """
        user = await self.user_repository.find_by_id(user_id, client_id=client_id)
        if not user:
            raise BusinessRuleException("User not found", "USER_NOT_FOUND")
        
        # Verify TOTP code
        if not self.verify_totp(secret, totp_code):
            raise ValidationException("Invalid TOTP code. Please try again.")
        
        # Enable MFA on user
        user.enable_mfa(secret)
        user.updated_at = datetime.utcnow()
        await self.user_repository.save(user)
        
        # Store backup codes
        await self._store_backup_codes(user_id, client_id, backup_codes)
        
        logger.info(f"MFA enabled for user {user_id}")
        return True
    
    async def _store_backup_codes(
        self,
        user_id: str,
        client_id: str,
        backup_codes: List[str]
    ) -> None:
        """Store backup codes in database (hashed)"""
        # Delete existing backup codes first
        await self.backup_code_repository.delete_by_user(user_id, client_id)
        
        # Save new backup codes
        for code in backup_codes:
            backup_code = BackupCode(
                id=None,
                user_id=user_id,
                client_id=client_id,
                code_hash=self._hash_backup_code(code),
                used=False,
                used_at=None,
                created_at=datetime.utcnow()
            )
            backup_code.validate()
            await self.backup_code_repository.save(backup_code)
    
    async def disable_mfa(self, user_id: str, client_id: str) -> bool:
        """
        Disable MFA for a user.
        
        Args:
            user_id: User ID
            client_id: Client ID
            
        Returns:
            True if MFA disabled successfully
        """
        user = await self.user_repository.find_by_id(user_id, client_id=client_id)
        if not user:
            raise BusinessRuleException("User not found", "USER_NOT_FOUND")
        
        user.disable_mfa()
        user.updated_at = datetime.utcnow()
        await self.user_repository.save(user)
        
        # Delete backup codes
        await self.backup_code_repository.delete_by_user(user_id, client_id)
        
        logger.info(f"MFA disabled for user {user_id}")
        return True
    
    def verify_totp(self, secret: str, totp_code: str) -> bool:
        """
        Verify a TOTP code.
        
        Args:
            secret: TOTP secret key
            totp_code: 6-digit TOTP code from authenticator app
            
        Returns:
            True if code is valid
        """
        try:
            totp = pyotp.TOTP(secret)
            # Verify with window of 1 (allows for 30s clock drift)
            return totp.verify(totp_code, valid_window=1)
        except Exception as e:
            logger.error(f"Error verifying TOTP: {e}")
            return False
    
    async def verify_backup_code_for_user(
        self,
        user_id: str,
        client_id: str,
        backup_code: str
    ) -> bool:
        """
        Verify and consume a backup code.
        
        Backup codes are single-use. Once verified, they are marked as used.
        
        Args:
            user_id: User ID
            client_id: Client ID
            backup_code: Backup code to verify
            
        Returns:
            True if backup code is valid and was successfully used
        """
        try:
            # Get unused backup codes
            codes = await self.backup_code_repository.find_unused_by_user(user_id, client_id)
            
            if not codes:
                logger.warning(f"No unused backup codes for user {user_id}")
                return False
            
            # Try to find matching code
            for db_code in codes:
                if self._verify_backup_code(backup_code, db_code.code_hash):
                    # Mark as used
                    db_code.mark_as_used()
                    await self.backup_code_repository.save(db_code)
                    
                    logger.info(f"Backup code used for user {user_id}")
                    return True
            
            logger.warning(f"Invalid backup code for user {user_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error verifying backup code: {e}", exc_info=True)
            return False
    
    async def regenerate_backup_codes(
        self,
        user_id: str,
        client_id: str
    ) -> List[str]:
        """
        Regenerate backup codes for a user.
        
        This invalidates all existing backup codes.
        
        Args:
            user_id: User ID
            client_id: Client ID
            
        Returns:
            List of new backup codes
        """
        user = await self.user_repository.find_by_id(user_id, client_id=client_id)
        if not user:
            raise BusinessRuleException("User not found", "USER_NOT_FOUND")
        
        if not user.has_mfa_enabled():
            raise BusinessRuleException(
                "MFA must be enabled to regenerate backup codes",
                "MFA_NOT_ENABLED"
            )
        
        # Generate new backup codes
        backup_codes = [
            self._generate_backup_code()
            for _ in range(self.settings.mfa_backup_codes_count)
        ]
        
        # Store new codes (this deletes old ones)
        await self._store_backup_codes(user_id, client_id, backup_codes)
        
        logger.info(f"Backup codes regenerated for user {user_id}")
        return backup_codes
    
    async def get_remaining_backup_codes_count(
        self,
        user_id: str,
        client_id: str
    ) -> int:
        """Get count of remaining (unused) backup codes"""
        try:
            codes = await self.backup_code_repository.find_unused_by_user(user_id, client_id)
            return len(codes)
        except Exception as e:
            logger.error(f"Error getting backup codes count: {e}", exc_info=True)
            return 0

