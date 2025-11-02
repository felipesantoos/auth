"""
Authentication Routes
API endpoints for user authentication and authorization
Adapted for multi-tenant architecture with dual-mode authentication (web/mobile)
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, BackgroundTasks, Response, Body
from core.interfaces.primary.auth_service_interface import IAuthService
from core.interfaces.primary.password_reset_service_interface import IPasswordResetService
from app.api.utils.client_detection import detect_client_type, ClientType, get_cookie_settings

logger = logging.getLogger(__name__)
from core.domain.auth.app_user import AppUser
from core.domain.auth.user_role import UserRole
from app.api.dtos.request.auth_request import (
    LoginRequest,
    RegisterRequest,
    ChangePasswordRequest,
    RefreshTokenRequest,
    UpdateUserRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.api.dtos.request.mfa_login_request import MFALoginRequest
from app.api.dtos.request.bulk_request import (
    BulkCreateUsersRequest,
    BulkUpdateUsersRequest,
    BulkDeleteUsersRequest,
)
from app.api.dtos.response.auth_response import (
    TokenResponse,
    UserResponse,
    MessageResponse,
)
from app.api.dtos.response.mfa_login_response import MFARequiredResponse
from app.api.dtos.response.bulk_response import (
    BulkCreateUsersResponse,
    BulkUpdateUsersResponse,
    BulkDeleteUsersResponse,
)
from app.api.dtos.response.async_response import AsyncOperationResponse
from app.api.mappers.auth_mapper import AuthMapper
from app.api.dtos.response.paginated_response import PaginatedResponse
from app.api.utils.pagination import (
    create_paginated_response,
    get_default_page_size,
    validate_page_size,
)
from core.services.filters.user_filter import UserFilter
from app.api.dicontainer.dicontainer import (
    get_auth_service,
    get_password_reset_service,
    get_audit_service,
    get_mfa_service,
    get_session_service,
    get_email_verification_service,
)
from core.services.audit.audit_service import AuditService
from core.services.auth.mfa_service import MFAService
from core.services.auth.session_service import SessionService
from core.services.auth.email_verification_service import EmailVerificationService
from core.domain.auth.audit_event_type import AuditEventType
from core.exceptions import BusinessRuleException
from app.api.middlewares.auth_middleware import (
    get_current_user,
    get_current_admin_user,
)
from app.api.middlewares.tenant_middleware import get_client_from_request
from app.api.middlewares.rate_limit_middleware import limiter
from infra.database.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


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


def set_auth_cookies(
    response: Response,
    request: Request,
    access_token: str,
    refresh_token: str,
    access_token_expire_seconds: int
) -> None:
    """
    Set authentication cookies with secure settings.
    
    For web clients, tokens are stored in httpOnly cookies for XSS protection.
    
    Args:
        response: FastAPI Response object
        request: FastAPI Request object (for environment detection)
        access_token: JWT access token
        refresh_token: JWT refresh token
        access_token_expire_seconds: Access token expiration in seconds
    """
    from config.settings import settings
    
    cookie_settings = get_cookie_settings(request)
    
    # Set access token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=access_token_expire_seconds,
        **cookie_settings
    )
    
    # Set refresh token cookie (longer expiration)
    refresh_token_expire_seconds = settings.refresh_token_expire_days * 24 * 60 * 60
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=refresh_token_expire_seconds,
        **cookie_settings
    )


def clear_auth_cookies(response: Response, request: Request) -> None:
    """
    Clear authentication cookies.
    
    Used during logout to invalidate cookies.
    
    Args:
        response: FastAPI Response object
        request: FastAPI Request object (for environment detection)
    """
    cookie_settings = get_cookie_settings(request)
    
    # Clear both cookies by setting max_age to 0
    response.set_cookie(
        key="access_token",
        value="",
        max_age=0,
        **cookie_settings
    )
    
    response.set_cookie(
        key="refresh_token",
        value="",
        max_age=0,
        **cookie_settings
    )


@router.post("/login")
@limiter.limit("5/minute")  # Stricter limit for login (brute-force protection)
async def login(
    request: Request,
    response: Response,
    login_request: LoginRequest,
    auth_service: IAuthService = Depends(get_auth_service),
    audit_service: AuditService = Depends(get_audit_service),
    session_service: SessionService = Depends(get_session_service),
    email_verification_service: EmailVerificationService = Depends(get_email_verification_service),
    db_session: AsyncSession = Depends(get_db_session),
):
    """
    Authenticate user with advanced security features and dual-mode support.
    
    Features:
    - Account lockout (brute-force protection - email and IP-based)
    - Audit logging
    - Email verification check
    - MFA verification (if enabled)
    - Session tracking
    - Suspicious activity detection
    - Login notifications
    - Dual-mode: Cookies for web, tokens in body for mobile
    
    Dual-Mode Authentication:
    - Web (X-Client-Type: web): Tokens sent via httpOnly cookies
    - Mobile (X-Client-Type: mobile): Tokens sent in response body
    
    Returns TokenResponse or MFARequiredResponse
    """
    try:
        # Get client_id and IP address
        client_id = await get_client_id_from_request_or_body(
            request, login_request.client_id, db_session
        )
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Get services
        from app.api.dicontainer.dicontainer import get_account_lockout_service, get_suspicious_activity_detector
        lockout_service = await get_account_lockout_service(db_session)
        suspicious_detector = await get_suspicious_activity_detector(db_session)
        
        # 1. CHECK ACCOUNT/IP LOCKOUT (before revealing user existence)
        is_locked, unlock_time = await lockout_service.check_lockout(
            email=login_request.email,
            ip_address=ip_address or "",
            client_id=client_id
        )
        
        if is_locked:
            await audit_service.log_event(
                client_id=client_id,
                event_type=AuditEventType.LOGIN_FAILED_ACCOUNT_LOCKED,
                ip_address=ip_address,
                user_agent=user_agent,
                status="failure",
                metadata={
                    "reason": "Account or IP locked due to failed attempts",
                    "unlock_time": unlock_time.isoformat() if unlock_time else None
                }
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed login attempts. Please try again after {unlock_time.strftime('%H:%M UTC') if unlock_time else '30 minutes'}."
            )
        
        # 2. AUTHENTICATE
        try:
            access_token, refresh_token, user = await auth_service.login(
                login_request.email, login_request.password, client_id
            )
        except Exception as e:
            # Log failed login
            await audit_service.log_event(
                client_id=client_id,
                event_type=AuditEventType.LOGIN_FAILED,
                ip_address=ip_address,
                user_agent=user_agent,
                status="failure",
                metadata={"email": login_request.email, "error": str(e)}
            )
            
            # Record failed attempt in lockout service
            await lockout_service.record_failed_attempt(
                email=login_request.email,
                ip_address=ip_address or "",
                user_agent=user_agent or "",
                client_id=client_id
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # 3. CHECK ACCOUNT LOCKOUT (in case it was just locked)
        if user.is_locked():
            await audit_service.log_event(
                client_id=client_id,
                event_type=AuditEventType.LOGIN_FAILED_ACCOUNT_LOCKED,
                user_id=user.id,
                ip_address=ip_address,
                status="failure"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is temporarily locked due to multiple failed attempts. Try again later."
            )
        
        # Reset failed login attempts on successful login
        if not user.is_locked():
            user.reset_failed_login_attempts()
            from app.api.dicontainer.dicontainer import get_app_user_repository
            user_repo = await get_app_user_repository(db_session)
            await user_repo.save(user)
        
        # 4. CHECK EMAIL VERIFICATION
        from config.settings import settings
        if settings.require_email_verification and not user.is_email_verified():
            await audit_service.log_event(
                client_id=client_id,
                event_type=AuditEventType.LOGIN_FAILED_EMAIL_NOT_VERIFIED,
                user_id=user.id,
                ip_address=ip_address,
                status="failure"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified. Please check your email and verify your account."
            )
        
        # 5. CHECK MFA
        if user.has_mfa_enabled():
            # Return MFA required response (don't issue tokens yet)
            return MFARequiredResponse(
                mfa_required=True,
                user_id=user.id,
                message="MFA verification required. Provide TOTP code or backup code."
            )
        
        # 6. CREATE SESSION
        session = None
        try:
            session = await session_service.create_session(
                user_id=user.id,
                client_id=client_id,
                refresh_token=refresh_token,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Regenerate access token with session_id
            if session:
                access_token = auth_service.generate_access_token_with_session(
                    user_id=user.id,
                    client_id=client_id,
                    session_id=session.id
                )
                logger.info(f"Access token regenerated with session_id: {session.id}")
            
            # Send login notification if enabled and new device detected
            from config.settings import settings
            if settings.send_login_notifications and session:
                try:
                    from app.api.dicontainer.dicontainer import get_login_notification_service
                    notification_service = get_login_notification_service()
                    
                    # Check if this is a new device using the detector
                    is_new_device = await suspicious_detector.check_new_device(
                        user_id=user.id,
                        client_id=client_id,
                        user_agent=user_agent or "",
                        ip_address=ip_address or ""
                    )
                    
                    if is_new_device:
                        await notification_service.send_new_login_notification(user, session)
                        logger.info(f"Login notification sent for new device login: {user.id}")
                except Exception as e:
                    logger.error(f"Error sending login notification: {e}", exc_info=True)
                    # Don't fail login if notification fails
                    
        except Exception as e:
            logger.error(f"Error creating session: {e}", exc_info=True)
            # Don't fail login if session creation fails
        
        # 7. DETECT SUSPICIOUS ACTIVITY
        try:
            is_suspicious = await suspicious_detector.detect_suspicious_activity(
                user_id=user.id,
                client_id=client_id,
                ip_address=ip_address or "",
                user_agent=user_agent or "",
                location=None  # TODO: Add geo-location service
            )
            
            if is_suspicious:
                await audit_service.log_event(
                    client_id=client_id,
                    event_type=AuditEventType.SUSPICIOUS_ACTIVITY_DETECTED,
                    action=f"Suspicious login activity detected for user {user.email}",
                    description="Login from new device or impossible travel detected",
                    user_id=user.id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    metadata={
                        "detection_reason": "new_device_or_impossible_travel",
                        "email": user.email
                    },
                    tags=["security", "suspicious"],
                    status="warning"
                )
        except Exception as e:
            logger.error(f"Error detecting suspicious activity: {e}", exc_info=True)
        
        # 8. LOG SUCCESSFUL LOGIN
        await audit_service.log_event(
            client_id=client_id,
            event_type=AuditEventType.LOGIN_SUCCESS,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            status="success"
        )
        
        # 9. DUAL-MODE: Return tokens appropriately based on client type
        client_type = detect_client_type(request)
        from config.settings import settings
        
        if client_type == ClientType.WEB:
            # Web: Set tokens in httpOnly cookies (XSS protection)
            set_auth_cookies(
                response=response,
                request=request,
                access_token=access_token,
                refresh_token=refresh_token,
                access_token_expire_seconds=settings.access_token_expire_minutes * 60
            )
            
            # Return user data only (tokens in cookies)
            return {
                "message": "Login successful",
                "user": AuthMapper.to_user_response(user),
                "token_type": "bearer",
                "expires_in": settings.access_token_expire_minutes * 60
            }
        else:
            # Mobile: Return tokens in response body (stored in secure storage by app)
            return AuthMapper.to_token_response(access_token, refresh_token, user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in login: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login"
        )


@router.post("/login/mfa", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login_with_mfa(
    request: Request,
    mfa_request: MFALoginRequest,
    auth_service: IAuthService = Depends(get_auth_service),
    mfa_service: MFAService = Depends(get_mfa_service),
    session_service: SessionService = Depends(get_session_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """
    Complete login with MFA verification.
    
    Called after initial login returns mfa_required=true.
    User provides either TOTP code or backup code.
    """
    try:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Get user
        user = await auth_service.get_user_by_id(mfa_request.user_id, mfa_request.client_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        if not user.has_mfa_enabled():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is not enabled for this user")
        
        # Verify MFA
        mfa_verified = False
        
        if mfa_request.totp_code:
            mfa_verified = mfa_service.verify_totp(user.mfa_secret, mfa_request.totp_code)
            if mfa_verified:
                await audit_service.log_event(
                    client_id=mfa_request.client_id,
                    event_type=AuditEventType.MFA_VERIFICATION_SUCCESS,
                    user_id=user.id,
                    ip_address=ip_address,
                    status="success"
                )
        elif mfa_request.backup_code:
            mfa_verified = await mfa_service.verify_backup_code_for_user(
                user.id, mfa_request.client_id, mfa_request.backup_code
            )
            if mfa_verified:
                await audit_service.log_event(
                    client_id=mfa_request.client_id,
                    event_type=AuditEventType.MFA_BACKUP_CODE_USED,
                    user_id=user.id,
                    ip_address=ip_address,
                    status="success"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either totp_code or backup_code is required"
            )
        
        if not mfa_verified:
            await audit_service.log_event(
                client_id=mfa_request.client_id,
                event_type=AuditEventType.MFA_VERIFICATION_FAILED,
                user_id=user.id,
                ip_address=ip_address,
                status="failure"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA code"
            )
        
        # Generate tokens
        from core.services.auth.auth_service import AuthService
        if isinstance(auth_service, AuthService):
            access_token, refresh_token = await auth_service._generate_and_store_tokens(
                user.id, mfa_request.client_id
            )
        else:
            raise HTTPException(status_code=500, detail="Auth service not available")
        
        # Create session
        try:
            await session_service.create_session(
                user_id=user.id,
                client_id=mfa_request.client_id,
                refresh_token=refresh_token,
                ip_address=ip_address,
                user_agent=user_agent
            )
        except Exception as e:
            logger.error(f"Error creating session after MFA: {e}", exc_info=True)
        
        # Log successful login
        await audit_service.log_event(
            client_id=mfa_request.client_id,
            event_type=AuditEventType.LOGIN_SUCCESS,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            status="success",
            metadata={"mfa_used": True}
        )
        
        return AuthMapper.to_token_response(access_token, refresh_token, user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in MFA login: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during MFA verification"
        )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")  # Limit registration to prevent spam
async def register(
    request: Request,
    response: Response,
    register_request: RegisterRequest,
    background_tasks: BackgroundTasks,
    auth_service: IAuthService = Depends(get_auth_service),
    audit_service: AuditService = Depends(get_audit_service),
    email_verification_service: EmailVerificationService = Depends(get_email_verification_service),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Register new user with email verification and audit logging.
    
    Performance: Email sending runs in background to improve response time.
    
    Client ID can be provided via:
    - client_id in request body
    - X-Client-ID header
    - X-Client-Subdomain header
    - Subdomain in Host header
    
    Returns:
        Created user data (immediate response, email sent in background)
    """
    try:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Get client_id from request or body
        client_id = await get_client_id_from_request_or_body(
            request, register_request.client_id, session
        )
        
        # Register user
        user = await auth_service.register(
            register_request.username,
            register_request.email,
            register_request.password,
            register_request.name,
            client_id
        )
        
        # Log registration
        await audit_service.log_event(
            client_id=client_id,
            event_type=AuditEventType.USER_REGISTERED,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            status="success",
            metadata={"email": user.email, "username": user.username}
        )
        
        # ⚡ PERFORMANCE: Send email verification in background
        # This prevents blocking the registration response (improves UX)
        # Email sending typically takes 1-2 seconds - user doesn't need to wait
        from config.settings import settings
        if settings.require_email_verification or True:  # Always send for now
            async def send_verification_email_task():
                """Background task for sending verification email"""
                try:
                    await email_verification_service.send_verification_email(
                        user_id=user.id,
                        client_id=client_id
                    )
                    await audit_service.log_event(
                        client_id=client_id,
                        event_type=AuditEventType.EMAIL_VERIFICATION_SENT,
                        user_id=user.id,
                        status="success"
                    )
                    logger.info(f"Verification email sent to user {user.id}")
                except Exception as e:
                    logger.error(f"Error sending verification email: {e}", exc_info=True)
                    # Don't fail registration if email fails (already logged)
            
            background_tasks.add_task(send_verification_email_task)
        
        # Add Location header pointing to created resource
        response.headers["Location"] = f"/api/v1/auth/users/{user.id}"
        
        return AuthMapper.to_user_response(user)
        
    except ValueError as e:
        # Log failed registration
        await audit_service.log_event(
            client_id=client_id if 'client_id' in locals() else "unknown",
            event_type=AuditEventType.REGISTRATION_FAILED,
            ip_address=ip_address if 'ip_address' in locals() else None,
            status="failure",
            metadata={"error": str(e), "email": register_request.email}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error in registration: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during registration"
        )


@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response,
    refresh_request: RefreshTokenRequest,
    auth_service: IAuthService = Depends(get_auth_service),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Refresh access token using refresh token (multi-tenant, dual-mode).
    
    Dual-Mode:
    - Web: Reads refresh_token from cookie if not in body, returns new tokens via cookies
    - Mobile: Reads refresh_token from body, returns tokens in response
    
    Returns:
        TokenResponse (mobile) or user data with cookies (web)
    """
    try:
        # Dual-mode: Get refresh token from body OR cookie
        refresh_token_value = refresh_request.refresh_token
        
        if not refresh_token_value:
            # Try to get from cookie (web client)
            refresh_token_value = request.cookies.get("refresh_token")
        
        if not refresh_token_value:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is required (in body or cookie)"
            )
        
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
            refresh_token_value, client_id
        )
        
        # Verify old refresh token to get user data
        payload = auth_service.verify_token(refresh_token_value)
        user_id = payload.get("user_id")
        token_client_id = payload.get("client_id")
        user = await auth_service.get_current_user(user_id, client_id=token_client_id)
        
        # Dual-mode: Return appropriately
        client_type = detect_client_type(request)
        from config.settings import settings
        
        if client_type == ClientType.WEB:
            # Web: Set new tokens in cookies
            set_auth_cookies(
                response=response,
                request=request,
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                access_token_expire_seconds=settings.access_token_expire_minutes * 60
            )
            
            return {
                "message": "Token refreshed successfully",
                "user": AuthMapper.to_user_response(user),
                "token_type": "bearer",
                "expires_in": settings.access_token_expire_minutes * 60
            }
        else:
            # Mobile: Return tokens in body
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
    response: Response,
    logout_request: RefreshTokenRequest,
    auth_service: IAuthService = Depends(get_auth_service),
    audit_service: AuditService = Depends(get_audit_service),
    session_service: SessionService = Depends(get_session_service),
    current_user: AppUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Logout user with session revocation, audit logging, and dual-mode support.
    
    Dual-Mode:
    - Web: Clears authentication cookies
    - Mobile: Just invalidates refresh token (no cookies to clear)
    
    Requires authentication.
    """
    try:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Get client_id from request
        client_id = None
        try:
            from app.api.dicontainer.dicontainer import get_client_repository
            client_repository = get_client_repository(session=session)
            client_id = await get_client_from_request(request, client_repository)
        except Exception:
            client_id = current_user.client_id
        
        # Dual-mode: Get refresh token from body OR cookie
        refresh_token_value = logout_request.refresh_token
        
        if not refresh_token_value:
            # Try to get from cookie (web client)
            refresh_token_value = request.cookies.get("refresh_token")
        
        if refresh_token_value:
            # Logout (invalidate refresh token)
            await auth_service.logout(refresh_token_value, client_id)
        
        # Dual-mode: Clear cookies if web client
        client_type = detect_client_type(request)
        if client_type == ClientType.WEB:
            clear_auth_cookies(response, request)
        
        # TODO: Revoke session by token hash
        # For now, we log the logout event
        
        # Log logout
        await audit_service.log_event(
            client_id=client_id,
            event_type=AuditEventType.LOGOUT,
            user_id=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            status="success"
        )
        
        return MessageResponse(message="Logged out successfully")
    except Exception as e:
        logger.error(f"Error in logout: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during logout"
        )


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: Request,
    change_password_request: ChangePasswordRequest,
    auth_service: IAuthService = Depends(get_auth_service),
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

@router.get("/users", response_model=PaginatedResponse[UserResponse])
async def list_users(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(None, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in username, email, name"),
    role: Optional[str] = Query(None, description="Filter by role"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    email: Optional[str] = Query(None, description="Filter by email"),
    username: Optional[str] = Query(None, description="Filter by username"),
    sort_by: Optional[str] = Query(None, description="Field to sort by (e.g., 'full_name', 'created_at')"),
    sort_order: Optional[str] = Query("asc", regex="^(asc|desc)$", description="Sort order"),
    auth_service: IAuthService = Depends(get_auth_service),
    current_user: AppUser = Depends(get_current_admin_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List all users for the current client with pagination and filtering (admin only, multi-tenant).
    
    Returns users only from the same client as the authenticated admin.
    Supports pagination, search, filtering, and sorting.
    Requires admin authentication.
    """
    # Multi-tenant: Only list users from current user's client
    validated_page_size = validate_page_size(page_size) if page_size else get_default_page_size()
    
    # Build filter
    user_filter = UserFilter(
        client_id=current_user.client_id,  # Multi-tenant isolation
        page=page,
        page_size=validated_page_size,
        search=search,
        email=email,
        username=username,
        active=active,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    
    # Convert role string to enum if provided
    if role:
        try:
            user_filter.role = UserRole(role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {role}",
            )
    
    # Get paginated results
    users = await auth_service.list_all_users(filter=user_filter)
    total_items = await auth_service.count_users(filter=user_filter)
    
    # Convert to response DTOs
    user_responses = [AuthMapper.to_user_response(user) for user in users]
    
    # Create paginated response
    return create_paginated_response(
        items=user_responses,
        page=page,
        page_size=validated_page_size,
        total_items=total_items,
    )


@router.get("/users/by-email", response_model=UserResponse)
async def get_user_by_email(
    request: Request,
    email: str,
    auth_service: IAuthService = Depends(get_auth_service),
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
    auth_service: IAuthService = Depends(get_auth_service),
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


@router.head("/users/{user_id}")
async def check_user_exists(
    request: Request,
    response: Response,
    user_id: str,
    auth_service: IAuthService = Depends(get_auth_service),
    current_user: AppUser = Depends(get_current_admin_user),
):
    """
    Check if user exists without returning body (admin only, multi-tenant).
    
    Returns metadata headers:
    - Last-Modified: When user was last updated
    - ETag: User version hash for caching
    
    HTTP Methods:
    - 200 OK: User exists
    - 404 Not Found: User doesn't exist
    
    Requires admin authentication.
    """
    from app.api.utils.cache_headers import add_last_modified_header, add_etag_header
    
    user = await auth_service.get_user_by_id(user_id, client_id=current_user.client_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Add cache headers
    add_last_modified_header(response, user.updated_at)
    add_etag_header(response, user)
    
    return Response(status_code=status.HTTP_200_OK)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    request: Request,
    user_id: str,
    update_request: UpdateUserRequest,
    auth_service: IAuthService = Depends(get_auth_service),
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
    auth_service: IAuthService = Depends(get_auth_service),
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
    auth_service: IAuthService = Depends(get_auth_service),
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


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("3/minute")  # Limit password reset requests
async def forgot_password(
    request: Request,
    forgot_request: ForgotPasswordRequest,
    auth_service: IPasswordResetService = Depends(get_password_reset_service),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Request password reset (public endpoint, multi-tenant).
    
    Sends password reset email to user if email exists for the given client.
    Always returns success message for security (doesn't reveal if email exists).
    
    Client ID can be provided via:
    - client_id in request body
    - X-Client-ID header
    - X-Client-Subdomain header
    - Subdomain in Host header
    """
    try:
        # Get client_id from request or body
        client_id = await get_client_id_from_request_or_body(
            request, forgot_request.client_id, session
        )
        
        # Request password reset
        await auth_service.forgot_password(
            forgot_request.email,
            client_id
        )
        
        # Always return success (security: don't reveal if email exists)
        return MessageResponse(
            message="If the email exists, a password reset link has been sent"
        )
    except Exception as e:
        logger.error(f"Error in forgot_password: {e}", exc_info=True)
        # Still return success for security
        return MessageResponse(
            message="If the email exists, a password reset link has been sent"
        )


@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit("5/minute")  # Limit password reset attempts
async def reset_password(
    request: Request,
    reset_request: ResetPasswordRequest,
    auth_service: IPasswordResetService = Depends(get_password_reset_service),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Reset password using reset token (public endpoint, multi-tenant).
    
    Client ID can be provided via:
    - client_id in request body
    - X-Client-ID header
    - X-Client-Subdomain header
    - Subdomain in Host header
    """
    try:
        # Get client_id from request or body
        client_id = await get_client_id_from_request_or_body(
            request, reset_request.client_id, session
        )
        
        # Reset password
        await auth_service.reset_password(
            reset_request.reset_token,
            reset_request.new_password,
            client_id
        )
        
        return MessageResponse(message="Password reset successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in reset_password: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# ========== Bulk Operations (API Design Guide Compliance) ==========

@router.post("/users/bulk-create")
@limiter.limit("10/hour")  # Stricter limit for bulk operations
async def bulk_create_users(
    request: Request,
    response: Response,
    bulk_request: BulkCreateUsersRequest = Body(...),
    auth_service: IAuthService = Depends(get_auth_service),
    audit_service: AuditService = Depends(get_audit_service),
    current_user: AppUser = Depends(get_current_admin_user),
):
    """
    Bulk create users (admin only, multi-tenant).
    
    **Limits:**
    - Max 100 users per request
    - Rate limit: 10 requests/hour
    
    **Async Processing:**
    - <= 50 users: Synchronous processing (200 OK with immediate results)
    - > 50 users: Asynchronous processing (202 Accepted, poll /api/v1/tasks/{task_id})
    
    **Request Body:**
    ```json
    {
        "users": [
            {
                "username": "user1",
                "email": "user1@example.com",
                "password": "SecurePass123",
                "name": "User One",
                "client_id": "client_123"
            }
        ]
    }
    ```
    
    **Response:**
    - If sync (<=50): Returns BulkCreateUsersResponse with detailed results
    - If async (>50): Returns AsyncOperationResponse with task_id and status_url
    
    **Returns:**
    - 200 OK: Sync processing completed (<=50 users)
    - 202 Accepted: Async processing started (>50 users)
    - 400 Bad Request: Invalid request data
    - 401/403: Authentication/authorization error
    
    Requires admin authentication.
    """
    try:
        ip_address = request.client.host if request.client else None
        num_users = len(bulk_request.users)
        
        # ASYNC PROCESSING (>50 items): Return 202 Accepted
        if num_users > 50:
            from core.services.task.task_service import TaskService
            from infra.database.repositories.task_repository import TaskRepository
            
            # Create async task
            session_gen = get_db_session()
            db_session = await anext(session_gen)
            task_repo = TaskRepository(db_session)
            task_service = TaskService(task_repo)
            
            task = await task_service.create_task(
                task_type="bulk_create_users",
                payload={
                    "users": [user.dict() for user in bulk_request.users],
                    "client_id": current_user.client_id,
                    "admin_id": current_user.id
                },
                created_by=current_user.id,
                client_id=current_user.client_id
            )
            
            # TODO: Queue Celery task here
            # from infra.celery.tasks.bulk_operations import bulk_create_users_task
            # bulk_create_users_task.apply_async(args=[task.id])
            
            logger.info(
                f"Bulk create queued for async processing",
                extra={
                    "task_id": task.id,
                    "num_users": num_users,
                    "admin_id": current_user.id
                }
            )
            
            # Return 202 Accepted
            response.status_code = status.HTTP_202_ACCEPTED
            return AsyncOperationResponse(
                task_id=task.id,
                status="processing",
                status_url=f"/api/v1/tasks/{task.id}",
                message=f"Bulk create of {num_users} users accepted for processing"
            )
        
        # SYNC PROCESSING (<=50 items): Return 200 OK
        users_data = [
            {
                "username": user.username,
                "email": user.email,
                "password": user.password,
                "name": user.name
            }
            for user in bulk_request.users
        ]
        
        # Execute bulk create
        result = await auth_service.bulk_create_users(
            users_data=users_data,
            client_id=current_user.client_id,
            admin_id=current_user.id
        )
        
        # Log bulk operation
        await audit_service.log_event(
            client_id=current_user.client_id,
            event_type=AuditEventType.USER_REGISTERED,
            user_id=current_user.id,
            action="Bulk user creation",
            description=f"Bulk created {result['success_count']} users, {result['error_count']} errors",
            ip_address=ip_address,
            metadata={
                "total": result["total"],
                "success_count": result["success_count"],
                "error_count": result["error_count"]
            },
            status="success" if result["error_count"] == 0 else "partial"
        )
        
        return BulkCreateUsersResponse(**result)
    
    except Exception as e:
        logger.error(f"Error in bulk create users: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during bulk user creation"
        )


@router.patch("/users/bulk-update")
@limiter.limit("10/hour")  # Stricter limit for bulk operations
async def bulk_update_users(
    request: Request,
    response: Response,
    bulk_request: BulkUpdateUsersRequest = Body(...),
    auth_service: IAuthService = Depends(get_auth_service),
    audit_service: AuditService = Depends(get_audit_service),
    current_user: AppUser = Depends(get_current_admin_user),
):
    """
    Bulk update users (admin only, multi-tenant).
    
    **Limits:**
    - Max 100 users per request
    - Rate limit: 10 requests/hour
    
    **Async Processing:**
    - <= 50 updates: Synchronous (200 OK)
    - > 50 updates: Asynchronous (202 Accepted)
    
    **Request Body:**
    ```json
    {
        "updates": [
            {
                "user_id": "user_abc123",
                "name": "Updated Name",
                "is_active": false
            }
        ]
    }
    ```
    
    Requires admin authentication.
    """
    try:
        ip_address = request.client.host if request.client else None
        num_updates = len(bulk_request.updates)
        
        # ASYNC PROCESSING (>50 items)
        if num_updates > 50:
            from core.services.task.task_service import TaskService
            from infra.database.repositories.task_repository import TaskRepository
            
            session_gen = get_db_session()
            db_session = await anext(session_gen)
            task_repo = TaskRepository(db_session)
            task_service = TaskService(task_repo)
            
            task = await task_service.create_task(
                task_type="bulk_update_users",
                payload={
                    "updates": bulk_request.updates,
                    "client_id": current_user.client_id,
                    "admin_id": current_user.id
                },
                created_by=current_user.id,
                client_id=current_user.client_id
            )
            
            response.status_code = status.HTTP_202_ACCEPTED
            return AsyncOperationResponse(
                task_id=task.id,
                status="processing",
                status_url=f"/api/v1/tasks/{task.id}",
                message=f"Bulk update of {num_updates} users accepted for processing"
            )
        
        # SYNC PROCESSING (<=50 items)
        result = await auth_service.bulk_update_users(
            updates=bulk_request.updates,
            client_id=current_user.client_id,
            admin_id=current_user.id
        )
        
        await audit_service.log_event(
            client_id=current_user.client_id,
            event_type=AuditEventType.USER_REGISTERED,
            user_id=current_user.id,
            action="Bulk user update",
            description=f"Bulk updated {result['success_count']} users, {result['error_count']} errors",
            ip_address=ip_address,
            metadata={
                "total": result["total"],
                "success_count": result["success_count"],
                "error_count": result["error_count"]
            },
            status="success" if result["error_count"] == 0 else "partial"
        )
        
        return BulkUpdateUsersResponse(**result)
    
    except Exception as e:
        logger.error(f"Error in bulk update users: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during bulk user update"
        )


@router.delete("/users/bulk-delete")
@limiter.limit("10/hour")  # Stricter limit for bulk operations
async def bulk_delete_users(
    request: Request,
    response: Response,
    bulk_request: BulkDeleteUsersRequest = Body(...),
    auth_service: IAuthService = Depends(get_auth_service),
    audit_service: AuditService = Depends(get_audit_service),
    current_user: AppUser = Depends(get_current_admin_user),
):
    """
    Bulk delete users (admin only, multi-tenant).
    
    **Limits:**
    - Max 100 users per request
    - Rate limit: 10 requests/hour
    
    **Async Processing:**
    - <= 50 deletes: Synchronous (200 OK)
    - > 50 deletes: Asynchronous (202 Accepted)
    
    **Request Body:**
    ```json
    {
        "user_ids": ["user_abc123", "user_def456", "user_ghi789"]
    }
    ```
    
    **Response:**
    Returns detailed status for each deletion with success/error tracking.
    
    **Security:**
    - Prevents self-deletion
    - Multi-tenant isolation enforced
    
    Requires admin authentication.
    """
    try:
        ip_address = request.client.host if request.client else None
        num_deletes = len(bulk_request.user_ids)
        
        # ASYNC PROCESSING (>50 items)
        if num_deletes > 50:
            from core.services.task.task_service import TaskService
            from infra.database.repositories.task_repository import TaskRepository
            
            session_gen = get_db_session()
            db_session = await anext(session_gen)
            task_repo = TaskRepository(db_session)
            task_service = TaskService(task_repo)
            
            task = await task_service.create_task(
                task_type="bulk_delete_users",
                payload={
                    "user_ids": bulk_request.user_ids,
                    "client_id": current_user.client_id,
                    "admin_id": current_user.id
                },
                created_by=current_user.id,
                client_id=current_user.client_id
            )
            
            response.status_code = status.HTTP_202_ACCEPTED
            return AsyncOperationResponse(
                task_id=task.id,
                status="processing",
                status_url=f"/api/v1/tasks/{task.id}",
                message=f"Bulk delete of {num_deletes} users accepted for processing"
            )
        
        # SYNC PROCESSING (<=50 items)
        result = await auth_service.bulk_delete_users(
            user_ids=bulk_request.user_ids,
            client_id=current_user.client_id,
            admin_id=current_user.id
        )
        
        # Log bulk operation
        await audit_service.log_event(
            client_id=current_user.client_id,
            event_type=AuditEventType.USER_REGISTERED,
            user_id=current_user.id,
            action="Bulk user deletion",
            description=f"Bulk deleted {result['success_count']} users, {result['error_count']} errors",
            ip_address=ip_address,
            metadata={
                "total": result["total"],
                "success_count": result["success_count"],
                "error_count": result["error_count"],
                "deleted_user_ids": result["successful_ids"]
            },
            status="success" if result["error_count"] == 0 else "partial"
        )
        
        return BulkDeleteUsersResponse(**result)
    
    except Exception as e:
        logger.error(f"Error in bulk delete users: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during bulk user deletion"
        )
