"""
API Versioning Middleware
Handles API versioning via headers
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)


class APIVersionMiddleware(BaseHTTPMiddleware):
    """
    API Versioning middleware supporting both URL and header-based versioning.
    
    Supports versioning via (in priority order):
    1. URL path (e.g., "/api/v1/...", "/api/v2/...")  - PREFERRED
    2. X-API-Version header (e.g., "1.0", "2.0")
    3. Accept header with version (e.g., "application/vnd.auth.v1+json")
    
    Default version: 1.0
    Supported versions: 1.0, 2.0
    
    URL-based versioning is preferred as it's more explicit and easier to cache.
    """
    
    SUPPORTED_VERSIONS = ["1.0", "2.0"]
    DEFAULT_VERSION = "1.0"
    
    async def dispatch(self, request: Request, call_next):
        """Process request and extract API version"""
        
        # Skip versioning for docs, health checks, metrics, and websockets
        skip_paths = ["/docs", "/redoc", "/openapi.json", "/health", "/metrics", "/ws"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)
        
        # Extract version from URL or headers
        api_version = self._extract_version(request)
        
        # Validate version
        if api_version not in self.SUPPORTED_VERSIONS:
            logger.warning(f"Unsupported API version requested: {api_version} from path: {request.url.path}")
            return Response(
                content=f'{{"error": "Unsupported API version: {api_version}", '
                        f'"supported_versions": {self.SUPPORTED_VERSIONS}, '
                        f'"message": "Use /api/v1/... or /api/v2/... in URL path"}}',
                status_code=status.HTTP_400_BAD_REQUEST,
                media_type="application/json"
            )
        
        # Add version to request state for use in route handlers
        request.state.api_version = api_version
        
        # Process request
        response = await call_next(request)
        
        # Add version header to response
        response.headers["X-API-Version"] = api_version
        
        return response
    
    def _extract_version(self, request: Request) -> str:
        """
        Extract API version from request URL or headers.
        
        Priority:
        1. URL path (/api/v1/..., /api/v2/...)
        2. X-API-Version header
        3. Accept header with version
        4. Default version
        """
        # Priority 1: Check URL path for version
        path = request.url.path
        if "/api/v1" in path:
            return "1.0"
        elif "/api/v2" in path:
            return "2.0"
        
        # Priority 2: Check X-API-Version header
        version = request.headers.get("X-API-Version")
        if version:
            return version
        
        # Priority 3: Check Accept header (e.g., "application/vnd.auth.v1+json")
        accept = request.headers.get("Accept", "")
        if "vnd.auth.v" in accept:
            try:
                # Extract version from "vnd.auth.v1+json" -> "1.0"
                version_part = accept.split("vnd.auth.v")[1].split("+")[0]
                return f"{version_part}.0"
            except:
                pass
        
        # Priority 4: Return default version
        return self.DEFAULT_VERSION


def get_api_version(request: Request) -> str:
    """
    Get API version from request state.
    
    Usage in route handlers:
        @router.get("/users")
        async def get_users(request: Request):
            version = get_api_version(request)
            if version == "2.0":
                # Return v2 response with pagination
                return {"users": [], "page": 1, "total": 0}
            else:
                # Return v1 response (legacy)
                return {"users": []}
    """
    return getattr(request.state, "api_version", APIVersionMiddleware.DEFAULT_VERSION)


def require_version(min_version: str):
    """
    Decorator to require minimum API version for a route.
    
    Usage:
        @router.get("/users")
        @require_version("2.0")
        async def get_users_v2(request: Request):
            # This endpoint only works with API version 2.0+
            return {"users": [], "page": 1}
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            current_version = get_api_version(request)
            
            if current_version < min_version:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"This endpoint requires API version {min_version} or higher. "
                           f"Current version: {current_version}"
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator

