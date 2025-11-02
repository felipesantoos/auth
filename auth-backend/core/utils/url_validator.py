"""
URL Validation Utility
Prevents SSRF (Server-Side Request Forgery) attacks
Reference: 18-security-best-practices.md lines 479-523
"""
import ipaddress
import logging
from urllib.parse import urlparse
from typing import List, Optional

logger = logging.getLogger(__name__)


# Default allowed domains (override in settings)
DEFAULT_ALLOWED_DOMAINS = [
    "api.github.com",
    "api.stripe.com",
    "api.sendgrid.com",
    "api.mailgun.net",
]


class SSRFProtectionError(Exception):
    """Raised when URL fails SSRF validation"""
    pass


def is_private_ip(hostname: str) -> bool:
    """
    Check if hostname is a private IP address.
    
    Blocks:
    - 127.0.0.0/8 (localhost)
    - 10.0.0.0/8 (private)
    - 172.16.0.0/12 (private)
    - 192.168.0.0/16 (private)
    - 169.254.0.0/16 (link-local, AWS metadata!)
    - ::1 (IPv6 localhost)
    - fc00::/7 (IPv6 private)
    
    Args:
        hostname: Hostname or IP address
        
    Returns:
        True if private IP, False otherwise
    """
    try:
        ip = ipaddress.ip_address(hostname)
        
        # Check if private, loopback, or link-local
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return True
        
        # Additional check for AWS metadata endpoint
        if hostname == "169.254.169.254":
            return True
        
        return False
        
    except ValueError:
        # Not an IP address, it's a hostname
        return False


def is_safe_url(
    url: str, 
    allowed_domains: Optional[List[str]] = None,
    allow_http: bool = False
) -> bool:
    """
    Validate URL to prevent SSRF attacks.
    
    Security checks:
    1. Scheme must be HTTPS (unless allow_http=True)
    2. Hostname must be in whitelist
    3. No private/internal IPs
    4. No localhost
    5. No AWS metadata endpoints
    
    Args:
        url: URL to validate
        allowed_domains: Whitelist of allowed domains (default: DEFAULT_ALLOWED_DOMAINS)
        allow_http: Allow HTTP scheme (default: False, HTTPS only)
        
    Returns:
        True if URL is safe, False otherwise
        
    Example:
        >>> is_safe_url("https://api.github.com/users")
        True
        
        >>> is_safe_url("http://localhost/admin")
        False
        
        >>> is_safe_url("https://169.254.169.254/latest/meta-data")
        False
    """
    if not url:
        return False
    
    if allowed_domains is None:
        allowed_domains = DEFAULT_ALLOWED_DOMAINS
    
    try:
        parsed = urlparse(url)
        
        # Check 1: Validate scheme (only HTTPS by default)
        if allow_http:
            if parsed.scheme not in ["http", "https"]:
                logger.warning(f"SSRF: Invalid scheme: {parsed.scheme}")
                return False
        else:
            if parsed.scheme != "https":
                logger.warning(f"SSRF: Only HTTPS allowed, got: {parsed.scheme}")
                return False
        
        # Check 2: Hostname must exist
        if not parsed.hostname:
            logger.warning("SSRF: No hostname in URL")
            return False
        
        # Check 3: Validate domain whitelist
        if parsed.hostname not in allowed_domains:
            logger.warning(f"SSRF: Domain not in whitelist: {parsed.hostname}")
            return False
        
        # Check 4: Block private IPs
        if is_private_ip(parsed.hostname):
            logger.warning(f"SSRF: Private IP detected: {parsed.hostname}")
            return False
        
        # Check 5: Block localhost variations
        localhost_names = [
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            "::1",
            "0:0:0:0:0:0:0:1",
        ]
        
        if parsed.hostname.lower() in localhost_names:
            logger.warning(f"SSRF: Localhost detected: {parsed.hostname}")
            return False
        
        # Check 6: Block AWS metadata endpoint (defense in depth)
        if parsed.hostname == "169.254.169.254":
            logger.warning("SSRF: AWS metadata endpoint blocked")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"SSRF: URL validation error: {e}")
        return False


def validate_url_or_raise(
    url: str,
    allowed_domains: Optional[List[str]] = None,
    allow_http: bool = False
) -> str:
    """
    Validate URL and raise exception if invalid.
    
    Convenience function for use in API endpoints.
    
    Args:
        url: URL to validate
        allowed_domains: Whitelist of allowed domains
        allow_http: Allow HTTP scheme
        
    Returns:
        The validated URL
        
    Raises:
        SSRFProtectionError: If URL fails validation
        
    Example:
        >>> validate_url_or_raise("https://api.github.com/users")
        'https://api.github.com/users'
        
        >>> validate_url_or_raise("http://localhost/admin")
        SSRFProtectionError: URL failed SSRF validation
    """
    if not is_safe_url(url, allowed_domains, allow_http):
        raise SSRFProtectionError(
            f"URL failed SSRF validation. Only whitelisted HTTPS domains are allowed."
        )
    
    return url


def get_allowed_domains_from_settings() -> List[str]:
    """
    Get allowed domains from settings.
    
    Returns:
        List of allowed domains
    """
    from config.settings import settings
    
    # Start with defaults
    allowed = list(DEFAULT_ALLOWED_DOMAINS)
    
    # Add any configured domains
    if hasattr(settings, "ssrf_allowed_domains"):
        allowed.extend(settings.ssrf_allowed_domains)
    
    return allowed


# Example usage in a route:
"""
from core.utils.url_validator import validate_url_or_raise, get_allowed_domains_from_settings

@router.post("/fetch-external")
async def fetch_external_data(url: str):
    # Validate URL before making request
    safe_url = validate_url_or_raise(
        url, 
        allowed_domains=get_allowed_domains_from_settings()
    )
    
    # Now safe to make request
    async with httpx.AsyncClient() as client:
        response = await client.get(safe_url)
        return response.json()
"""

