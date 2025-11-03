"""
Unit tests for BackupCode domain model
Tests backup code validation and usage logic
"""
import pytest
from datetime import datetime
from core.domain.auth.backup_code import BackupCode
from core.exceptions import MissingRequiredFieldException, BusinessRuleException
from tests.factories import BackupCodeFactory


@pytest.mark.unit
class TestBackupCodeValidation:
    """Test BackupCode validation rules"""
    
    def test_valid_backup_code_passes_validation(self):
        """Test that a valid backup code passes validation"""
        code = BackupCodeFactory.build()
        # Should not raise
        code.validate()
    
    def test_missing_client_id_raises_exception(self):
        """Test that missing client_id raises exception"""
        code = BackupCodeFactory.build(client_id="")
        
        with pytest.raises(MissingRequiredFieldException, match="client_id"):
            code.validate()
    
    def test_missing_code_hash_raises_exception(self):
        """Test that missing code_hash raises exception"""
        code = BackupCodeFactory.build()
        code.code_hash = ""
        
        with pytest.raises(MissingRequiredFieldException, match="code_hash"):
            code.validate()


@pytest.mark.unit
class TestBackupCodeUsage:
    """Test backup code usage logic"""
    
    def test_is_used_returns_false_for_new_code(self):
        """Test is_used returns False for unused code"""
        code = BackupCodeFactory.build(used=False)
        
        assert code.is_used() is False
    
    def test_is_used_returns_true_for_used_code(self):
        """Test is_used returns True for used code"""
        code = BackupCodeFactory.create_used(user_id="user-123")
        
        assert code.is_used() is True
    
    def test_can_be_used_returns_true_for_unused_code(self):
        """Test can_be_used returns True for unused code"""
        code = BackupCodeFactory.build(used=False)
        
        assert code.can_be_used() is True
    
    def test_can_be_used_returns_false_for_used_code(self):
        """Test can_be_used returns False for used code"""
        code = BackupCodeFactory.create_used(user_id="user-123")
        
        assert code.can_be_used() is False
    
    def test_mark_as_used_sets_used_to_true(self):
        """Test mark_as_used sets used flag and timestamp"""
        code = BackupCodeFactory.build(used=False)
        
        code.mark_as_used()
        
        assert code.used is True
        assert code.used_at is not None
        assert isinstance(code.used_at, datetime)
    
    def test_mark_as_used_on_used_code_raises_exception(self):
        """Test mark_as_used on already used code raises exception"""
        code = BackupCodeFactory.create_used(user_id="user-123")
        
        with pytest.raises(BusinessRuleException, match="already been used"):
            code.mark_as_used()


@pytest.mark.unit
class TestBackupCodeCreation:
    """Test backup code creation"""
    
    def test_backup_code_created_with_all_fields(self):
        """Test creating backup code with all fields"""
        code = BackupCode(
            id="code-123",
            user_id="user-456",
            client_id="client-789",
            code_hash="hashed_code_value",
            used=False
        )
        
        assert code.id == "code-123"
        assert code.user_id == "user-456"
        assert code.client_id == "client-789"
        assert code.code_hash == "hashed_code_value"
        assert code.used is False
        assert code.used_at is None
    
    def test_backup_code_defaults_to_unused(self):
        """Test backup code defaults to used=False"""
        code = BackupCode(
            id="code-123",
            user_id="user-456",
            client_id="client-789",
            code_hash="hashed_code_value"
        )
        
        assert code.used is False
        assert code.used_at is None


@pytest.mark.unit
class TestBackupCodeBatch:
    """Test batch creation of backup codes"""
    
    def test_create_batch_creates_multiple_codes(self):
        """Test creating a batch of backup codes"""
        codes = BackupCodeFactory.create_batch(
            user_id="user-123",
            client_id="client-456",
            count=10
        )
        
        assert len(codes) == 10
        assert all(isinstance(code, BackupCode) for code in codes)
        assert all(code.user_id == "user-123" for code in codes)
        assert all(code.client_id == "client-456" for code in codes)
        assert all(not code.used for code in codes)
    
    def test_batch_codes_have_unique_ids(self):
        """Test batch codes have unique IDs"""
        codes = BackupCodeFactory.create_batch(
            user_id="user-123",
            count=5
        )
        
        ids = [code.id for code in codes]
        assert len(ids) == len(set(ids))  # All unique
    
    def test_batch_codes_have_different_hashes(self):
        """Test batch codes have different code hashes"""
        codes = BackupCodeFactory.create_batch(
            user_id="user-123",
            count=5
        )
        
        hashes = [code.code_hash for code in codes]
        assert len(hashes) == len(set(hashes))  # All unique

