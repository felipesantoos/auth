"""
Unit tests for AuditLog domain model
Tests domain logic without external dependencies
"""
import pytest
from datetime import datetime
from core.domain.auth.audit_log import AuditLog
from core.domain.auth.audit_event_type import AuditEventType
from core.domain.audit.audit_event_category import AuditEventCategory
from core.exceptions import MissingRequiredFieldException


@pytest.mark.unit
class TestAuditLogCreation:
    """Test audit log creation and initialization"""
    
    def test_create_minimal_audit_log(self):
        """Test creating minimal valid audit log"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="test-client",
            status="success"
        )
        
        assert log.event_type == AuditEventType.LOGIN_SUCCESS
        assert log.client_id == "test-client"
        assert log.status == "success"
        assert log.event_id is not None
        assert log.created_at is not None
    
    def test_event_category_auto_calculated(self):
        """Test that event_category is auto-calculated from event_type"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="test-client",
            status="success"
        )
        
        assert log.event_category == AuditEventCategory.AUTHENTICATION
    
    def test_event_id_auto_generated(self):
        """Test that event_id is auto-generated if not provided"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="test-client",
            status="success"
        )
        
        assert log.event_id is not None
        assert len(log.event_id) > 0
    
    def test_created_at_auto_set(self):
        """Test that created_at is auto-set if not provided"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="test-client",
            status="success"
        )
        
        assert log.created_at is not None
        assert isinstance(log.created_at, datetime)
    
    def test_status_synced_with_success_field(self):
        """Test that status and success fields are synced"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_FAILED,
            client_id="test-client",
            success=False
        )
        
        assert log.status == "failure"
        assert log.success is False


@pytest.mark.unit
class TestAuditLogValidation:
    """Test audit log validation"""
    
    def test_validation_passes_with_required_fields(self):
        """Test validation passes with all required fields"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="test-client",
            status="success"
        )
        
        # Should not raise
        log.validate()
    
    def test_validation_fails_without_client_id(self):
        """Test validation fails without client_id"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="",
            status="success"
        )
        
        with pytest.raises(MissingRequiredFieldException, match="client_id"):
            log.validate()
    
    def test_validation_fails_without_event_type(self):
        """Test validation fails without event_type"""
        log = AuditLog(
            event_type=None,
            client_id="test-client",
            status="success"
        )
        
        with pytest.raises(MissingRequiredFieldException, match="event_type"):
            log.validate()
    
    def test_validation_fails_without_status(self):
        """Test validation fails without status"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="test-client",
            status=""
        )
        
        with pytest.raises(MissingRequiredFieldException, match="status"):
            log.validate()


@pytest.mark.unit
class TestAuditLogStatusChecks:
    """Test status check methods"""
    
    def test_is_success_returns_true_for_successful_event(self):
        """Test is_success returns True for successful events"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="test-client",
            success=True,
            status="success"
        )
        
        assert log.is_success() is True
    
    def test_is_success_returns_false_for_failed_event(self):
        """Test is_success returns False for failed events"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_FAILED,
            client_id="test-client",
            success=False,
            status="failure"
        )
        
        assert log.is_success() is False
    
    def test_is_failure_returns_true_for_failed_event(self):
        """Test is_failure returns True for failed events"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_FAILED,
            client_id="test-client",
            success=False,
            status="failure"
        )
        
        assert log.is_failure() is True
    
    def test_is_failure_returns_false_for_successful_event(self):
        """Test is_failure returns False for successful events"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="test-client",
            success=True,
            status="success"
        )
        
        assert log.is_failure() is False
    
    def test_is_warning_returns_true_for_warning_status(self):
        """Test is_warning returns True for warning status"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="test-client",
            status="warning"
        )
        
        assert log.is_warning() is True
    
    def test_is_warning_returns_false_for_non_warning_status(self):
        """Test is_warning returns False for non-warning status"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="test-client",
            status="success"
        )
        
        assert log.is_warning() is False
    
    def test_is_security_critical_for_critical_event(self):
        """Test is_security_critical for security-critical events"""
        log = AuditLog(
            event_type=AuditEventType.SUSPICIOUS_ACTIVITY_DETECTED,
            client_id="test-client",
            status="success"
        )
        
        assert log.is_security_critical() is True
    
    def test_is_security_critical_for_non_critical_event(self):
        """Test is_security_critical for non-critical events"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="test-client",
            status="success"
        )
        
        assert log.is_security_critical() is False


@pytest.mark.unit
class TestAuditLogTags:
    """Test tag-based methods"""
    
    def test_is_sensitive_with_sensitive_tag(self):
        """Test is_sensitive returns True with sensitive tag"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="test-client",
            status="success",
            tags=["sensitive"]
        )
        
        assert log.is_sensitive() is True
    
    def test_is_sensitive_with_pii_tag(self):
        """Test is_sensitive returns True with pii tag"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="test-client",
            status="success",
            tags=["pii"]
        )
        
        assert log.is_sensitive() is True
    
    def test_is_sensitive_without_tags(self):
        """Test is_sensitive returns False without sensitive tags"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="test-client",
            status="success",
            tags=[]
        )
        
        assert log.is_sensitive() is False
    
    def test_is_critical_with_critical_tag(self):
        """Test is_critical returns True with critical tag"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="test-client",
            status="success",
            tags=["critical"]
        )
        
        assert log.is_critical() is True
    
    def test_is_critical_for_security_critical_event(self):
        """Test is_critical returns True for security-critical events"""
        log = AuditLog(
            event_type=AuditEventType.ACCOUNT_LOCKED,
            client_id="test-client",
            status="success"
        )
        
        assert log.is_critical() is True
    
    def test_requires_compliance_with_compliance_tag(self):
        """Test requires_compliance returns True with compliance tag"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="test-client",
            status="success",
            tags=["compliance"]
        )
        
        assert log.requires_compliance() is True
    
    def test_requires_compliance_with_gdpr_tag(self):
        """Test requires_compliance returns True with gdpr tag"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="test-client",
            status="success",
            tags=["gdpr"]
        )
        
        assert log.requires_compliance() is True


@pytest.mark.unit
class TestAuditLogResourceChecks:
    """Test resource-related methods"""
    
    def test_involves_entity_returns_true_for_matching_entity(self):
        """Test involves_entity returns True for matching entity"""
        log = AuditLog(
            event_type=AuditEventType.ENTITY_UPDATED,
            client_id="test-client",
            status="success",
            resource_type="user",
            resource_id="user-123"
        )
        
        assert log.involves_entity("user", "user-123") is True
    
    def test_involves_entity_returns_false_for_different_type(self):
        """Test involves_entity returns False for different type"""
        log = AuditLog(
            event_type=AuditEventType.ENTITY_UPDATED,
            client_id="test-client",
            status="success",
            resource_type="user",
            resource_id="user-123"
        )
        
        assert log.involves_entity("project", "user-123") is False
    
    def test_involves_entity_returns_false_for_different_id(self):
        """Test involves_entity returns False for different ID"""
        log = AuditLog(
            event_type=AuditEventType.ENTITY_UPDATED,
            client_id="test-client",
            status="success",
            resource_type="user",
            resource_id="user-123"
        )
        
        assert log.involves_entity("user", "user-456") is False


@pytest.mark.unit
class TestAuditLogChangeTracking:
    """Test change tracking methods"""
    
    def test_get_changed_fields_returns_field_names(self):
        """Test get_changed_fields returns list of field names"""
        log = AuditLog(
            event_type=AuditEventType.ENTITY_UPDATED,
            client_id="test-client",
            status="success",
            changes=[
                {"field": "email", "old_value": "old@example.com", "new_value": "new@example.com"},
                {"field": "name", "old_value": "Old Name", "new_value": "New Name"}
            ]
        )
        
        fields = log.get_changed_fields()
        
        assert len(fields) == 2
        assert "email" in fields
        assert "name" in fields
    
    def test_get_changed_fields_returns_empty_without_changes(self):
        """Test get_changed_fields returns empty list without changes"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="test-client",
            status="success"
        )
        
        fields = log.get_changed_fields()
        
        assert len(fields) == 0
    
    def test_get_change_summary_returns_summary_string(self):
        """Test get_change_summary returns summary string"""
        log = AuditLog(
            event_type=AuditEventType.ENTITY_UPDATED,
            client_id="test-client",
            status="success",
            changes=[
                {"field": "email", "old_value": "old@example.com", "new_value": "new@example.com"}
            ]
        )
        
        summary = log.get_change_summary()
        
        assert "email" in summary
        assert "old@example.com" in summary
        assert "new@example.com" in summary
        assert "→" in summary
    
    def test_get_change_summary_limits_to_five_changes(self):
        """Test get_change_summary limits to 5 changes"""
        log = AuditLog(
            event_type=AuditEventType.ENTITY_UPDATED,
            client_id="test-client",
            status="success",
            changes=[
                {"field": f"field{i}", "old_value": f"old{i}", "new_value": f"new{i}"}
                for i in range(10)
            ]
        )
        
        summary = log.get_change_summary()
        
        assert "and 5 more change(s)" in summary
    
    def test_has_changes_returns_true_with_changes(self):
        """Test has_changes returns True with changes"""
        log = AuditLog(
            event_type=AuditEventType.ENTITY_UPDATED,
            client_id="test-client",
            status="success",
            changes=[
                {"field": "email", "old_value": "old@example.com", "new_value": "new@example.com"}
            ]
        )
        
        assert log.has_changes() is True
    
    def test_has_changes_returns_false_without_changes(self):
        """Test has_changes returns False without changes"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="test-client",
            status="success"
        )
        
        assert log.has_changes() is False


@pytest.mark.unit
class TestAuditLogDisplayMethods:
    """Test display methods"""
    
    def test_get_summary_returns_action_if_set(self):
        """Test get_summary returns action if set"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="test-client",
            status="success",
            action="User logged in successfully"
        )
        
        summary = log.get_summary()
        
        assert summary == "User logged in successfully"
    
    def test_get_summary_includes_username_if_available(self):
        """Test get_summary includes username if available"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="test-client",
            status="success",
            user_id="user-123",
            username="john_doe"
        )
        
        summary = log.get_summary()
        
        assert "john_doe" in summary
    
    def test_get_summary_includes_user_id_if_no_username(self):
        """Test get_summary includes user_id if no username"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="test-client",
            status="success",
            user_id="user-123"
        )
        
        summary = log.get_summary()
        
        assert "user-123" in summary


@pytest.mark.unit
class TestAuditLogMetadataAndTags:
    """Test metadata and tag manipulation"""
    
    def test_add_metadata_adds_key_value_pair(self):
        """Test add_metadata adds key-value pair"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="test-client",
            status="success"
        )
        
        log.add_metadata("browser", "Chrome")
        
        assert log.metadata["browser"] == "Chrome"
    
    def test_add_metadata_initializes_dict_if_none(self):
        """Test add_metadata initializes dict if None"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="test-client",
            status="success",
            metadata=None
        )
        
        log.add_metadata("key", "value")
        
        assert log.metadata is not None
        assert log.metadata["key"] == "value"
    
    def test_add_tag_adds_tag_to_list(self):
        """Test add_tag adds tag to list"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="test-client",
            status="success"
        )
        
        log.add_tag("important")
        
        assert "important" in log.tags
    
    def test_add_tag_does_not_duplicate(self):
        """Test add_tag does not add duplicate tags"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="test-client",
            status="success",
            tags=["important"]
        )
        
        log.add_tag("important")
        
        assert log.tags.count("important") == 1
    
    def test_add_tags_adds_multiple_tags(self):
        """Test add_tags adds multiple tags"""
        log = AuditLog(
            event_type=AuditEventType.LOGIN_SUCCESS,
            client_id="test-client",
            status="success"
        )
        
        log.add_tags(["important", "security", "compliance"])
        
        assert "important" in log.tags
        assert "security" in log.tags
        assert "compliance" in log.tags

