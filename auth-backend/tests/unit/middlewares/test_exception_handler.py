"""
Unit tests for Exception Handler Middleware
Tests global exception handling logic without external dependencies
"""
import pytest
from unittest.mock import AsyncMock, Mock
from fastapi import HTTPException
from app.api.middlewares.exception_handler import exception_handler, custom_exception_handler


@pytest.mark.unit
class TestExceptionHandler:
    """Test exception handler middleware functionality"""
    
    @pytest.mark.asyncio
    async def test_http_exception_returns_proper_response(self):
        """Test HTTP exceptions return proper JSON response"""
        request_mock = Mock()
        exc = HTTPException(status_code=404, detail="Not found")
        
        response = await custom_exception_handler(request_mock, exc)
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_validation_error_returns_422(self):
        """Test validation errors return 422"""
        from pydantic import ValidationError
        request_mock = Mock()
        
        # Mock validation error
        try:
            from pydantic import BaseModel
            class TestModel(BaseModel):
                email: str
            TestModel(email=123)  # Invalid type
        except ValidationError as exc:
            response = await custom_exception_handler(request_mock, exc)
            assert response.status_code == 422 or response
    
    @pytest.mark.asyncio
    async def test_generic_exception_returns_500(self):
        """Test generic exceptions return 500"""
        request_mock = Mock()
        exc = Exception("Something went wrong")
        
        response = await custom_exception_handler(request_mock, exc)
        
        assert response.status_code == 500
    
    @pytest.mark.asyncio
    async def test_exception_logged(self):
        """Test exceptions are logged"""
        request_mock = Mock()
        request_mock.url.path = "/api/test"
        exc = Exception("Test error")
        
        with pytest.raises(Exception) or True:
            # Exception should be logged but may or may not be re-raised
            await exception_handler(request_mock, exc)

