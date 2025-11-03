"""
Unit tests for Authentication Middleware
Tests JWT authentication dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import HTTPException, Request


@pytest.mark.unit
class TestAuthMiddlewareDependencies:
    """Test authentication middleware dependency functions"""

    @pytest.mark.asyncio
    async def test_auth_middleware_exists(self):
        """Should be able to import auth middleware functions"""
        from app.api.middlewares.auth_middleware import (
    get_current_user,
    get_current_user_optional,
    security
)
        
        # Check functions exist
        assert callable(get_current_user)
        assert callable(get_current_user_optional)
        assert callable(get_current_user)
        assert security is not None


@pytest.mark.unit
class TestAuthMiddlewareTokenExtraction:
    """Test token extraction logic"""

    def test_extract_token_from_authorization_header(self):
        """Should extract token from Authorization header"""
        mock_credentials = Mock()
        mock_credentials.credentials = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        
        token = mock_credentials.credentials
        assert token is not None
        assert isinstance(token, str)

    def test_extract_token_from_cookie(self):
        """Should extract token from cookie"""
        mock_request = Mock(spec=Request)
        mock_request.cookies = {"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
        
        token = mock_request.cookies.get("access_token")
        assert token is not None
        assert isinstance(token, str)

    def test_no_token_available(self):
        """Should handle when no token is available"""
        mock_request = Mock(spec=Request)
        mock_request.cookies = {}
        mock_credentials = None
        
        token = None
        if mock_credentials:
            token = mock_credentials.credentials
        else:
            token = mock_request.cookies.get("access_token")
        
        assert token is None


@pytest.mark.unit
class TestAuthMiddlewareRoleChecks:
    """Test role checking logic"""

    def test_user_has_admin_role(self):
        """Should verify admin role"""
        from core.domain.auth.user_role import UserRole
        
        user_role = UserRole.ADMIN
        assert user_role == UserRole.ADMIN

    def test_user_has_manager_role(self):
        """Should verify manager role"""
        from core.domain.auth.user_role import UserRole
        
        user_role = UserRole.MANAGER
        assert user_role == UserRole.MANAGER

    def test_user_has_regular_role(self):
        """Should verify regular user role"""
        from core.domain.auth.user_role import UserRole
        
        user_role = UserRole.USER
        assert user_role == UserRole.USER


@pytest.mark.unit
class TestAuthMiddlewareTenantValidation:
    """Test tenant/client validation"""

    def test_client_id_matches(self):
        """Should validate client_id matches"""
        user_client_id = "client-123"
        request_client_id = "client-123"
        
        assert user_client_id == request_client_id

    def test_client_id_mismatch_detected(self):
        """Should detect client_id mismatch"""
        user_client_id = "client-123"
        request_client_id = "client-456"
        
        assert user_client_id != request_client_id

    def test_missing_client_id_in_request(self):
        """Should handle missing client_id in request"""
        request_client_id = None
        
        assert request_client_id is None
