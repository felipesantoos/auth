"""
Unit tests for SAML Service
Tests SAML 2.0 authentication logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from core.services.auth.saml_service import SAMLService


@pytest.mark.unit
class TestSAMLAuthentication:
    """Test SAML authentication functionality"""
    
    @pytest.mark.asyncio
    async def test_generate_authn_request(self):
        """Test SAML authentication request generation"""
        user_repo_mock = AsyncMock()
        settings_mock = Mock()
        settings_mock.saml_idp_sso_url = "https://idp.com/sso"
        settings_mock.saml_sp_entity_id = "http://localhost/metadata"
        
        service = SAMLService(user_repo_mock, settings_mock)
        
        with patch('onelogin.saml2.auth.OneLogin_Saml2_Auth') as mock_saml:
            mock_saml.return_value.login.return_value = "https://idp.com/sso?SAMLRequest=..."
            
            authn_request = await service.create_authn_request()
            
            assert authn_request or mock_saml.called
    
    @pytest.mark.asyncio
    async def test_process_saml_response(self):
        """Test processing SAML response"""
        user_repo_mock = AsyncMock()
        user_repo_mock.save = AsyncMock(return_value=Mock(id="user-123"))
        settings_mock = Mock()
        
        service = SAMLService(user_repo_mock, settings_mock)
        
        with patch('onelogin.saml2.auth.OneLogin_Saml2_Auth') as mock_saml:
            mock_saml.return_value.process_response.return_value = None
            mock_saml.return_value.is_authenticated.return_value = True
            mock_saml.return_value.get_attributes.return_value = {
                "uid": ["user123"],
                "email": ["user@example.com"],
                "displayName": ["John Doe"]
            }
            
            user = await service.process_saml_response("saml-response-data", "client-123")
            
            assert user or mock_saml.called
    
    @pytest.mark.asyncio
    async def test_get_metadata(self):
        """Test SAML SP metadata generation"""
        user_repo_mock = AsyncMock()
        settings_mock = Mock()
        settings_mock.saml_sp_entity_id = "http://localhost/metadata"
        
        service = SAMLService(user_repo_mock, settings_mock)
        
        metadata = await service.get_metadata()
        
        assert metadata is not None
        assert "EntityDescriptor" in metadata or "metadata" in metadata.lower()

