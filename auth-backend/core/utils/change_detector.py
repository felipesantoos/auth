"""
Entity Change Detector
Utility to detect and track changes between entity states for audit purposes
"""
from typing import Any, List, Dict
from dataclasses import fields, is_dataclass
from datetime import datetime
import logging

from core.domain.audit.entity_change import EntityChange

logger = logging.getLogger(__name__)


class ChangeDetector:
    """
    Utility to detect changes between two entity states.
    
    Compares old and new entity and returns detailed list of changes.
    Supports both dataclasses and dictionaries.
    """
    
    @staticmethod
    def detect_changes(
        old_entity: Any,
        new_entity: Any,
        ignore_fields: List[str] = None
    ) -> List[EntityChange]:
        """
        Detect changes between two entities.
        
        Supports:
        - Dataclasses (domain models)
        - Dictionaries (DTOs, JSON data)
        
        Args:
            old_entity: Previous entity state
            new_entity: New entity state
            ignore_fields: Fields to ignore (e.g., ["updated_at", "id"])
            
        Returns:
            List of EntityChange objects (only significant changes)
            
        Example:
            >>> old_user = User(name="John", email="old@example.com")
            >>> new_user = User(name="John", email="new@example.com")
            >>> changes = ChangeDetector.detect_changes(old_user, new_user)
            >>> assert len(changes) == 1
            >>> assert changes[0].field == "email"
        """
        if ignore_fields is None:
            ignore_fields = ["updated_at", "id"]
        
        changes = []
        
        # For dataclasses
        if is_dataclass(old_entity) and is_dataclass(new_entity):
            changes = ChangeDetector._detect_dataclass_changes(
                old_entity, new_entity, ignore_fields
            )
        
        # For dictionaries
        elif isinstance(old_entity, dict) and isinstance(new_entity, dict):
            changes = ChangeDetector._detect_dict_changes(
                old_entity, new_entity, ignore_fields
            )
        
        # Filter only significant changes
        return [change for change in changes if change.is_significant()]
    
    @staticmethod
    def _detect_dataclass_changes(
        old_entity: Any,
        new_entity: Any,
        ignore_fields: List[str]
    ) -> List[EntityChange]:
        """Detect changes in dataclasses"""
        changes = []
        
        for field in fields(old_entity):
            field_name = field.name
            
            if field_name in ignore_fields:
                continue
            
            old_value = getattr(old_entity, field_name, None)
            new_value = getattr(new_entity, field_name, None)
            
            if old_value != new_value:
                changes.append(EntityChange(
                    field=field_name,
                    old_value=old_value,
                    new_value=new_value,
                    field_type=type(new_value).__name__ if new_value is not None else "None",
                    change_type="modified"
                ))
        
        return changes
    
    @staticmethod
    def _detect_dict_changes(
        old_entity: dict,
        new_entity: dict,
        ignore_fields: List[str]
    ) -> List[EntityChange]:
        """Detect changes in dictionaries"""
        changes = []
        all_keys = set(old_entity.keys()) | set(new_entity.keys())
        
        for key in all_keys:
            if key in ignore_fields:
                continue
            
            old_value = old_entity.get(key)
            new_value = new_entity.get(key)
            
            # Determine change type
            if key not in old_entity:
                change_type = "added"
            elif key not in new_entity:
                change_type = "removed"
            elif old_value != new_value:
                change_type = "modified"
            else:
                continue  # No change
            
            changes.append(EntityChange(
                field=key,
                old_value=old_value,
                new_value=new_value,
                field_type=type(new_value).__name__ if new_value is not None else "None",
                change_type=change_type
            ))
        
        return changes
    
    @staticmethod
    def entity_to_dict(
        entity: Any,
        exclude_fields: List[str] = None
    ) -> Dict[str, Any]:
        """
        Convert entity to dictionary for storage in audit logs.
        
        Automatically excludes sensitive fields like passwords and secrets.
        
        Args:
            entity: Entity to convert (dataclass or dict)
            exclude_fields: Additional fields to exclude
            
        Returns:
            Dictionary representation safe for audit storage
            
        Example:
            >>> user = User(id="123", name="John", password_hash="secret")
            >>> user_dict = ChangeDetector.entity_to_dict(user)
            >>> assert "password_hash" not in user_dict
        """
        if exclude_fields is None:
            exclude_fields = []
        
        # Default sensitive fields to always exclude
        default_exclusions = [
            "password", "password_hash", "hashed_password",
            "two_factor_secret", "mfa_secret",
            "api_key", "secret_key", "private_key",
            "token", "refresh_token",
            "salt"
        ]
        all_exclusions = set(default_exclusions + exclude_fields)
        
        result = {}
        
        # For dataclasses
        if is_dataclass(entity):
            for field in fields(entity):
                field_name = field.name
                
                if field_name in all_exclusions:
                    result[field_name] = "[REDACTED]"
                    continue
                
                value = getattr(entity, field_name)
                result[field_name] = ChangeDetector._serialize_value(value)
        
        # For dictionaries
        elif isinstance(entity, dict):
            for key, value in entity.items():
                if key in all_exclusions:
                    result[key] = "[REDACTED]"
                    continue
                
                result[key] = ChangeDetector._serialize_value(value)
        
        return result
    
    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """Serialize value for JSON storage"""
        # Handle None
        if value is None:
            return None
        
        # Handle datetime
        if isinstance(value, datetime):
            return value.isoformat()
        
        # Handle enums
        if hasattr(value, 'value'):
            return value.value
        
        # Handle primitives
        if isinstance(value, (str, int, float, bool)):
            return value
        
        # Handle lists/dicts (recursive)
        if isinstance(value, list):
            return [ChangeDetector._serialize_value(item) for item in value]
        
        if isinstance(value, dict):
            return {k: ChangeDetector._serialize_value(v) for k, v in value.items()}
        
        # Complex objects - convert to string
        return str(value)
    
    @staticmethod
    def get_change_summary(changes: List[EntityChange], max_changes: int = 5) -> str:
        """
        Get human-readable summary of all changes.
        
        Args:
            changes: List of EntityChange objects
            max_changes: Maximum changes to include in summary
            
        Returns:
            String like "email: old → new; name: Old Name → New Name; ...and 3 more"
        """
        if not changes:
            return "No changes"
        
        summaries = [change.get_summary() for change in changes[:max_changes]]
        
        if len(changes) > max_changes:
            summaries.append(f"...and {len(changes) - max_changes} more change(s)")
        
        return "; ".join(summaries)

