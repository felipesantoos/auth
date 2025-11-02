"""
Application Settings
Centralized configuration using Pydantic Settings
Loads configuration from environment variables (.env files)
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
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
    
    # Email Service
    email_backend: str = "console"  # smtp, console, sendgrid, ses, mailgun
    email_templates_dir: str = "templates/emails"
    email_tracking_enabled: bool = True
    
    # SMTP Configuration
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: str = "noreply@authsystem.com"
    smtp_from_name: str = "Auth System"
    smtp_use_tls: bool = True
    smtp_timeout: int = 30
    
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
    
    # Account Lockout Protection
    account_lockout_max_attempts: int = 5  # Lock after N failed attempts
    account_lockout_duration_minutes: int = 30  # How long to lock account
    account_lockout_window_minutes: int = 15  # Time window for counting attempts
    ip_lockout_enabled: bool = True  # Enable IP-based lockout in addition to account lockout
    send_login_notifications: bool = True  # Send email notifications for new device logins
    
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
    
    # Login Notifications
    send_login_notifications: bool = False  # Send email on new device login
    
    # Email Providers (Optional)
    sendgrid_api_key: Optional[str] = None
    mailgun_api_key: Optional[str] = None
    mailgun_domain: Optional[str] = None
    aws_region: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    
    # Background Jobs (Celery)
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/1"
    email_use_background_queue: bool = False
    
    # Elasticsearch (Optional - for >10M audit logs)
    elasticsearch_enabled: bool = False
    elasticsearch_host: str = "localhost"
    elasticsearch_port: int = 9200
    elasticsearch_index_prefix: str = "auth_audit"
    elasticsearch_user: Optional[str] = None
    elasticsearch_password: Optional[str] = None
    
    # File Upload & Storage
    file_upload_max_size: int = 100 * 1024 * 1024  # 100MB default
    allowed_file_types: list = [
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'application/pdf', 'video/mp4', 'audio/mpeg', 'text/plain'
    ]
    storage_provider: str = "local"  # local, s3, s3-cdn, azure, gcs, cloudinary, cloudflare
    local_storage_path: str = "uploads"
    
    # AWS S3 Storage
    aws_s3_bucket: Optional[str] = None
    aws_s3_region: Optional[str] = None
    aws_s3_base_url: Optional[str] = None
    # aws_access_key_id and aws_secret_access_key already defined above
    
    # Azure Blob Storage
    azure_storage_connection_string: Optional[str] = None
    azure_container_name: Optional[str] = None
    
    # Google Cloud Storage
    gcp_project_id: Optional[str] = None
    gcs_bucket_name: Optional[str] = None
    
    # Cloudinary
    cloudinary_cloud_name: Optional[str] = None
    cloudinary_api_key: Optional[str] = None
    cloudinary_api_secret: Optional[str] = None
    
    # Cloudflare Images
    cloudflare_account_id: Optional[str] = None
    cloudflare_api_token: Optional[str] = None
    
    # CDN (CloudFront)
    cloudfront_domain: Optional[str] = None
    cloudfront_key_id: Optional[str] = None
    cloudfront_private_key: Optional[str] = None
    
    # ClamAV (Malware Scanning)
    clamav_enabled: bool = False
    clamav_socket_path: str = "/var/run/clamav/clamd.ctl"
    
    # Monitoring (Optional)
    sentry_dsn: Optional[str] = None
    
    @field_validator('jwt_secret')
    @classmethod
    def validate_jwt_secret_production(cls, v, info):
        """Validate JWT secret is strong in production"""
        environment = info.data.get('environment', 'development')
        
        if environment == 'production':
            # Check if using default/weak secret
            weak_secrets = [
                'change-this-secret-key-in-production-use-openssl-rand',
                'dev-secret',
                'test-secret',
            ]
            
            if v in weak_secrets or len(v) < 32:
                raise ValueError(
                    'JWT_SECRET must be at least 32 characters in production. '
                    'Generate a strong secret: python -c "import secrets; print(secrets.token_urlsafe(32))"'
                )
        
        return v
    
    @field_validator('default_admin_password')
    @classmethod
    def validate_admin_password(cls, v, info):
        """Warn about default admin password"""
        environment = info.data.get('environment', 'development')
        
        if environment == 'production' and v == 'admin123':
            raise ValueError(
                'Cannot use default admin password in production. '
                'Set DEFAULT_ADMIN_PASSWORD in environment variables.'
            )
        
        return v
    
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

