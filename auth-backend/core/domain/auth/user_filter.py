"""
User Filter
Filter parameters for querying users (Value Object)
"""
from dataclasses import dataclass
from typing import Optional
from core.domain.auth.user_role import UserRole


@dataclass
class UserFilter:
    """
    Filter parameters for user queries.
    
    This is a Value Object in the domain layer.
    Used to encapsulate filter criteria for querying users.
    """
    client_id: Optional[str] = None  # Filter by client (tenant)
    role: Optional[UserRole] = None
    active: Optional[bool] = None
    email: Optional[str] = None
    username: Optional[str] = None

