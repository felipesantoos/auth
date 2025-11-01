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
    smtp_from_email: str = "noreply@authsystem.com"
    smtp_from_name: str = "Auth System"
    
    # OAuth2 Providers (Optional)
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    github_client_id: Optional[str] = None
    github_client_secret: Optional[str] = None
    
    # API Base URL (for OAuth redirects)
    api_base_url: str = "http://localhost:8080"
    frontend_url: str = "http://localhost:5173"
    
    # Email Verification
    require_email_verification: bool = False
    email_verification_expire_hours: int = 24
    
    # MFA/2FA
    mfa_issuer_name: str = "Auth System"
    mfa_backup_codes_count: int = 10
    
    # Session Management
    session_max_devices: int = 10  # Maximum active sessions per user
    session_inactivity_timeout_days: int = 30
    
    # Account Security
    max_login_attempts: int = 5
    account_lockout_duration_minutes: int = 30
    
    # Passwordless Auth (Magic Links)
    magic_link_expire_minutes: int = 15
    magic_link_rate_limit: int = 2  # per 5 minutes
    
    # API Keys
    api_key_default_expire_days: int = 365
    api_key_max_per_user: int = 20
    
    # WebAuthn
    webauthn_rp_name: str = "Auth System"
    webauthn_rp_id: str = "localhost"
    webauthn_origin: str = "http://localhost:5173"
    
    # SSO - SAML
    saml_enabled: bool = False
    saml_entity_id: Optional[str] = None
    saml_idp_metadata_url: Optional[str] = None
    saml_sp_x509_cert: Optional[str] = None
    saml_sp_private_key: Optional[str] = None
    
    # SSO - OIDC
    oidc_enabled: bool = False
    oidc_issuer: Optional[str] = None
    oidc_client_id: Optional[str] = None
    oidc_client_secret: Optional[str] = None
    oidc_redirect_uri: Optional[str] = None
    
    # SSO - LDAP
    ldap_enabled: bool = False
    ldap_server: Optional[str] = None
    ldap_port: int = 389
    ldap_use_ssl: bool = False
    ldap_bind_dn: Optional[str] = None
    ldap_bind_password: Optional[str] = None
    ldap_base_dn: Optional[str] = None
    ldap_user_filter: str = "(uid={username})"
    
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

