"""
HTTPS Redirect Middleware
Forces HTTPS in production environment
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware to force HTTPS connections in production.
    
    In production, redirects all HTTP requests to HTTPS.
    In development, allows HTTP for local testing.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Only enforce HTTPS in production
        if settings.environment == "production":
            if request.url.scheme != "https":
                # Redirect to HTTPS
                https_url = request.url.replace(scheme="https")
                logger.warning(
                    f"HTTP request redirected to HTTPS: {request.url} -> {https_url}"
                )
                return RedirectResponse(url=str(https_url), status_code=301)
        
        response = await call_next(request)
        
        # Add security headers
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

