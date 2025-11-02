"""
Unit tests for BackupCodeMapper
Tests conversion between database model and domain model
"""
import pytest
from datetime import datetime
from infra.database.mappers.backup_code_mapper import BackupCodeMapper
from core.domain.auth.backup_code import BackupCode
from infra.database.models.backup_code import DBBackupCode


@pytest.mark.unit
class TestBackupCodeMapperToDomain:
    """Test converting DB model to domain model"""
    
    def test_to_domain_maps_all_fields(self):
        """Test to_domain maps all fields correctly"""
        db_code = DBBackupCode(
            id="code-123",
            user_id="user-123",
            code_hash="hashed_code",
            used=False,
            used_at=None,
            created_at=datetime(2023, 1, 1)
        )
        
        domain_code = BackupCodeMapper.to_domain(db_code)
        
        assert isinstance(domain_code, BackupCode)
        assert domain_code.id == "code-123"
        assert domain_code.user_id == "user-123"
        assert domain_code.code_hash == "hashed_code"
        assert domain_code.used is False
        assert domain_code.used_at is None
    
    def test_to_domain_with_used_code(self):
        """Test converting used backup code"""
        db_code = DBBackupCode(
            id="code-123",
            user_id="user-123",
            code_hash="hashed_code",
            used=True,
            used_at=datetime(2023, 2, 1)
        )
        
        domain_code = BackupCodeMapper.to_domain(db_code)
        
        assert domain_code.used is True
        assert domain_code.used_at == datetime(2023, 2, 1)


@pytest.mark.unit
class TestBackupCodeMapperToDatabase:
    """Test converting domain model to DB model"""
    
    def test_to_database_maps_all_fields(self):
        """Test to_database maps all fields correctly"""
        domain_code = BackupCode(
            id="code-123",
            user_id="user-123",
            code_hash="hashed_backup_code",
            used=False,
            used_at=None,
            created_at=datetime(2023, 1, 1)
        )
        
        db_code = BackupCodeMapper.to_database(domain_code)
        
        assert isinstance(db_code, DBBackupCode)
        assert db_code.id == "code-123"
        assert db_code.user_id == "user-123"
        assert db_code.code_hash == "hashed_backup_code"
        assert db_code.used is False

