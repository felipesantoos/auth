"""
Unit tests for Email Click Repository
"""
import pytest
from unittest.mock import AsyncMock, Mock


@pytest.mark.unit
class TestEmailClickRepository:
    """Test email click repository"""
    
    @pytest.mark.asyncio
    async def test_save_click(self):
        """Test saving email click event"""
        session_mock = AsyncMock()
        session_mock.add = Mock()
        session_mock.commit = AsyncMock()
        
        from infra.database.repositories.email_click_repository import EmailClickRepository
        repository = EmailClickRepository(session_mock)
        
        click_data = Mock(id=None, tracking_id="track-123", url="https://example.com")
        await repository.save(click_data)
        
        session_mock.add.assert_called_once()
        session_mock.commit.assert_called_once()

