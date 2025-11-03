"""
Unit tests for Pending Upload Repository
"""
import pytest
from unittest.mock import AsyncMock, Mock


@pytest.mark.unit
class TestPendingUploadRepository:
    """Test pending upload repository"""
    
    @pytest.mark.asyncio
    async def test_save_pending_upload(self):
        """Test creating pending upload"""
        session_mock = AsyncMock()
        session_mock.add = Mock()
        session_mock.flush = AsyncMock()
        session_mock.refresh = AsyncMock()
        
        from infra.database.repositories.pending_upload_repository import PendingUploadRepository
        repository = PendingUploadRepository(session_mock)
        
        # Fixed: create() expects dict, PendingUploadRepository has no save()
        upload_data = {
            "user_id": "user-123",
            "filename": "file.mp4",
            "file_size": 1048576
        }
        
        result = await repository.create(upload_data)
        
        session_mock.add.assert_called_once()
        session_mock.flush.assert_called_once()
