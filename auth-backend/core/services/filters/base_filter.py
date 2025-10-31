"""
Base Filter
Common filter attributes for all domain queries
Following DRY (Don't Repeat Yourself) principle
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class BaseFilter:
    """
    Base filter with common attributes applied to all domain queries.
    
    Provides search, pagination, and sorting capabilities that all filters can inherit.
    Following DRY (Don't Repeat Yourself) principle.
    """
    # Search
    search: Optional[str] = None  # General search term applied to main text fields
    
    # Pagination (two approaches)
    page: Optional[int] = None  # Page number (1-based)
    page_size: Optional[int] = None  # Items per page
    offset: Optional[int] = None  # Alternative to page - direct offset
    limit: Optional[int] = None  # Alternative to page_size - direct limit
    
    # Sorting
    sort_by: Optional[str] = None  # Field to sort by
    sort_order: Optional[str] = None  # 'asc' or 'desc'
    
    def get_offset(self) -> int:
        """
        Calculates offset from page/page_size or uses direct offset.
        
        Returns:
            Calculated offset value (defaults to 0)
        """
        if self.offset is not None:
            return self.offset
        
        if self.page is not None and self.page_size is not None:
            return (self.page - 1) * self.page_size
        
        return 0
    
    def get_limit(self) -> int:
        """
        Gets limit from page_size or direct limit.
        
        Returns:
            Limit value (defaults to 50 if not specified)
        """
        if self.limit is not None:
            return self.limit
        
        if self.page_size is not None:
            return self.page_size
        
        return 50  # Default page size

