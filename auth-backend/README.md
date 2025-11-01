# Auth System API

Multi-tenant Authentication and Authorization System built with FastAPI.

## Features

### Core Features
- ✅ Multi-tenant architecture (clients with isolated users)
- ✅ JWT authentication with refresh tokens
- ✅ Role-based access control (RBAC)
- ✅ User management per client
- ✅ Redis caching
- ✅ PostgreSQL database
- ✅ Structured logging
- ✅ OAuth2 integration (Google, GitHub)

### Advanced Authentication Features
- ✅ **Email Verification** - Verify user emails with secure tokens
- ✅ **Two-Factor Authentication (2FA/MFA)** - TOTP + QR codes + backup codes
- ✅ **Session Management** - Track and manage sessions across multiple devices
- ✅ **Audit Logging** - Comprehensive security event tracking (70+ event types)
- ✅ **Account Lockout** - Brute-force protection with automatic account locking
- ✅ **API Keys** - Personal Access Tokens for programmatic API access
- ✅ **Passwordless Auth** - Magic links for email-based login
- ✅ **Suspicious Activity Detection** - Alert on logins from new devices/locations
- ✅ **Login Notifications** - Email alerts for new device logins
- ✅ **Fine-Grained Permissions** - Resource-level access control beyond RBAC
- ✅ **User Profile Management** - Self-service profile updates and account deletion

### Enterprise Features
- ✅ **WebAuthn/Passkeys** - Biometric authentication support (Face ID, Touch ID, YubiKey)
- ✅ **SAML 2.0** - Enterprise SSO integration
- ✅ **OIDC** - OpenID Connect support
- ✅ **LDAP/AD** - Active Directory integration

## Setup

### Prerequisites

- Python 3.12+
- PostgreSQL
- Redis

### Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy environment file:
   ```bash
   cp .env.example .env
   ```

5. Configure `.env` with your database and Redis settings

6. Run migrations:
   ```bash
   alembic upgrade head
   ```

7. Run the application:
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8080`
API docs at `http://localhost:8080/docs`

## Project Structure

```
auth-backend/
├── alembic/              # Database migrations
│   └── versions/        # Migration files (20251102_0001_add_permissions_table.py)
├── app/                  # Application layer
│   └── api/             
│       ├── routes/      # REST API endpoints (14 route files)
│       │   ├── auth_routes.py
│       │   ├── oauth_routes.py
│       │   ├── mfa_routes.py
│       │   ├── session_routes.py
│       │   ├── email_verification_routes.py
│       │   ├── passwordless_routes.py
│       │   ├── api_key_routes.py
│       │   ├── webauthn_routes.py
│       │   ├── audit_routes.py
│       │   ├── sso_routes.py
│       │   ├── permission_routes.py ✨
│       │   └── profile_routes.py ✨
│       ├── dtos/        # Request/Response DTOs (15+ DTOs)
│       ├── middlewares/ # Auth, API Key, Rate Limiting, HTTPS, etc.
│       └── dicontainer/ # Dependency Injection
├── config/              # Configuration (settings, logging)
├── core/                # Core business logic (Hexagonal Architecture)
│   ├── domain/         # Domain models (AppUser, Permission ✨, BackupCode, UserSession, AuditLog, ApiKey, WebAuthnCredential)
│   ├── interfaces/     # Port interfaces (primary & secondary)
│   └── services/       # Business services (15+ services)
│       ├── auth/       # Auth services (MFA, Permissions ✨, Profile ✨, Sessions, Email, Passwordless, API Keys, etc.)
│       └── audit/      # Audit service
├── infra/              # Infrastructure (Adapters)
│   ├── database/       # Database models, repositories, mappers
│   │   ├── models/     # SQLAlchemy models (8 models + PermissionModel ✨)
│   │   ├── repositories/ # Data access (8 repositories + PermissionRepository ✨)
│   │   └── mappers/    # Domain ↔ DB mappers (8 mappers + PermissionMapper ✨)
│   ├── email/         # Email service (SMTP)
│   └── redis/         # Redis client and cache
├── tests/              # Test suite
│   ├── unit/          # Unit tests (permission_service ✨, profile_service ✨, auth_service, etc.)
│   └── integration/   # Integration tests (permissions_api ✨, profile_api ✨, auth_security, etc.)
├── docs/               # Documentation
└── main.py            # Application entry point
```

✨ = **New in this update**

## Architecture

This project follows Hexagonal Architecture (Ports & Adapters) principles:

- **Domain Layer**: Pure business logic, no dependencies
- **Service Layer**: Business use cases, depends on interfaces
- **Infrastructure Layer**: Database, Redis, external services
- **API Layer**: HTTP endpoints, DTOs, validation

## Advanced Features Guide

### 🔒 Email Verification

Verify user emails during registration:

```bash
# Enable in .env
REQUIRE_EMAIL_VERIFICATION=true
EMAIL_VERIFICATION_EXPIRE_HOURS=24

# Configure SMTP
SMTP_HOST="smtp.gmail.com"
SMTP_USER="your-email@gmail.com"
SMTP_PASSWORD="your-app-password"
```

**Endpoints**:
- `POST /auth/email/verify` - Verify email with token
- `POST /auth/email/resend-verification` - Resend verification email
- `GET /auth/email/status` - Check verification status

### 🔐 Two-Factor Authentication (MFA)

TOTP-based 2FA with backup codes:

**Setup Flow**:
1. `POST /auth/mfa/setup` - Get QR code + secret + backup codes
2. Scan QR code with Google Authenticator / Authy
3. `POST /auth/mfa/enable` - Enable with TOTP verification
4. Save backup codes securely!

**Endpoints**:
- `POST /auth/mfa/setup` - Initialize MFA setup
- `POST /auth/mfa/enable` - Enable MFA
- `POST /auth/mfa/disable` - Disable MFA
- `GET /auth/mfa/status` - Get MFA status
- `POST /auth/mfa/backup-codes/regenerate` - Regenerate backup codes

### 📱 Session Management

Track and manage sessions across devices:

```bash
SESSION_MAX_DEVICES=10
SESSION_INACTIVITY_TIMEOUT_DAYS=30
```

**Endpoints**:
- `GET /auth/sessions` - List active sessions (shows device, IP, location)
- `DELETE /auth/sessions/{id}` - Logout from specific device
- `DELETE /auth/sessions/all` - Logout from all devices

### 📊 Audit Logging

Track all security events:

**Endpoints**:
- `GET /auth/audit` - View your own audit logs
- `GET /admin/audit` - View all logs (admin only)
- `GET /admin/audit/security` - Security-critical events (admin only)

**Events Tracked**:
- Login/Logout (success/failure)
- Password changes
- MFA enable/disable
- Session management
- Account lockouts
- Suspicious activity
- And 60+ more event types

### 🔑 API Keys

Create Personal Access Tokens for API integrations:

```bash
API_KEY_DEFAULT_EXPIRE_DAYS=365
API_KEY_MAX_PER_USER=20
```

**Usage**:
```bash
# Create key
POST /auth/api-keys
{
  "name": "My Integration",
  "scopes": ["read:user", "write:user"],
  "expires_in_days": 365
}

# Use key
curl -H "X-API-Key: ask_your_key_here" http://localhost:8080/auth/me
```

**Endpoints**:
- `POST /auth/api-keys` - Create API key (shown only once!)
- `GET /auth/api-keys` - List your API keys
- `DELETE /auth/api-keys/{id}` - Revoke API key

### 🪄 Passwordless Authentication

Login via magic links sent to email:

```bash
MAGIC_LINK_EXPIRE_MINUTES=15
MAGIC_LINK_RATE_LIMIT=2  # per 5 minutes
```

**Endpoints**:
- `POST /auth/passwordless/send` - Send magic link to email
- `POST /auth/passwordless/verify` - Login with magic link

### 🛡️ Account Security

**Brute-Force Protection**:
- Automatic account lockout after 5 failed attempts
- Lock duration: 30 minutes (configurable)
- IP-based and user-based detection

```bash
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_DURATION_MINUTES=30
```

### 🔐 Fine-Grained Permissions

Resource-level access control beyond basic RBAC:

**Features**:
- Assign permissions per resource (e.g., Project #123)
- Actions: CREATE, READ, UPDATE, DELETE, MANAGE
- Resource types: PROJECT, TEAM, DOCUMENT, REPORT, USER, CLIENT
- Admin can grant/revoke permissions
- Users can view their own permissions

**Endpoints**:
- `POST /api/auth/permissions` - Grant permission (admin only)
- `GET /api/auth/permissions/user/{user_id}` - List user permissions
- `DELETE /api/auth/permissions/{permission_id}` - Revoke permission

**Example**:
```bash
# Grant user UPDATE permission on Project #123
POST /api/auth/permissions
{
  "user_id": "user-456",
  "resource_type": "project",
  "action": "update",
  "resource_id": "project-123"
}

# Grant user MANAGE permission on all teams
POST /api/auth/permissions
{
  "user_id": "user-456",
  "resource_type": "team",
  "action": "manage",
  "resource_id": null
}
```

### 👤 User Profile Management

Self-service profile management endpoints:

**Endpoints**:
- `GET /api/auth/profile/me` - Get own profile
- `PUT /api/auth/profile/me` - Update profile (name, username)
- `POST /api/auth/profile/change-email` - Request email change (requires password)
- `DELETE /api/auth/profile/me` - Delete account (soft delete, requires password)

**Example**:
```bash
# Update profile
PUT /api/auth/profile/me
{
  "name": "John Doe",
  "username": "johndoe"
}

# Delete account (requires password confirmation)
DELETE /api/auth/profile/me
{
  "password": "current_password"
}
```

## Database Migrations

This project uses Alembic for database migrations. All migrations are in the `alembic/versions/` directory.

### Common Commands

#### Create New Migration
```bash
# Auto-generate migration by comparing models with database
alembic revision --autogenerate -m "description"

# Example: Add new column
alembic revision --autogenerate -m "add_user_phone_column"

# Manual migration (for complex changes)
alembic revision -m "add_custom_index"
```

#### Apply Migrations
```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific number of migrations
alembic upgrade +2

# Apply to specific revision
alembic upgrade abc123
```

#### Revert Migrations
```bash
# Revert last migration
alembic downgrade -1

# Revert all migrations
alembic downgrade base

# Revert to specific revision
alembic downgrade abc123
```

#### Check Status
```bash
# Show current version
alembic current

# Show migration history
alembic history

# Show migration history with details
alembic history --verbose

# Show SQL without executing
alembic upgrade head --sql
```

### Best Practices

#### 1. Always Review Auto-generated Migrations

Alembic auto-generation might not detect:
- Column renames (appears as drop + add)
- Table renames
- Data migrations
- Complex constraints

Always review and manually adjust the generated migration file if needed.

#### 2. Migration Naming Convention

Use descriptive names that clearly indicate what the migration does:

**Good names:**
```bash
alembic revision --autogenerate -m "add_user_email_index"
alembic revision --autogenerate -m "create_products_table"
alembic revision --autogenerate -m "add_user_role_column"
```

**Bad names:**
```bash
alembic revision --autogenerate -m "changes"
alembic revision --autogenerate -m "update"
alembic revision --autogenerate -m "fix"
```

#### 3. Test Migrations Before Deploying

Always test both upgrade and downgrade:

```bash
# Test upgrade
alembic upgrade head

# Test downgrade
alembic downgrade -1

# Test upgrade again
alembic upgrade head
```

#### 4. Data Migrations

When you need to transform data during migration:

```python
def upgrade() -> None:
    """Migration with data transformation"""
    # 1. Add new column (nullable first)
    op.add_column('users', sa.Column('full_name', sa.String(500), nullable=True))
    
    # 2. Migrate data
    connection = op.get_bind()
    connection.execute(
        sa.text("UPDATE users SET full_name = first_name || ' ' || last_name")
    )
    
    # 3. Make column non-nullable
    op.alter_column('users', 'full_name', nullable=False)
    
    # 4. Drop old columns
    op.drop_column('users', 'first_name')
    op.drop_column('users', 'last_name')

def downgrade() -> None:
    """Reverse migration"""
    # Add old columns back
    op.add_column('users', sa.Column('first_name', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('last_name', sa.String(255), nullable=True))
    
    # Migrate data back
    connection = op.get_bind()
    connection.execute(
        sa.text("""
            UPDATE users 
            SET first_name = split_part(full_name, ' ', 1),
                last_name = split_part(full_name, ' ', 2)
        """)
    )
    
    # Make columns non-nullable
    op.alter_column('users', 'first_name', nullable=False)
    op.alter_column('users', 'last_name', nullable=False)
    
    # Drop new column
    op.drop_column('users', 'full_name')
```

### Troubleshooting

#### "Target database is not up to date"
```bash
# Check current version
alembic current

# Check migration history
alembic history

# If database state doesn't match, you can force stamp
# WARNING: Only use if you know what you're doing
alembic stamp head
```

#### "Can't locate revision identified by 'xyz'"
```bash
# Migration file was deleted or not committed
# Option 1: Restore the missing migration file from git
git checkout <commit> -- alembic/versions/xyz_description.py

# Option 2: If you can't restore, create a new baseline (DANGEROUS)
alembic stamp head
```

#### "FAILED: Target database is not up to date"
This usually means someone else applied migrations. Pull latest migrations and upgrade:
```bash
git pull
alembic upgrade head
```

#### Database Connection Errors
Make sure your `DATABASE_URL` in `.env` is correct:
```bash
# Check your connection string
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

### Docker Integration

When running in Docker, migrations are automatically applied on container startup via the entrypoint script.

```bash
# Build and start containers
docker-compose up --build

# Migrations run automatically before the API starts
```

To manually run migrations in Docker:
```bash
# Run migrations in running container
docker-compose exec api alembic upgrade head

# Run migrations in new container
docker-compose run --rm api alembic upgrade head
```

### CI/CD Integration

In your CI/CD pipeline, run migrations before deploying:

```bash
# Example GitHub Actions
- name: Run migrations
  run: alembic upgrade head
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

### Migration File Structure

Each migration file contains:

```python
"""Description of what this migration does

Revision ID: abc123
Revises: xyz789
Create Date: 2024-01-01 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# Revision identifiers
revision = 'abc123'
down_revision = 'xyz789'  # Previous migration
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Apply migration"""
    # Your schema changes here
    pass

def downgrade() -> None:
    """Revert migration"""
    # Reverse your schema changes here
    pass
```

---

## 📚 API Documentation

Complete API reference and guides:

- **[API Endpoints Reference](docs/API_ENDPOINTS.md)** - Full documentation of all authentication endpoints
- Swagger/OpenAPI: Available at `/docs` when running in development mode

### Quick Links

- [Authentication Endpoints](docs/API_ENDPOINTS.md#authentication)
- [OAuth2 Integration](docs/API_ENDPOINTS.md#oauth2-social-login)
- [MFA Setup](docs/API_ENDPOINTS.md#multi-factor-authentication-mfa)
- [Session Management](docs/API_ENDPOINTS.md#session-management)
- [Admin User Management](docs/API_ENDPOINTS.md#authentication)
- [Permissions & Access Control](docs/API_ENDPOINTS.md#permissions)
- [User Profile Management](docs/API_ENDPOINTS.md#profile)

---

## 🔒 Security

### Production Deployment Checklist

Before deploying to production, ensure:

- [ ] Change `JWT_SECRET` to a strong random value (32+ chars)
- [ ] Change `DEFAULT_ADMIN_PASSWORD` to a secure password
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEBUG=False`
- [ ] Configure specific CORS origins (no wildcards)
- [ ] Enable HTTPS (SSL certificates configured)
- [ ] Set strong database passwords
- [ ] Enable Redis password authentication
- [ ] Review rate limiting settings
- [ ] Run security tests: `pytest tests/`

### Generate Secure Secrets

```bash
# JWT Secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Or using OpenSSL
openssl rand -base64 32
```

### Run Tests

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov=app --cov=infra

# Run security tests only
pytest tests/integration/test_auth_security.py -v
```

### Security Features

- ✅ **Password Hashing**: bcrypt with 12 rounds
- ✅ **JWT Tokens**: HS256 with configurable expiration
- ✅ **Rate Limiting**: SlowAPI with Redis storage
- ✅ **CORS Protection**: Configurable origins, methods, and headers
- ✅ **HTTPS Redirect**: Automatic in production
- ✅ **Input Validation**: Pydantic validators on all endpoints
- ✅ **SQL Injection Protection**: SQLAlchemy ORM
- ✅ **Password Strength**: Minimum 8 chars, uppercase, lowercase, digit
- ✅ **Account Lockout**: Automatic after failed login attempts
- ✅ **Audit Logging**: Comprehensive security event tracking

---

