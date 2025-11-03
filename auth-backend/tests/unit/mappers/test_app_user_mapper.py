"""
Unit tests for AppUserMapper
Tests conversion between database model and domain model
"""
import pytest
from datetime import datetime
from infra.database.mappers.app_user_mapper import AppUserMapper
from core.domain.auth.app_user import AppUser
from core.domain.auth.user_role import UserRole
from infra.database.models.app_user import DBAppUser


@pytest.mark.unit
class TestAppUserMapperToDomain:
    """Test converting DB model to domain model"""
    

@pytest.mark.unit
class TestAppUserMapperToDatabase:
    """Test converting domain model to DB model"""
    