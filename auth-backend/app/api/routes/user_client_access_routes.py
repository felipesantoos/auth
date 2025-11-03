"""
User Client Access Routes
Manage direct user access to clients/applications
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from core.domain.auth.app_user import AppUser
from app.api.middlewares.auth_middleware import get_current_user
from infra.database.database import get_db_session
from infra.database.repositories.user_client_repository import UserClientRepository
from infra.database.models.user_client import DBUserClient
from core.exceptions import NotFoundException, DuplicateEntityException

router = APIRouter(prefix="/api/v1/users", tags=["User Client Access"])


# DTOs
class GrantClientAccessRequest(BaseModel):
    """Request to grant client access to user"""
    client_id: str = Field(..., description="Client ID to grant access")
    workspace_id: str = Field(None, description="Optional workspace context")


class UserClientAccessResponse(BaseModel):
    """User client access response"""
    id: str
    user_id: str
    client_id: str
    workspace_id: str = None
    active: bool
    granted_at: datetime
    
    class Config:
        from_attributes = True


@router.post("/{user_id}/clients", response_model=UserClientAccessResponse, status_code=status.HTTP_201_CREATED)
async def grant_user_client_access(
    user_id: str,
    request: GrantClientAccessRequest,
    current_user: AppUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Grant direct access to a client for a specific user.
    
    This creates a direct user→client relationship, independent of workspace.
    
    Authorization:
    - Users can grant access to themselves (self-service)
    - TODO: Add workspace admin check for granting to others
    
    Args:
        user_id: User ID to grant access to
        request: Client access request
        
    Returns:
        Created access record
    """
    try:
        # Check if user is granting to themselves or is admin
        if user_id != current_user.id:
            # TODO: Verify current_user is workspace admin
            # For now, only allow self-service
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only grant access to yourself. Admin features coming soon."
            )
        
        # Create user-client access
        user_client_repo = UserClientRepository(session)
        
        # Check if access already exists
        existing = await user_client_repo.find_by_user_and_client(user_id, request.client_id)
        if existing:
            if existing.active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User already has access to this client"
                )
            else:
                # Reactivate existing access
                existing.active = True
                existing.updated_at = datetime.utcnow()
                await user_client_repo.save(existing)
                return UserClientAccessResponse(
                    id=existing.id,
                    user_id=existing.user_id,
                    client_id=existing.client_id,
                    workspace_id=existing.workspace_id,
                    active=existing.active,
                    granted_at=existing.granted_at
                )
        
        # Create new access
        user_client = DBUserClient(
            id=str(uuid.uuid4()),
            user_id=user_id,
            client_id=request.client_id,
            workspace_id=request.workspace_id,
            active=True,
            granted_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        saved = await user_client_repo.save(user_client)
        
        return UserClientAccessResponse(
            id=saved.id,
            user_id=saved.user_id,
            client_id=saved.client_id,
            workspace_id=saved.workspace_id,
            active=saved.active,
            granted_at=saved.granted_at
        )
        
    except HTTPException:
        raise
    except DuplicateEntityException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to grant client access: {str(e)}"
        )


@router.get("/{user_id}/clients", response_model=List[UserClientAccessResponse])
async def list_user_client_access(
    user_id: str,
    active_only: bool = True,
    current_user: AppUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List all direct client accesses for a user.
    
    Returns only direct user→client relationships.
    For complete list including workspace access, use GET /users/me/clients
    
    Authorization:
    - Users can view their own accesses
    - TODO: Add admin check for viewing others
    """
    try:
        # Check if viewing own data or is admin
        if user_id != current_user.id:
            # TODO: Verify current_user is workspace admin
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own client accesses"
            )
        
        user_client_repo = UserClientRepository(session)
        accesses = await user_client_repo.find_by_user(user_id, active_only=active_only)
        
        return [
            UserClientAccessResponse(
                id=access.id,
                user_id=access.user_id,
                client_id=access.client_id,
                workspace_id=access.workspace_id,
                active=access.active,
                granted_at=access.granted_at
            )
            for access in accesses
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list client accesses: {str(e)}"
        )


@router.delete("/{user_id}/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_user_client_access(
    user_id: str,
    client_id: str,
    current_user: AppUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Revoke direct client access from user.
    
    Only removes direct user→client access.
    User may still have access via workspace.
    
    Authorization:
    - Users can revoke their own access
    - TODO: Add admin check for revoking others
    """
    try:
        # Check if revoking own access or is admin
        if user_id != current_user.id:
            # TODO: Verify current_user is workspace admin
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only revoke your own client access"
            )
        
        user_client_repo = UserClientRepository(session)
        deleted = await user_client_repo.delete(user_id, client_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client access not found"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke client access: {str(e)}"
        )


@router.get("/me/all-clients")
async def get_all_my_accessible_clients(
    current_user: AppUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get ALL clients accessible by current user.
    
    Returns clients from:
    1. Direct user→client access (user_client table)
    2. Workspace→client access (via user's workspace memberships)
    
    This is the COMPLETE list of clients the user can access.
    """
    from infra.database.repositories.workspace_member_repository import WorkspaceMemberRepository
    from infra.database.models.workspace_client import DBWorkspaceClient
    from infra.database.models.workspace import DBWorkspace
    from infra.database.models.client import DBClient
    from sqlalchemy import select
    
    try:
        accessible_clients = []
        seen_clients = set()  # Avoid duplicates
        
        # 1. Get direct user→client access
        user_client_repo = UserClientRepository(session)
        direct_accesses = await user_client_repo.find_by_user(current_user.id, active_only=True)
        
        for access in direct_accesses:
            # Get client details
            result = await session.execute(
                select(DBClient).where(DBClient.id == access.client_id)
            )
            client = result.scalar_one_or_none()
            
            if client and client.id not in seen_clients:
                accessible_clients.append({
                    "client_id": client.id,
                    "client_name": client.name,
                    "access_type": "direct",
                    "workspace_id": access.workspace_id,
                    "workspace_name": None
                })
                seen_clients.add(client.id)
        
        # 2. Get workspace→client access (via user's workspaces)
        workspace_member_repo = WorkspaceMemberRepository(session)
        user_workspaces = await workspace_member_repo.find_by_user(current_user.id, active_only=True)
        
        for membership in user_workspaces:
            # Get workspace name
            ws_result = await session.execute(
                select(DBWorkspace).where(DBWorkspace.id == membership.workspace_id)
            )
            workspace = ws_result.scalar_one_or_none()
            workspace_name = workspace.name if workspace else None
            
            # Get clients for this workspace
            wc_result = await session.execute(
                select(DBWorkspaceClient).where(
                    DBWorkspaceClient.workspace_id == membership.workspace_id,
                    DBWorkspaceClient.active == True
                )
            )
            workspace_clients = wc_result.scalars().all()
            
            for wc in workspace_clients:
                if wc.client_id not in seen_clients:
                    # Get client details
                    client_result = await session.execute(
                        select(DBClient).where(DBClient.id == wc.client_id)
                    )
                    client = client_result.scalar_one_or_none()
                    
                    if client:
                        accessible_clients.append({
                            "client_id": client.id,
                            "client_name": client.name,
                            "access_type": "workspace",
                            "workspace_id": membership.workspace_id,
                            "workspace_name": workspace_name,
                            "workspace_role": membership.role.value
                        })
                        seen_clients.add(client.id)
        
        return {
            "clients": accessible_clients,
            "total": len(accessible_clients)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get accessible clients: {str(e)}"
        )

