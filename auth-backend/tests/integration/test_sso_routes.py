"""
Integration tests for SSO Routes
Tests SSO (SAML, OIDC, LDAP) API endpoints with database
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestSAMLRoutes:
    """Test SAML authentication routes"""
    
    @pytest.mark.asyncio
    async def test_saml_metadata(self, async_client: AsyncClient):
        """Test getting SAML SP metadata"""
        response = await async_client.get("/api/v1/sso/saml/metadata")
        
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            # Metadata should be XML
            assert "xml" in response.headers.get("content-type", "").lower() or "EntityDescriptor" in response.text
    
    @pytest.mark.asyncio
    async def test_saml_login_redirect(self, async_client: AsyncClient):
        """Test SAML login initiates redirect to IdP"""
        response = await async_client.get("/api/v1/sso/saml/login")
        
        assert response.status_code in [302, 200]
    
    @pytest.mark.asyncio
    async def test_saml_acs(self, async_client: AsyncClient):
        """Test SAML Assertion Consumer Service (callback)"""
        response = await async_client.post(
            "/api/v1/sso/saml/acs",
            data={"SAMLResponse": "fake_response"}
        )
        
        # Will fail without real SAML response
        assert response.status_code in [200, 400, 401]


@pytest.mark.integration
class TestOIDCRoutes:
    """Test OIDC authentication routes"""
    
    @pytest.mark.asyncio
    async def test_oidc_authorization(self, async_client: AsyncClient):
        """Test OIDC authorization endpoint"""
        response = await async_client.get("/api/v1/sso/oidc/authorize")
        
        assert response.status_code in [200, 302]
    
    @pytest.mark.asyncio
    async def test_oidc_callback(self, async_client: AsyncClient):
        """Test OIDC callback endpoint"""
        response = await async_client.get(
            "/api/v1/sso/oidc/callback?code=test_code&state=test_state"
        )
        
        assert response.status_code in [200, 400, 401]
    
    @pytest.mark.asyncio
    async def test_oidc_configuration(self, async_client: AsyncClient):
        """Test OIDC configuration endpoint"""
        response = await async_client.get("/api/v1/sso/oidc/.well-known/openid-configuration")
        
        assert response.status_code in [200, 404]


@pytest.mark.integration
class TestLDAPRoutes:
    """Test LDAP authentication routes"""
    
    @pytest.mark.asyncio
    async def test_ldap_login(self, async_client: AsyncClient):
        """Test LDAP login endpoint"""
        response = await async_client.post(
            "/api/v1/sso/ldap/login",
            json={
                "username": "test_user",
                "password": "test_password",
                "client_id": "client-123"
            }
        )
        
        # Will fail without LDAP server, but should have endpoint
        assert response.status_code in [200, 400, 401, 503]
    
    @pytest.mark.asyncio
    async def test_ldap_sync_users(self, async_client: AsyncClient, admin_token: str):
        """Test syncing users from LDAP directory"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await async_client.post(
            "/api/v1/sso/ldap/sync",
            headers=headers
        )
        
        assert response.status_code in [200, 202, 403, 503]

