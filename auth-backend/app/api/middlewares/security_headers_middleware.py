"""
Security Headers Middleware
Adds security headers to all HTTP responses
Implements OWASP security best practices
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    
    Headers added:
    - X-Content-Type-Options: nosniff (prevents MIME sniffing)
    - X-Frame-Options: DENY (prevents clickjacking)
    - X-XSS-Protection: 1; mode=block (enables XSS filter)
    - Content-Security-Policy: Restricts resource loading
    - Strict-Transport-Security: Forces HTTPS (production only)
    
    Compliance: OWASP Top 10 - Security Misconfiguration
    Reference: 18-security-best-practices.md lines 303-312
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # X-Content-Type-Options: Prevents MIME-type sniffing
        # Browsers must respect the Content-Type header
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-Frame-Options: Prevents clickjacking attacks
        # Page cannot be displayed in iframe/frame/embed/object
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-XSS-Protection: Enables browser's XSS filter
        # mode=block stops page rendering if XSS detected
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Content-Security-Policy: Restricts resource loading
        # default-src 'self': Only load resources from same origin
        # upgrade-insecure-requests: Upgrade HTTP to HTTPS
        csp_directives = [
            "default-src 'self'",
            "script-src 'self'",
            "style-src 'self' 'unsafe-inline'",  # unsafe-inline needed for some CSS
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'none'",  # Same as X-Frame-Options
            "base-uri 'self'",
            "form-action 'self'",
        ]
        
        # Add upgrade-insecure-requests in production
        if settings.environment == "production":
            csp_directives.append("upgrade-insecure-requests")
        
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # Strict-Transport-Security: Force HTTPS (production only)
        # max-age=31536000: 1 year
        # includeSubDomains: Apply to all subdomains
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        
        # Referrer-Policy: Control referrer information
        # strict-origin-when-cross-origin: Send full URL for same-origin, only origin for cross-origin
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions-Policy: Control browser features
        # Disable potentially dangerous features
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=(), usb=()"
        )
        
        return response

