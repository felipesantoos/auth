"""
Paginated Response
Generic paginated response DTO with metadata
"""
from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field

T = TypeVar('T')


class PaginationMetadata(BaseModel):
    """Pagination metadata"""
    page: int = Field(..., description="Current page number (1-based)")
    page_size: int = Field(..., description="Number of items per page")
    total_items: int = Field(..., description="Total number of items matching filter")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response.
    
    Usage:
        PaginatedResponse[UserResponse]  # For user lists
        PaginatedResponse[ClientResponse]  # For client lists
    """
    items: List[T] = Field(..., description="List of items in current page")
    pagination: PaginationMetadata = Field(..., description="Pagination metadata")
    
    class Config:
        from_attributes = True

