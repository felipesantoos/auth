"""
Rate Limiting Middleware
Protects against brute-force attacks using SlowAPI with Redis storage
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from config.settings import settings

# Create limiter instance with Redis storage for distributed rate limiting
limiter = Limiter(
    key_func=get_remote_address,  # Rate limit by IP address
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],  # Default: 60 req/min from settings
    storage_uri=f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",  # Use Redis for distributed rate limiting
)


def get_limiter():
    """Get rate limiter instance"""
    return limiter

