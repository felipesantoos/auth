"""
Pagination Utilities
Helper functions for creating paginated responses with optimized queries
"""
from typing import List, TypeVar, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select
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


async def paginate_query(
    session: AsyncSession,
    query: Select,
    page: int = 1,
    page_size: int = None,
) -> Tuple[List[T], int]:
    """
    Execute paginated query with separate count query for optimization.
    
    Benefits:
    - Count query doesn't load data (faster)
    - Data query only loads requested page
    - Prevents loading entire dataset into memory
    
    Args:
        session: SQLAlchemy async session
        query: Base SQLAlchemy select query (without limit/offset)
        page: Page number (1-based)
        page_size: Items per page (uses default if None)
    
    Returns:
        Tuple of (items_list, total_count)
    
    Example:
        >>> from sqlalchemy import select
        >>> query = select(DBUser).where(DBUser.is_active == True)
        >>> items, total = await paginate_query(session, query, page=1, page_size=20)
        >>> response = create_paginated_response(items, page, page_size, total)
    """
    # Validate inputs
    if page_size is None:
        page_size = get_default_page_size()
    page_size = validate_page_size(page_size)
    page = max(1, page)
    
    # Separate count query (efficient - doesn't load data)
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await session.execute(count_query)
    total_count = count_result.scalar() or 0
    
    # Data query with pagination
    offset = (page - 1) * page_size
    data_query = query.limit(page_size).offset(offset)
    data_result = await session.execute(data_query)
    items = data_result.scalars().all()
    
    return list(items), total_count


async def paginate_query_with_response(
    session: AsyncSession,
    query: Select,
    page: int = 1,
    page_size: int = None,
) -> PaginatedResponse[T]:
    """
    Execute paginated query and return formatted response.
    
    Convenience method that combines paginate_query() and create_paginated_response().
    
    Args:
        session: SQLAlchemy async session
        query: Base SQLAlchemy select query (without limit/offset)
        page: Page number (1-based)
        page_size: Items per page (uses default if None)
    
    Returns:
        PaginatedResponse with items and metadata
    
    Example:
        >>> from sqlalchemy import select
        >>> query = select(DBUser).where(DBUser.is_active == True)
        >>> response = await paginate_query_with_response(session, query, page=2, page_size=50)
        >>> print(f"Page {response.pagination.page} of {response.pagination.total_pages}")
    """
    if page_size is None:
        page_size = get_default_page_size()
    
    items, total_count = await paginate_query(session, query, page, page_size)
    
    return create_paginated_response(
        items=items,
        page=page,
        page_size=page_size,
        total_items=total_count
    )

