"""
Permission Database Model
"""
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from infra.database.database import Base
import enum


class PermissionActionDB(str, enum.Enum):
    """Permission actions - Database enum"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    MANAGE = "manage"


# ResourceTypeDB removed - now using free string!
# This allows any system to define their own resource types
# without modifying the auth system code.


class PermissionModel(Base):
    """
    Permission model for database.
    
    **Design Note**: resource_type is a free string (not enum) to allow
    maximum flexibility. Each system can define its own resource types.
    """
    __tablename__ = "permission"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    client_id = Column(String, nullable=False, index=True)
    resource_type = Column(String, nullable=False)  # String livre! ✨
    resource_id = Column(String, nullable=True)
    action = Column(SQLEnum(PermissionActionDB), nullable=False)
    granted_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

