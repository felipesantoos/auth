"""
Unit tests for AuthMapper
Tests conversion between domain models and DTOs
"""
import pytest
from datetime import datetime
from app.api.mappers.auth_mapper import AuthMapper
from app.api.dtos.response.auth_response import UserResponse, TokenResponse
from core.domain.auth.user_role import UserRole
from tests.factories import UserFactory


@pytest.mark.unit
class TestAuthMapperToUserResponse:
    """Test converting AppUser domain to UserResponse DTO"""
    