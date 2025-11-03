"""
Unit tests for Upload Part Repository
"""
import pytest
from unittest.mock import AsyncMock, Mock


@pytest.mark.unit
class TestUploadPartRepository:
    """Test upload part repository"""
    
    @pytest.mark.asyncio
    async def test_save_upload_part(self):
        """Test creating upload part"""
        session_mock = AsyncMock()
        session_mock.add = Mock()
        session_mock.flush = AsyncMock()
        session_mock.refresh = AsyncMock()
        
        from infra.database.repositories.upload_part_repository import UploadPartRepository
        repository = UploadPartRepository(session_mock)
        
        # Fixed: create() expects dict, UploadPartRepository has no save()
        part_data = {
            "upload_id": "upload-123",
            "part_number": 1,
            "etag": "etag-123"
        }
        
        result = await repository.create(part_data)
        
        session_mock.add.assert_called_once()
        session_mock.flush.assert_called_once()
