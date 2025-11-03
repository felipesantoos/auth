"""
Unit tests for OAuth Service
Tests OAuth authentication logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock
from core.services.auth.oauth_service import OAuthService


@pytest.mark.unit
class TestOAuthService:
    """Test OAuth service functionality"""
    
    @pytest.mark.asyncio
    async def test_generate_authorization_url_returns_url(self):
        """Test OAuth authorization URL generation"""
        user_repo_mock = AsyncMock()
        settings_mock = Mock()
        settings_mock.oauth_google_client_id = "test-client-id"
        settings_mock.oauth_google_redirect_uri = "http://localhost/callback"
        
        service = OAuthService(user_repo_mock, settings_mock, settings_provider_mock := AsyncMock())
        
        url = await service.generate_authorization_url("google", "state-123")
        
        assert "http" in url
        assert "client_id" in url or "state" in url  # URL should have OAuth params
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_token_calls_provider(self):
        """Test exchanging authorization code for token"""
        user_repo_mock = AsyncMock()
        settings_mock = Mock()
        
        service = OAuthService(user_repo_mock, settings_mock, settings_provider_mock := AsyncMock())
        service._exchange_code_google = AsyncMock(return_value={"access_token": "token123"})
        
        token = await service.exchange_code_for_token("google", "code123")
        
        assert "access_token" in token

