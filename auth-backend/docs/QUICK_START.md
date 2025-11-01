# 🚀 Quick Start - Advanced Auth Features

## Início Rápido em 5 Minutos

### 1. Aplicar Migrations (1 min)

```bash
cd auth-backend
alembic upgrade head
```

Cria 5 novas tabelas e adiciona campos no `app_user`.

### 2. Instalar Dependências (2 min)

```bash
pip install -r requirements.txt
```

### 3. Configurar Environment (1 min)

Crie arquivo `.env`:

```bash
# Copie de env.example.txt ou use o mínimo:

DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/auth_system"
REDIS_HOST="localhost"
JWT_SECRET="change-this-to-random-32-chars"

# Para email funcionar (opcional)
SMTP_HOST="smtp.gmail.com"
SMTP_USER="your-email@gmail.com"
SMTP_PASSWORD="your-app-password"
```

### 4. Rodar Servidor (30 seg)

```bash
python main.py
```

### 5. Testar! (30 seg)

Acesse: **http://localhost:8080/docs**

---

## 🎯 Fluxo de Teste Completo

### Teste 1: Autenticação Básica

```bash
# 1. Register
POST /api/auth/register
{
  "username": "johndoe",
  "email": "john@test.com",
  "password": "SecurePass123!",
  "name": "John Doe",
  "client_id": "default"
}

# 2. Login
POST /api/auth/login
{
  "email": "john@test.com",
  "password": "SecurePass123!",
  "client_id": "default"
}
# ✅ Retorna: access_token, refresh_token

# 3. Get Profile
GET /api/auth/me
# Header: Authorization: Bearer {access_token}
```

### Teste 2: MFA/2FA

```bash
# 1. Setup MFA
POST /auth/mfa/setup
# Header: Authorization: Bearer {token}
# ✅ Retorna: QR code, secret, backup codes

# 2. Scan QR code com Google Authenticator

# 3. Enable MFA
POST /auth/mfa/enable
{
  "secret": "JBSWY3DPEHPK3PXP",
  "totp_code": "123456",
  "backup_codes": ["1234-5678-9012", ...]
}

# 4. Login agora requer MFA
POST /api/auth/login
# ✅ Retorna: { "mfa_required": true, "user_id": "..." }

# 5. Complete login com TOTP
POST /api/auth/login/mfa
{
  "user_id": "...",
  "client_id": "default",
  "totp_code": "123456"
}
# ✅ Retorna: access_token, refresh_token
```

### Teste 3: Session Management

```bash
# 1. List active sessions
GET /auth/sessions
# ✅ Shows: device, IP, location, last activity

# 2. Logout from specific device
DELETE /auth/sessions/{session-id}

# 3. Logout from all devices
DELETE /auth/sessions/all
```

### Teste 4: API Keys

```bash
# 1. Create API Key
POST /auth/api-keys
{
  "name": "My Integration",
  "scopes": ["read:user", "write:user"],
  "expires_in_days": 365
}
# ✅ Returns: api_key (SAVE IT!)

# 2. Use API Key
GET /api/auth/me
# Header: X-API-Key: ask_your_key_here
# ✅ Works! No JWT needed

# 3. List keys
GET /auth/api-keys

# 4. Revoke key
DELETE /auth/api-keys/{key-id}
```

### Teste 5: Passwordless Auth

```bash
# 1. Send magic link
POST /auth/passwordless/send
{
  "email": "john@test.com",
  "client_id": "default"
}
# ✅ Email sent with login link

# 2. Login with magic link
POST /auth/passwordless/verify
{
  "user_id": "...",
  "token": "magic-link-token",
  "client_id": "default"
}
# ✅ Returns: access_token, refresh_token
```

### Teste 6: Audit Logs

```bash
# 1. View your activity
GET /auth/audit?days=7

# 2. Admin: View all logs
GET /admin/audit?days=30

# 3. Admin: Security events only
GET /admin/audit/security
# ✅ Shows: failed logins, lockouts, suspicious activity
```

---

## 📊 Endpoints Disponíveis

**Total: 29 endpoints**

### Auth Básico (10)
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/login/mfa ⚡ NOVO
- POST /api/auth/refresh
- POST /api/auth/logout
- POST /api/auth/change-password
- GET /api/auth/me
- POST /api/auth/forgot-password
- POST /api/auth/reset-password
- GET /api/auth/users (admin)

### MFA (5) ⚡ NOVO
- POST /auth/mfa/setup
- POST /auth/mfa/enable
- POST /auth/mfa/disable
- GET /auth/mfa/status
- POST /auth/mfa/backup-codes/regenerate

### Sessions (3) ⚡ NOVO
- GET /auth/sessions
- DELETE /auth/sessions/{id}
- DELETE /auth/sessions/all

### Email Verification (3) ⚡ NOVO
- POST /auth/email/verify
- POST /auth/email/resend-verification
- GET /auth/email/status

### API Keys (3) ⚡ NOVO
- POST /auth/api-keys
- GET /auth/api-keys
- DELETE /auth/api-keys/{id}

### Passwordless (2) ⚡ NOVO
- POST /auth/passwordless/send
- POST /auth/passwordless/verify

### Audit (3) ⚡ NOVO
- GET /auth/audit
- GET /admin/audit
- GET /admin/audit/security

---

## 🔥 Features Automáticas

Quando você faz login agora, **automaticamente** acontece:

1. ✅ Verificação de brute-force (IP)
2. ✅ Verificação de account lockout
3. ✅ Verificação de email (se habilitado)
4. ✅ Detecção de MFA (redireciona se necessário)
5. ✅ Criação de sessão (tracking device)
6. ✅ Detecção de atividade suspeita
7. ✅ Audit logging (LOGIN_SUCCESS)

---

## 🛡️ Segurança Automática

- ✅ **Brute-force**: Bloqueia após 5 tentativas (IP-based)
- ✅ **Account Lockout**: Lock por 30 minutos após falhas
- ✅ **Audit**: Todos eventos registrados automaticamente
- ✅ **Session Limit**: Máximo 10 devices (revoga oldest)
- ✅ **Token Expiry**: Access 30min, Refresh 7 days
- ✅ **Rate Limiting**: Login 5/min, Register 3/min

---

## ⚙️ Configurações Opcionais

### Habilitar Email Verification

```bash
# .env
REQUIRE_EMAIL_VERIFICATION=true
```

Agora registro bloqueará login até email ser verificado.

### Ajustar Limites de Segurança

```bash
# .env
MAX_LOGIN_ATTEMPTS=3  # Default: 5
ACCOUNT_LOCKOUT_DURATION_MINUTES=60  # Default: 30
SESSION_MAX_DEVICES=5  # Default: 10
```

### Configurar MFA

```bash
# .env
MFA_ISSUER_NAME="Your App"  # Aparece no Google Authenticator
MFA_BACKUP_CODES_COUNT=10  # Número de backup codes
```

---

## 📖 Documentação Completa

- **AUTHENTICATION.md** - Guia completo de todas features
- **INTEGRATION_GUIDE.md** - Detalhes de implementação
- **COMPLETE_IMPLEMENTATION.md** - Status final

---

## 🎉 Pronto!

Seu sistema agora tem:
- ✅ Email Verification
- ✅ MFA/2FA
- ✅ Session Management
- ✅ Audit Logging
- ✅ API Keys
- ✅ Passwordless Auth
- ✅ Account Security

**Tudo funcionando e integrado!** 🚀

---

*Need help? Check AUTHENTICATION.md for detailed guides*

