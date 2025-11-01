# 🔐 Authentication & Authorization - Complete Guide

## Visão Geral

Este sistema implementa um conjunto completo de funcionalidades de autenticação e autorização enterprise-grade, seguindo as melhores práticas de segurança (OWASP) e arquitetura hexagonal.

---

## 📚 Índice

1. [Autenticação Básica](#autenticação-básica)
2. [Email Verification](#email-verification)
3. [Two-Factor Authentication (MFA)](#two-factor-authentication-mfa)
4. [Session Management](#session-management)
5. [Audit Logging](#audit-logging)
6. [API Keys](#api-keys)
7. [Passwordless Authentication](#passwordless-authentication)
8. [Account Security](#account-security)
9. [Configuração](#configuração)
10. [Deployment](#deployment)

---

## 1. Autenticação Básica

### JWT + Refresh Tokens

**Endpoints**:
- `POST /auth/register` - Criar nova conta
- `POST /auth/login` - Login (retorna access + refresh tokens)
- `POST /auth/refresh` - Renovar access token
- `POST /auth/logout` - Logout (invalida refresh token)
- `GET /auth/me` - Obter usuário atual

**Exemplo de Uso**:
```bash
# Register
curl -X POST http://localhost:8080/auth/register \
  -H "Content-Type: application/json" \
  -H "X-Client-ID: your-client-id" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "name": "John Doe"
  }'

# Login
curl -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -H "X-Client-ID: your-client-id" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123!"
  }'

# Response
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "Bearer",
  "user": { ... }
}

# Use token
curl http://localhost:8080/auth/me \
  -H "Authorization: Bearer eyJ..."
```

---

## 2. Email Verification

### Como Funciona

1. Usuário se registra
2. Sistema gera token de verificação (24h)
3. Email é enviado com link de verificação
4. Usuário clica no link
5. Email é marcado como verificado

### Configuração

```bash
# .env
REQUIRE_EMAIL_VERIFICATION=true
EMAIL_VERIFICATION_EXPIRE_HOURS=24

# SMTP Configuration
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=587
SMTP_USER="your-email@gmail.com"
SMTP_PASSWORD="your-app-password"
SMTP_FROM_EMAIL="noreply@yourapp.com"
```

### Endpoints

```bash
# Verify email
POST /auth/email/verify
{
  "user_id": "user-id",
  "token": "verification-token"
}

# Resend verification
POST /auth/email/resend-verification
# (uses auth token, no body needed)

# Check status
GET /auth/email/status
```

---

## 3. Two-Factor Authentication (MFA)

### Features

- ✅ TOTP (Time-based One-Time Password)
- ✅ QR Code generation para Google Authenticator / Authy
- ✅ 10 Backup Codes (single-use, hashed com bcrypt)
- ✅ Backup code regeneration

### Setup Flow

```bash
# 1. Initialize setup (get QR code)
POST /auth/mfa/setup
Authorization: Bearer {token}

# Response:
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,iVBORw0KGgo...",
  "backup_codes": [
    "1234-5678-9012",
    "2345-6789-0123",
    ...
  ]
}

# 2. Scan QR code with authenticator app

# 3. Enable MFA (verify TOTP)
POST /auth/mfa/enable
{
  "secret": "JBSWY3DPEHPK3PXP",
  "totp_code": "123456",
  "backup_codes": ["1234-5678-9012", ...]
}

# 4. Save backup codes securely!
```

### Login with MFA

```bash
# Step 1: Normal login
POST /auth/login
{
  "email": "user@example.com",
  "password": "password"
}

# If MFA enabled, response:
{
  "mfa_required": true,
  "user_id": "user-id",
  "challenge_id": "temp-challenge"
}

# Step 2: Verify TOTP or Backup Code
POST /auth/login/mfa
{
  "user_id": "user-id",
  "totp_code": "123456"
  # OR
  "backup_code": "1234-5678-9012"
}

# Response: access_token + refresh_token
```

### Management

```bash
# Check status
GET /auth/mfa/status

# Disable MFA
POST /auth/mfa/disable
{ "password": "your-password" }

# Regenerate backup codes
POST /auth/mfa/backup-codes/regenerate
```

---

## 4. Session Management

### Features

- ✅ Track sessions across múltiplos dispositivos
- ✅ Device information (browser, OS, type)
- ✅ IP address and location tracking
- ✅ Last activity timestamp
- ✅ Logout from specific device
- ✅ Logout from all devices
- ✅ Automatic session limit (revoke oldest)

### Endpoints

```bash
# List active sessions
GET /auth/sessions
Authorization: Bearer {token}

# Response:
{
  "sessions": [
    {
      "id": "session-id",
      "device_name": "Chrome on Windows",
      "device_type": "desktop",
      "ip_address": "192.168.1.1",
      "location": "São Paulo, Brazil",
      "last_activity": "2025-01-31T12:00:00Z",
      "created_at": "2025-01-30T10:00:00Z",
      "is_current": true
    },
    {
      "id": "session-id-2",
      "device_name": "Safari on iPhone",
      "device_type": "mobile",
      ...
    }
  ],
  "total": 2
}

# Revoke specific session (logout from device)
DELETE /auth/sessions/{session-id}

# Logout from all devices (except current)
DELETE /auth/sessions/all
{ "except_current": true }
```

---

## 5. Audit Logging

### Event Types (70+)

- **Authentication**: login_success, login_failed, logout
- **Tokens**: token_refresh, token_revoked
- **Registration**: user_registered
- **Email**: email_verified, email_verification_sent
- **Password**: password_changed, password_reset
- **MFA**: mfa_enabled, mfa_disabled, mfa_verification_success
- **Security**: account_locked, suspicious_activity_detected
- **Sessions**: session_revoked, logout_all_sessions
- **API Keys**: api_key_created, api_key_used, api_key_revoked
- **Admin**: user_created_by_admin, user_deleted_by_admin
- E mais 50+ tipos...

### Endpoints

```bash
# User's own audit logs
GET /auth/audit?days=30&limit=100

# Admin: all logs for tenant
GET /admin/audit?days=30&event_types=login_success,login_failed

# Admin: security events only
GET /admin/audit/security?days=7
```

### Detecção de Ameaças

**Brute-Force Detection**:
- Conta tentativas de login falhadas
- Por usuário e por IP
- Threshold configurável (default: 5 tentativas em 30 min)

**Suspicious Activity Detection**:
- Login de novo IP + novo device
- Padrões anormais de acesso
- Logs automáticos

---

## 6. API Keys

### Personal Access Tokens

API Keys permitem acesso programático à API sem usar credenciais de usuário.

### Features

- ✅ Scopes (permissões granulares)
- ✅ Expiration configurável
- ✅ Revogação
- ✅ Tracking de uso (last_used_at)
- ✅ Limite por usuário (default: 20)

### Available Scopes

- `read:user` - Ler informações de usuário
- `write:user` - Modificar usuário
- `delete:user` - Deletar usuário
- `read:session` - Ler sessões
- `manage:session` - Gerenciar sessões
- `read:audit` - Ler audit logs
- `admin` - Acesso total (admin)

### Criação e Uso

```bash
# Create API key
POST /auth/api-keys
Authorization: Bearer {jwt-token}
{
  "name": "Production API",
  "scopes": ["read:user", "write:user"],
  "expires_in_days": 365
}

# Response (KEY SHOWN ONLY ONCE!):
{
  "api_key": "ask_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6",
  "key_info": {
    "id": "key-id",
    "name": "Production API",
    "scopes": ["read:user", "write:user"],
    "expires_at": "2026-01-31T00:00:00Z",
    ...
  }
}

# Use API key
curl http://localhost:8080/auth/me \
  -H "X-API-Key: ask_a1b2c3d4e5f6g7h8..."

# List keys
GET /auth/api-keys

# Revoke key
DELETE /auth/api-keys/{key-id}
```

---

## 7. Passwordless Authentication

### Magic Links

Login sem senha via link enviado por email.

### Features

- ✅ Links expiram em 15 minutos
- ✅ Single-use (one-time link)
- ✅ Rate limiting (2 requests / 5 minutos)
- ✅ Secure tokens (32 bytes urlsafe)

### Flow

```bash
# Step 1: Request magic link
POST /auth/passwordless/send
{
  "email": "user@example.com",
  "client_id": "client-id"
}

# Step 2: User receives email with link
# Link format: https://yourapp.com/auth/magic-link?token={token}&user_id={id}

# Step 3: Verify and login
POST /auth/passwordless/verify
{
  "user_id": "user-id",
  "token": "magic-link-token",
  "client_id": "client-id"
}

# Response: access_token + refresh_token
```

---

## 8. Account Security

### Brute-Force Protection

**Automatic Lockout**:
- Conta tentativas de login falhadas
- Lock após 5 tentativas (configurável)
- Duration: 30 minutos (configurável)
- Reset automático após login bem-sucedido

```bash
# Configuration
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_DURATION_MINUTES=30
```

**Implementation**:
- Integrado no login flow
- Incrementa contador em `AppUser.failed_login_attempts`
- Define `AppUser.locked_until` timestamp
- Logs audit event `ACCOUNT_LOCKED`

### Suspicious Activity Detection

Detecta:
- Login de novo IP address
- Login de novo device/browser
- Padrões anormais

Quando detectado:
- Log audit event `SUSPICIOUS_ACTIVITY_DETECTED`
- Notificação por email (TODO)
- Admin pode revisar em `/admin/audit/security`

---

## 9. Configuração

### Environment Variables

Veja arquivo completo: `env.example.txt`

**Essenciais**:
```bash
# Database
DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db"

# Redis
REDIS_HOST="localhost"
REDIS_PORT=6379

# JWT
JWT_SECRET="generate-with-openssl-rand-hex-32"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email (SMTP)
SMTP_HOST="smtp.gmail.com"
SMTP_USER="your-email@gmail.com"
SMTP_PASSWORD="your-app-password"
```

**Advanced Features**:
```bash
# Email Verification
REQUIRE_EMAIL_VERIFICATION=false  # true em produção
EMAIL_VERIFICATION_EXPIRE_HOURS=24

# MFA
MFA_ISSUER_NAME="Your App Name"
MFA_BACKUP_CODES_COUNT=10

# Sessions
SESSION_MAX_DEVICES=10

# Security
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_DURATION_MINUTES=30

# Passwordless
MAGIC_LINK_EXPIRE_MINUTES=15

# API Keys
API_KEY_DEFAULT_EXPIRE_DAYS=365
API_KEY_MAX_PER_USER=20
```

### Security Best Practices

**Production Checklist**:
- [ ] `DEBUG=false`
- [ ] `ENVIRONMENT="production"`
- [ ] Strong `JWT_SECRET` (min 32 chars random)
- [ ] `REQUIRE_EMAIL_VERIFICATION=true`
- [ ] Configure HTTPS (update CORS_ORIGINS, API_BASE_URL)
- [ ] Configure SMTP for production
- [ ] Set strong password policies
- [ ] Enable rate limiting
- [ ] Monitor audit logs regularly
- [ ] Backup database regularly

---

## 10. Deployment

### 1. Apply Migrations

```bash
alembic upgrade head
```

Creates tables:
- `app_user` (updated with new fields)
- `backup_code`
- `user_session`
- `audit_log`
- `api_key`
- `webauthn_credential`

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

New dependencies:
- `pyotp` - TOTP
- `qrcode` + `pillow` - QR code generation
- `webauthn` - Biometric auth
- `python3-saml` - SAML SSO
- `ldap3` - LDAP/AD
- `user-agents` - User agent parsing

### 3. Configure Environment

Copy `env.example.txt` to `.env` and configure all variables.

### 4. Run Application

```bash
# Development
python main.py

# Production (with gunicorn/uvicorn)
uvicorn main:app --host 0.0.0.0 --port 8080 --workers 4
```

### 5. Access API

- API: `http://localhost:8080`
- Docs: `http://localhost:8080/docs`
- Health: `http://localhost:8080/health`

---

## 📊 API Endpoints Summary

### Authentication (Basic)
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`
- `POST /auth/change-password`

### Email Verification
- `POST /auth/email/verify`
- `POST /auth/email/resend-verification`
- `GET /auth/email/status`

### MFA
- `POST /auth/mfa/setup`
- `POST /auth/mfa/enable`
- `POST /auth/mfa/disable`
- `GET /auth/mfa/status`
- `POST /auth/mfa/backup-codes/regenerate`

### Sessions
- `GET /auth/sessions`
- `DELETE /auth/sessions/{id}`
- `DELETE /auth/sessions/all`

### Audit
- `GET /auth/audit`
- `GET /admin/audit` (admin)
- `GET /admin/audit/security` (admin)

### API Keys
- `POST /auth/api-keys`
- `GET /auth/api-keys`
- `DELETE /auth/api-keys/{id}`

### Passwordless
- `POST /auth/passwordless/send`
- `POST /auth/passwordless/verify`

### OAuth2
- `GET /auth/oauth/{provider}/login`
- `GET /auth/oauth/{provider}/callback`

---

## 🔧 Troubleshooting

### Email não está sendo enviado

1. Verificar configuração SMTP no `.env`
2. Gmail: usar App Password (não senha regular)
3. Verificar logs: `LOG_LEVEL=DEBUG`

### MFA QR Code não aparece

1. Verificar dependências instaladas: `pip install qrcode pillow`
2. Verificar logs do serviço

### Sessões não sendo criadas

1. Verificar se Redis está rodando
2. Verificar conexão Redis no `.env`
3. Verificar logs

### Audit logs vazios

1. Verificar se migration foi aplicada: `alembic current`
2. Verificar tabela `audit_log` existe no DB
3. Eventos são logados mesmo se insert falhar (graceful degradation)

---

## 📖 Documentation Files

- `README.md` - Overview e quick start
- `AUTHENTICATION.md` - Este arquivo (guia completo)
- `IMPLEMENTATION_STATUS.md` - Status da implementação
- `IMPLEMENTATION_SUMMARY.md` - Resumo executivo
- `INTEGRATION_GUIDE.md` - Guia de integração (para completar pendências)
- `ENVIRONMENT_VARIABLES.md` - Todas as variáveis de ambiente

---

## 🚀 Quick Start Examples

### Enable Email Verification

```python
# .env
REQUIRE_EMAIL_VERIFICATION=true
SMTP_HOST="smtp.gmail.com"
SMTP_USER="your-email@gmail.com"
SMTP_PASSWORD="your-app-password"
```

Restart server. Agora registro enviará email de verificação automaticamente.

### Enable MFA for User

1. Login normally
2. Call `POST /auth/mfa/setup`
3. Scan QR code
4. Call `POST /auth/mfa/enable` with TOTP code
5. Done! Next login will require TOTP

### Create API Key

```bash
curl -X POST http://localhost:8080/auth/api-keys \
  -H "Authorization: Bearer {your-token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Integration",
    "scopes": ["read:user"],
    "expires_in_days": 365
  }'
```

Save the returned API key! Use it with `X-API-Key` header.

---

## 📚 Related Guides

Based on **Colabora Project** authentication guides:
- `07a-backend-authentication.md` - Backend auth core
- `07b-authorization-rbac.md` - RBAC & middleware
- `07c-routes-rate-limiting-oauth.md` - Routes & OAuth
- `07f-email-verification-mfa.md` - Email & MFA
- `07g-session-audit-management.md` - Sessions & Audit
- `07h-advanced-features.md` - API Keys, Passwordless, WebAuthn, SSO

---

*Última atualização: 2025-01-31*

