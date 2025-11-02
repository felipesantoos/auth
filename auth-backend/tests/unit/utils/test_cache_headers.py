"""
Unit tests for Cache Headers utility
Tests cache control logic without external dependencies
"""
import pytest
from unittest.mock import Mock
from app.api.utils.cache_headers import (
    set_no_cache,
    set_cache_public,
    set_cache_private,
    get_cache_control_header
)


@pytest.mark.unit
class TestCacheHeaders:
    """Test cache header utilities"""
    
    def test_set_no_cache_adds_headers(self):
        """Test set_no_cache adds no-cache headers"""
        response = Mock()
        response.headers = {}
        
        set_no_cache(response)
        
        assert "Cache-Control" in response.headers
        assert "no-store" in response.headers["Cache-Control"]
        assert "no-cache" in response.headers["Cache-Control"]
    
    def test_set_cache_public_adds_headers(self):
        """Test set_cache_public adds public cache headers"""
        response = Mock()
        response.headers = {}
        
        set_cache_public(response, max_age=3600)
        
        assert "Cache-Control" in response.headers
        assert "public" in response.headers["Cache-Control"]
        assert "3600" in response.headers["Cache-Control"]
    
    def test_set_cache_private_adds_headers(self):
        """Test set_cache_private adds private cache headers"""
        response = Mock()
        response.headers = {}
        
        set_cache_private(response, max_age=300)
        
        assert "Cache-Control" in response.headers
        assert "private" in response.headers["Cache-Control"]
        assert "300" in response.headers["Cache-Control"]
    
    def test_get_cache_control_no_cache(self):
        """Test get_cache_control_header for no-cache"""
        header = get_cache_control_header(cache_type="no-cache")
        
        assert "no-store" in header
        assert "no-cache" in header
    
    def test_get_cache_control_public(self):
        """Test get_cache_control_header for public cache"""
        header = get_cache_control_header(cache_type="public", max_age=7200)
        
        assert "public" in header
        assert "max-age=7200" in header
    
    def test_get_cache_control_private(self):
        """Test get_cache_control_header for private cache"""
        header = get_cache_control_header(cache_type="private", max_age=600)
        
        assert "private" in header
        assert "max-age=600" in header

