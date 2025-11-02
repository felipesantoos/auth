"""
Automatic Audit Middleware
Captures all HTTP requests automatically for comprehensive audit trail
"""
import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.responses import Response
import logging

from core.services.audit.audit_service import AuditService
from core.domain.auth.audit_event_type import AuditEventType

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically audit all HTTP requests.
    
    Captures:
    - User who made request (from request.state.user)
    - Endpoint accessed (method + path)
    - Resource type/ID (extracted from path)
    - Request context (IP, user agent, etc.)
    - Duration (response time)
    - Success/failure (status code)
    
    This provides automatic baseline auditing for all endpoints.
    Services can add more detailed auditing using AuditService directly.
    """
    
    def __init__(self, app: ASGIApp, audit_service: AuditService):
        super().__init__(app)
        self.audit_service = audit_service
    
    async def dispatch(self, request: Request, call_next):
        """Process request and audit it"""
        # Skip auditing for certain paths
        if self._should_skip_audit(request.url.path):
            return await call_next(request)
        
        # Generate request ID (for correlation)
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Extract user info (if authenticated)
        user_id = None
        username = None
        user_email = None
        client_id = None
        session_id = None
        
        if hasattr(request.state, "user"):
            user = request.state.user
            user_id = getattr(user, "id", None)
            username = getattr(user, "username", None)
            user_email = getattr(user, "email", None)
            client_id = getattr(user, "client_id", None)
        
        if hasattr(request.state, "session_id"):
            session_id = request.state.session_id
        
        # Start timer
        start_time = time.time()
        
        # Determine event type based on HTTP method
        method_to_event = {
            "POST": AuditEventType.ENTITY_CREATED,
            "PUT": AuditEventType.ENTITY_UPDATED,
            "PATCH": AuditEventType.ENTITY_UPDATED,
            "DELETE": AuditEventType.ENTITY_DELETED,
            "GET": AuditEventType.ENTITY_VIEWED
        }
        
        event_type = method_to_event.get(request.method, AuditEventType.ENTITY_VIEWED)
        
        # Extract resource info from path
        resource_type, resource_id = self._extract_resource_from_path(request.url.path)
        
        try:
            # Process request
            response: Response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Only audit if we have a client_id (authenticated requests)
            # Or if it's a security-relevant endpoint (login, register, etc.)
            if client_id or self._is_security_endpoint(request.url.path):
                # Use default client if not authenticated
                if not client_id:
                    client_id = "system"
                
                # Log successful request
                try:
                    await self.audit_service.log_event(
                        client_id=client_id,
                        event_type=event_type,
                        action=f"{request.method} {request.url.path}",
                        user_id=user_id,
                        username=username,
                        user_email=user_email,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        ip_address=self._get_client_ip(request),
                        user_agent=request.headers.get("user-agent"),
                        request_id=request_id,
                        session_id=session_id,
                        metadata={
                            "method": request.method,
                            "path": request.url.path,
                            "query_params": str(request.query_params),
                            "status_code": response.status_code,
                            "duration_ms": round(duration_ms, 2)
                        },
                        success=200 <= response.status_code < 400,
                        status="success" if 200 <= response.status_code < 400 else "failure"
                    )
                except Exception as audit_error:
                    # Don't fail the request if audit logging fails
                    logger.error(f"Audit middleware error: {audit_error}", exc_info=True)
            
            return response
            
        except Exception as e:
            # Log failed request
            duration_ms = (time.time() - start_time) * 1000
            
            if client_id or self._is_security_endpoint(request.url.path):
                if not client_id:
                    client_id = "system"
                
                try:
                    await self.audit_service.log_event(
                        client_id=client_id,
                        event_type=event_type,
                        action=f"{request.method} {request.url.path}",
                        user_id=user_id,
                        username=username,
                        user_email=user_email,
                        resource_type=resource_type,
                        resource_id=resource_id,
                        ip_address=self._get_client_ip(request),
                        user_agent=request.headers.get("user-agent"),
                        request_id=request_id,
                        session_id=session_id,
                        metadata={
                            "method": request.method,
                            "path": request.url.path,
                            "duration_ms": round(duration_ms, 2)
                        },
                        success=False,
                        status="failure",
                        error_message=str(e)
                    )
                except Exception as audit_error:
                    logger.error(f"Audit middleware error: {audit_error}", exc_info=True)
            
            raise
    
    def _extract_resource_from_path(self, path: str) -> tuple:
        """
        Extract resource type and ID from URL path.
        
        Examples:
            /api/projects/123 → ("project", "123")
            /api/users/456/documents/789 → ("document", "789")
            /api/auth/login → ("auth", None)
        
        Args:
            path: URL path
            
        Returns:
            Tuple of (resource_type, resource_id)
        """
        parts = path.strip("/").split("/")
        
        # Remove 'api' prefix
        if parts and parts[0] == "api":
            parts = parts[1:]
        
        if not parts:
            return None, None
        
        # First part is usually the resource type (plural)
        resource_type = parts[0].rstrip("s") if len(parts) > 0 else None
        
        # Second part is usually the ID (if it exists and looks like an ID)
        resource_id = None
        if len(parts) >= 2 and parts[1]:
            # Check if it looks like an ID (not a sub-resource name)
            if not parts[1] in ["login", "logout", "register", "me", "list", "search"]:
                resource_id = parts[1]
        
        # Handle nested resources (e.g., /users/123/documents/456)
        # Last pair takes precedence
        if len(parts) >= 4:
            resource_type = parts[2].rstrip("s")
            if parts[3]:
                resource_id = parts[3]
        
        return resource_type, resource_id
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address (handles proxies).
        
        Checks headers in order:
        1. X-Forwarded-For (from reverse proxy)
        2. X-Real-IP (from nginx)
        3. Direct client IP
        
        Args:
            request: FastAPI request
            
        Returns:
            Client IP address
        """
        # Check for X-Forwarded-For header (reverse proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take first IP in chain (original client)
            return forwarded.split(",")[0].strip()
        
        # Check for X-Real-IP header (nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct client
        return request.client.host if request.client else "unknown"
    
    def _should_skip_audit(self, path: str) -> bool:
        """
        Check if path should skip audit logging.
        
        Skips:
        - Health checks (/health, /health/*)
        - Metrics endpoint (/metrics)
        - API documentation (/docs, /redoc, /openapi.json)
        - Static files (/favicon.ico, /static/*)
        
        Args:
            path: URL path
            
        Returns:
            True if should skip audit, False otherwise
        """
        skip_prefixes = [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
            "/static/",
        ]
        
        return any(path.startswith(prefix) for prefix in skip_prefixes)
    
    def _is_security_endpoint(self, path: str) -> bool:
        """
        Check if this is a security-relevant endpoint that should always be audited.
        
        Even unauthenticated requests to these endpoints are logged.
        
        Args:
            path: URL path
            
        Returns:
            True if security endpoint
        """
        security_paths = [
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/logout",
            "/api/auth/password/reset",
            "/api/auth/password/change",
            "/api/auth/mfa/",
            "/api/auth/oauth/",
            "/api/auth/sso/",
        ]
        
        return any(path.startswith(sec_path) for sec_path in security_paths)

