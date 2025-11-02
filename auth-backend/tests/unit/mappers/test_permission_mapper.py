"""
Unit tests for PermissionMapper
Tests conversion between database model and domain model
"""
import pytest
from datetime import datetime
from infra.database.mappers.permission_mapper import PermissionMapper
from core.domain.auth.permission import Permission
from infra.database.models.permission import DBPermission


@pytest.mark.unit
class TestPermissionMapperToDomain:
    """Test converting DB model to domain model"""
    
    def test_to_domain_maps_all_fields(self):
        """Test to_domain maps all fields correctly"""
        db_permission = DBPermission(
            id="perm-123",
            name="users.create",
            description="Create new users",
            resource="users",
            action="create",
            client_id="client-123",
            created_at=datetime(2023, 1, 1)
        )
        
        domain_permission = PermissionMapper.to_domain(db_permission)
        
        assert isinstance(domain_permission, Permission)
        assert domain_permission.id == "perm-123"
        assert domain_permission.name == "users.create"
        assert domain_permission.description == "Create new users"
        assert domain_permission.resource == "users"
        assert domain_permission.action == "create"
        assert domain_permission.client_id == "client-123"


@pytest.mark.unit
class TestPermissionMapperToDatabase:
    """Test converting domain model to DB model"""
    
    def test_to_database_maps_all_fields(self):
        """Test to_database maps all fields correctly"""
        domain_permission = Permission(
            id="perm-123",
            name="projects.delete",
            description="Delete projects",
            resource="projects",
            action="delete",
            client_id="client-123",
            created_at=datetime(2023, 1, 1)
        )
        
        db_permission = PermissionMapper.to_database(domain_permission)
        
        assert isinstance(db_permission, DBPermission)
        assert db_permission.id == "perm-123"
        assert db_permission.name == "projects.delete"
        assert db_permission.description == "Delete projects"
        assert db_permission.resource == "projects"
        assert db_permission.action == "delete"

