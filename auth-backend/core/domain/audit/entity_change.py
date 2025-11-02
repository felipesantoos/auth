"""
Entity Change Tracking Model
Represents field-level changes for comprehensive audit trails
"""
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class EntityChange:
    """
    Represents a single field change in an entity.
    
    Used for detailed change tracking in audit logs.
    Enables compliance with SOX, GDPR, and other regulations
    that require tracking of data modifications.
    """
    field: str  # Field name (e.g., "email", "status", "price")
    old_value: Any  # Previous value
    new_value: Any  # New value
    field_type: str  # Data type ("string", "integer", "boolean", "datetime", etc.)
    change_type: str  # "added", "modified", "removed"
    
    def is_significant(self) -> bool:
        """
        Check if this is a significant change (not just whitespace, etc.).
        
        Filters out trivial changes to reduce noise in audit logs.
        
        Returns:
            True if change is significant, False otherwise
        """
        if self.old_value == self.new_value:
            return False
        
        # String comparison (ignore whitespace)
        if isinstance(self.old_value, str) and isinstance(self.new_value, str):
            return self.old_value.strip() != self.new_value.strip()
        
        # None to empty string is not significant
        if self.old_value is None and self.new_value == "":
            return False
        if self.old_value == "" and self.new_value is None:
            return False
        
        return True
    
    def to_dict(self) -> dict:
        """
        Convert to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of the change
        """
        return {
            "field": self.field,
            "old_value": self._serialize_value(self.old_value),
            "new_value": self._serialize_value(self.new_value),
            "field_type": self.field_type,
            "change_type": self.change_type
        }
    
    def _serialize_value(self, value: Any) -> Any:
        """Serialize value for JSON storage"""
        # Handle datetime
        if hasattr(value, 'isoformat'):
            return value.isoformat()
        
        # Handle enums
        if hasattr(value, 'value'):
            return value.value
        
        # Handle complex objects (fallback to string)
        if not isinstance(value, (str, int, float, bool, type(None), list, dict)):
            return str(value)
        
        return value
    
    def get_summary(self) -> str:
        """
        Get human-readable summary of the change.
        
        Returns:
            String like "email: old@example.com → new@example.com"
        """
        old_str = str(self.old_value) if self.old_value is not None else "None"
        new_str = str(self.new_value) if self.new_value is not None else "None"
        
        # Truncate long values
        if len(old_str) > 50:
            old_str = old_str[:47] + "..."
        if len(new_str) > 50:
            new_str = new_str[:47] + "..."
        
        return f"{self.field}: {old_str} → {new_str}"
    
    def is_sensitive_field(self) -> bool:
        """
        Check if this field contains sensitive data.
        
        Returns:
            True if field is sensitive (password, SSN, credit card, etc.)
        """
        sensitive_keywords = [
            "password", "secret", "token", "key",
            "ssn", "social_security",
            "credit_card", "card_number", "cvv",
            "api_key", "private_key",
            "salt", "hash"
        ]
        
        field_lower = self.field.lower()
        return any(keyword in field_lower for keyword in sensitive_keywords)

