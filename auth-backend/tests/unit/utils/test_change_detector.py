"""
Unit tests for ChangeDetector utility
Tests change detection logic without external dependencies
"""
import pytest
from dataclasses import dataclass
from datetime import datetime
from core.utils.change_detector import ChangeDetector
from core.domain.audit.entity_change import EntityChange


@dataclass
class TestUser:
    """Test dataclass for testing"""
    id: str
    name: str
    email: str
    age: int


@pytest.mark.unit
class TestChangeDetectorDataclass:
    """Test change detection for dataclasses"""
    
    def test_detect_changes_in_dataclass(self):
        """Test detecting changes in dataclass entities"""
        old_user = TestUser(id="123", name="John", email="old@example.com", age=30)
        new_user = TestUser(id="123", name="John", email="new@example.com", age=31)
        
        changes = ChangeDetector.detect_changes(old_user, new_user)
        
        assert len(changes) == 2  # email and age changed
        field_names = [c.field for c in changes]
        assert "email" in field_names
        assert "age" in field_names
    
    def test_no_changes_returns_empty_list(self):
        """Test no changes returns empty list"""
        user1 = TestUser(id="123", name="John", email="john@example.com", age=30)
        user2 = TestUser(id="123", name="John", email="john@example.com", age=30)
        
        changes = ChangeDetector.detect_changes(user1, user2)
        
        assert len(changes) == 0
    
    def test_ignores_specified_fields(self):
        """Test specified fields are ignored"""
        old_user = TestUser(id="123", name="John", email="old@example.com", age=30)
        new_user = TestUser(id="456", name="John", email="new@example.com", age=30)
        
        changes = ChangeDetector.detect_changes(old_user, new_user, ignore_fields=["id"])
        
        field_names = [c.field for c in changes]
        assert "id" not in field_names
        assert "email" in field_names


@pytest.mark.unit
class TestChangeDetectorDict:
    """Test change detection for dictionaries"""
    
    def test_detect_changes_in_dict(self):
        """Test detecting changes in dictionary entities"""
        old_data = {"id": "123", "name": "John", "email": "old@example.com"}
        new_data = {"id": "123", "name": "Jane", "email": "old@example.com"}
        
        changes = ChangeDetector.detect_changes(old_data, new_data)
        
        assert len(changes) == 1
        assert changes[0].field == "name"
        assert changes[0].old_value == "John"
        assert changes[0].new_value == "Jane"
    
    def test_detect_added_field(self):
        """Test detecting added fields"""
        old_data = {"id": "123", "name": "John"}
        new_data = {"id": "123", "name": "John", "email": "john@example.com"}
        
        changes = ChangeDetector.detect_changes(old_data, new_data)
        
        assert len(changes) == 1
        assert changes[0].field == "email"
        assert changes[0].change_type == "added"
    
    def test_detect_removed_field(self):
        """Test detecting removed fields"""
        old_data = {"id": "123", "name": "John", "email": "john@example.com"}
        new_data = {"id": "123", "name": "John"}
        
        changes = ChangeDetector.detect_changes(old_data, new_data)
        
        assert len(changes) == 1
        assert changes[0].field == "email"
        assert changes[0].change_type == "removed"


@pytest.mark.unit
class TestChangeDetectorSerialization:
    """Test entity serialization"""
    
    def test_entity_to_dict_converts_dataclass(self):
        """Test converting dataclass to dict"""
        user = TestUser(id="123", name="John", email="john@example.com", age=30)
        
        user_dict = ChangeDetector.entity_to_dict(user)
        
        assert user_dict["id"] == "123"
        assert user_dict["name"] == "John"
        assert user_dict["email"] == "john@example.com"
        assert user_dict["age"] == 30
    
    def test_entity_to_dict_redacts_sensitive_fields(self):
        """Test sensitive fields are redacted"""
        @dataclass
        class UserWithPassword:
            id: str
            name: str
            password_hash: str
        
        user = UserWithPassword(id="123", name="John", password_hash="secret_hash")
        
        user_dict = ChangeDetector.entity_to_dict(user)
        
        assert user_dict["password_hash"] == "[REDACTED]"
    
    def test_entity_to_dict_serializes_datetime(self):
        """Test datetime values are serialized"""
        @dataclass
        class UserWithDate:
            id: str
            created_at: datetime
        
        now = datetime.utcnow()
        user = UserWithDate(id="123", created_at=now)
        
        user_dict = ChangeDetector.entity_to_dict(user)
        
        assert isinstance(user_dict["created_at"], str)
        assert "T" in user_dict["created_at"]  # ISO format


@pytest.mark.unit
class TestChangeSummary:
    """Test change summary generation"""
    
    def test_get_change_summary(self):
        """Test generating change summary"""
        changes = [
            EntityChange("email", "old@ex.com", "new@ex.com", "string", "modified"),
            EntityChange("name", "John", "Jane", "string", "modified")
        ]
        
        summary = ChangeDetector.get_change_summary(changes)
        
        assert "email" in summary
        assert "name" in summary
        assert "→" in summary
    
    def test_get_change_summary_limits_changes(self):
        """Test summary limits number of changes shown"""
        changes = [
            EntityChange(f"field{i}", f"old{i}", f"new{i}", "string", "modified")
            for i in range(10)
        ]
        
        summary = ChangeDetector.get_change_summary(changes, max_changes=3)
        
        assert "and 7 more" in summary

