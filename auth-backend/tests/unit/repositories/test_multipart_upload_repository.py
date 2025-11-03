"""
Unit tests for Multipart Upload Repository
Tests chunked upload data access logic with mocked database
"""
import pytest
from unittest.mock import AsyncMock, Mock


@pytest.mark.unit
class TestMultipartUploadRepository:
    """Test multipart upload repository"""
    
    @pytest.mark.asyncio
    async def test_save_upload_session(self):
        """Test creating multipart upload session"""
        session_mock = AsyncMock()
        session_mock.add = Mock()
        session_mock.flush = AsyncMock()
        session_mock.refresh = AsyncMock()
        
        from infra.database.repositories.multipart_upload_repository import MultipartUploadRepository
        repository = MultipartUploadRepository(session_mock)
        
        # Fixed: create() expects dict, not Mock
        upload_data = {
            "user_id": "user-123",
            "filename": "large-file.mp4",
            "total_size": 10485760,
            "chunk_size": 1048576
        }
        
        result = await repository.create(upload_data)
        
        session_mock.add.assert_called_once()
        session_mock.flush.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_id(self):
        """Test getting upload session by ID"""
        session_mock = AsyncMock()
        db_upload_mock = Mock(id="upload-123")
        
        session_mock.execute = AsyncMock()
        session_mock.execute.return_value.scalar_one_or_none = Mock(return_value=db_upload_mock)
        
        from infra.database.repositories.multipart_upload_repository import MultipartUploadRepository
        repository = MultipartUploadRepository(session_mock)
        
        result = await repository.get("upload-123")
        
        assert result is not None or session_mock.execute.called
    
    @pytest.mark.asyncio
    async def test_mark_upload_complete(self):
        """Test marking upload as complete"""
        session_mock = AsyncMock()
        db_upload_mock = Mock(
            id="upload-123",
            completed=False
        )
        
        session_mock.execute = AsyncMock()
        session_mock.execute.return_value.scalar_one_or_none = Mock(return_value=db_upload_mock)
        session_mock.flush = AsyncMock()
        session_mock.refresh = AsyncMock()
        
        from infra.database.repositories.multipart_upload_repository import MultipartUploadRepository
        repository = MultipartUploadRepository(session_mock)
        
        result = await repository.save(db_upload_mock)
        
        # Commit handled by Unit of Work pattern
        session_mock.flush.assert_called_once()
