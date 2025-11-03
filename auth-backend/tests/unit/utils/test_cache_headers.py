"""
Unit tests for Cache Headers Utilities
Tests ETag and cache header generation
"""
import pytest
from datetime import datetime
from unittest.mock import Mock
from fastapi import Response

from app.api.utils.cache_headers import (
    generate_etag,
    add_etag_header,
    add_last_modified_header,
    add_cache_headers,
    check_if_none_match,
    check_if_modified_since
)


@pytest.mark.unit
class TestETagGeneration:
    """Test ETag generation"""

    def test_generate_etag_from_dict(self):
        """Should generate ETag from dictionary"""
        data = {"id": "123", "name": "John", "email": "john@example.com"}
        etag = generate_etag(data)
        
        assert etag is not None
        assert etag.startswith('"')
        assert etag.endswith('"')

    def test_same_data_generates_same_etag(self):
        """Should generate same ETag for same data"""
        data1 = {"id": "123", "name": "John"}
        data2 = {"id": "123", "name": "John"}
        
        etag1 = generate_etag(data1)
        etag2 = generate_etag(data2)
        
        assert etag1 == etag2

    def test_different_data_generates_different_etag(self):
        """Should generate different ETag for different data"""
        data1 = {"id": "123", "name": "John"}
        data2 = {"id": "456", "name": "Jane"}
        
        etag1 = generate_etag(data1)
        etag2 = generate_etag(data2)
        
        assert etag1 != etag2

    def test_generate_etag_from_list(self):
        """Should generate ETag from list"""
        data = [{"id": "1"}, {"id": "2"}, {"id": "3"}]
        etag = generate_etag(data)
        
        assert etag is not None
        assert isinstance(etag, str)


@pytest.mark.unit
class TestETagHeader:
    """Test ETag header functions"""

    def test_add_etag_header(self):
        """Should add ETag header to response"""
        response = Response()
        data = {"id": "123", "name": "Test"}
        
        add_etag_header(response, data)
        
        assert "ETag" in response.headers
        assert response.headers["ETag"].startswith('"')
        assert "Cache-Control" in response.headers

    def test_etag_header_format(self):
        """Should format ETag header correctly (quoted)"""
        response = Response()
        data = {"test": "data"}
        
        add_etag_header(response, data)
        
        etag = response.headers["ETag"]
        assert etag.startswith('"')
        assert etag.endswith('"')


@pytest.mark.unit
class TestLastModifiedHeader:
    """Test Last-Modified header"""

    def test_add_last_modified_header(self):
        """Should add Last-Modified header"""
        response = Response()
        last_modified = datetime(2024, 1, 1, 12, 0, 0)
        
        add_last_modified_header(response, last_modified)
        
        assert "Last-Modified" in response.headers
        assert "2024" in response.headers["Last-Modified"]

    def test_last_modified_http_date_format(self):
        """Should format Last-Modified as HTTP date"""
        response = Response()
        last_modified = datetime(2024, 1, 1, 12, 0, 0)
        
        add_last_modified_header(response, last_modified)
        
        http_date = response.headers["Last-Modified"]
        # HTTP date format: "Mon, 01 Jan 2024 12:00:00 GMT"
        assert "GMT" in http_date


@pytest.mark.unit
class TestCacheHeaders:
    """Test comprehensive cache headers"""

    def test_add_cache_headers(self):
        """Should add all cache headers"""
        response = Response()
        data = {"id": "123"}
        last_modified = datetime(2024, 1, 1)
        
        add_cache_headers(response, data, last_modified, max_age=300)
        
        assert "ETag" in response.headers
        assert "Last-Modified" in response.headers
        assert "Cache-Control" in response.headers

    def test_cache_control_with_max_age(self):
        """Should set Cache-Control with max-age"""
        response = Response()
        data = {"test": "data"}
        
        add_cache_headers(response, data, max_age=600)
        
        assert "max-age=600" in response.headers["Cache-Control"]

    def test_cache_control_without_max_age(self):
        """Should set Cache-Control to no-cache without max-age"""
        response = Response()
        data = {"test": "data"}
        
        add_cache_headers(response, data)
        
        assert "no-cache" in response.headers["Cache-Control"]


@pytest.mark.unit
class TestConditionalRequests:
    """Test conditional request helpers"""

    def test_check_if_none_match_matches(self):
        """Should return True when ETags match"""
        request_etag = '"abc123"'
        current_etag = '"abc123"'
        
        result = check_if_none_match(request_etag, current_etag)
        
        assert result is True

    def test_check_if_none_match_no_match(self):
        """Should return False when ETags don't match"""
        request_etag = '"abc123"'
        current_etag = '"xyz789"'
        
        result = check_if_none_match(request_etag, current_etag)
        
        assert result is False

    def test_check_if_none_match_wildcard(self):
        """Should match wildcard ETag"""
        request_etag = "*"
        current_etag = '"anything"'
        
        result = check_if_none_match(request_etag, current_etag)
        
        assert result is True

    def test_check_if_modified_since_modified(self):
        """Should return True when resource was modified"""
        request_date = datetime(2024, 1, 1, 12, 0, 0)
        last_modified = datetime(2024, 1, 2, 12, 0, 0)
        
        result = check_if_modified_since(request_date, last_modified)
        
        assert result is True

    def test_check_if_modified_since_not_modified(self):
        """Should return False when resource not modified"""
        request_date = datetime(2024, 1, 2, 12, 0, 0)
        last_modified = datetime(2024, 1, 1, 12, 0, 0)
        
        result = check_if_modified_since(request_date, last_modified)
        
        assert result is False
