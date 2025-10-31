"""
OAuth2 Social Login Routes
Google, GitHub, etc. (multi-tenant support)
"""
import logging
from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.responses import RedirectResponse
from config.oauth_config import oauth
from config.settings import settings
from core.interfaces.primary.oauth_service_interface import IOAuthService
from app.api.dicontainer.dicontainer import get_auth_service
from app.api.middlewares.tenant_middleware import get_client_from_request
from infra.database.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.mappers.auth_mapper import AuthMapper
from app.api.dtos.response.auth_response import TokenResponse

router = APIRouter(prefix="/api/auth/oauth", tags=["OAuth2"])
logger = logging.getLogger(__name__)


@router.get("/{provider}")
async def oauth_login(
    request: Request,
    provider: str,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Redirect to OAuth provider login (multi-tenant).
    
    Supports: google, github
    
    Client ID can be provided via:
    - X-Client-ID header
    - client_id query parameter
    - Subdomain in Host header
    """
    if provider not in ['google', 'github']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}"
        )
    
    # Get client_id from request (multi-tenant)
    # Try query parameter first, then header, then get_client_from_request
    client_id = request.query_params.get("client_id")
    if not client_id:
        try:
            from app.api.dicontainer.dicontainer import get_client_repository
            client_repository = get_client_repository(session=session)
            client_id = await get_client_from_request(request, client_repository)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Client ID is required. Provide via X-Client-ID header, client_id query param, or subdomain"
            )
    
    # Store client_id in session/state for callback
    # Use query parameter to pass client_id to callback
    redirect_uri = f"{settings.api_base_url}/api/auth/oauth/{provider}/callback?client_id={client_id}"
    
    try:
        provider_client = getattr(oauth, provider)
        return await provider_client.authorize_redirect(request, redirect_uri)
    except AttributeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth provider '{provider}' is not configured"
        )


@router.get("/{provider}/callback")
async def oauth_callback(
    request: Request,
    provider: str,
    session: AsyncSession = Depends(get_db_session),
    auth_service: IOAuthService = Depends(get_auth_service),
):
    """
    Handle OAuth provider callback (multi-tenant).
    
    Called by provider after user authorizes.
    Creates or updates user and returns tokens.
    """
    if provider not in ['google', 'github']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}"
        )
    
    # Get client_id from query parameter (stored during login redirect)
    client_id = request.query_params.get("client_id")
    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client ID is required in callback"
        )
    
    try:
        provider_client = getattr(oauth, provider)
        
        # Exchange code for token
        token = await provider_client.authorize_access_token(request)
        
        # Get user info from provider
        if provider == 'google':
            # Google OpenID Connect
            user_info = token.get('userinfo')
            if not user_info:
                user_info = await provider_client.userinfo(token=token)
            
            email = user_info.get('email')
            name = user_info.get('name', email.split('@')[0] if email else 'User')
            oauth_id = user_info.get('sub')
            
        elif provider == 'github':
            # GitHub OAuth2
            resp = await provider_client.get('user', token=token)
            user_info = resp.json()
            
            # Get email from GitHub (may require additional API call)
            email_resp = await provider_client.get('user/emails', token=token)
            emails = email_resp.json()
            primary_email = next((e['email'] for e in emails if e.get('primary')), None)
            
            if not primary_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No email associated with GitHub account"
                )
            
            email = primary_email
            name = user_info.get('name', user_info.get('login', 'User'))
            oauth_id = str(user_info.get('id'))
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not available from OAuth provider"
            )
        
        # Login or register user via OAuth
        access_token, refresh_token, user = await auth_service.oauth_login(
            provider=provider,
            email=email,
            name=name,
            oauth_id=oauth_id,
            client_id=client_id
        )
        
        # Redirect to frontend with tokens in query params
        # Frontend will handle token storage and redirect
        frontend_url = settings.cors_origins_list[0] if settings.cors_origins_list else "http://localhost:5173"
        redirect_url = (
            f"{frontend_url}/auth/oauth/callback"
            f"?access_token={access_token}"
            f"&refresh_token={refresh_token}"
            f"&token_type=bearer"
        )
        
        logger.info("OAuth login successful", extra={"provider": provider, "user_id": user.id, "client_id": client_id})
        return RedirectResponse(url=redirect_url)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth {provider} error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth authentication failed: {str(e)}"
        )

