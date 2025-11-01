"""
Tests for error handling across layers
Validates exception format and API error mapping
"""
import pytest
from httpx import AsyncClient
from core.exceptions import (
    ValidationException,
    EntityNotFoundException,
    DuplicateEntityException,
    MissingRequiredFieldException,
    InvalidEmailException,
    InvalidValueException,
    BusinessRuleException,
    InvalidTokenException,
    TokenExpiredException,
)


@pytest.mark.unit
class TestDomainExceptions:
    """Test domain exception format and behavior"""
    
    def test_validation_exception_has_message(self):
        """Test ValidationException has message"""
        exc = ValidationException("Invalid input")
        
        assert exc.message == "Invalid input"
        assert "Invalid input" in str(exc)
    
    def test_entity_not_found_exception_format(self):
        """Test EntityNotFoundException message format"""
        exc = EntityNotFoundException("User", "user-123")
        
        assert "User" in exc.message
        assert "user-123" in exc.message
        assert "not found" in exc.message.lower()
    
    def test_duplicate_entity_exception_format(self):
        """Test DuplicateEntityException format"""
        exc = DuplicateEntityException("User", "email", "test@example.com")
        
        assert "User" in exc.message
        assert "email" in exc.message
        assert "test@example.com" in exc.message
    
    def test_missing_required_field_exception(self):
        """Test MissingRequiredFieldException format"""
        exc = MissingRequiredFieldException("username")
        
        assert "username" in exc.message
        assert "required" in exc.message.lower()
    
    def test_invalid_email_exception(self):
        """Test InvalidEmailException format"""
        exc = InvalidEmailException("not-an-email")
        
        assert "not-an-email" in exc.message
        assert "email" in exc.message.lower()
    
    def test_invalid_value_exception(self):
        """Test InvalidValueException format"""
        exc = InvalidValueException("age", "-5", "must be positive")
        
        assert "age" in exc.message
        assert "-5" in exc.message
        assert "must be positive" in exc.message
    
    def test_business_rule_exception(self):
        """Test BusinessRuleException format"""
        exc = BusinessRuleException("Cannot delete active entity", "ACTIVE_ENTITY_DELETE")
        
        assert exc.message == "Cannot delete active entity"
        assert exc.code == "ACTIVE_ENTITY_DELETE"
    
    def test_invalid_token_exception(self):
        """Test InvalidTokenException format"""
        exc = InvalidTokenException("Invalid verification token")
        
        assert "Invalid verification token" in exc.message
        assert "token" in exc.message.lower()
    
    def test_token_expired_exception(self):
        """Test TokenExpiredException format"""
        exc = TokenExpiredException("Reset token has expired")
        
        assert "expired" in exc.message.lower()


@pytest.mark.integration
class TestAPIErrorMapping:
    """Test that domain exceptions map to correct HTTP status codes"""
    
    @pytest.mark.asyncio
    async def test_validation_error_returns_400(self, async_client: AsyncClient):
        """Test ValidationException → 400 Bad Request"""
        # Try to register with invalid data (empty fields)
        response = await async_client.post("/api/auth/register", json={
            "username": "",  # Invalid (empty)
            "email": "test@example.com",
            "password": "Pass123",
            "name": "Test",
            "client_id": "test"
        })
        
        # Should return 400 or 422 (validation error)
        assert response.status_code in [400, 422]
        data = response.json()
        assert "detail" in data or "error" in data
    
    @pytest.mark.asyncio
    async def test_not_found_returns_404(self, async_client: AsyncClient, auth_token):
        """Test EntityNotFoundException → 404 Not Found"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Try to access non-existent resource
        response = await async_client.get(
            "/api/auth/permissions/nonexistent-permission-id",
            headers=headers
        )
        
        # Should return 404
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_duplicate_returns_409_or_400(self, async_client: AsyncClient):
        """Test DuplicateEntityException → 409 Conflict or 400"""
        # Create first user
        await async_client.post("/api/auth/register", json={
            "username": "duplicate_test",
            "email": "duplicate@test.com",
            "password": "Pass123!",
            "name": "Test",
            "client_id": "dup-test"
        })
        
        # Try to create duplicate email
        response = await async_client.post("/api/auth/register", json={
            "username": "different_username",
            "email": "duplicate@test.com",  # Same email
            "password": "Pass123!",
            "name": "Test2",
            "client_id": "dup-test"
        })
        
        # Should return 400 or 409 (conflict/duplicate)
        assert response.status_code in [400, 409]
        data = response.json()
        assert "detail" in data or "error" in data
    
    @pytest.mark.asyncio
    async def test_unauthorized_returns_401(self, async_client: AsyncClient):
        """Test authentication failure → 401 Unauthorized"""
        # Try to access protected endpoint without token
        response = await async_client.get("/api/auth/me")
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_forbidden_returns_403(self, async_client: AsyncClient, auth_token):
        """Test authorization failure → 403 Forbidden"""
        # Regular user trying to access admin endpoint
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = await async_client.get(
            "/api/auth/users",  # Admin endpoint
            headers=headers
        )
        
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_weak_password_returns_422(self, async_client: AsyncClient):
        """Test password validation → 422 Unprocessable Entity"""
        response = await async_client.post("/api/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "weak",  # Too weak
            "name": "Test",
            "client_id": "test"
        })
        
        # Should return 422 (validation error)
        assert response.status_code == 422


@pytest.mark.unit
class TestServiceErrorTranslation:
    """Test that services translate infrastructure errors to domain exceptions"""
    
    @pytest.mark.asyncio
    async def test_service_translates_integrity_error_to_duplicate(self):
        """Test service translates SQLAlchemy IntegrityError to DuplicateEntityException"""
        from unittest.mock import Mock, AsyncMock
        from sqlalchemy.exc import IntegrityError
        from core.services.auth.auth_service import AuthService
        from infra.redis.cache_service import get_cache_service
        from infra.config.settings_provider import SettingsProvider
        
        # Create mock repository that raises IntegrityError
        mock_repo = Mock()
        mock_repo.find_by_email = AsyncMock(return_value=None)
        mock_repo.find_by_username = AsyncMock(return_value=None)
        mock_repo.save = AsyncMock(side_effect=IntegrityError("", "", ""))
        
        cache = await get_cache_service()
        settings = SettingsProvider()
        auth_service = AuthService(mock_repo, cache, settings)
        
        # Should translate to domain exception
        with pytest.raises(DuplicateEntityException):
            await auth_service.register(
                username="test",
                email="test@test.com",
                password="Pass123!",
                name="Test",
                client_id="test"
            )

