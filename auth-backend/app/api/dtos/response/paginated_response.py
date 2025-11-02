"""
Paginated Response
Generic paginated response DTOs with metadata for different pagination strategies
"""
from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, Field

T = TypeVar('T')


class PaginationMetadata(BaseModel):
    """Offset-based pagination metadata"""
    page: int = Field(..., description="Current page number (1-based)")
    page_size: int = Field(..., description="Number of items per page")
    total_items: int = Field(..., description="Total number of items matching filter")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic offset-based paginated response.
    
    Usage:
        PaginatedResponse[UserResponse]  # For user lists
        PaginatedResponse[ClientResponse]  # For client lists
    """
    items: List[T] = Field(..., description="List of items in current page")
    pagination: PaginationMetadata = Field(..., description="Pagination metadata")
    
    class Config:
        from_attributes = True


class CursorPaginationMetadata(BaseModel):
    """Cursor-based pagination metadata"""
    cursor: Optional[str] = Field(None, description="Current cursor (opaque token)")
    next_cursor: Optional[str] = Field(None, description="Cursor for next page")
    has_next: bool = Field(..., description="Whether there is a next page")
    limit: int = Field(..., description="Items per page")


class CursorPaginatedResponse(BaseModel, Generic[T]):
    """
    Generic cursor-based paginated response.
    
    Better for large datasets and real-time data.
    Cursors are opaque tokens encoding position in dataset.
    
    Usage:
        CursorPaginatedResponse[UserResponse]
    """
    items: List[T] = Field(..., description="List of items in current page")
    pagination: CursorPaginationMetadata = Field(..., description="Cursor pagination metadata")
    
    class Config:
        from_attributes = True

