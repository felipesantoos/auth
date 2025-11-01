"""
Backup Code Domain Model
Represents a backup code for 2FA/MFA recovery
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from core.exceptions import MissingRequiredFieldException, BusinessRuleException


@dataclass
class BackupCode:
    """
    Domain model for MFA backup codes.
    
    Backup codes are single-use codes that can be used when TOTP is unavailable.
    Following security best practices:
    - Codes are hashed in database
    - Each code can only be used once
    - Codes are regenerated after use (user gets new set)
    """
    id: Optional[str]
    user_id: str
    client_id: str
    code_hash: str  # bcrypt hash of the code
    used: bool = False
    used_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    def validate(self) -> None:
        """
        Validate backup code according to business rules.
        
        Raises:
            MissingRequiredFieldException: If required fields are missing
        """
        if not self.user_id or not self.user_id.strip():
            raise MissingRequiredFieldException("user_id")
        
        if not self.client_id or not self.client_id.strip():
            raise MissingRequiredFieldException("client_id")
        
        if not self.code_hash or not self.code_hash.strip():
            raise MissingRequiredFieldException("code_hash")
    
    def mark_as_used(self) -> None:
        """
        Mark backup code as used.
        
        Raises:
            BusinessRuleException: If code was already used
        """
        if self.used:
            raise BusinessRuleException(
                "Backup code has already been used",
                "BACKUP_CODE_ALREADY_USED"
            )
        
        self.used = True
        self.used_at = datetime.utcnow()
    
    def is_used(self) -> bool:
        """Check if backup code has been used"""
        return self.used
    
    def can_be_used(self) -> bool:
        """Check if backup code can still be used"""
        return not self.used

