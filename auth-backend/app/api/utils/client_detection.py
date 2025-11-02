"""
Client Detection Utility
Detects whether the request comes from web browser or mobile app
Used for dual-mode authentication (cookies vs tokens)
"""
from enum import Enum
from fastapi import Request
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ClientType(str, Enum):
    """Client type enumeration"""
    WEB = "web"
    MOBILE = "mobile"
    UNKNOWN = "unknown"


def detect_client_type(request: Request) -> ClientType:
    """
    Detect client type from request headers.
    
    Priority:
    1. X-Client-Type header (explicit declaration by client)
    2. User-Agent analysis (fallback detection)
    
    Args:
        request: FastAPI Request object
        
    Returns:
        ClientType enum (WEB, MOBILE, or UNKNOWN)
        
    Examples:
        # Mobile app explicitly declares itself
        headers = {"X-Client-Type": "mobile"}
        → ClientType.MOBILE
        
        # Web browser explicitly declares itself
        headers = {"X-Client-Type": "web"}
        → ClientType.WEB
        
        # Fallback: analyze user-agent
        headers = {"User-Agent": "Mozilla/5.0 (iPhone...)"}
        → ClientType.MOBILE
    """
    # Priority 1: Check explicit X-Client-Type header
    client_type_header = request.headers.get("X-Client-Type", "").lower()
    
    if client_type_header == "web":
        return ClientType.WEB
    elif client_type_header == "mobile":
        return ClientType.MOBILE
    
    # Priority 2: Analyze User-Agent (fallback)
    user_agent = request.headers.get("User-Agent", "").lower()
    
    # Mobile app indicators
    mobile_indicators = [
        "okhttp",  # Android (Kotlin/Java)
        "alamofire",  # iOS (Swift)
        "cfnetwork",  # iOS native
        "dart",  # Flutter
        "react-native",  # React Native
        "expo",  # Expo (React Native framework)
    ]
    
    for indicator in mobile_indicators:
        if indicator in user_agent:
            logger.debug(f"Detected mobile client via User-Agent: {indicator}")
            return ClientType.MOBILE
    
    # Web browser indicators
    browser_indicators = [
        "mozilla",
        "chrome",
        "safari",
        "firefox",
        "edge",
        "opera",
    ]
    
    for indicator in browser_indicators:
        if indicator in user_agent:
            logger.debug(f"Detected web client via User-Agent: {indicator}")
            return ClientType.WEB
    
    # Default: treat as web for backward compatibility
    # Most traditional web browsers will have one of the above indicators
    logger.warning(f"Could not detect client type, defaulting to WEB. User-Agent: {user_agent[:100]}")
    return ClientType.WEB


def is_web_client(request: Request) -> bool:
    """Check if request comes from web browser"""
    return detect_client_type(request) == ClientType.WEB


def is_mobile_client(request: Request) -> bool:
    """Check if request comes from mobile app"""
    return detect_client_type(request) == ClientType.MOBILE


def get_cookie_settings(request: Request) -> dict:
    """
    Get appropriate cookie settings based on environment and client type.
    
    Returns dictionary with cookie configuration:
    - httponly: Always True for security
    - secure: True in production (HTTPS only)
    - samesite: "strict" for web, "none" for cross-origin mobile
    - domain: From settings (production only)
    - path: "/"
    - max_age: Token expiration time
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Dictionary with cookie settings
    """
    from config.settings import settings
    
    client_type = detect_client_type(request)
    
    cookie_settings = {
        "httponly": True,  # Prevent JavaScript access (XSS protection)
        "secure": settings.environment == "production",  # HTTPS only in production
        "path": "/",
    }
    
    # SameSite policy
    if client_type == ClientType.WEB:
        # Web: Use strict for best security
        cookie_settings["samesite"] = "strict"
    else:
        # Mobile: May need lax or none for cross-origin requests
        # Mobile apps typically use tokens, but if cookies are needed:
        cookie_settings["samesite"] = "lax"
    
    # Domain (production only, for subdomain support)
    if settings.environment == "production" and hasattr(settings, "cookie_domain"):
        cookie_settings["domain"] = settings.cookie_domain
    
    return cookie_settings

