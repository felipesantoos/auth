"""
Unit tests for FileShare domain model
Tests domain logic without external dependencies
"""
import pytest
from datetime import datetime, timedelta
from core.domain.files.file_share import FileShare, FilePermission
from core.exceptions import (
    MissingRequiredFieldException,
    ValidationException,
    InvalidValueException
)


@pytest.mark.unit
class TestFileShareValidation:
    """Test file share validation"""
    
    def test_valid_file_share_passes_validation(self):
        """Test that valid file share passes validation"""
        share = FileShare(
            id="share-123",
            file_id="file-123",
            shared_by="user-123",
            shared_with="user-456",
            permission=FilePermission.READ
        )
        
        # Should not raise
        share.validate()
    
    def test_missing_file_id_raises_exception(self):
        """Test that missing file_id raises exception"""
        share = FileShare(
            id="share-123",
            file_id="",
            shared_by="user-123",
            shared_with="user-456",
            permission=FilePermission.READ
        )
        
        with pytest.raises(MissingRequiredFieldException, match="file_id"):
            share.validate()
    
    def test_missing_shared_by_raises_exception(self):
        """Test that missing shared_by raises exception"""
        share = FileShare(
            id="share-123",
            file_id="file-123",
            shared_by="",
            shared_with="user-456",
            permission=FilePermission.READ
        )
        
        with pytest.raises(MissingRequiredFieldException, match="shared_by"):
            share.validate()
    
    def test_missing_shared_with_raises_exception(self):
        """Test that missing shared_with raises exception"""
        share = FileShare(
            id="share-123",
            file_id="file-123",
            shared_by="user-123",
            shared_with="",
            permission=FilePermission.READ
        )
        
        with pytest.raises(MissingRequiredFieldException, match="shared_with"):
            share.validate()
    
    def test_sharing_with_self_raises_exception(self):
        """Test that sharing with self raises exception"""
        share = FileShare(
            id="share-123",
            file_id="file-123",
            shared_by="user-123",
            shared_with="user-123",
            permission=FilePermission.READ
        )
        
        with pytest.raises(ValidationException, match="Cannot share file with yourself"):
            share.validate()
    
    def test_expiration_in_past_raises_exception(self):
        """Test that expiration date in past raises exception"""
        share = FileShare(
            id="share-123",
            file_id="file-123",
            shared_by="user-123",
            shared_with="user-456",
            permission=FilePermission.READ,
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        
        with pytest.raises(ValidationException, match="cannot be in the past"):
            share.validate()


@pytest.mark.unit
class TestFileShareExpiration:
    """Test expiration checks"""
    
    def test_is_expired_returns_true_for_expired_share(self):
        """Test is_expired returns True for expired share"""
        share = FileShare(
            id="share-123",
            file_id="file-123",
            shared_by="user-123",
            shared_with="user-456",
            permission=FilePermission.READ,
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        
        assert share.is_expired() is True
    
    def test_is_expired_returns_false_for_active_share(self):
        """Test is_expired returns False for active share"""
        share = FileShare(
            id="share-123",
            file_id="file-123",
            shared_by="user-123",
            shared_with="user-456",
            permission=FilePermission.READ,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        assert share.is_expired() is False
    
    def test_is_expired_returns_false_when_no_expiration(self):
        """Test is_expired returns False when no expiration set"""
        share = FileShare(
            id="share-123",
            file_id="file-123",
            shared_by="user-123",
            shared_with="user-456",
            permission=FilePermission.READ,
            expires_at=None
        )
        
        assert share.is_expired() is False
    
    def test_is_active_returns_true_for_active_share(self):
        """Test is_active returns True for active share"""
        share = FileShare(
            id="share-123",
            file_id="file-123",
            shared_by="user-123",
            shared_with="user-456",
            permission=FilePermission.READ,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        assert share.is_active() is True
    
    def test_is_active_returns_false_for_expired_share(self):
        """Test is_active returns False for expired share"""
        share = FileShare(
            id="share-123",
            file_id="file-123",
            shared_by="user-123",
            shared_with="user-456",
            permission=FilePermission.READ,
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        
        assert share.is_active() is False


@pytest.mark.unit
class TestFileSharePermissions:
    """Test permission checks"""
    
    def test_has_read_permission_returns_true_for_read_permission(self):
        """Test has_read_permission returns True for READ permission"""
        share = FileShare(
            id="share-123",
            file_id="file-123",
            shared_by="user-123",
            shared_with="user-456",
            permission=FilePermission.READ
        )
        
        assert share.has_read_permission() is True
    
    def test_has_read_permission_returns_true_for_write_permission(self):
        """Test has_read_permission returns True for WRITE permission (includes read)"""
        share = FileShare(
            id="share-123",
            file_id="file-123",
            shared_by="user-123",
            shared_with="user-456",
            permission=FilePermission.WRITE
        )
        
        assert share.has_read_permission() is True
    
    def test_has_write_permission_returns_true_for_write_permission(self):
        """Test has_write_permission returns True for WRITE permission"""
        share = FileShare(
            id="share-123",
            file_id="file-123",
            shared_by="user-123",
            shared_with="user-456",
            permission=FilePermission.WRITE
        )
        
        assert share.has_write_permission() is True
    
    def test_has_write_permission_returns_false_for_read_permission(self):
        """Test has_write_permission returns False for READ permission"""
        share = FileShare(
            id="share-123",
            file_id="file-123",
            shared_by="user-123",
            shared_with="user-456",
            permission=FilePermission.READ
        )
        
        assert share.has_write_permission() is False


@pytest.mark.unit
class TestFileShareExpirationManagement:
    """Test expiration management methods"""
    
    def test_extend_expiration_extends_by_hours(self):
        """Test extend_expiration extends expiration by hours"""
        initial_expiration = datetime.utcnow() + timedelta(hours=24)
        share = FileShare(
            id="share-123",
            file_id="file-123",
            shared_by="user-123",
            shared_with="user-456",
            permission=FilePermission.READ,
            expires_at=initial_expiration
        )
        
        share.extend_expiration(12)
        
        expected_expiration = initial_expiration + timedelta(hours=12)
        time_diff = abs((share.expires_at - expected_expiration).total_seconds())
        assert time_diff < 1  # Within 1 second tolerance
    
    def test_extend_expiration_sets_expiration_if_none(self):
        """Test extend_expiration sets expiration if not set"""
        share = FileShare(
            id="share-123",
            file_id="file-123",
            shared_by="user-123",
            shared_with="user-456",
            permission=FilePermission.READ,
            expires_at=None
        )
        
        share.extend_expiration(24)
        
        assert share.expires_at is not None
    
    def test_set_expiration_sets_expiration_from_now(self):
        """Test set_expiration sets expiration from now"""
        share = FileShare(
            id="share-123",
            file_id="file-123",
            shared_by="user-123",
            shared_with="user-456",
            permission=FilePermission.READ
        )
        
        share.set_expiration(48)
        
        expected_expiration = datetime.utcnow() + timedelta(hours=48)
        time_diff = abs((share.expires_at - expected_expiration).total_seconds())
        assert time_diff < 1  # Within 1 second tolerance
    
    def test_revoke_sets_expiration_to_now(self):
        """Test revoke sets expiration to now"""
        share = FileShare(
            id="share-123",
            file_id="file-123",
            shared_by="user-123",
            shared_with="user-456",
            permission=FilePermission.READ,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        share.revoke()
        
        assert share.expires_at is not None
        time_diff = abs((share.expires_at - datetime.utcnow()).total_seconds())
        assert time_diff < 1  # Within 1 second tolerance


@pytest.mark.unit
class TestFileSharePermissionManagement:
    """Test permission upgrade/downgrade"""
    
    def test_upgrade_to_write_changes_permission_to_write(self):
        """Test upgrade_to_write changes permission to WRITE"""
        share = FileShare(
            id="share-123",
            file_id="file-123",
            shared_by="user-123",
            shared_with="user-456",
            permission=FilePermission.READ
        )
        
        share.upgrade_to_write()
        
        assert share.permission == FilePermission.WRITE
    
    def test_downgrade_to_read_changes_permission_to_read(self):
        """Test downgrade_to_read changes permission to READ"""
        share = FileShare(
            id="share-123",
            file_id="file-123",
            shared_by="user-123",
            shared_with="user-456",
            permission=FilePermission.WRITE
        )
        
        share.downgrade_to_read()
        
        assert share.permission == FilePermission.READ


@pytest.mark.unit
class TestFilePermissionEnum:
    """Test FilePermission enum"""
    
    def test_read_permission_value(self):
        """Test READ permission has correct value"""
        assert FilePermission.READ.value == "read"
    
    def test_write_permission_value(self):
        """Test WRITE permission has correct value"""
        assert FilePermission.WRITE.value == "write"

