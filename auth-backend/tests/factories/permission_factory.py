"""
Permission factory for generating test data
"""
from datetime import datetime
from typing import Optional
from faker import Faker

from core.domain.auth.permission import Permission, PermissionAction


# Initialize Faker with Portuguese locale
fake = Faker('pt_BR')


class PermissionFactory:
    """Factory for creating Permission instances with realistic data"""
    
    @staticmethod
    def build(
        id: Optional[str] = None,
        user_id: Optional[str] = None,
        client_id: str = "test-client-id",
        resource_type: str = "project",
        resource_id: Optional[str] = "__AUTO__",  # Sentinel value
        action: PermissionAction = PermissionAction.READ,
        granted_by: Optional[str] = None,
        **kwargs
    ) -> Permission:
        """
        Create a test Permission with realistic data.
        
        Args:
            id: Permission ID (auto-generated if not provided)
            user_id: User ID (auto-generated if not provided)
            client_id: Client ID
            resource_type: Type of resource (e.g., "project", "ticket")
            resource_id: Specific resource ID (None for all resources, auto-generated if not specified)
            action: Permission action
            granted_by: ID of user who granted permission
            **kwargs: Additional fields to override
        
        Returns:
            Permission instance with realistic test data
        """
        if not id:
            id = fake.uuid4()
        if not user_id:
            user_id = fake.uuid4()
        # Auto-generate resource_id only if not explicitly set
        if resource_id == "__AUTO__":
            resource_id = fake.uuid4()
        if not granted_by:
            granted_by = fake.uuid4()
        
        return Permission(
            id=id,
            user_id=user_id,
            client_id=client_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            granted_by=granted_by,
            created_at=kwargs.get('created_at', datetime.utcnow())
        )
    
    @staticmethod
    async def create_persisted(db_session, **kwargs) -> Permission:
        """Create and persist permission to database"""
        from infra.database.repositories.permission_repository import PermissionRepository
        
        permission = PermissionFactory.build(**kwargs)
        repository = PermissionRepository(db_session)
        saved = await repository.save(permission)
        await db_session.commit()
        return saved
    
    @staticmethod
    def create_manage_permission(
        user_id: str,
        client_id: str = "test-client-id",
        resource_type: str = "project",
        resource_id: Optional[str] = None,
        **kwargs
    ) -> Permission:
        """Create a MANAGE permission (grants all actions)"""
        return PermissionFactory.build(
            user_id=user_id,
            client_id=client_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=PermissionAction.MANAGE,
            **kwargs
        )
    
    @staticmethod
    def create_wildcard_permission(
        user_id: str,
        client_id: str = "test-client-id",
        resource_type: str = "project",
        action: PermissionAction = PermissionAction.READ,
        **kwargs
    ) -> Permission:
        """Create a wildcard permission (applies to all resources of a type)"""
        return PermissionFactory.build(
            user_id=user_id,
            client_id=client_id,
            resource_type=resource_type,
            resource_id=None,  # None means all resources
            action=action,
            **kwargs
        )


class PermissionFactoryTraits:
    """Predefined permission configurations (Trait pattern)"""
    
    @staticmethod
    def read_only(user_id: str, resource_type: str = "project") -> Permission:
        """Create read-only permission"""
        return PermissionFactory.build(
            user_id=user_id,
            resource_type=resource_type,
            action=PermissionAction.READ
        )
    
    @staticmethod
    def full_access(user_id: str, resource_type: str = "project") -> Permission:
        """Create full access (MANAGE) permission"""
        return PermissionFactory.create_manage_permission(
            user_id=user_id,
            resource_type=resource_type
        )
    
    @staticmethod
    def wildcard(user_id: str, resource_type: str = "project") -> Permission:
        """Create wildcard permission (all resources of type)"""
        return PermissionFactory.create_wildcard_permission(
            user_id=user_id,
            resource_type=resource_type
        )
    
    @staticmethod
    def minimal(user_id: str) -> Permission:
        """Create minimal valid permission"""
        return PermissionFactory.build(
            user_id=user_id,
            resource_type="test",
            action=PermissionAction.READ
        )
