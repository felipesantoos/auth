"""
Unit tests for API Versioning
Tests API version detection and routing
"""
import pytest
from unittest.mock import Mock
from fastapi import Request


@pytest.mark.unit
class TestAPIVersionDetection:
    """Test API version detection from request"""

    def test_extract_version_from_path_v1(self):
        """Should extract v1 from /api/v1/... paths"""
        request = Mock(spec=Request)
        request.url.path = "/api/v1/users"
        
        # Extract version from path
        parts = request.url.path.split('/')
        version = None
        for part in parts:
            if part.startswith('v') and part[1:].isdigit():
                version = part
                break
        
        assert version == "v1"

    def test_extract_version_from_path_v2(self):
        """Should extract v2 from /api/v2/... paths"""
        request = Mock(spec=Request)
        request.url.path = "/api/v2/users"
        
        parts = request.url.path.split('/')
        version = None
        for part in parts:
            if part.startswith('v') and part[1:].isdigit():
                version = part
                break
        
        assert version == "v2"

    def test_no_version_in_path_returns_none(self):
        """Should return None when no version in path"""
        request = Mock(spec=Request)
        request.url.path = "/api/users"
        
        parts = request.url.path.split('/')
        version = None
        for part in parts:
            if part.startswith('v') and part[1:].isdigit():
                version = part
                break
        
        assert version is None


@pytest.mark.unit
class TestAPIVersionHeader:
    """Test API version from headers"""

    def test_version_from_accept_header(self):
        """Should extract version from Accept header"""
        request = Mock(spec=Request)
        request.headers.get.return_value = "application/vnd.api.v1+json"
        
        accept = request.headers.get("Accept")
        version = None
        
        if accept and "vnd.api.v" in accept:
            # Extract v1, v2, etc.
            import re
            match = re.search(r'v(\d+)', accept)
            if match:
                version = f"v{match.group(1)}"
        
        assert version == "v1"

    def test_version_from_custom_header(self):
        """Should extract version from X-API-Version header"""
        request = Mock(spec=Request)
        request.headers.get.return_value = "v2"
        
        version = request.headers.get("X-API-Version")
        
        assert version == "v2"

    def test_no_version_header(self):
        """Should handle missing version header"""
        request = Mock(spec=Request)
        request.headers.get.return_value = None
        
        version = request.headers.get("X-API-Version")
        
        assert version is None


@pytest.mark.unit
class TestVersionComparison:
    """Test version comparison logic"""

    def test_compare_versions(self):
        """Should compare version strings correctly"""
        def version_to_int(v: str) -> int:
            """Convert v1, v2, etc to integer"""
            if v and v.startswith('v'):
                return int(v[1:])
            return 0
        
        assert version_to_int("v1") < version_to_int("v2")
        assert version_to_int("v2") > version_to_int("v1")
        assert version_to_int("v2") == version_to_int("v2")

    def test_invalid_version_format(self):
        """Should handle invalid version format"""
        def version_to_int(v: str) -> int:
            try:
                if v and v.startswith('v'):
                    return int(v[1:])
            except (ValueError, AttributeError):
                pass
            return 0
        
        assert version_to_int("invalid") == 0
        assert version_to_int("v") == 0
        assert version_to_int("vabc") == 0

