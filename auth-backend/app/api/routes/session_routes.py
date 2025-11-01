"""
Session Management Routes
Endpoints for managing user sessions across devices
"""
from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import Annotated
import logging

from app.api.dtos.request.session_request import RevokeAllSessionsRequest
from app.api.dtos.response.session_response import (
    ActiveSessionsResponse,
    SessionInfoResponse,
    RevokeSessionResponse,
    RevokeAllSessionsResponse
)
from app.api.middlewares.auth_middleware import get_current_user
from app.api.dicontainer.dicontainer import get_session_service
from core.domain.auth.app_user import AppUser
from core.services.auth.session_service import SessionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/sessions", tags=["Sessions"])


@router.get("", response_model=ActiveSessionsResponse)
async def get_active_sessions(
    current_user: Annotated[AppUser, Depends(get_current_user)],
    session_service: Annotated[SessionService, Depends(get_session_service)]
):
    """
    Get all active sessions for current user.
    
    Shows devices, locations, last activity, etc.
    """
    try:
        sessions_data = await session_service.get_active_sessions(
            user_id=current_user.id,
            client_id=current_user.client_id
        )
        
        sessions = [SessionInfoResponse(**session) for session in sessions_data]
        
        return ActiveSessionsResponse(
            sessions=sessions,
            total=len(sessions)
        )
    except Exception as e:
        logger.error(f"Error getting sessions: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get sessions")


@router.delete("/{session_id}", response_model=RevokeSessionResponse)
async def revoke_session(
    session_id: Annotated[str, Path(description="Session ID to revoke")],
    current_user: Annotated[AppUser, Depends(get_current_user)],
    session_service: Annotated[SessionService, Depends(get_session_service)]
):
    """
    Revoke specific session (logout from specific device).
    
    Cannot revoke current session (use logout endpoint instead).
    """
    try:
        success = await session_service.revoke_session(
            session_id=session_id,
            user_id=current_user.id,
            client_id=current_user.client_id
        )
        
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found or already revoked")
        
        return RevokeSessionResponse(
            success=True,
            message="Session revoked successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking session: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to revoke session")


@router.delete("/all", response_model=RevokeAllSessionsResponse)
async def revoke_all_sessions(
    request: RevokeAllSessionsRequest,
    current_user: Annotated[AppUser, Depends(get_current_user)],
    session_service: Annotated[SessionService, Depends(get_session_service)]
):
    """
    Revoke all sessions (logout from all devices).
    
    By default, keeps current session active unless except_current=False.
    """
    try:
        # TODO: Get current session ID from token
        current_session_id = None if not request.except_current else "current_session_id"
        
        revoked_count = await session_service.revoke_all_sessions(
            user_id=current_user.id,
            client_id=current_user.client_id,
            except_current=current_session_id
        )
        
        return RevokeAllSessionsResponse(
            success=True,
            sessions_revoked=revoked_count,
            message=f"Revoked {revoked_count} session(s)"
        )
    except Exception as e:
        logger.error(f"Error revoking all sessions: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to revoke sessions")

