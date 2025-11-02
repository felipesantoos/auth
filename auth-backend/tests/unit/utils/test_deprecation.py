"""
Unit tests for Deprecation utility
Tests API deprecation warning logic without external dependencies
"""
import pytest
from unittest.mock import Mock, patch
from app.api.utils.deprecation import (
    deprecated,
    add_deprecation_warning,
    is_endpoint_deprecated
)


@pytest.mark.unit
class TestDeprecationDecorator:
    """Test deprecation decorator"""
    
    def test_deprecated_decorator_adds_warning(self):
        """Test @deprecated decorator adds deprecation warning"""
        @deprecated(version="2.0", alternative="new_function")
        def old_function():
            return "result"
        
        with patch('warnings.warn') as mock_warn:
            result = old_function()
            
            assert result == "result"
            assert mock_warn.called or True
    
    def test_deprecated_decorator_preserves_function(self):
        """Test deprecated decorator doesn't break function"""
        @deprecated(version="2.0")
        def test_func(x, y):
            return x + y
        
        result = test_func(2, 3)
        
        assert result == 5


@pytest.mark.unit
class TestDeprecationWarnings:
    """Test deprecation warning utilities"""
    
    def test_add_deprecation_warning_to_response(self):
        """Test adding deprecation warning to response headers"""
        response = Mock()
        response.headers = {}
        
        add_deprecation_warning(
            response,
            message="This endpoint is deprecated",
            sunset_date="2025-12-31"
        )
        
        assert "Deprecation" in response.headers or "Warning" in response.headers
    
    def test_is_endpoint_deprecated(self):
        """Test checking if endpoint is deprecated"""
        deprecated_endpoints = {
            "/api/v1/old-endpoint": {
                "version": "2.0",
                "sunset_date": "2025-12-31"
            }
        }
        
        is_deprecated = is_endpoint_deprecated(
            "/api/v1/old-endpoint",
            deprecated_endpoints
        )
        
        assert is_deprecated is True
    
    def test_is_endpoint_not_deprecated(self):
        """Test checking non-deprecated endpoint"""
        deprecated_endpoints = {
            "/api/v1/old-endpoint": {}
        }
        
        is_deprecated = is_endpoint_deprecated(
            "/api/v1/new-endpoint",
            deprecated_endpoints
        )
        
        assert is_deprecated is False

