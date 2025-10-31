"""
Authentication Routes
API endpoints for user authentication and authorization
Adapted for multi-tenant architecture
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from core.interfaces.primary.auth_service_interface import AuthServiceInterface
from core.domain.auth.app_user import AppUser
from core.domain.auth.user_role import UserRole
from app.api.dtos.request.auth_request import (
    LoginRequest,
    RegisterRequest,
    ChangePasswordRequest,
    RefreshTokenRequest,
    UpdateUserRequest,
)
from app.api.dtos.response.auth_response import (
    TokenResponse,
    UserResponse,
    MessageResponse,
)
from app.api.mappers.auth_mapper import AuthMapper
from app.api.dicontainer.dicontainer import get_auth_service
from app.api.middlewares.auth_middleware import (
    get_current_user,
    get_current_admin_user,
)
from app.api.middlewares.tenant_middleware import get_client_from_request
from infra.database.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


async def get_client_id_from_request_or_body(
    request: Request,
    body_client_id: Optional[str],
    session: AsyncSession
) -> str:
    """
    Get client_id from request (header/subdomain) or request body.
    
    Priority:
    1. Body parameter (client_id)
    2. X-Client-ID header
    3. X-Client-Subdomain header or subdomain from Host
    """
    # Try body first
    if body_client_id:
        return body_client_id
    
    # Try from request
    try:
        from app.api.dicontainer.dicontainer import get_client_repository
        client_repository = get_client_repository(session=session)
        client_id = await get_client_from_request(request, client_repository)
        if client_id:
            return client_id
    except Exception:
        pass
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Client ID is required. Provide via client_id in body, X-Client-ID header, or subdomain"
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    login_request: LoginRequest,
    auth_service: AuthServiceInterface = Depends(get_auth_service),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Authenticate user and get access tokens (multi-tenant).
    
    Client ID can be provided via:
    - client_id in request body
    - X-Client-ID header
    - X-Client-Subdomain header
    - Subdomain in Host header (e.g., client1.example.com)
    
    Returns:
        TokenResponse with access_token, refresh_token, and user data
    """
    try:
        # Get client_id from request or body
        client_id = await get_client_id_from_request_or_body(
            request, login_request.client_id, session
        )
        
        access_token, refresh_token, user = await auth_service.login(
            login_request.email, login_request.password, client_id
        )
        return AuthMapper.to_token_response(access_token, refresh_token, user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    register_request: RegisterRequest,
    auth_service: AuthServiceInterface = Depends(get_auth_service),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Register new user (multi-tenant).
    
    Client ID can be provided via:
    - client_id in request body
    - X-Client-ID header
    - X-Client-Subdomain header
    - Subdomain in Host header
    
    Returns:
        Created user data
    """
    try:
        # Get client_id from request or body
        client_id = await get_client_id_from_request_or_body(
            request, register_request.client_id, session
        )
        
        user = await auth_service.register(
            register_request.username,
            register_request.email,
            register_request.password,
            register_request.name,
            client_id
        )
        return AuthMapper.to_user_response(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    refresh_request: RefreshTokenRequest,
    auth_service: AuthServiceInterface = Depends(get_auth_service),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Refresh access token using refresh token (multi-tenant).
    
    Returns:
        New TokenResponse with fresh tokens
    """
    try:
        # Get client_id from request (optional, will be validated from token)
        client_id = None
        try:
            from app.api.dicontainer.dicontainer import get_client_repository
            client_repository = get_client_repository(session=session)
            client_id = await get_client_from_request(request, client_repository)
        except Exception:
            pass
        
        # Get new tokens
        new_access_token, new_refresh_token = await auth_service.refresh_access_token(
            refresh_request.refresh_token, client_id
        )
        
        # Verify old refresh token to get user data
        payload = auth_service.verify_token(refresh_request.refresh_token)
        user_id = payload.get("user_id")
        token_client_id = payload.get("client_id")
        user = await auth_service.get_current_user(user_id, client_id=token_client_id)
        
        return AuthMapper.to_token_response(
            new_access_token, new_refresh_token, user
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    logout_request: RefreshTokenRequest,
    auth_service: AuthServiceInterface = Depends(get_auth_service),
    current_user: AppUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Logout user by invalidating refresh token (multi-tenant).
    
    Requires authentication.
    """
    # Get client_id from request
    client_id = None
    try:
        from app.api.dicontainer.dicontainer import get_client_repository
        client_repository = get_client_repository(session=session)
        client_id = await get_client_from_request(request, client_repository)
    except Exception:
        client_id = current_user.client_id
    
    await auth_service.logout(logout_request.refresh_token, client_id)
    return MessageResponse(message="Logged out successfully")


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: Request,
    change_password_request: ChangePasswordRequest,
    auth_service: AuthServiceInterface = Depends(get_auth_service),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Change current user's password (multi-tenant).
    
    Requires authentication.
    """
    try:
        await auth_service.change_password(
            current_user.id,
            change_password_request.old_password,
            change_password_request.new_password,
            current_user.client_id
        )
        return MessageResponse(message="Password changed successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: AppUser = Depends(get_current_user),
):
    """
    Get current authenticated user data.
    
    Requires authentication.
    """
    return AuthMapper.to_user_response(current_user)


# ========== Admin User Management Endpoints ==========

@router.get("/users", response_model=list[UserResponse])
async def list_users(
    request: Request,
    auth_service: AuthServiceInterface = Depends(get_auth_service),
    current_user: AppUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List all users for the current client (admin only, multi-tenant).
    
    Returns users only from the same client as the authenticated admin.
    Requires admin authentication.
    """
    # Multi-tenant: Only list users from current user's client
    users = await auth_service.list_all_users(client_id=current_user.client_id)
    return [AuthMapper.to_user_response(user) for user in users]


@router.get("/users/by-email", response_model=UserResponse)
async def get_user_by_email(
    request: Request,
    email: str,
    auth_service: AuthServiceInterface = Depends(get_auth_service),
    current_user: AppUser = Depends(get_current_admin_user),
):
    """
    Get user by email within current client (admin only, multi-tenant).
    
    Query parameter: email
    Requires admin authentication.
    """
    user = await auth_service.get_user_by_email(email, client_id=current_user.client_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return AuthMapper.to_user_response(user)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    request: Request,
    user_id: str,
    auth_service: AuthServiceInterface = Depends(get_auth_service),
    current_user: AppUser = Depends(get_current_admin_user),
):
    """
    Get user by ID within current client (admin only, multi-tenant).
    
    Requires admin authentication.
    """
    user = await auth_service.get_user_by_id(user_id, client_id=current_user.client_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return AuthMapper.to_user_response(user)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    request: Request,
    user_id: str,
    update_request: UpdateUserRequest,
    auth_service: AuthServiceInterface = Depends(get_auth_service),
    current_user: AppUser = Depends(get_current_admin_user),
):
    """
    Update user within current client (admin only, multi-tenant).
    
    Requires admin authentication.
    """
    user = await auth_service.get_user_by_id(user_id, client_id=current_user.client_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields if provided
    if update_request.username is not None:
        user.username = update_request.username
    if update_request.email is not None:
        user.email = update_request.email
    if update_request.name is not None:
        user.name = update_request.name
    if update_request.role is not None:
        try:
            user.role = UserRole(update_request.role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {update_request.role}"
            )
    if update_request.is_active is not None:
        user.active = update_request.is_active
    
    updated_user = await auth_service.admin_update_user(user)
    
    return AuthMapper.to_user_response(updated_user)


@router.patch("/users/{user_id}", response_model=UserResponse)
async def partial_update_user(
    request: Request,
    user_id: str,
    update_request: UpdateUserRequest,
    auth_service: AuthServiceInterface = Depends(get_auth_service),
    current_user: AppUser = Depends(get_current_admin_user),
):
    """
    Partial update user within current client (admin only, multi-tenant).
    
    Requires admin authentication.
    """
    user = await auth_service.get_user_by_id(user_id, client_id=current_user.client_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields if provided
    if update_request.username is not None:
        user.username = update_request.username
    if update_request.email is not None:
        user.email = update_request.email
    if update_request.name is not None:
        user.name = update_request.name
    if update_request.role is not None:
        try:
            user.role = UserRole(update_request.role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {update_request.role}"
            )
    if update_request.is_active is not None:
        user.active = update_request.is_active
    
    updated_user = await auth_service.admin_update_user(user)
    
    return AuthMapper.to_user_response(updated_user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    request: Request,
    user_id: str,
    auth_service: AuthServiceInterface = Depends(get_auth_service),
    current_user: AppUser = Depends(get_current_admin_user),
):
    """
    Delete user within current client (admin only, multi-tenant).
    
    Requires admin authentication.
    """
    try:
        success = await auth_service.admin_delete_user(
            user_id, current_user.id, client_id=current_user.client_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

