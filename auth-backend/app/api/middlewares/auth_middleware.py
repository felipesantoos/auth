"""
Authentication Middleware
FastAPI dependency for JWT validation and user authorization
Adapted for multi-tenant architecture with dual-mode support (cookies/headers)
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from core.domain.auth.app_user import AppUser
from core.domain.auth.user_role import UserRole
from core.interfaces.primary.auth_service_interface import IAuthService
from infra.database.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dicontainer.dicontainer import get_auth_service
from app.api.middlewares.tenant_middleware import get_client_from_request

# HTTP Bearer token scheme (auto_error=False for dual-mode support)
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: IAuthService = Depends(get_auth_service),
    session: AsyncSession = Depends(get_db_session),
) -> AppUser:
    """
    Dependency to get current authenticated user from JWT token (multi-tenant, dual-mode).
    
    Dual-Mode Support:
    - Web: Reads token from httpOnly cookie (XSS protection)
    - Mobile: Reads token from Authorization header (Bearer token)
    
    Priority:
    1. Authorization header (if present)
    2. Cookie (if header not present)
    
    Validates that the user's client_id matches the client_id from the request.
    
    Args:
        request: FastAPI request object
        credentials: HTTP Authorization header with Bearer token (optional)
        auth_service: Auth service instance
        session: Database session
        
    Returns:
        Current authenticated user
        
    Raises:
        HTTPException: If token is invalid, user not found, or client mismatch
    """
    # Dual-mode: Get token from Authorization header OR cookie
    token = None
    
    if credentials:
        # Priority 1: Authorization header (mobile apps, API clients)
        token = credentials.credentials
    else:
        # Priority 2: Cookie (web browsers)
        token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required (token not found in header or cookie)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify token
    payload = auth_service.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user
    user_id = payload.get("user_id")
    token_client_id = payload.get("client_id")  # Multi-tenant
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get client_id from request (multi-tenant validation)
    request_client_id = None
    try:
        from app.api.dicontainer.dicontainer import get_client_repository
        client_repository = get_client_repository(session=session)
        request_client_id = await get_client_from_request(request, client_repository)
    except Exception:
        # If client_id extraction fails, use token's client_id
        request_client_id = token_client_id
    
    # Multi-tenant: Validate client_id matches
    if token_client_id and request_client_id and token_client_id != request_client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token client_id does not match request client",
        )
    
    # Use request_client_id or token_client_id for user lookup
    client_id_to_use = request_client_id or token_client_id
    
    # Get user with client_id filtering (multi-tenant)
    user = await auth_service.get_current_user(user_id, client_id=client_id_to_use)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )
    
    # Store client_id in request state for later use
    request.state.client_id = user.client_id
    
    # Store session_id if present in token (for session management)
    session_id = payload.get("session_id")
    if session_id:
        request.state.session_id = session_id
    
    return user


async def get_current_admin_user(
    current_user: AppUser = Depends(get_current_user),
) -> AppUser:
    """
    Dependency to ensure current user is an admin.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user if admin
        
    Raises:
        HTTPException: If user is not admin
    """
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def get_current_manager_user(
    current_user: AppUser = Depends(get_current_user),
) -> AppUser:
    """
    Dependency to ensure current user is admin or manager.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user if admin or manager
        
    Raises:
        HTTPException: If user is not admin or manager
    """
    if not current_user.can_manage_users():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager or admin access required",
        )
    return current_user


# Optional authentication (doesn't raise error if no token)
async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    session: AsyncSession = Depends(get_db_session),
) -> Optional[AppUser]:
    """
    Optional authentication dependency (multi-tenant).
    Returns user if token is valid, None otherwise (doesn't raise error).
    """
    if not credentials:
        return None
    
    try:
        auth_service = await get_auth_service(session=session)
        token = credentials.credentials
        
        payload = auth_service.verify_token(token)
        if not payload or payload.get("type") != "access":
            return None
        
        user_id = payload.get("user_id")
        token_client_id = payload.get("client_id")
        
        if not user_id:
            return None
        
        # Get client_id from request
        request_client_id = None
        try:
            from app.api.dicontainer.dicontainer import get_client_repository
            client_repository = get_client_repository(session=session)
            request_client_id = await get_client_from_request(request, client_repository)
        except Exception:
            request_client_id = token_client_id
        
        client_id_to_use = request_client_id or token_client_id
        
        user = await auth_service.get_current_user(user_id, client_id=client_id_to_use)
        if not user or not user.active:
            return None
        
        return user
    except Exception:
        return None

