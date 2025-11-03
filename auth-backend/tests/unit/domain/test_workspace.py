"""Unit tests for Workspace domain model"""
import pytest
from core.domain.workspace.workspace import Workspace
from core.exceptions import MissingRequiredFieldException, InvalidValueException


def test_workspace_creation():
    """Test creating a valid workspace"""
    workspace = Workspace(
        id="test-id",
        name="Test Workspace",
        slug="test-workspace",
        description="A test workspace",
        settings={"theme": "dark"},
        active=True
    )
    
    assert workspace.id == "test-id"
    assert workspace.name == "Test Workspace"
    assert workspace.slug == "test-workspace"
    assert workspace.description == "A test workspace"
    assert workspace.settings == {"theme": "dark"}
    assert workspace.active is True


def test_workspace_validation_success():
    """Test workspace validation with valid data"""
    workspace = Workspace(
        id=None,
        name="Valid Workspace",
        slug="valid-workspace",
        description="Test"
    )
    
    workspace.validate()  # Should not raise


def test_workspace_validation_missing_name():
    """Test validation fails when name is missing"""
    workspace = Workspace(
        id=None,
        name="",
        slug="test-slug"
    )
    
    with pytest.raises(MissingRequiredFieldException):
        workspace.validate()


def test_workspace_validation_missing_slug():
    """Test validation fails when slug is missing"""
    workspace = Workspace(
        id=None,
        name="Test Workspace",
        slug=""
    )
    
    with pytest.raises(MissingRequiredFieldException):
        workspace.validate()


def test_workspace_validation_name_too_short():
    """Test validation fails when name is too short"""
    workspace = Workspace(
        id=None,
        name="A",
        slug="test-slug"
    )
    
    with pytest.raises(InvalidValueException):
        workspace.validate()


def test_workspace_validation_invalid_slug():
    """Test validation fails with invalid slug characters"""
    workspace = Workspace(
        id=None,
        name="Test Workspace",
        slug="Test Workspace!"  # Invalid: uppercase and special chars
    )
    
    with pytest.raises(InvalidValueException):
        workspace.validate()


def test_workspace_activate():
    """Test activating workspace"""
    workspace = Workspace(
        id="test-id",
        name="Test",
        slug="test",
        active=False
    )
    
    workspace.activate()
    assert workspace.active is True


def test_workspace_deactivate():
    """Test deactivating workspace"""
    workspace = Workspace(
        id="test-id",
        name="Test",
        slug="test",
        active=True
    )
    
    workspace.deactivate()
    assert workspace.active is False


def test_workspace_update_name():
    """Test updating workspace name"""
    workspace = Workspace(
        id="test-id",
        name="Old Name",
        slug="test"
    )
    
    workspace.update_name("New Name")
    assert workspace.name == "New Name"


def test_workspace_update_name_invalid():
    """Test updating with invalid name"""
    workspace = Workspace(
        id="test-id",
        name="Old Name",
        slug="test"
    )
    
    with pytest.raises(InvalidValueException):
        workspace.update_name("A")  # Too short


def test_workspace_update_slug():
    """Test updating workspace slug"""
    workspace = Workspace(
        id="test-id",
        name="Test",
        slug="old-slug"
    )
    
    workspace.update_slug("new-slug")
    assert workspace.slug == "new-slug"


def test_workspace_generate_slug_from_name():
    """Test auto-generating slug from name"""
    slug = Workspace.generate_slug_from_name("My Company Name")
    assert slug == "my-company-name"
    
    slug = Workspace.generate_slug_from_name("Test  Multiple   Spaces")
    assert slug == "test-multiple-spaces"
    
    slug = Workspace.generate_slug_from_name("Special!@#$%Characters")
    assert slug == "specialcharacters"

