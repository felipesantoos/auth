"""
API Deprecation Utilities
Decorators and tools for managing deprecated endpoints
"""
from functools import wraps
from typing import Optional
from fastapi import Response, Request
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def deprecated_endpoint(
    deprecation_date: str,
    sunset_date: str,
    alternative: str,
    message: Optional[str] = None
):
    """
    Decorator to mark endpoints as deprecated.
    
    Adds deprecation headers to responses following RFC 8594 (Sunset header).
    
    Args:
        deprecation_date: ISO 8601 date when endpoint was deprecated (e.g., "2024-01-01")
        sunset_date: ISO 8601 date when endpoint will be removed (e.g., "2024-06-01")
        alternative: URL path or description of alternative endpoint
        message: Optional custom deprecation message
    
    Headers added to response:
        - Deprecation: RFC 8594 deprecation header
        - Sunset: RFC 8594 sunset header (removal date)
        - Link: Link to alternative endpoint
        - X-API-Warn: Warning message for developers
    
    Example:
        >>> @router.get("/old-endpoint")
        >>> @deprecated_endpoint(
        ...     deprecation_date="2024-01-01",
        ...     sunset_date="2024-06-01",
        ...     alternative="/api/v2/new-endpoint",
        ...     message="Use the new endpoint for better performance"
        ... )
        >>> async def old_endpoint():
        ...     return {"data": "old format"}
    
    References:
        - RFC 8594: https://www.rfc-editor.org/rfc/rfc8594.html
        - Deprecation header draft: https://tools.ietf.org/id/draft-dalal-deprecation-header-01.html
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find Response object in kwargs
            response = kwargs.get('response')
            if response is None:
                # Try to find in args
                for arg in args:
                    if isinstance(arg, Response):
                        response = arg
                        break
            
            # If no Response object, call function normally
            if response is None:
                logger.warning(
                    f"Deprecated endpoint {func.__name__} called but no Response object found"
                )
                return await func(*args, **kwargs)
            
            # Add deprecation headers
            response.headers["Deprecation"] = deprecation_date
            response.headers["Sunset"] = sunset_date
            response.headers["Link"] = f'<{alternative}>; rel="alternate"'
            
            # Create warning message
            default_message = (
                f"This endpoint is deprecated as of {deprecation_date} and will be "
                f"removed on {sunset_date}. Use {alternative} instead."
            )
            warn_message = message or default_message
            response.headers["X-API-Warn"] = warn_message
            
            # Log deprecation warning
            request = kwargs.get('request')
            if request:
                logger.warning(
                    f"Deprecated endpoint accessed: {request.url.path} "
                    f"(will be removed on {sunset_date})"
                )
            
            return await func(*args, **kwargs)
        
        # Update function docstring
        deprecation_notice = f"""
        
        **⚠️ DEPRECATED**
        
        - **Deprecated**: {deprecation_date}
        - **Removal Date**: {sunset_date}
        - **Alternative**: `{alternative}`
        
        {message or 'Please migrate to the new endpoint.'}
        """
        
        if func.__doc__:
            func.__doc__ = func.__doc__ + deprecation_notice
        else:
            func.__doc__ = deprecation_notice
        
        return wrapper
    return decorator


def deprecation_middleware(deprecation_date: str, sunset_date: str):
    """
    Middleware to add deprecation headers to all responses.
    
    Use this for deprecating an entire API version.
    
    Example:
        >>> # In main.py
        >>> @app.middleware("http")
        >>> async def add_v1_deprecation(request: Request, call_next):
        ...     if request.url.path.startswith("/api/v1"):
        ...         response = await call_next(request)
        ...         response.headers["Deprecation"] = "2024-01-01"
        ...         response.headers["Sunset"] = "2024-12-31"
        ...         response.headers["X-API-Warn"] = "API v1 is deprecated. Migrate to v2."
        ...         return response
        ...     return await call_next(request)
    """
    async def middleware(request: Request, call_next):
        response = await call_next(request)
        response.headers["Deprecation"] = deprecation_date
        response.headers["Sunset"] = sunset_date
        return response
    
    return middleware

