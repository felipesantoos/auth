"""
Unit tests for Tenant Middleware
Tests multi-tenant client isolation
"""
import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import Request

from app.api.middlewares.tenant_middleware import (
    get_client_id_from_request,
    get_client_from_request
)


@pytest.mark.unit
class TestClientIDExtraction:
    """Test client ID extraction from request"""

    def test_extract_from_x_client_id_header(self):
        """Should extract client_id from X-Client-ID header"""
        request = Mock(spec=Request)
        request.headers.get.side_effect = lambda key: {
            "X-Client-ID": "client-123"
        }.get(key)
        
        client_id = get_client_id_from_request(request)
        assert client_id == "client-123"

    def test_extract_from_query_parameter(self):
        """Should extract client_id from query parameter (development)"""
        request = Mock(spec=Request)
        request.headers.get.return_value = None
        request.query_params = Mock()
        request.query_params.get.return_value = "client-456"
        
        client_id = get_client_id_from_request(request)
        assert client_id == "client-456"

    def test_no_client_id_returns_none(self):
        """Should return None when no client_id found"""
        request = Mock(spec=Request)
        request.headers.get.return_value = None
        request.query_params = Mock()
        request.query_params.get.return_value = None
        
        client_id = get_client_id_from_request(request)
        assert client_id is None


@pytest.mark.unit
class TestSubdomainExtraction:
    """Test subdomain extraction"""


@pytest.mark.unit
class TestTenantMiddlewarePriority:
    """Test extraction priority order"""

    def test_header_takes_priority_over_query(self):
        """Should prioritize X-Client-ID header over query param"""
        request = Mock(spec=Request)
        request.headers.get.side_effect = lambda key: {
            "X-Client-ID": "header-client"
        }.get(key)
        request.query_params = Mock()
        request.query_params.get.return_value = "query-client"
        
        client_id = get_client_id_from_request(request)
        assert client_id == "header-client"

    def test_priority_order(self):
        """Should follow correct priority: header > subdomain > query"""
        # 1. Header has highest priority
        request1 = Mock(spec=Request)
        request1.headers.get.return_value = "from-header"
        assert get_client_id_from_request(request1) == "from-header"
        
        # 2. Query param is fallback
        request2 = Mock(spec=Request)
        request2.headers.get.return_value = None
        request2.query_params = Mock()
        request2.query_params.get.return_value = "from-query"
        assert get_client_id_from_request(request2) == "from-query"
