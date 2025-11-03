"""
Workspace Authorization Middleware
Verifies user permissions within workspaces
"""
from typing import Optional
from fastapi import HTTPException, status
from core.domain.auth.app_user import AppUser
from core.domain.workspace.workspace_role import WorkspaceRole
from core.services.workspace.workspace_member_service import WorkspaceMemberService


async def verify_workspace_member(
    user: AppUser,
    workspace_id: str,
    member_service: WorkspaceMemberService
) -> None:
    """
    Verify user is a member of the workspace.
    
    Args:
        user: Current authenticated user
        workspace_id: Workspace ID
        member_service: Workspace member service
        
    Raises:
        HTTPException 403: If user is not a member
    """
    member = await member_service.get_member(user.id, workspace_id)
    
    if not member or not member.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this workspace"
        )


async def verify_workspace_admin(
    user: AppUser,
    workspace_id: str,
    member_service: WorkspaceMemberService
) -> None:
    """
    Verify user is an admin of the workspace.
    
    Args:
        user: Current authenticated user
        workspace_id: Workspace ID
        member_service: Workspace member service
        
    Raises:
        HTTPException 403: If user is not an admin
    """
    member = await member_service.get_member(user.id, workspace_id)
    
    if not member or not member.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this workspace"
        )
    
    if not member.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be an admin to perform this action"
        )


async def verify_workspace_manager_or_admin(
    user: AppUser,
    workspace_id: str,
    member_service: WorkspaceMemberService
) -> None:
    """
    Verify user is a manager or admin of the workspace.
    
    Args:
        user: Current authenticated user
        workspace_id: Workspace ID
        member_service: Workspace member service
        
    Raises:
        HTTPException 403: If user is not a manager or admin
    """
    member = await member_service.get_member(user.id, workspace_id)
    
    if not member or not member.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this workspace"
        )
    
    if not member.can_manage_users():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a manager or admin to perform this action"
        )

