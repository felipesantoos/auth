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
        """Test saving pending upload"""
        session_mock = AsyncMock()
        session_mock.add = Mock()
        session_mock.commit = AsyncMock()
        
        from infra.database.repositories.pending_upload_repository import PendingUploadRepository
        repository = PendingUploadRepository(session_mock)
        
        upload_data = Mock(id=None, user_id="user-123", filename="file.mp4")
        await repository.save(upload_data)
        
        session_mock.add.assert_called_once()
        session_mock.commit.assert_called_once()

