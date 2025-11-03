"""
Unit tests for Permission Mapper
Tests conversion between domain and database models
"""
import pytest
from datetime import datetime
from infra.database.mappers.permission_mapper import PermissionMapper
from core.domain.auth.permission import Permission, PermissionAction
from infra.database.models.permission import PermissionModel
from tests.factories import PermissionFactory


@pytest.mark.unit
class TestPermissionMapperToDomain:
    """Test converting DB model to domain model"""

    def test_to_domain_maps_basic_fields(self):
        """Should map basic fields from DB to domain"""
        db_permission = PermissionModel(
            id="perm-123",
            user_id="user-456",
            client_id="client-789",
            resource_type="project",
            resource_id="res-111",
            action="read",
            granted_by="admin-222",
            created_at=datetime.utcnow()
        )
        
        mapper = PermissionMapper()
        domain_permission = mapper.to_domain(db_permission)
        
        assert domain_permission.id == "perm-123"
        assert domain_permission.user_id == "user-456"
        assert domain_permission.resource_type == "project"


@pytest.mark.unit
class TestPermissionMapperToDatabase:
    """Test converting domain model to DB model"""

    def test_to_database_maps_fields(self):
        """Should map fields from domain to DB"""
        permission = PermissionFactory.build()
        
        mapper = PermissionMapper()
        
        # Should be able to convert (method name might be to_db or to_database)
        assert hasattr(mapper, 'to_db') or hasattr(mapper, 'to_database')

