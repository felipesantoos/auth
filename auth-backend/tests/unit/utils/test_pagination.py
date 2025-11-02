"""
Unit tests for Pagination utilities
Tests pagination logic without external dependencies
"""
import pytest
from app.api.utils.pagination import (
    create_paginated_response,
    validate_page_size,
    encode_cursor,
    decode_cursor
)


@pytest.mark.unit
class TestPaginationResponse:
    """Test paginated response creation"""
    
    def test_create_paginated_response(self):
        """Test creating paginated response with metadata"""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        
        response = create_paginated_response(
            items=items,
            page=1,
            page_size=20,
            total_items=50
        )
        
        assert response.items == items
        assert response.pagination.page == 1
        assert response.pagination.page_size == 20
        assert response.pagination.total_items == 50
        assert response.pagination.total_pages == 3
        assert response.pagination.has_next is True
        assert response.pagination.has_previous is False
    
    def test_pagination_calculates_total_pages(self):
        """Test total pages calculation"""
        response = create_paginated_response(
            items=[],
            page=1,
            page_size=20,
            total_items=45
        )
        
        # 45 items / 20 per page = 3 pages
        assert response.pagination.total_pages == 3
    
    def test_pagination_has_next_on_middle_page(self):
        """Test has_next is True on middle pages"""
        response = create_paginated_response(
            items=[],
            page=2,
            page_size=20,
            total_items=100
        )
        
        assert response.pagination.has_next is True
        assert response.pagination.has_previous is True
    
    def test_pagination_no_next_on_last_page(self):
        """Test has_next is False on last page"""
        response = create_paginated_response(
            items=[],
            page=5,
            page_size=20,
            total_items=100
        )
        
        assert response.pagination.has_next is False
        assert response.pagination.has_previous is True


@pytest.mark.unit
class TestPageSizeValidation:
    """Test page size validation"""
    
    def test_validate_page_size_clamps_to_minimum(self):
        """Test page size is clamped to minimum of 1"""
        result = validate_page_size(0)
        assert result >= 1
        
        result = validate_page_size(-10)
        assert result >= 1
    
    def test_validate_page_size_clamps_to_maximum(self):
        """Test page size is clamped to maximum"""
        result = validate_page_size(10000)
        # Should be clamped to max_page_size from settings (typically 100)
        assert result <= 1000


@pytest.mark.unit
class TestCursorPagination:
    """Test cursor-based pagination utilities"""
    
    def test_encode_cursor_creates_base64_string(self):
        """Test encode_cursor creates base64 string"""
        data = {"created_at": "2024-01-15T10:30:00", "id": "user_123"}
        
        cursor = encode_cursor(data)
        
        assert isinstance(cursor, str)
        assert len(cursor) > 0
    
    def test_decode_cursor_reverses_encoding(self):
        """Test decode_cursor reverses encode_cursor"""
        original = {"created_at": "2024-01-15T10:30:00", "id": "user_123"}
        
        cursor = encode_cursor(original)
        decoded = decode_cursor(cursor)
        
        assert decoded == original
    
    def test_decode_invalid_cursor_raises_error(self):
        """Test decoding invalid cursor raises ValueError"""
        invalid_cursor = "invalid_base64_!@#$"
        
        with pytest.raises(ValueError, match="Invalid cursor"):
            decode_cursor(invalid_cursor)
    
    def test_cursor_handles_datetime_serialization(self):
        """Test cursor handles datetime serialization"""
        from datetime import datetime
        
        now = datetime.utcnow()
        data = {"created_at": now, "id": "user_123"}
        
        cursor = encode_cursor(data)
        decoded = decode_cursor(cursor)
        
        # Datetime should be serialized as string
        assert isinstance(decoded["created_at"], str)

