"""
Workspace Leave Routes
Endpoint for users to leave workspaces
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.services.workspace.workspace_member_service import WorkspaceMemberService
from core.domain.workspace.workspace_role import WorkspaceRole
from core.domain.auth.app_user import AppUser
from app.api.middlewares.auth_middleware import get_current_user
from infra.database.database import get_db_session
from core.exceptions import NotFoundException

router = APIRouter(prefix="/api/v1/workspaces", tags=["Workspace Members"])


def get_workspace_member_service(
    session: AsyncSession = Depends(get_db_session)
) -> WorkspaceMemberService:
    """Dependency to get workspace member service"""
    from infra.database.repositories.workspace_member_repository import WorkspaceMemberRepository
    repository = WorkspaceMemberRepository(session)
    return WorkspaceMemberService(repository)


@router.post("/{workspace_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_workspace(
    workspace_id: str,
    current_user: AppUser = Depends(get_current_user),
    member_service: WorkspaceMemberService = Depends(get_workspace_member_service),
):
    """
    Leave a workspace.
    
    User removes themselves from the workspace.
    Cannot leave if you're the last admin.
    """
    try:
        # Get user's membership
        member = await member_service.get_member(current_user.id, workspace_id)
        
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You are not a member of this workspace"
            )
        
        # Check if user is the last admin
        if member.role == WorkspaceRole.ADMIN:
            members = await member_service.get_workspace_members(workspace_id, active_only=True)
            admin_count = sum(1 for m in members if m.role == WorkspaceRole.ADMIN)
            
            if admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot leave workspace: you are the last admin. Promote another member to admin first."
                )
        
        # Check if this is user's last workspace
        user_workspaces = await member_service.get_user_workspaces(current_user.id, active_only=True)
        if len(user_workspaces) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot leave your last workspace. Join or create another workspace first."
            )
        
        # Remove user from workspace
        await member_service.remove_member(current_user.id, workspace_id)
        
        return None
        
    except HTTPException:
        raise
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to leave workspace: {str(e)}"
        )

