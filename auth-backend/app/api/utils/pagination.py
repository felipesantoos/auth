"""
Pagination Utilities
Helper functions for creating paginated responses
"""
from typing import List, TypeVar
from app.api.dtos.response.paginated_response import PaginatedResponse, PaginationMetadata
from config.settings import settings

T = TypeVar('T')


def create_paginated_response(
    items: List[T],
    page: int,
    page_size: int,
    total_items: int,
) -> PaginatedResponse[T]:
    """
    Creates a paginated response with metadata.
    
    Args:
        items: List of items in current page
        page: Current page number (1-based)
        page_size: Number of items per page
        total_items: Total number of items matching filter (unpaginated)
    
    Returns:
        PaginatedResponse with items and pagination metadata
    
    Example:
        >>> users = [user1, user2, user3]
        >>> response = create_paginated_response(users, page=1, page_size=20, total_items=50)
        >>> response.pagination.total_pages  # 3
        >>> response.pagination.has_next  # True
    """
    total_pages = (total_items + page_size - 1) // page_size if page_size > 0 else 0
    has_next = page < total_pages
    has_previous = page > 1
    
    metadata = PaginationMetadata(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        has_next=has_next,
        has_previous=has_previous,
    )
    
    return PaginatedResponse(
        items=items,
        pagination=metadata,
    )


def get_default_page_size() -> int:
    """Gets default page size from settings"""
    return settings.default_page_size


def get_max_page_size() -> int:
    """Gets maximum page size from settings"""
    return settings.max_page_size


def validate_page_size(page_size: int) -> int:
    """
    Validates and clamps page size to valid range.
    
    Args:
        page_size: Requested page size
    
    Returns:
        Validated page size (clamped to [1, max_page_size])
    """
    max_size = get_max_page_size()
    return min(max(1, page_size), max_size)

