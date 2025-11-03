"""
Workspace Routes
REST API endpoints for workspace management
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dtos.request.workspace_request import (
    WorkspaceCreateRequest,
    WorkspaceUpdateRequest,
)
from app.api.dtos.response.workspace_response import (
    WorkspaceResponse,
    WorkspaceListResponse,
)
from core.services.workspace.workspace_service import WorkspaceService
from core.services.workspace.workspace_member_service import WorkspaceMemberService
from core.domain.auth.app_user import AppUser
from app.api.middlewares.auth_middleware import get_current_user
from app.api.middlewares.workspace_middleware import (
    verify_workspace_member,
    verify_workspace_admin,
    verify_workspace_manager_or_admin
)
from infra.database.database import get_db_session
from core.exceptions import NotFoundException, ValidationException, BusinessRuleException

router = APIRouter(prefix="/api/v1/workspaces", tags=["Workspaces"])


def get_workspace_service(session: AsyncSession = Depends(get_db_session)) -> WorkspaceService:
    """Dependency to get workspace service"""
    from infra.database.repositories.workspace_repository import WorkspaceRepository
    repository = WorkspaceRepository(session)
    return WorkspaceService(repository)


def get_workspace_member_service(session: AsyncSession = Depends(get_db_session)) -> WorkspaceMemberService:
    """Dependency to get workspace member service"""
    from infra.database.repositories.workspace_member_repository import WorkspaceMemberRepository
    repository = WorkspaceMemberRepository(session)
    return WorkspaceMemberService(repository)


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    request: WorkspaceCreateRequest,
    current_user: AppUser = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    member_service: WorkspaceMemberService = Depends(get_workspace_member_service),
):
    """
    Create a new workspace.
    
    Creates a new workspace with the authenticated user as owner/admin.
    The slug will be auto-generated from the name if not provided.
    """
    try:
        workspace = await workspace_service.create_workspace(
            name=request.name,
            slug=request.slug,
            description=request.description,
            settings=request.settings
        )
        
        # Add current user as admin member of the workspace
        from core.domain.workspace.workspace_role import WorkspaceRole
        await member_service.add_member(
            user_id=current_user.id,
            workspace_id=workspace.id,
            role=WorkspaceRole.ADMIN
        )
        
        return WorkspaceResponse(
            id=workspace.id,
            name=workspace.name,
            slug=workspace.slug,
            description=workspace.description,
            settings=workspace.settings,
            active=workspace.active,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at
        )
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workspace: {str(e)}"
        )


@router.get("", response_model=WorkspaceListResponse)
async def list_workspaces(
    active_only: bool = True,
    current_user: AppUser = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    member_service: WorkspaceMemberService = Depends(get_workspace_member_service),
):
    """
    List workspaces the current user is a member of.
    
    Returns only workspaces where the user has active membership.
    """
    try:
        # Get user's workspace memberships
        memberships = await member_service.get_user_workspaces(
            user_id=current_user.id,
            active_only=active_only
        )
        
        # Fetch workspace details for each membership
        workspaces = []
        for membership in memberships:
            workspace = await workspace_service.get_workspace(membership.workspace_id)
            if workspace and (not active_only or workspace.active):
                workspaces.append(workspace)
        
        return WorkspaceListResponse(
            workspaces=[
                WorkspaceResponse(
                    id=ws.id,
                    name=ws.name,
                    slug=ws.slug,
                    description=ws.description,
                    settings=ws.settings,
                    active=ws.active,
                    created_at=ws.created_at,
                    updated_at=ws.updated_at
                )
                for ws in workspaces
            ],
            total=len(workspaces)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list workspaces: {str(e)}"
        )


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    current_user: AppUser = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    member_service: WorkspaceMemberService = Depends(get_workspace_member_service),
):
    """
    Get workspace by ID.
    
    Requires user to be a member of the workspace.
    """
    try:
        # Verify user is a member
        await verify_workspace_member(current_user, workspace_id, member_service)
        
        workspace = await workspace_service.get_workspace(workspace_id)
        
        return WorkspaceResponse(
            id=workspace.id,
            name=workspace.name,
            slug=workspace.slug,
            description=workspace.description,
            settings=workspace.settings,
            active=workspace.active,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at
        )
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workspace: {str(e)}"
        )


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: str,
    request: WorkspaceUpdateRequest,
    current_user: AppUser = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    member_service: WorkspaceMemberService = Depends(get_workspace_member_service),
):
    """
    Update workspace.
    
    Requires user to be an admin of the workspace.
    """
    try:
        # Verify user is admin
        await verify_workspace_admin(current_user, workspace_id, member_service)
        
        workspace = await workspace_service.update_workspace(
            workspace_id=workspace_id,
            name=request.name,
            slug=request.slug,
            description=request.description,
            settings=request.settings
        )
        
        return WorkspaceResponse(
            id=workspace.id,
            name=workspace.name,
            slug=workspace.slug,
            description=workspace.description,
            settings=workspace.settings,
            active=workspace.active,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at
        )
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update workspace: {str(e)}"
        )


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: str,
    current_user: AppUser = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    member_service: WorkspaceMemberService = Depends(get_workspace_member_service),
):
    """
    Delete workspace.
    
    Requires user to be an admin of the workspace.
    Warning: This will remove all members and associations.
    """
    try:
        # Verify user is admin
        await verify_workspace_admin(current_user, workspace_id, member_service)
        
        # Check if it's the user's last workspace
        user_workspaces = await member_service.get_user_workspaces(current_user.id, active_only=True)
        if len(user_workspaces) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your last workspace. Create another workspace first."
            )
        
        await workspace_service.delete_workspace(workspace_id)
        return None
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete workspace: {str(e)}"
        )


@router.post("/{workspace_id}/activate", response_model=WorkspaceResponse)
async def activate_workspace(
    workspace_id: str,
    current_user: AppUser = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    """Activate workspace (admin only)"""
    try:
        workspace = await workspace_service.activate_workspace(workspace_id)
        
        return WorkspaceResponse(
            id=workspace.id,
            name=workspace.name,
            slug=workspace.slug,
            description=workspace.description,
            settings=workspace.settings,
            active=workspace.active,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at
        )
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate workspace: {str(e)}"
        )


@router.post("/{workspace_id}/deactivate", response_model=WorkspaceResponse)
async def deactivate_workspace(
    workspace_id: str,
    current_user: AppUser = Depends(get_current_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
):
    """Deactivate workspace (admin only)"""
    try:
        workspace = await workspace_service.deactivate_workspace(workspace_id)
        
        return WorkspaceResponse(
            id=workspace.id,
            name=workspace.name,
            slug=workspace.slug,
            description=workspace.description,
            settings=workspace.settings,
            active=workspace.active,
            created_at=workspace.created_at,
            updated_at=workspace.updated_at
        )
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate workspace: {str(e)}"
        )

