"""
Unit tests for File Repository
Tests file data access logic with mocked database
"""
import pytest
from unittest.mock import AsyncMock, Mock


@pytest.mark.unit
class TestFileRepository:
    """Test file repository"""
    
    @pytest.mark.asyncio
    async def test_save_file_metadata(self):
        """Test saving file metadata"""
        session_mock = AsyncMock()
        session_mock.add = Mock()
        session_mock.commit = AsyncMock()
        session_mock.refresh = AsyncMock()
        
        from infra.database.repositories.file_repository import FileRepository
        repository = FileRepository(session_mock)
        
        file_data = Mock(
            id=None,
            user_id="user-123",
            original_filename="test.pdf",
            stored_filename="abc123.pdf",
            file_size=1024,
            mime_type="application/pdf"
        )
        
        await repository.save(file_data)
        
        session_mock.add.assert_called_once()
        # Commit is not automatic in repositories
    
    @pytest.mark.asyncio
    async def test_get_by_user_id(self):
        """Test getting files by user ID"""
        session_mock = AsyncMock()
        session_mock.execute = AsyncMock()
        session_mock.execute.return_value.scalars = Mock()
        session_mock.execute.return_value.scalars.return_value.all = Mock(return_value=[])
        
        from infra.database.repositories.file_repository import FileRepository
        repository = FileRepository(session_mock)
        
        result = await repository.find_by_user("user-123")
        
        assert isinstance(result, list)
        session_mock.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_delete_file(self):
        """Test deleting file"""
        session_mock = AsyncMock()
        db_file_mock = Mock(id="file-123")
        
        session_mock.execute = AsyncMock()
        session_mock.execute.return_value.scalar_one_or_none = Mock(return_value=db_file_mock)
        session_mock.delete = Mock()
        session_mock.commit = AsyncMock()
        
        from infra.database.repositories.file_repository import FileRepository
        repository = FileRepository(session_mock)
        
        await repository.delete("file-123")
        
        session_mock.delete.assert_called_with(db_file_mock)
        session_mock.commit.assert_called()

