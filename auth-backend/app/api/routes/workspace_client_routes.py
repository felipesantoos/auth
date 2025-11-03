"""
Workspace Client Routes
Manage client access within workspaces
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from core.services.workspace.workspace_member_service import WorkspaceMemberService
from core.domain.auth.app_user import AppUser
from app.api.middlewares.auth_middleware import get_current_user
from app.api.middlewares.workspace_middleware import verify_workspace_admin
from infra.database.database import get_db_session
from infra.database.repositories.user_client_repository import UserClientRepository
from infra.database.models.workspace_client import DBWorkspaceClient
from infra.database.models.user_client import DBUserClient
from sqlalchemy import select

router = APIRouter(prefix="/api/v1", tags=["Workspace Clients"])


# DTOs
class AddClientToWorkspaceRequest(BaseModel):
    """Request to add client access to workspace"""
    client_id: str = Field(..., description="Client ID to grant access")


class WorkspaceClientResponse(BaseModel):
    """Workspace client access response"""
    id: str
    workspace_id: str
    client_id: str
    active: bool
    
    class Config:
        from_attributes = True


class UserClientResponse(BaseModel):
    """User's accessible clients response"""
    client_id: str
    access_type: str  # 'direct' or 'workspace'
    workspace_id: str = None
    workspace_name: str = None


def get_workspace_member_service(
    session: AsyncSession = Depends(get_db_session)
) -> WorkspaceMemberService:
    """Dependency to get workspace member service"""
    from infra.database.repositories.workspace_member_repository import WorkspaceMemberRepository
    repository = WorkspaceMemberRepository(session)
    return WorkspaceMemberService(repository)


@router.post("/workspaces/{workspace_id}/clients", response_model=WorkspaceClientResponse, status_code=status.HTTP_201_CREATED)
async def add_client_to_workspace(
    workspace_id: str,
    request: AddClientToWorkspaceRequest,
    current_user: AppUser = Depends(get_current_user),
    member_service: WorkspaceMemberService = Depends(get_workspace_member_service),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Grant workspace access to a client/application.
    
    All members of the workspace will inherit access to this client.
    Requires admin permission.
    """
    try:
        # Verify user is admin
        await verify_workspace_admin(current_user, workspace_id, member_service)
        
        # Create workspace-client access
        from datetime import datetime
        import uuid
        
        workspace_client = DBWorkspaceClient(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            client_id=request.client_id,
            active=True,
            granted_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        session.add(workspace_client)
        await session.flush()
        await session.refresh(workspace_client)
        
        return WorkspaceClientResponse(
            id=workspace_client.id,
            workspace_id=workspace_client.workspace_id,
            client_id=workspace_client.client_id,
            active=workspace_client.active
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add client to workspace: {str(e)}"
        )


@router.get("/workspaces/{workspace_id}/clients", response_model=List[WorkspaceClientResponse])
async def list_workspace_clients(
    workspace_id: str,
    current_user: AppUser = Depends(get_current_user),
    member_service: WorkspaceMemberService = Depends(get_workspace_member_service),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List all clients accessible by this workspace.
    
    Requires user to be a member of the workspace.
    """
    try:
        # Verify user is member
        from app.api.middlewares.workspace_middleware import verify_workspace_member
        await verify_workspace_member(current_user, workspace_id, member_service)
        
        # Query workspace clients
        result = await session.execute(
            select(DBWorkspaceClient).where(
                DBWorkspaceClient.workspace_id == workspace_id,
                DBWorkspaceClient.active == True
            )
        )
        workspace_clients = result.scalars().all()
        
        return [
            WorkspaceClientResponse(
                id=wc.id,
                workspace_id=wc.workspace_id,
                client_id=wc.client_id,
                active=wc.active
            )
            for wc in workspace_clients
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list workspace clients: {str(e)}"
        )


@router.delete("/workspaces/{workspace_id}/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_client_from_workspace(
    workspace_id: str,
    client_id: str,
    current_user: AppUser = Depends(get_current_user),
    member_service: WorkspaceMemberService = Depends(get_workspace_member_service),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Remove client access from workspace.
    
    Requires admin permission.
    """
    try:
        # Verify user is admin
        await verify_workspace_admin(current_user, workspace_id, member_service)
        
        # Find and delete workspace-client
        result = await session.execute(
            select(DBWorkspaceClient).where(
                DBWorkspaceClient.workspace_id == workspace_id,
                DBWorkspaceClient.client_id == client_id
            )
        )
        workspace_client = result.scalar_one_or_none()
        
        if not workspace_client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client access not found"
            )
        
        await session.delete(workspace_client)
        await session.flush()
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove client from workspace: {str(e)}"
        )


@router.get("/users/me/clients", response_model=List[UserClientResponse])
async def get_my_accessible_clients(
    current_user: AppUser = Depends(get_current_user),
    member_service: WorkspaceMemberService = Depends(get_workspace_member_service),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get all clients accessible by the current user.
    
    Returns clients from:
    1. Direct user-client access
    2. Workspace-client access (via user's workspaces)
    """
    try:
        accessible_clients = []
        
        # 1. Get direct user-client access
        user_client_repo = UserClientRepository(session)
        direct_accesses = await user_client_repo.find_by_user(current_user.id, active_only=True)
        
        for access in direct_accesses:
            accessible_clients.append(
                UserClientResponse(
                    client_id=access.client_id,
                    access_type="direct",
                    workspace_id=access.workspace_id,
                    workspace_name=None
                )
            )
        
        # 2. Get workspace-client access (via user's workspaces)
        user_workspaces = await member_service.get_user_workspaces(current_user.id, active_only=True)
        
        for membership in user_workspaces:
            # Get clients for this workspace
            result = await session.execute(
                select(DBWorkspaceClient).where(
                    DBWorkspaceClient.workspace_id == membership.workspace_id,
                    DBWorkspaceClient.active == True
                )
            )
            workspace_clients = result.scalars().all()
            
            # Get workspace name
            from infra.database.models.workspace import DBWorkspace
            ws_result = await session.execute(
                select(DBWorkspace).where(DBWorkspace.id == membership.workspace_id)
            )
            workspace = ws_result.scalar_one_or_none()
            workspace_name = workspace.name if workspace else None
            
            for wc in workspace_clients:
                # Avoid duplicates (in case user has direct + workspace access)
                if not any(c.client_id == wc.client_id for c in accessible_clients):
                    accessible_clients.append(
                        UserClientResponse(
                            client_id=wc.client_id,
                            access_type="workspace",
                            workspace_id=membership.workspace_id,
                            workspace_name=workspace_name
                        )
                    )
        
        return accessible_clients
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get accessible clients: {str(e)}"
        )

