"""
User Filter
Filter parameters for querying users with advanced filtering capabilities
Inherits from BaseFilter for search, pagination, and sorting
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from .base_filter import BaseFilter
from core.domain.auth.user_role import UserRole


@dataclass
class UserFilter(BaseFilter):
    """
    Advanced filter criteria for user queries.
    
    Inherits from BaseFilter for:
    - search: General search term (searches in username, email, name)
    - page/page_size: Pagination (1-based page number)
    - offset/limit: Alternative pagination (direct offset)
    - sort_by/sort_order: Sorting (e.g., "full_name", "created_at")
    
    Adds user-specific filters:
    
    **Basic Filters:**
    - client_id: Filter by client (tenant) - required for multi-tenant isolation
    - role: Filter by user role
    - active: Filter by active status
    - email: Filter by email (exact or partial match)
    - username: Filter by username (exact or partial match)
    
    **Date Range Filters:**
    - created_after: Users created after this datetime
    - created_before: Users created before this datetime
    - updated_after: Users updated after this datetime
    - updated_before: Users updated before this datetime
    - last_login_after: Users who logged in after this datetime
    - last_login_before: Users who logged in before this datetime
    
    **Numeric Range Filters:**
    - min_failed_login_attempts: Minimum failed login attempts
    - max_failed_login_attempts: Maximum failed login attempts
    
    **Boolean Filters:**
    - email_verified: Filter by email verification status
    - mfa_enabled: Filter by MFA enabled status
    - is_locked: Filter by account lock status
    
    **Array Filters:**
    - roles: Filter by multiple roles (OR logic - any of these roles)
    - exclude_roles: Exclude users with these roles
    
    Example:
        >>> # Find active users created in January 2024
        >>> filter = UserFilter(
        ...     client_id="client_123",
        ...     active=True,
        ...     created_after=datetime(2024, 1, 1),
        ...     created_before=datetime(2024, 2, 1),
        ...     email_verified=True
        ... )
    """
    # ===== Multi-tenant =====
    client_id: Optional[str] = None
    
    # ===== Basic Filters =====
    role: Optional[UserRole] = None
    active: Optional[bool] = None
    email: Optional[str] = None
    username: Optional[str] = None
    
    # ===== Date Range Filters =====
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    updated_after: Optional[datetime] = None
    updated_before: Optional[datetime] = None
    last_login_after: Optional[datetime] = None
    last_login_before: Optional[datetime] = None
    
    # ===== Numeric Range Filters =====
    min_failed_login_attempts: Optional[int] = None
    max_failed_login_attempts: Optional[int] = None
    
    # ===== Boolean Filters =====
    email_verified: Optional[bool] = None
    mfa_enabled: Optional[bool] = None
    is_locked: Optional[bool] = None
    
    # ===== Array Filters =====
    # OR logic: user must have any of these roles
    roles: Optional[List[UserRole]] = None
    # Exclude users with any of these roles
    exclude_roles: Optional[List[UserRole]] = None

