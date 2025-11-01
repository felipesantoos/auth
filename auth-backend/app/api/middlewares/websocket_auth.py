"""
WebSocket Authentication
Validates JWT tokens for WebSocket connections
"""
from fastapi import WebSocket, HTTPException, status
from typing import Optional
import logging

from core.domain.auth.app_user import AppUser
from core.interfaces.primary.auth_service_interface import IAuthService
from app.api.dicontainer.dicontainer import get_auth_service, get_app_user_repository

logger = logging.getLogger(__name__)


async def get_current_user_ws(
    websocket: WebSocket,
    token: Optional[str] = None
) -> AppUser:
    """
    Authenticate WebSocket connection using JWT token.
    
    Args:
        websocket: WebSocket connection
        token: JWT access token (from query parameter)
    
    Returns:
        Authenticated user
    
    Raises:
        Exception: If authentication fails
    
    Usage:
        @router.websocket("/ws")
        async def ws_endpoint(websocket: WebSocket, token: str = Query(None)):
            user = await get_current_user_ws(websocket, token)
            # ... proceed with WebSocket logic
    """
    # Check if token is provided
    if not token:
        logger.warning("WebSocket connection attempt without token")
        raise Exception("Authentication token required")
    
    try:
        # Validate token
        auth_service: IAuthService = get_auth_service()
        payload = auth_service.verify_token(token)
        
        # Extract user data from payload
        user_id = payload.get("sub")
        client_id = payload.get("client_id")
        
        if not user_id or not client_id:
            raise Exception("Invalid token payload")
        
        # Get user from repository
        user_repository = get_app_user_repository()
        
        user = await user_repository.find_by_id(user_id, client_id)
        
        if not user:
            raise Exception("User not found")
        
        if not user.active:
            raise Exception("User is inactive")
        
        logger.debug(f"WebSocket user authenticated: {user_id}")
        return user
    
    except Exception as e:
        logger.warning(f"WebSocket authentication failed: {e}")
        raise Exception(f"Authentication failed: {str(e)}")


async def verify_websocket_permissions(
    user: AppUser,
    required_permission: str
) -> bool:
    """
    Verify if user has required permission for WebSocket action.
    
    Args:
        user: Authenticated user
        required_permission: Permission string required
    
    Returns:
        True if user has permission, False otherwise
    
    Usage:
        if not await verify_websocket_permissions(user, "room:join"):
            await websocket.send_json({"error": "Permission denied"})
            return
    """
    # Implement permission check based on your permission system
    # For now, allow all authenticated users
    # You can extend this to check specific permissions
    
    # Example:
    # if user.role == UserRole.ADMIN:
    #     return True
    # 
    # user_permissions = await get_user_permissions(user.id)
    # return required_permission in user_permissions
    
    return True

