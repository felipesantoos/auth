"""
Unit tests for Cache Helper
Tests cache utility logic without external dependencies
"""
import pytest
from unittest.mock import Mock
from core.services.cache.cache_helper import CacheHelper


@pytest.mark.unit
class TestCacheHelper:
    """Test cache helper utilities"""
    
    def test_generate_cache_key_includes_prefix(self):
        """Test cache key generation includes prefix"""
        key = CacheHelper.build_key("user", "123")
        
        assert "user" in key
        assert "123" in key
    
    def test_generate_cache_key_unique_for_different_inputs(self):
        """Test cache keys are unique for different inputs"""
        key1 = CacheHelper.build_key("user", "123")
        key2 = CacheHelper.build_key("user", "456")
        
        assert key1 != key2

