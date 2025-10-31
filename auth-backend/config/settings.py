"""
Application Settings
Centralized configuration using Pydantic Settings
Loads configuration from environment variables (.env files)
"""
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Uses pydantic-settings to validate and parse environment variables.
    Supports multiple environments via .env files (.env, .env.staging, .env.production)
    """
    
    # Application
    app_name: str = "Auth System API"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    
    # Database (PostgreSQL)
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/auth_system"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0
    
    # JWT Authentication
    jwt_secret: str = "change-this-secret-key-in-production-use-openssl-rand"
    jwt_algorithm: str = "HS256"
    jwt_audience: str = "auth-system-api"
    jwt_issuer: str = "auth-system-api"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Default Admin User
    default_admin_email: str = "admin@authsystem.com"
    default_admin_password: str = "admin123"
    default_admin_name: str = "Administrator"
    
    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    login_rate_limit_per_minute: int = 5
    
    # External Services (Optional)
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    
    # OAuth2 Providers (Optional)
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    github_client_id: Optional[str] = None
    github_client_secret: Optional[str] = None
    
    # API Base URL (for OAuth redirects)
    api_base_url: str = "http://localhost:8080"
    
    # Monitoring (Optional)
    sentry_dsn: Optional[str] = None
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Convert CORS_ORIGINS string to list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()

