"""
Pagination Utilities
Helper functions for creating paginated responses with optimized queries.
Supports offset, cursor, and keyset pagination strategies.
"""
from typing import List, TypeVar, Tuple, Optional, Any
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select
from app.api.dtos.response.paginated_response import (
    PaginatedResponse, 
    PaginationMetadata,
    CursorPaginatedResponse,
    CursorPaginationMetadata
)
from config.settings import settings
from datetime import datetime
import base64
import json

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


# ===============================================================================
# CURSOR-BASED PAGINATION (Better for large datasets and real-time data)
# ===============================================================================

def encode_cursor(data: dict) -> str:
    """
    Encode cursor data to base64 string.
    
    Args:
        data: Dictionary with cursor position (e.g., {"created_at": "...", "id": "..."})
    
    Returns:
        Base64-encoded cursor string
    
    Example:
        >>> cursor = encode_cursor({"created_at": "2024-01-15T10:30:00", "id": "user_123"})
        >>> print(cursor)  # eyJjcmVhdGVkX2F0IjogIjIwMjQtMDEtMTVUMTA6MzA6MDAiLCAiaWQiOiAidXNlcl8xMjMifQ==
    """
    json_str = json.dumps(data, sort_keys=True, default=str)
    return base64.b64encode(json_str.encode()).decode()


def decode_cursor(cursor: str) -> dict:
    """
    Decode cursor from base64 string to dictionary.
    
    Args:
        cursor: Base64-encoded cursor string
    
    Returns:
        Dictionary with cursor position
    
    Raises:
        ValueError: If cursor is invalid
    
    Example:
        >>> data = decode_cursor("eyJjcmVhdGVkX2F0IjogIjIwMjQtMDEtMTVUMTA6MzA6MDAiLCAiaWQiOiAidXNlcl8xMjMifQ==")
        >>> print(data)  # {"created_at": "2024-01-15T10:30:00", "id": "user_123"}
    """
    try:
        json_str = base64.b64decode(cursor.encode()).decode()
        return json.loads(json_str)
    except Exception as e:
        raise ValueError(f"Invalid cursor: {e}")


async def paginate_cursor(
    session: AsyncSession,
    query: Select,
    model_class: Any,
    cursor: Optional[str] = None,
    limit: int = 20,
    sort_column: str = "created_at",
    sort_order: str = "desc",
) -> Tuple[List[T], Optional[str], bool]:
    """
    Execute cursor-based pagination query.
    
    Cursor pagination is better than offset for:
    - Large datasets (no counting overhead)
    - Real-time data (consistent results)
    - Deep pagination (O(1) instead of O(n))
    
    Args:
        session: SQLAlchemy async session
        query: Base query (without order/limit)
        model_class: SQLAlchemy model class (e.g., DBUser)
        cursor: Current cursor (None for first page)
        limit: Items per page
        sort_column: Column to sort by (must have index!)
        sort_order: "asc" or "desc"
    
    Returns:
        Tuple of (items, next_cursor, has_next)
    
    Example:
        >>> query = select(DBUser).where(DBUser.is_active == True)
        >>> items, next_cursor, has_next = await paginate_cursor(
        ...     session, query, DBUser, cursor=None, limit=20
        ... )
        >>> # Get next page:
        >>> items2, next_cursor2, has_next2 = await paginate_cursor(
        ...     session, query, DBUser, cursor=next_cursor, limit=20
        ... )
    """
    # Get sort column from model
    sort_col = getattr(model_class, sort_column)
    id_col = getattr(model_class, "id")
    
    # Add ordering
    if sort_order.lower() == "desc":
        query = query.order_by(sort_col.desc(), id_col.desc())
    else:
        query = query.order_by(sort_col.asc(), id_col.asc())
    
    # Apply cursor if provided
    if cursor:
        cursor_data = decode_cursor(cursor)
        cursor_value = cursor_data.get(sort_column)
        cursor_id = cursor_data.get("id")
        
        # Parse datetime if needed
        if isinstance(cursor_value, str) and sort_column.endswith("_at"):
            cursor_value = datetime.fromisoformat(cursor_value)
        
        # Filter: items after cursor position
        if sort_order.lower() == "desc":
            query = query.where(
                or_(
                    sort_col < cursor_value,
                    and_(sort_col == cursor_value, id_col < cursor_id)
                )
            )
        else:
            query = query.where(
                or_(
                    sort_col > cursor_value,
                    and_(sort_col == cursor_value, id_col > cursor_id)
                )
            )
    
    # Fetch limit + 1 to check if there are more items
    query = query.limit(limit + 1)
    result = await session.execute(query)
    items = list(result.scalars().all())
    
    # Check if there are more items
    has_next = len(items) > limit
    if has_next:
        items = items[:-1]  # Remove extra item
    
    # Create next cursor
    next_cursor = None
    if has_next and items:
        last_item = items[-1]
        next_cursor = encode_cursor({
            sort_column: getattr(last_item, sort_column),
            "id": getattr(last_item, "id")
        })
    
    return items, next_cursor, has_next


def create_cursor_paginated_response(
    items: List[T],
    cursor: Optional[str],
    next_cursor: Optional[str],
    has_next: bool,
    limit: int,
) -> CursorPaginatedResponse[T]:
    """
    Create cursor-based paginated response.
    
    Args:
        items: List of items in current page
        cursor: Current cursor
        next_cursor: Cursor for next page (None if no next page)
        has_next: Whether there is a next page
        limit: Items per page
    
    Returns:
        CursorPaginatedResponse with items and metadata
    """
    metadata = CursorPaginationMetadata(
        cursor=cursor,
        next_cursor=next_cursor,
        has_next=has_next,
        limit=limit
    )
    
    return CursorPaginatedResponse(
        items=items,
        pagination=metadata
    )


# ===============================================================================
# KEYSET PAGINATION (Most efficient for ordered datasets)
# ===============================================================================

async def paginate_keyset(
    session: AsyncSession,
    query: Select,
    model_class: Any,
    after_id: Optional[str] = None,
    limit: int = 20,
) -> Tuple[List[T], Optional[str], bool]:
    """
    Execute keyset pagination (simplest and most efficient).
    
    Keyset pagination using ID is:
    - Simplest to implement
    - Most efficient (indexed lookups)
    - Always consistent
    - Best for infinite scroll
    
    Limitation: Can only sort by ID (ascending)
    
    Args:
        session: SQLAlchemy async session
        query: Base query
        model_class: SQLAlchemy model class
        after_id: Get items after this ID
        limit: Items per page
    
    Returns:
        Tuple of (items, next_id, has_next)
    
    Example:
        >>> query = select(DBUser).where(DBUser.is_active == True)
        >>> items, next_id, has_next = await paginate_keyset(
        ...     session, query, DBUser, after_id=None, limit=20
        ... )
        >>> # Get next page:
        >>> items2, next_id2, has_next2 = await paginate_keyset(
        ...     session, query, DBUser, after_id=next_id, limit=20
        ... )
    """
    id_col = getattr(model_class, "id")
    
    # Add ordering by ID
    query = query.order_by(id_col.asc())
    
    # Filter: items after the given ID
    if after_id:
        query = query.where(id_col > after_id)
    
    # Fetch limit + 1 to check if there are more items
    query = query.limit(limit + 1)
    result = await session.execute(query)
    items = list(result.scalars().all())
    
    # Check if there are more items
    has_next = len(items) > limit
    if has_next:
        items = items[:-1]  # Remove extra item
    
    # Get next ID
    next_id = None
    if has_next and items:
        next_id = getattr(items[-1], "id")
    
    return items, next_id, has_next

