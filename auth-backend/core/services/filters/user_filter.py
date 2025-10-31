"""
User Filter
Filter parameters for querying users
Inherits from BaseFilter for search, pagination, and sorting
"""
from dataclasses import dataclass
from typing import Optional
from .base_filter import BaseFilter
from core.domain.auth.user_role import UserRole


@dataclass
class UserFilter(BaseFilter):
    """
    Filter criteria for user queries.
    
    Inherits from BaseFilter for:
    - search: General search term (searches in username, email, name)
    - page/page_size: Pagination (1-based page number)
    - offset/limit: Alternative pagination (direct offset)
    - sort_by/sort_order: Sorting (e.g., "full_name", "created_at")
    
    Adds user-specific filters:
    - client_id: Filter by client (tenant) - required for multi-tenant isolation
    - role: Filter by user role
    - active: Filter by active status
    - email: Filter by email (exact or partial match)
    - username: Filter by username (exact or partial match)
    """
    # Multi-tenant: Filter by client (tenant)
    client_id: Optional[str] = None
    
    # User-specific filters
    role: Optional[UserRole] = None
    active: Optional[bool] = None
    email: Optional[str] = None
    username: Optional[str] = None

