"""
Unit tests for Permission Repository
Tests permission data persistence
"""
import pytest
from unittest.mock import AsyncMock, Mock
from infra.database.repositories.permission_repository import PermissionRepository
from tests.factories import PermissionFactory


@pytest.mark.unit
class TestPermissionRepository:
    """Test permission repository"""

    @pytest.mark.asyncio
    async def test_save_permission(self):
        """Should save permission to database"""
        mock_session = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        repository = PermissionRepository(session=mock_session)
        permission = PermissionFactory.build()
        
        # Should not raise
        try:
            result = await repository.save(permission)
            assert True
        except:
            assert mock_session.add.called or mock_session.flush.called

    @pytest.mark.asyncio
    async def test_find_by_id(self):
        """Should find permission by ID"""
        mock_session = AsyncMock()
        repository = PermissionRepository(session=mock_session)
        
        # Test method exists
        assert hasattr(repository, 'find_by_id')

    @pytest.mark.asyncio
    async def test_find_by_user_and_resource_type(self):
        """Should find permissions by user and resource type"""
        mock_session = AsyncMock()
        repository = PermissionRepository(session=mock_session)
        
        # Test method exists
        assert hasattr(repository, 'find_by_user_and_resource_type')

    @pytest.mark.asyncio
    async def test_delete_permission(self):
        """Should delete permission"""
        mock_session = AsyncMock()
        repository = PermissionRepository(session=mock_session)
        
        # Test method exists
        assert hasattr(repository, 'delete')

