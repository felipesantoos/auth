"""
Permission Mapper
Maps between Permission domain model and PermissionModel database model
"""
from typing import Optional
import uuid
from core.domain.auth.permission import Permission, PermissionAction
from infra.database.models.permission import PermissionModel, PermissionActionDB


class PermissionMapper:
    """Mapper for Permission domain <-> database model"""
    
    @staticmethod
    def to_domain(model: PermissionModel) -> Permission:
        """Convert database model to domain model"""
        if model is None:
            return None
        
        return Permission(
            id=model.id,
            user_id=model.user_id,
            client_id=model.client_id,
            resource_type=model.resource_type,  # String direto! ✨
            resource_id=model.resource_id,
            action=PermissionAction(model.action.value),
            granted_by=model.granted_by,
            created_at=model.created_at
        )
    
    @staticmethod
    def to_model(domain: Permission) -> PermissionModel:
        """Convert domain model to database model"""
        if domain is None:
            return None
        
        # Generate ID if not present
        if not domain.id:
            domain.id = str(uuid.uuid4())
        
        return PermissionModel(
            id=domain.id,
            user_id=domain.user_id,
            client_id=domain.client_id,
            resource_type=domain.resource_type,  # String direto! ✨
            resource_id=domain.resource_id,
            action=PermissionActionDB(domain.action.value),
            granted_by=domain.granted_by,
            created_at=domain.created_at
        )

