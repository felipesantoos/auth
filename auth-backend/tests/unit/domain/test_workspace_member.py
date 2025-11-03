"""Unit tests for WorkspaceMember domain model"""
import pytest
from datetime import datetime
from core.domain.workspace.workspace_member import WorkspaceMember
from core.domain.workspace.workspace_role import WorkspaceRole
from core.exceptions import MissingRequiredFieldException


def test_workspace_member_creation():
    """Test creating a valid workspace member"""
    member = WorkspaceMember(
        id="member-id",
        user_id="user-id",
        workspace_id="workspace-id",
        role=WorkspaceRole.ADMIN,
        active=True
    )
    
    assert member.id == "member-id"
    assert member.user_id == "user-id"
    assert member.workspace_id == "workspace-id"
    assert member.role == WorkspaceRole.ADMIN
    assert member.active is True


def test_workspace_member_validation_success():
    """Test validation with valid data"""
    member = WorkspaceMember(
        id=None,
        user_id="user-123",
        workspace_id="workspace-123",
        role=WorkspaceRole.USER
    )
    
    member.validate()  # Should not raise


def test_workspace_member_validation_missing_user_id():
    """Test validation fails when user_id is missing"""
    member = WorkspaceMember(
        id=None,
        user_id="",
        workspace_id="workspace-123",
        role=WorkspaceRole.USER
    )
    
    with pytest.raises(MissingRequiredFieldException):
        member.validate()


def test_workspace_member_validation_missing_workspace_id():
    """Test validation fails when workspace_id is missing"""
    member = WorkspaceMember(
        id=None,
        user_id="user-123",
        workspace_id="",
        role=WorkspaceRole.USER
    )
    
    with pytest.raises(MissingRequiredFieldException):
        member.validate()


def test_workspace_member_is_admin():
    """Test checking if member is admin"""
    admin = WorkspaceMember(
        id="1",
        user_id="user-1",
        workspace_id="ws-1",
        role=WorkspaceRole.ADMIN
    )
    
    user = WorkspaceMember(
        id="2",
        user_id="user-2",
        workspace_id="ws-1",
        role=WorkspaceRole.USER
    )
    
    assert admin.is_admin() is True
    assert user.is_admin() is False


def test_workspace_member_is_manager():
    """Test checking if member is manager"""
    manager = WorkspaceMember(
        id="1",
        user_id="user-1",
        workspace_id="ws-1",
        role=WorkspaceRole.MANAGER
    )
    
    user = WorkspaceMember(
        id="2",
        user_id="user-2",
        workspace_id="ws-1",
        role=WorkspaceRole.USER
    )
    
    assert manager.is_manager() is True
    assert user.is_manager() is False


def test_workspace_member_can_manage_users():
    """Test permission to manage users"""
    admin = WorkspaceMember(
        id="1",
        user_id="user-1",
        workspace_id="ws-1",
        role=WorkspaceRole.ADMIN
    )
    
    manager = WorkspaceMember(
        id="2",
        user_id="user-2",
        workspace_id="ws-1",
        role=WorkspaceRole.MANAGER
    )
    
    user = WorkspaceMember(
        id="3",
        user_id="user-3",
        workspace_id="ws-1",
        role=WorkspaceRole.USER
    )
    
    assert admin.can_manage_users() is True
    assert manager.can_manage_users() is True
    assert user.can_manage_users() is False


def test_workspace_member_can_manage_workspace():
    """Test permission to manage workspace"""
    admin = WorkspaceMember(
        id="1",
        user_id="user-1",
        workspace_id="ws-1",
        role=WorkspaceRole.ADMIN
    )
    
    manager = WorkspaceMember(
        id="2",
        user_id="user-2",
        workspace_id="ws-1",
        role=WorkspaceRole.MANAGER
    )
    
    assert admin.can_manage_workspace() is True
    assert manager.can_manage_workspace() is False


def test_workspace_member_update_role():
    """Test updating member role"""
    member = WorkspaceMember(
        id="1",
        user_id="user-1",
        workspace_id="ws-1",
        role=WorkspaceRole.USER
    )
    
    member.update_role(WorkspaceRole.ADMIN)
    assert member.role == WorkspaceRole.ADMIN


def test_workspace_member_activate_deactivate():
    """Test activating and deactivating membership"""
    member = WorkspaceMember(
        id="1",
        user_id="user-1",
        workspace_id="ws-1",
        role=WorkspaceRole.USER,
        active=False
    )
    
    member.activate()
    assert member.active is True
    
    member.deactivate()
    assert member.active is False


def test_workspace_member_mark_as_joined():
    """Test marking member as joined"""
    member = WorkspaceMember(
        id="1",
        user_id="user-1",
        workspace_id="ws-1",
        role=WorkspaceRole.USER
    )
    
    assert member.joined_at is None
    member.mark_as_joined()
    assert member.joined_at is not None
    assert isinstance(member.joined_at, datetime)

