"""
Unit tests for EntityChange domain model
Tests domain logic without external dependencies
"""
import pytest
from datetime import datetime
from core.domain.audit.entity_change import EntityChange
from enum import Enum


class TestStatus(Enum):
    """Test enum for testing"""
    ACTIVE = "active"
    INACTIVE = "inactive"


@pytest.mark.unit
class TestEntityChangeSignificance:
    """Test significance detection"""
    
    def test_identical_values_not_significant(self):
        """Test that identical values are not significant"""
        change = EntityChange(
            field="status",
            old_value="active",
            new_value="active",
            field_type="string",
            change_type="modified"
        )
        assert change.is_significant() is False
    
    def test_different_values_are_significant(self):
        """Test that different values are significant"""
        change = EntityChange(
            field="status",
            old_value="active",
            new_value="inactive",
            field_type="string",
            change_type="modified"
        )
        assert change.is_significant() is True
    
    def test_string_whitespace_only_difference_not_significant(self):
        """Test that whitespace-only differences are not significant"""
        change = EntityChange(
            field="name",
            old_value="  John Doe  ",
            new_value="John Doe",
            field_type="string",
            change_type="modified"
        )
        assert change.is_significant() is False
    
    def test_none_to_empty_string_not_significant(self):
        """Test that None to empty string is not significant"""
        change = EntityChange(
            field="description",
            old_value=None,
            new_value="",
            field_type="string",
            change_type="modified"
        )
        assert change.is_significant() is False
    
    def test_empty_string_to_none_not_significant(self):
        """Test that empty string to None is not significant"""
        change = EntityChange(
            field="description",
            old_value="",
            new_value=None,
            field_type="string",
            change_type="modified"
        )
        assert change.is_significant() is False
    
    def test_number_change_is_significant(self):
        """Test that number changes are significant"""
        change = EntityChange(
            field="price",
            old_value=100,
            new_value=150,
            field_type="integer",
            change_type="modified"
        )
        assert change.is_significant() is True


@pytest.mark.unit
class TestEntityChangeSerialization:
    """Test serialization to dictionary"""
    
    def test_to_dict_contains_all_fields(self):
        """Test that to_dict contains all expected fields"""
        change = EntityChange(
            field="email",
            old_value="old@example.com",
            new_value="new@example.com",
            field_type="string",
            change_type="modified"
        )
        
        result = change.to_dict()
        
        assert result["field"] == "email"
        assert result["old_value"] == "old@example.com"
        assert result["new_value"] == "new@example.com"
        assert result["field_type"] == "string"
        assert result["change_type"] == "modified"
    
    def test_to_dict_serializes_datetime(self):
        """Test that datetime values are serialized to ISO format"""
        now = datetime.utcnow()
        change = EntityChange(
            field="created_at",
            old_value=now,
            new_value=now,
            field_type="datetime",
            change_type="modified"
        )
        
        result = change.to_dict()
        
        assert isinstance(result["old_value"], str)
        assert isinstance(result["new_value"], str)
        assert "T" in result["old_value"]  # ISO format includes T
    
    def test_to_dict_serializes_enum(self):
        """Test that enum values are serialized to their value"""
        change = EntityChange(
            field="status",
            old_value=TestStatus.ACTIVE,
            new_value=TestStatus.INACTIVE,
            field_type="enum",
            change_type="modified"
        )
        
        result = change.to_dict()
        
        assert result["old_value"] == "active"
        assert result["new_value"] == "inactive"
    
    def test_to_dict_handles_complex_objects(self):
        """Test that complex objects are converted to string"""
        class ComplexObject:
            def __str__(self):
                return "ComplexObject()"
        
        obj = ComplexObject()
        change = EntityChange(
            field="data",
            old_value=obj,
            new_value=obj,
            field_type="object",
            change_type="modified"
        )
        
        result = change.to_dict()
        
        assert result["old_value"] == "ComplexObject()"
        assert result["new_value"] == "ComplexObject()"


@pytest.mark.unit
class TestEntityChangeSummary:
    """Test summary generation"""
    
    def test_get_summary_shows_field_and_values(self):
        """Test that summary shows field name and values"""
        change = EntityChange(
            field="email",
            old_value="old@example.com",
            new_value="new@example.com",
            field_type="string",
            change_type="modified"
        )
        
        summary = change.get_summary()
        
        assert "email" in summary
        assert "old@example.com" in summary
        assert "new@example.com" in summary
        assert "→" in summary
    
    def test_get_summary_handles_none_values(self):
        """Test that summary handles None values"""
        change = EntityChange(
            field="description",
            old_value=None,
            new_value="New description",
            field_type="string",
            change_type="added"
        )
        
        summary = change.get_summary()
        
        assert "description" in summary
        assert "None" in summary
        assert "New description" in summary
    
    def test_get_summary_truncates_long_values(self):
        """Test that summary truncates long values"""
        long_value = "a" * 100
        change = EntityChange(
            field="description",
            old_value=long_value,
            new_value="Short",
            field_type="string",
            change_type="modified"
        )
        
        summary = change.get_summary()
        
        # Summary should contain truncation indicator
        assert "..." in summary
        # Summary should be shorter than original value
        assert len(summary) < len(long_value)


@pytest.mark.unit
class TestEntityChangeSensitivity:
    """Test sensitive field detection"""
    
    def test_password_field_is_sensitive(self):
        """Test that password field is detected as sensitive"""
        change = EntityChange(
            field="password",
            old_value="old_hash",
            new_value="new_hash",
            field_type="string",
            change_type="modified"
        )
        assert change.is_sensitive_field() is True
    
    def test_secret_field_is_sensitive(self):
        """Test that secret field is detected as sensitive"""
        change = EntityChange(
            field="api_secret",
            old_value="old_secret",
            new_value="new_secret",
            field_type="string",
            change_type="modified"
        )
        assert change.is_sensitive_field() is True
    
    def test_token_field_is_sensitive(self):
        """Test that token field is detected as sensitive"""
        change = EntityChange(
            field="access_token",
            old_value="old_token",
            new_value="new_token",
            field_type="string",
            change_type="modified"
        )
        assert change.is_sensitive_field() is True
    
    def test_ssn_field_is_sensitive(self):
        """Test that SSN field is detected as sensitive"""
        change = EntityChange(
            field="social_security_number",
            old_value="123-45-6789",
            new_value="987-65-4321",
            field_type="string",
            change_type="modified"
        )
        assert change.is_sensitive_field() is True
    
    def test_credit_card_field_is_sensitive(self):
        """Test that credit card field is detected as sensitive"""
        change = EntityChange(
            field="credit_card_number",
            old_value="1234567890123456",
            new_value="9876543210987654",
            field_type="string",
            change_type="modified"
        )
        assert change.is_sensitive_field() is True
    
    def test_api_key_field_is_sensitive(self):
        """Test that API key field is detected as sensitive"""
        change = EntityChange(
            field="api_key",
            old_value="old_key",
            new_value="new_key",
            field_type="string",
            change_type="modified"
        )
        assert change.is_sensitive_field() is True
    
    def test_normal_field_is_not_sensitive(self):
        """Test that normal fields are not sensitive"""
        change = EntityChange(
            field="name",
            old_value="John",
            new_value="Jane",
            field_type="string",
            change_type="modified"
        )
        assert change.is_sensitive_field() is False
    
    def test_email_field_is_not_sensitive(self):
        """Test that email field is not sensitive"""
        change = EntityChange(
            field="email",
            old_value="old@example.com",
            new_value="new@example.com",
            field_type="string",
            change_type="modified"
        )
        assert change.is_sensitive_field() is False


@pytest.mark.unit
class TestEntityChangeTypes:
    """Test different change types"""
    
    def test_added_change_type(self):
        """Test added change type"""
        change = EntityChange(
            field="status",
            old_value=None,
            new_value="active",
            field_type="string",
            change_type="added"
        )
        assert change.change_type == "added"
    
    def test_modified_change_type(self):
        """Test modified change type"""
        change = EntityChange(
            field="status",
            old_value="pending",
            new_value="active",
            field_type="string",
            change_type="modified"
        )
        assert change.change_type == "modified"
    
    def test_removed_change_type(self):
        """Test removed change type"""
        change = EntityChange(
            field="status",
            old_value="active",
            new_value=None,
            field_type="string",
            change_type="removed"
        )
        assert change.change_type == "removed"

