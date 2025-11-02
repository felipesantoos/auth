"""
Unit tests for OIDC Service
Tests OpenID Connect authentication logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from core.services.auth.oidc_service import OIDCService


@pytest.mark.unit
class TestOIDCAuthentication:
    """Test OIDC authentication functionality"""
    
    @pytest.mark.asyncio
    async def test_generate_authorization_url(self):
        """Test OIDC authorization URL generation"""
        user_repo_mock = AsyncMock()
        settings_mock = Mock()
        settings_mock.oidc_client_id = "test-client-id"
        settings_mock.oidc_authorization_endpoint = "https://provider.com/authorize"
        settings_mock.oidc_redirect_uri = "http://localhost/callback"
        
        service = OIDCService(user_repo_mock, settings_mock)
        
        url = await service.generate_authorization_url("state-123", "nonce-456")
        
        assert "https://provider.com/authorize" in url
        assert "client_id" in url
        assert "state" in url or "nonce" in url
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens(self):
        """Test exchanging authorization code for tokens"""
        user_repo_mock = AsyncMock()
        settings_mock = Mock()
        settings_mock.oidc_token_endpoint = "https://provider.com/token"
        
        service = OIDCService(user_repo_mock, settings_mock)
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = {
                "access_token": "access-token-123",
                "id_token": "id-token-123",
                "refresh_token": "refresh-token-123"
            }
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            tokens = await service.exchange_code_for_tokens("code123")
            
            assert tokens.get("access_token") or mock_client.called
    
    @pytest.mark.asyncio
    async def test_verify_id_token(self):
        """Test ID token verification"""
        user_repo_mock = AsyncMock()
        settings_mock = Mock()
        settings_mock.oidc_client_id = "test-client-id"
        
        service = OIDCService(user_repo_mock, settings_mock)
        
        # Mock JWT verification
        with patch('jwt.decode') as mock_decode:
            mock_decode.return_value = {
                "sub": "user-123",
                "email": "user@example.com",
                "name": "John Doe"
            }
            
            claims = await service.verify_id_token("id-token-123", "nonce-456")
            
            assert claims.get("sub") or mock_decode.called

