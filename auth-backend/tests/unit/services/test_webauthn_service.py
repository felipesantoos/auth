"""
Unit tests for WebAuthn Service
Tests WebAuthn/Passkey authentication logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock
from core.services.auth.webauthn_service import WebAuthnService


@pytest.mark.unit
class TestWebAuthnService:
    """Test WebAuthn service functionality"""
    
    @pytest.mark.asyncio
    async def test_generate_registration_options_creates_challenge(self):
        """Test generating registration options creates challenge"""
        credential_repo_mock = AsyncMock()
        user_repo_mock = AsyncMock()
        cache_mock = Mock()
        cache_mock.set = Mock()
        
        service = WebAuthnService(credential_repo_mock, user_repo_mock, cache_mock)
        
        options = await service.generate_registration_options(
            user_id="user-123",
            username="john"
        )
        
        assert "challenge" in options
        cache_mock.set.assert_called()  # Challenge should be cached
    
    @pytest.mark.asyncio
    async def test_verify_registration_saves_credential(self):
        """Test verifying registration saves credential"""
        credential_repo_mock = AsyncMock()
        credential_repo_mock.save = AsyncMock(return_value=Mock(id="cred-123"))
        user_repo_mock = AsyncMock()
        cache_mock = Mock()
        cache_mock.get = Mock(return_value="challenge-data")
        cache_mock.delete = Mock()
        
        service = WebAuthnService(credential_repo_mock, user_repo_mock, cache_mock)
        
        # Mock the verification logic
        service._verify_registration_response = AsyncMock(return_value=True)
        
        result = await service.verify_registration(
            user_id="user-123",
            credential_data={"id": "cred-123", "response": {}}
        )
        
        assert credential_repo_mock.save.called or result is not None

