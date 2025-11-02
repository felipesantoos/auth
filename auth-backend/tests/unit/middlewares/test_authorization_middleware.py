"""
Unit tests for Authorization Middleware
Tests permission/role checking logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import HTTPException
from app.api.middlewares.authorization import check_permission, require_role


@pytest.mark.unit
class TestPermissionCheck:
    """Test permission checking functionality"""
    
    @pytest.mark.asyncio
    async def test_user_with_permission_allowed(self):
        """Test user with required permission is allowed"""
        user_mock = Mock()
        user_mock.id = "user-123"
        user_mock.permissions = ["users.read", "users.write"]
        
        # Should not raise
        await check_permission(user_mock, "users.read")
    
    @pytest.mark.asyncio
    async def test_user_without_permission_denied(self):
        """Test user without required permission is denied"""
        user_mock = Mock()
        user_mock.id = "user-123"
        user_mock.permissions = ["users.read"]
        
        with pytest.raises(HTTPException) as exc_info:
            await check_permission(user_mock, "users.delete")
        
        assert exc_info.value.status_code == 403
    
    @pytest.mark.asyncio
    async def test_admin_has_all_permissions(self):
        """Test admin users have all permissions"""
        admin_mock = Mock()
        admin_mock.id = "admin-123"
        admin_mock.is_admin.return_value = True
        
        # Should allow any permission for admin
        await check_permission(admin_mock, "any.permission")


@pytest.mark.unit
class TestRoleCheck:
    """Test role checking functionality"""
    
    @pytest.mark.asyncio
    async def test_user_with_required_role_allowed(self):
        """Test user with required role is allowed"""
        user_mock = Mock()
        user_mock.role = "admin"
        
        # Should not raise
        await require_role(user_mock, "admin")
    
    @pytest.mark.asyncio
    async def test_user_without_required_role_denied(self):
        """Test user without required role is denied"""
        user_mock = Mock()
        user_mock.role = "user"
        
        with pytest.raises(HTTPException) as exc_info:
            await require_role(user_mock, "admin")
        
        assert exc_info.value.status_code == 403

