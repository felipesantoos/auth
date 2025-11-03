"""
Unit tests for Backup Code Repository
Tests backup code data access logic with mocked database
"""
import pytest
from unittest.mock import AsyncMock, Mock
from infra.database.repositories.backup_code_repository import BackupCodeRepository
from core.domain.auth.backup_code import BackupCode


@pytest.mark.unit
class TestBackupCodeRepositorySave:
    """Test saving backup codes"""
    
    @pytest.mark.asyncio
    async def test_save_backup_code(self):
        """Test saving backup code to database"""
        session_mock = AsyncMock()
        session_mock.add = Mock()
        session_mock.commit = AsyncMock()
        session_mock.refresh = AsyncMock()
        
        repository = BackupCodeRepository(session_mock)
        
        code = BackupCode(
            client_id="test-client",
            id=None,
            user_id="user-123",
            code_hash="hashed_code",
            used=False
        )
        
        result = await repository.save(code)
        
        session_mock.add.assert_called_once()
        # Commit is not automatic in repositories


@pytest.mark.unit
class TestBackupCodeRepositoryGet:
    """Test retrieving backup codes"""
    
    @pytest.mark.asyncio
    async def test_get_by_user_id(self):
        """Test getting backup codes by user ID"""
        session_mock = AsyncMock()
        session_mock.execute = AsyncMock()
        session_mock.execute.return_value.scalars = Mock()
        session_mock.execute.return_value.scalars.return_value.all = Mock(return_value=[])
        
        repository = BackupCodeRepository(session_mock)
        
        result = await repository.find_unused_codes(user_id="user-123", client_id="test-client")
        
        assert isinstance(result, list)
        session_mock.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_unused_codes(self):
        """Test getting unused backup codes"""
        session_mock = AsyncMock()
        session_mock.execute = AsyncMock()
        session_mock.execute.return_value.scalars = Mock()
        session_mock.execute.return_value.scalars.return_value.all = Mock(return_value=[])
        
        repository = BackupCodeRepository(session_mock)
        
        result = await repository.get_unused_codes("user-123")
        
        assert isinstance(result, list)


@pytest.mark.unit
class TestBackupCodeRepositoryMarkUsed:
    """Test marking backup codes as used"""
    
    @pytest.mark.asyncio
    async def test_mark_code_as_used(self):
        """Test marking backup code as used"""
        session_mock = AsyncMock()
        db_code_mock = Mock(
            id="code-123",
            used=False,
            mark_used=Mock()
        )
        
        session_mock.execute = AsyncMock()
        session_mock.execute.return_value.scalar_one_or_none = Mock(return_value=db_code_mock)
        session_mock.commit = AsyncMock()
        
        repository = BackupCodeRepository(session_mock)
        
        await repository.mark_used("code-123")
        
        session_mock.commit.assert_called()

