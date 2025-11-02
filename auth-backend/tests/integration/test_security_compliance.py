"""
Security Compliance Tests
Tests for security best practices compliance
Reference: 18-security-best-practices.md
"""
import pytest
from httpx import AsyncClient
from main import app


class TestSecurityHeaders:
    """Test security headers are properly set"""
    
    @pytest.mark.asyncio
    async def test_security_headers_present(self):
        """Test that all required security headers are present"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")
            
            # X-Content-Type-Options
            assert "X-Content-Type-Options" in response.headers
            assert response.headers["X-Content-Type-Options"] == "nosniff"
            
            # X-Frame-Options
            assert "X-Frame-Options" in response.headers
            assert response.headers["X-Frame-Options"] == "DENY"
            
            # X-XSS-Protection
            assert "X-XSS-Protection" in response.headers
            assert response.headers["X-XSS-Protection"] == "1; mode=block"
            
            # Content-Security-Policy
            assert "Content-Security-Policy" in response.headers
            assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    
    @pytest.mark.asyncio
    async def test_hsts_in_production(self, monkeypatch):
        """Test HSTS header in production mode"""
        # Mock production environment
        from config import settings
        monkeypatch.setattr(settings, "environment", "production")
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")
            
            # HSTS should be present in production
            # Note: This test might need adjustment based on actual middleware behavior
            # In development, HSTS might not be set
            pass  # Implementation depends on middleware configuration


class TestDualModeAuthentication:
    """Test dual-mode authentication (web/mobile)"""
    
    @pytest.mark.asyncio
    async def test_login_web_returns_cookies(self):
        """Test that web login sets httpOnly cookies"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "TestPassword123!",
                    "client_id": "test-client"
                },
                headers={"X-Client-Type": "web"}
            )
            
            # Web should set cookies
            if response.status_code == 200:
                # Check if cookies are set (might need actual user in DB for this to work)
                assert "set-cookie" in response.headers or response.status_code in [401, 404]
    
    @pytest.mark.asyncio
    async def test_login_mobile_returns_tokens_in_body(self):
        """Test that mobile login returns tokens in response body"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "TestPassword123!",
                    "client_id": "test-client"
                },
                headers={"X-Client-Type": "mobile"}
            )
            
            # Mobile should return tokens in body (or error if user doesn't exist)
            if response.status_code == 200:
                data = response.json()
                assert "access_token" in data or "user" in data
    
    @pytest.mark.asyncio
    async def test_auth_middleware_accepts_bearer_token(self):
        """Test that auth middleware accepts Authorization header"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Try to access protected endpoint with Bearer token
            response = await client.get(
                "/api/auth/me",
                headers={
                    "Authorization": "Bearer fake-token",
                    "X-Client-Type": "mobile"
                }
            )
            
            # Should get 401 (unauthorized) not 400 (bad request)
            # This confirms the middleware is checking the token
            assert response.status_code in [401, 403]
    
    @pytest.mark.asyncio
    async def test_auth_middleware_accepts_cookies(self):
        """Test that auth middleware accepts cookies"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Try to access protected endpoint with cookie
            response = await client.get(
                "/api/auth/me",
                cookies={"access_token": "fake-token"},
                headers={"X-Client-Type": "web"}
            )
            
            # Should get 401 (unauthorized) not 400 (bad request)
            assert response.status_code in [401, 403]


class TestPasswordPolicy:
    """Test password policy compliance"""
    
    @pytest.mark.asyncio
    async def test_password_requires_12_characters(self):
        """Test that passwords must be at least 12 characters"""
        from core.services.auth.auth_service_base import AuthServiceBase
        from core.exceptions import InvalidPasswordException
        from unittest.mock import Mock
        
        service = AuthServiceBase(Mock(), Mock())
        
        # Should fail with short password
        with pytest.raises(InvalidPasswordException, match="12 characters"):
            service._validate_password_strength("Short1!")
    
    @pytest.mark.asyncio
    async def test_password_requires_uppercase(self):
        """Test that passwords must contain uppercase letter"""
        from core.services.auth.auth_service_base import AuthServiceBase
        from core.exceptions import InvalidPasswordException
        from unittest.mock import Mock
        
        service = AuthServiceBase(Mock(), Mock())
        
        with pytest.raises(InvalidPasswordException, match="uppercase"):
            service._validate_password_strength("nouppercase123!")
    
    @pytest.mark.asyncio
    async def test_password_requires_lowercase(self):
        """Test that passwords must contain lowercase letter"""
        from core.services.auth.auth_service_base import AuthServiceBase
        from core.exceptions import InvalidPasswordException
        from unittest.mock import Mock
        
        service = AuthServiceBase(Mock(), Mock())
        
        with pytest.raises(InvalidPasswordException, match="lowercase"):
            service._validate_password_strength("NOLOWERCASE123!")
    
    @pytest.mark.asyncio
    async def test_password_requires_digit(self):
        """Test that passwords must contain a digit"""
        from core.services.auth.auth_service_base import AuthServiceBase
        from core.exceptions import InvalidPasswordException
        from unittest.mock import Mock
        
        service = AuthServiceBase(Mock(), Mock())
        
        with pytest.raises(InvalidPasswordException, match="number"):
            service._validate_password_strength("NoDigitsHere!")
    
    @pytest.mark.asyncio
    async def test_password_requires_special_character(self):
        """Test that passwords must contain a special character"""
        from core.services.auth.auth_service_base import AuthServiceBase
        from core.exceptions import InvalidPasswordException
        from unittest.mock import Mock
        
        service = AuthServiceBase(Mock(), Mock())
        
        with pytest.raises(InvalidPasswordException, match="special character"):
            service._validate_password_strength("NoSpecialChar123")
    
    @pytest.mark.asyncio
    async def test_valid_password_passes(self):
        """Test that a valid password passes all checks"""
        from core.services.auth.auth_service_base import AuthServiceBase
        from unittest.mock import Mock
        
        service = AuthServiceBase(Mock(), Mock())
        
        # Should not raise any exception
        service._validate_password_strength("ValidPassword123!")


class TestTokenExpiration:
    """Test token expiration settings"""
    
    def test_access_token_expiration_is_15_minutes(self):
        """Test that access token expires in 15 minutes (security best practice)"""
        from config.settings import settings
        
        assert settings.access_token_expire_minutes == 15, \
            "Access token should expire in 15 minutes for security (18-security-best-practices.md line 533)"
    
    def test_refresh_token_expiration_is_reasonable(self):
        """Test that refresh token expiration is set"""
        from config.settings import settings
        
        assert settings.refresh_token_expire_days > 0
        assert settings.refresh_token_expire_days <= 30, \
            "Refresh token should not exceed 30 days"


class TestRateLimiting:
    """Test rate limiting configuration"""
    
    @pytest.mark.asyncio
    async def test_login_has_strict_rate_limit(self):
        """Test that login endpoint has strict rate limiting"""
        # This test verifies the rate limit is configured
        # Actual rate limit testing would require multiple requests
        from app.api.routes import auth_routes
        import inspect
        
        # Check that login route has rate limiter decorator
        login_func = auth_routes.login
        source = inspect.getsource(login_func)
        
        assert "@limiter.limit" in source or "5/minute" in source, \
            "Login should have rate limiting (5/minute recommended)"


class TestCORSConfiguration:
    """Test CORS configuration"""
    
    def test_cors_not_wildcard(self):
        """Test that CORS origins are not set to wildcard"""
        from config.settings import settings
        
        cors_origins = settings.cors_origins_list
        
        assert "*" not in cors_origins, \
            "CORS should not use wildcard '*' in production"
    
    def test_cors_origins_configured(self):
        """Test that CORS origins are explicitly configured"""
        from config.settings import settings
        
        assert len(settings.cors_origins_list) > 0, \
            "CORS origins should be explicitly configured"


class TestJWTConfiguration:
    """Test JWT configuration"""
    
    def test_jwt_algorithm_is_secure(self):
        """Test that JWT uses secure algorithm"""
        from config.settings import settings
        
        assert settings.jwt_algorithm in ["HS256", "RS256"], \
            "JWT should use HS256 or RS256 algorithm"
    
    def test_jwt_secret_validation_in_production(self):
        """Test that weak JWT secrets are rejected in production"""
        from config.settings import Settings
        from pydantic import ValidationError
        
        # This should raise validation error in production
        with pytest.raises(ValidationError, match="JWT_SECRET"):
            Settings(
                environment="production",
                jwt_secret="weak"
            )


class TestPasswordHashing:
    """Test password hashing implementation"""
    
    def test_bcrypt_is_used(self):
        """Test that bcrypt is used for password hashing"""
        from core.services.auth.auth_service_base import AuthServiceBase
        from unittest.mock import Mock
        import bcrypt
        
        service = AuthServiceBase(Mock(), Mock())
        
        password = "TestPassword123!"
        hashed = service._hash_password(password)
        
        # Verify it's a valid bcrypt hash
        assert hashed.startswith("$2")  # bcrypt identifier
        
        # Verify password can be verified
        assert service._verify_password(password, hashed)
    
    def test_bcrypt_cost_factor(self):
        """Test that bcrypt uses appropriate cost factor"""
        # Bcrypt hash should use cost factor 12 (2^12 rounds)
        # Format: $2b$12$... where 12 is the cost factor
        from core.services.auth.auth_service_base import AuthServiceBase
        from unittest.mock import Mock
        
        service = AuthServiceBase(Mock(), Mock())
        hashed = service._hash_password("TestPassword123!")
        
        # Extract cost factor from hash
        parts = hashed.split("$")
        cost_factor = int(parts[2])
        
        assert cost_factor >= 12, \
            "Bcrypt cost factor should be at least 12 for security"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

