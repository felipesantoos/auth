"""
Workspace Member Routes
REST API endpoints for workspace member management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dtos.request.workspace_request import (
    AddWorkspaceMemberRequest,
    UpdateMemberRoleRequest,
)
from app.api.dtos.response.workspace_response import (
    WorkspaceMemberResponse,
    WorkspaceMemberListResponse,
)
from core.services.workspace.workspace_member_service import WorkspaceMemberService
from core.domain.workspace.workspace_role import WorkspaceRole
from core.domain.auth.app_user import AppUser
from app.api.middlewares.auth_middleware import get_current_user
from app.api.middlewares.workspace_middleware import verify_workspace_manager_or_admin
from infra.database.database import get_db_session
from core.exceptions import NotFoundException, BusinessRuleException

router = APIRouter(prefix="/api/v1/workspaces", tags=["Workspace Members"])


def get_workspace_member_service(
    session: AsyncSession = Depends(get_db_session)
) -> WorkspaceMemberService:
    """Dependency to get workspace member service"""
    from infra.database.repositories.workspace_member_repository import WorkspaceMemberRepository
    repository = WorkspaceMemberRepository(session)
    return WorkspaceMemberService(repository)


@router.post("/{workspace_id}/members", response_model=WorkspaceMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_workspace_member(
    workspace_id: str,
    request: AddWorkspaceMemberRequest,
    current_user: AppUser = Depends(get_current_user),
    member_service: WorkspaceMemberService = Depends(get_workspace_member_service),
):
    """
    Add a member to workspace.
    
    Requires current user to be a manager or admin of the workspace.
    """
    try:
        # Verify user is manager or admin
        await verify_workspace_manager_or_admin(current_user, workspace_id, member_service)
        
        # Convert string role to enum
        role = WorkspaceRole(request.role)
        
        member = await member_service.add_member(
            user_id=request.user_id,
            workspace_id=workspace_id,
            role=role
        )
        
        return WorkspaceMemberResponse(
            id=member.id,
            user_id=member.user_id,
            workspace_id=member.workspace_id,
            role=member.role.value,
            active=member.active,
            invited_at=member.invited_at,
            joined_at=member.joined_at,
            created_at=member.created_at,
            updated_at=member.updated_at
        )
    except BusinessRuleException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add member: {str(e)}"
        )


@router.get("/{workspace_id}/members", response_model=WorkspaceMemberListResponse)
async def list_workspace_members(
    workspace_id: str,
    active_only: bool = True,
    current_user: AppUser = Depends(get_current_user),
    member_service: WorkspaceMemberService = Depends(get_workspace_member_service),
):
    """
    List all members of a workspace.
    
    TODO: Check if current user is a member of the workspace.
    """
    try:
        members = await member_service.get_workspace_members(
            workspace_id=workspace_id,
            active_only=active_only
        )
        
        return WorkspaceMemberListResponse(
            members=[
                WorkspaceMemberResponse(
                    id=m.id,
                    user_id=m.user_id,
                    workspace_id=m.workspace_id,
                    role=m.role.value,
                    active=m.active,
                    invited_at=m.invited_at,
                    joined_at=m.joined_at,
                    created_at=m.created_at,
                    updated_at=m.updated_at
                )
                for m in members
            ],
            total=len(members)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list members: {str(e)}"
        )


@router.patch("/{workspace_id}/members/{user_id}", response_model=WorkspaceMemberResponse)
async def update_member_role(
    workspace_id: str,
    user_id: str,
    request: UpdateMemberRoleRequest,
    current_user: AppUser = Depends(get_current_user),
    member_service: WorkspaceMemberService = Depends(get_workspace_member_service),
):
    """
    Update member role in workspace.
    
    Requires current user to be a manager or admin of the workspace.
    """
    try:
        # Verify user is manager or admin
        await verify_workspace_manager_or_admin(current_user, workspace_id, member_service)
        
        # Prevent user from demoting themselves if they're the last admin
        if user_id == current_user.id and request.role != "admin":
            members = await member_service.get_workspace_members(workspace_id, active_only=True)
            admin_count = sum(1 for m in members if m.role == WorkspaceRole.ADMIN)
            
            if admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot change role: you are the last admin of this workspace"
                )
        
        # Convert string role to enum
        new_role = WorkspaceRole(request.role)
        
        member = await member_service.update_member_role(
            user_id=user_id,
            workspace_id=workspace_id,
            new_role=new_role
        )
        
        return WorkspaceMemberResponse(
            id=member.id,
            user_id=member.user_id,
            workspace_id=member.workspace_id,
            role=member.role.value,
            active=member.active,
            invited_at=member.invited_at,
            joined_at=member.joined_at,
            created_at=member.created_at,
            updated_at=member.updated_at
        )
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update member role: {str(e)}"
        )


@router.delete("/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_workspace_member(
    workspace_id: str,
    user_id: str,
    current_user: AppUser = Depends(get_current_user),
    member_service: WorkspaceMemberService = Depends(get_workspace_member_service),
):
    """
    Remove member from workspace.
    
    Requires current user to be a manager or admin of the workspace.
    Cannot remove yourself or the last admin.
    """
    try:
        # Verify user is manager or admin
        await verify_workspace_manager_or_admin(current_user, workspace_id, member_service)
        
        # Prevent users from removing themselves
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove yourself from workspace. Use leave endpoint instead."
            )
        
        # Prevent removing the last admin
        target_member = await member_service.get_member(user_id, workspace_id)
        if target_member and target_member.role == WorkspaceRole.ADMIN:
            members = await member_service.get_workspace_members(workspace_id, active_only=True)
            admin_count = sum(1 for m in members if m.role == WorkspaceRole.ADMIN)
            
            if admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot remove the last admin from workspace"
                )
        
        await member_service.remove_member(
            user_id=user_id,
            workspace_id=workspace_id
        )
        return None
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove member: {str(e)}"
        )


@router.get("/my-workspaces", response_model=WorkspaceMemberListResponse)
async def get_my_workspaces(
    active_only: bool = True,
    current_user: AppUser = Depends(get_current_user),
    member_service: WorkspaceMemberService = Depends(get_workspace_member_service),
):
    """
    Get all workspaces the current user is a member of.
    """
    try:
        members = await member_service.get_user_workspaces(
            user_id=current_user.id,
            active_only=active_only
        )
        
        return WorkspaceMemberListResponse(
            members=[
                WorkspaceMemberResponse(
                    id=m.id,
                    user_id=m.user_id,
                    workspace_id=m.workspace_id,
                    role=m.role.value,
                    active=m.active,
                    invited_at=m.invited_at,
                    joined_at=m.joined_at,
                    created_at=m.created_at,
                    updated_at=m.updated_at
                )
                for m in members
            ],
            total=len(members)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user workspaces: {str(e)}"
        )

