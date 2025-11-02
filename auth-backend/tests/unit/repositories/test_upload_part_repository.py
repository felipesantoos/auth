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
        """Test saving upload part"""
        session_mock = AsyncMock()
        session_mock.add = Mock()
        session_mock.commit = AsyncMock()
        
        from infra.database.repositories.upload_part_repository import UploadPartRepository
        repository = UploadPartRepository(session_mock)
        
        part_data = Mock(id=None, upload_id="upload-123", part_number=1)
        await repository.save(part_data)
        
        session_mock.add.assert_called_once()
        session_mock.commit.assert_called_once()

