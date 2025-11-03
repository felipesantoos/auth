"""
Unit tests for Exception Handler
Tests exception mapping to HTTP responses
"""
import pytest
from unittest.mock import Mock
from fastapi import Request
from fastapi.responses import JSONResponse

from app.api.middlewares.exception_handler import (
    ErrorResponse,
    handle_exception
)
from core.exceptions import (
    DomainException,
    ValidationException,
    NotFoundException,
    AuthenticationException,
    AuthorizationException
)


@pytest.mark.unit
class TestErrorResponse:
    """Test ErrorResponse class"""

    def test_create_error_response(self):
        """Should create error response with message"""
        error_resp = ErrorResponse(
            error="Validation failed",
            message="Invalid email format",
            status_code=400
        )
        
        assert error_resp.error == "Validation failed"
        assert error_resp.message == "Invalid email format"
        assert error_resp.status_code == 400

    def test_error_response_to_dict(self):
        """Should convert error response to dictionary"""
        error_resp = ErrorResponse(
            error="Not found",
            message="User not found",
            status_code=404
        )
        
        error_dict = error_resp.to_dict()
        assert "error" in error_dict
        assert "message" in error_dict
        assert error_dict["error"] == "Not found"
        assert error_dict["message"] == "User not found"

    def test_error_response_with_code(self):
        """Should include error code if provided"""
        error_resp = ErrorResponse(
            error="Business Error",
            message="Cannot proceed",
            code="BUS001",
            status_code=400
        )
        
        error_dict = error_resp.to_dict()
        assert error_dict["code"] == "BUS001"

    def test_error_response_with_details(self):
        """Should include details if provided"""
        error_resp = ErrorResponse(
            error="Validation Error",
            message="Multiple fields invalid",
            details={"field1": "Required", "field2": "Invalid format"},
            status_code=400
        )
        
        error_dict = error_resp.to_dict()
        assert "details" in error_dict
        assert error_dict["details"]["field1"] == "Required"


@pytest.mark.unit
class TestExceptionHandling:
    """Test exception handling function"""

    def test_handle_validation_exception(self):
        """Should handle validation exceptions"""
        request = Mock(spec=Request)
        request.url.path = "/test"
        exc = ValidationException("Invalid input")
        
        response = handle_exception(request, exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400

    def test_handle_not_found_exception(self):
        """Should handle not found exceptions"""
        request = Mock(spec=Request)
        request.url.path = "/test"
        exc = NotFoundException("Resource not found")
        
        response = handle_exception(request, exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 404

    def test_handle_authentication_exception(self):
        """Should handle authentication exceptions"""
        request = Mock(spec=Request)
        request.url.path = "/test"
        exc = AuthenticationException("Invalid credentials")
        
        response = handle_exception(request, exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 401

    def test_handle_authorization_exception(self):
        """Should handle authorization exceptions"""
        request = Mock(spec=Request)
        request.url.path = "/test"
        exc = AuthorizationException("Access denied")
        
        response = handle_exception(request, exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 403


@pytest.mark.unit
class TestGenericExceptionHandling:
    """Test generic exception handling"""

    def test_handle_generic_exception(self):
        """Should handle generic exceptions as 500"""
        request = Mock(spec=Request)
        request.url.path = "/test"
        exc = Exception("Unexpected error")
        
        response = handle_exception(request, exc)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
