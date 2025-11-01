"""
SSO Routes (SAML, OIDC, LDAP)
Endpoints for enterprise Single Sign-On
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Annotated, Optional
import logging

from app.api.dicontainer.dicontainer import (
    get_saml_service,
    get_oidc_service,
    get_ldap_service,
    get_auth_service,
    get_audit_service
)
from core.services.auth.saml_service import SAMLService
from core.services.auth.oidc_service import OIDCService
from core.services.auth.ldap_service import LDAPService
from core.interfaces.primary.auth_service_interface import IAuthService
from core.services.audit.audit_service import AuditService
from core.domain.auth.audit_event_type import AuditEventType
from core.exceptions import BusinessRuleException, InvalidCredentialsException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth/sso", tags=["SSO"])


# ========== SAML Routes ==========

@router.get("/saml/login")
async def saml_login(
    saml_service: Annotated[SAMLService, Depends(get_saml_service)],
    client_id: str = Query(..., description="Client ID"),
    return_url: Optional[str] = Query(None, description="Return URL")
):
    """
    Initiate SAML login (redirect to IdP).
    
    Redirects user to enterprise identity provider for authentication.
    """
    try:
        # Encode client_id and return_url in relay state
        import json
        import base64
        relay_state_data = {
            "client_id": client_id,
            "return_url": return_url
        }
        relay_state = base64.b64encode(json.dumps(relay_state_data).encode()).decode()
        
        login_url = saml_service.get_login_url(client_id=client_id, relay_state=relay_state)
        return RedirectResponse(url=login_url)
    except BusinessRuleException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        logger.error(f"Error initiating SAML login: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to initiate SAML login")


@router.post("/saml/acs")
async def saml_acs(
    saml_service: Annotated[SAMLService, Depends(get_saml_service)],
    auth_service: Annotated[IAuthService, Depends(get_auth_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    request: Request = None,
    SAMLResponse: str = Form(...),
    RelayState: Optional[str] = Form(None)
):
    """
    SAML Assertion Consumer Service (ACS).
    
    Receives SAML response from IdP after user authenticates.
    """
    try:
        ip_address = request.client.host if request.client else None
        
        # Extract client_id from relay state
        import json
        import base64
        client_id = "default"
        return_url = None
        
        if RelayState:
            try:
                relay_state_data = json.loads(base64.b64decode(RelayState).decode())
                client_id = relay_state_data.get("client_id", "default")
                return_url = relay_state_data.get("return_url")
            except Exception as e:
                logger.warning(f"Failed to decode relay state: {e}")
        
        # Process SAML response
        user = await saml_service.process_saml_response(
            saml_response=SAMLResponse,
            client_id=client_id
        )
        
        # Generate tokens
        from core.services.auth.auth_service import AuthService
        if isinstance(auth_service, AuthService):
            access_token, refresh_token = await auth_service._generate_and_store_tokens(
                user.id, user.client_id
            )
        else:
            raise HTTPException(status_code=500, detail="Auth service not available")
        
        # Log SAML login
        await audit_service.log_event(
            client_id=user.client_id,
            event_type=AuditEventType.SAML_LOGIN_SUCCESS,
            user_id=user.id,
            ip_address=ip_address,
            status="success"
        )
        
        # Redirect to frontend with tokens
        frontend_url = return_url or f"{auth_service.settings.frontend_url}/login/success"
        return RedirectResponse(url=f"{frontend_url}?access_token={access_token}&refresh_token={refresh_token}")
        
    except BusinessRuleException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        logger.error(f"Error processing SAML response: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process SAML response")


@router.get("/saml/metadata", response_class=HTMLResponse)
async def saml_metadata(
    saml_service: Annotated[SAMLService, Depends(get_saml_service)]
):
    """
    Get SAML SP metadata XML.
    
    Provide this to your identity provider for configuration.
    """
    try:
        metadata_xml = saml_service.get_metadata()
        return HTMLResponse(content=metadata_xml, media_type="application/xml")
    except BusinessRuleException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        logger.error(f"Error getting SAML metadata: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get SAML metadata")


# ========== OIDC Routes ==========

@router.get("/oidc/login")
async def oidc_login(
    oidc_service: Annotated[OIDCService, Depends(get_oidc_service)],
    client_id: str = Query(..., description="Client ID")
):
    """
    Initiate OIDC login (redirect to provider).
    
    Compatible with Google, Microsoft, Okta, Auth0, etc.
    """
    try:
        authorization_url = await oidc_service.get_authorization_url(client_id=client_id)
        return RedirectResponse(url=authorization_url)
    except BusinessRuleException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        logger.error(f"Error initiating OIDC login: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to initiate OIDC login")


@router.get("/oidc/callback")
async def oidc_callback(
    oidc_service: Annotated[OIDCService, Depends(get_oidc_service)],
    auth_service: Annotated[IAuthService, Depends(get_auth_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    code: str = Query(..., description="Authorization code"),
    state: str = Query(..., description="State parameter")
):
    """
    OIDC callback (exchange code for tokens).
    
    Called by identity provider after user authenticates.
    """
    try:
        # Extract client_id from state
        import json
        import base64
        client_id = "default"
        
        try:
            state_data = json.loads(base64.b64decode(state).decode())
            client_id = state_data.get("client_id", "default")
        except Exception as e:
            logger.warning(f"Failed to decode OIDC state: {e}")
        
        # Handle OIDC callback
        user = await oidc_service.handle_callback(
            code=code,
            state=state,
            client_id=client_id
        )
        
        # Generate tokens
        from core.services.auth.auth_service import AuthService
        if isinstance(auth_service, AuthService):
            access_token, refresh_token = await auth_service._generate_and_store_tokens(
                user.id, user.client_id
            )
        else:
            raise HTTPException(status_code=500, detail="Auth service not available")
        
        # Log OIDC login
        await audit_service.log_event(
            client_id=user.client_id,
            event_type=AuditEventType.OIDC_LOGIN_SUCCESS,
            user_id=user.id,
            status="success"
        )
        
        # Redirect to frontend with tokens
        from config.settings import settings
        frontend_url = f"{settings.frontend_url}/login/success"
        return RedirectResponse(url=f"{frontend_url}?access_token={access_token}&refresh_token={refresh_token}")
        
    except BusinessRuleException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        logger.error(f"Error handling OIDC callback: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to handle OIDC callback")


# ========== LDAP Routes ==========

@router.post("/ldap/login")
async def ldap_login(
    ldap_service: Annotated[LDAPService, Depends(get_ldap_service)],
    auth_service: Annotated[IAuthService, Depends(get_auth_service)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
    username: str = Form(...),
    password: str = Form(...),
    client_id: str = Form(...),
    request: Request = None
):
    """
    Authenticate via LDAP/Active Directory.
    
    Uses corporate credentials instead of local database.
    Auto-provisions users on first login.
    """
    try:
        ip_address = request.client.host if request and request.client else None
        
        # Authenticate via LDAP
        user = await ldap_service.authenticate_ldap(
            username=username,
            password=password,
            client_id=client_id
        )
        
        # Generate tokens
        from core.services.auth.auth_service import AuthService
        if isinstance(auth_service, AuthService):
            access_token, refresh_token = await auth_service._generate_and_store_tokens(
                user.id, client_id
            )
        else:
            raise HTTPException(status_code=500, detail="Auth service not available")
        
        # Log LDAP login
        await audit_service.log_event(
            client_id=client_id,
            event_type=AuditEventType.LDAP_LOGIN_SUCCESS,
            user_id=user.id,
            ip_address=ip_address,
            status="success",
            metadata={"username": username}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role.value
            }
        }
        
    except InvalidCredentialsException:
        # Log failed LDAP login
        await audit_service.log_event(
            client_id=client_id,
            event_type=AuditEventType.LDAP_LOGIN_FAILED,
            ip_address=ip_address if 'ip_address' in locals() else None,
            status="failure",
            metadata={"username": username}
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid LDAP credentials")
    except BusinessRuleException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        logger.error(f"Error in LDAP login: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to authenticate via LDAP")

