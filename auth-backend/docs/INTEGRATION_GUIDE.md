# 🔧 Guia de Integração - Próximos Passos

## ✅ O Que Já Está Pronto

1. **Domain Layer** (100%) - Todos models com lógica completa
2. **Database Layer** (100%) - Migration + Models + Mappers + Repositories
3. **Services** (60%) - 6 services completos e funcionais
4. **DTOs** (100%) - Todos Request/Response DTOs criados

## ❌ O Que Falta Para Funcionar

### 1. **Criar Routes Restantes** (2-3 horas)

Criar arquivos em `app/api/routes/`:

#### `session_routes.py`
```python
@router.get("/auth/sessions") # List active sessions
@router.delete("/auth/sessions/{session_id}") # Revoke session
@router.delete("/auth/sessions/all") # Revoke all
```

#### `email_verification_routes.py`
```python
@router.post("/auth/verify-email") # Verify email
@router.post("/auth/resend-verification") # Resend
```

#### `api_key_routes.py`
```python
@router.post("/auth/api-keys") # Create
@router.get("/auth/api-keys") # List
@router.delete("/auth/api-keys/{key_id}") # Revoke
```

#### `passwordless_routes.py`
```python
@router.post("/auth/passwordless/send") # Send magic link
@router.post("/auth/passwordless/verify") # Verify & login
```

#### `audit_routes.py`
```python
@router.get("/auth/audit") # User's audit logs
@router.get("/admin/audit") # All audit logs (admin)
@router.get("/admin/audit/security") # Security events (admin)
```

### 2. **Dependency Injection** (1-2 horas)

Atualizar `app/api/dicontainer/dicontainer.py` para injetar os services:

```python
# Add to DIContainer
def get_audit_service(session: AsyncSession) -> AuditService:
    repo = AuditLogRepository(session)
    return AuditService(repository=repo)

def get_mfa_service(session: AsyncSession) -> MFAService:
    user_repo = AppUserRepository(session)
    backup_code_repo = BackupCodeRepository(session)
    settings = get_settings_provider()
    return MFAService(user_repo, backup_code_repo, settings)

# Similar for SessionService, EmailVerificationService, etc.
```

### 3. **ApiKeyAuthMiddleware** (1 hora)

Criar `app/api/middlewares/api_key_middleware.py`:

```python
async def get_current_user_from_api_key(
    api_key: str = Header(None, alias="X-API-Key")
) -> Optional[AppUser]:
    \"\"\"
    Authenticate via API key header.
    
    Used for programmatic API access.
    \"\"\"
    if not api_key or not api_key.startswith("ask_"):
        return None
    
    # Hash and validate key
    api_key_service = get_api_key_service()
    validated_key = await api_key_service.validate_api_key(api_key)
    
    if not validated_key or not validated_key.is_active():
        return None
    
    # Get user
    user_repo = get_user_repository()
    user = await user_repo.find_by_id(
        validated_key.user_id,
        client_id=validated_key.client_id
    )
    
    return user
```

### 4. **Integrar no Login Existente** (CRÍTICO - 2-3 horas)

Atualizar `core/services/auth/auth_service.py` → método `login()`:

```python
async def login(
    self, email: str, password: str, client_id: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Tuple[str, str, AppUser]:
    \"\"\"Login with advanced features\"\"\"
    
    # 1. CHECK ACCOUNT LOCKOUT (BEFORE password validation!)
    if await self.audit_service.detect_brute_force(
        user_id=None, ip_address=ip_address, threshold=5, minutes=30
    ):
        await self.audit_service.log_event(
            client_id=client_id,
            event_type=AuditEventType.LOGIN_FAILED_ACCOUNT_LOCKED,
            ip_address=ip_address,
            status="failure"
        )
        raise BusinessRuleException(
            "Account temporarily locked due to multiple failed attempts",
            "ACCOUNT_LOCKED"
        )
    
    # 2. VALIDATE CREDENTIALS
    try:
        user = await self._validate_login_credentials(email, password, client_id)
    except InvalidCredentialsException:
        # Log failed login
        await self.audit_service.log_event(
            client_id=client_id,
            event_type=AuditEventType.LOGIN_FAILED,
            ip_address=ip_address,
            user_agent=user_agent,
            status="failure",
            metadata={"email": email}
        )
        
        # Increment failed attempts
        if user:
            user.increment_failed_login()
            if user.failed_login_attempts >= 5:
                user.lock_account(duration_minutes=30)
                await self.audit_service.log_event(
                    client_id=client_id,
                    event_type=AuditEventType.ACCOUNT_LOCKED,
                    user_id=user.id,
                    status="warning"
                )
            await self.repository.save(user)
        
        raise
    
    # 3. CHECK IF ACCOUNT IS LOCKED
    if user.is_locked():
        await self.audit_service.log_event(
            client_id=client_id,
            event_type=AuditEventType.LOGIN_FAILED_ACCOUNT_LOCKED,
            user_id=user.id,
            ip_address=ip_address,
            status="failure"
        )
        raise BusinessRuleException(
            "Account is locked. Try again later.",
            "ACCOUNT_LOCKED"
        )
    
    # 4. CHECK EMAIL VERIFICATION (if required)
    if self.settings.require_email_verification and not user.is_email_verified():
        await self.audit_service.log_event(
            client_id=client_id,
            event_type=AuditEventType.LOGIN_FAILED_EMAIL_NOT_VERIFIED,
            user_id=user.id,
            status="failure"
        )
        raise BusinessRuleException(
            "Email not verified. Please check your email.",
            "EMAIL_NOT_VERIFIED"
        )
    
    # 5. CHECK MFA (if enabled)
    if user.has_mfa_enabled():
        # Return special response indicating MFA required
        # Frontend will show MFA input
        return {
            "mfa_required": True,
            "user_id": user.id,
            "challenge_id": "temp_challenge_token"
        }
    
    # 6. RESET FAILED LOGIN ATTEMPTS
    user.reset_failed_login_attempts()
    await self.repository.save(user)
    
    # 7. GENERATE TOKENS
    access_token, refresh_token = await self._generate_and_store_tokens(
        user.id, client_id
    )
    
    # 8. CREATE SESSION
    session = await self.session_service.create_session(
        user_id=user.id,
        client_id=client_id,
        refresh_token=refresh_token,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    # 9. DETECT SUSPICIOUS ACTIVITY
    is_suspicious = await self.audit_service.detect_suspicious_activity(
        user_id=user.id,
        client_id=client_id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if is_suspicious:
        await self.audit_service.log_event(
            client_id=client_id,
            event_type=AuditEventType.SUSPICIOUS_ACTIVITY_DETECTED,
            user_id=user.id,
            ip_address=ip_address,
            status="warning"
        )
        # TODO: Send email notification to user
    
    # 10. LOG SUCCESSFUL LOGIN
    await self.audit_service.log_event(
        client_id=client_id,
        event_type=AuditEventType.LOGIN_SUCCESS,
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
        status="success"
    )
    
    return access_token, refresh_token, user
```

### 5. **MFA Login Flow** (1-2 horas)

Criar endpoint separado para verificação MFA:

```python
@router.post("/auth/login/mfa")
async def login_with_mfa(
    user_id: str,
    totp_code: Optional[str] = None,
    backup_code: Optional[str] = None,
    client_id: str = Header(..., alias="X-Client-ID")
):
    \"\"\"
    Complete login after MFA verification.
    
    User must provide either TOTP code or backup code.
    \"\"\"
    user = await user_repository.find_by_id(user_id, client_id)
    
    if totp_code:
        if not mfa_service.verify_totp(user.mfa_secret, totp_code):
            # Log failed MFA
            await audit_service.log_event(
                client_id=client_id,
                event_type=AuditEventType.MFA_VERIFICATION_FAILED,
                user_id=user_id,
                status="failure"
            )
            raise HTTPException(status_code=401, detail="Invalid TOTP code")
    elif backup_code:
        if not await mfa_service.verify_backup_code_for_user(
            user_id, client_id, backup_code
        ):
            raise HTTPException(status_code=401, detail="Invalid backup code")
        
        # Log backup code usage
        await audit_service.log_event(
            client_id=client_id,
            event_type=AuditEventType.MFA_BACKUP_CODE_USED,
            user_id=user_id,
            status="success"
        )
    else:
        raise HTTPException(status_code=400, detail="TOTP or backup code required")
    
    # Generate tokens and create session (same as normal login)
    # ...
```

### 6. **Registrar Novas Routes** (15 minutos)

Atualizar `main.py`:

```python
from app.api.routes import (
    client_routes,
    auth_routes,
    oauth_routes,
    mfa_routes,      # NEW
    session_routes,   # NEW
    api_key_routes,   # NEW
    # ... etc
)

app.include_router(mfa_routes.router)
app.include_router(session_routes.router)
app.include_router(api_key_routes.router)
# ... etc
```

### 7. **Registrar no Email Service** (30 min)

Verificar se `infra/email/email_service.py` está configurado para SMTP.

---

## 🎯 Ordem de Implementação Recomendada

### Fase 1 - Fazer Funcionar (PRIORITY)
1. ✅ Dependency Injection setup
2. ✅ Criar routes restantes (sessions, email, api_keys, passwordless, audit)
3. ✅ Integrar no login existente (account lockout + audit logging)
4. ✅ Testar fluxo completo

### Fase 2 - MFA
5. ✅ MFA login flow
6. ✅ Testar MFA end-to-end

### Fase 3 - API Keys
7. ✅ ApiKeyAuthMiddleware
8. ✅ Testar autenticação via API key

### Fase 4 - Polimento
9. ✅ Email templates (melhorar)
10. ✅ Testes
11. ✅ Documentação

---

## 📋 Checklist Final

- [ ] Dependency injection configurado
- [ ] Todas as routes criadas e registradas
- [ ] Login integrado com: Audit + Lockout + Sessions
- [ ] MFA login flow funcionando
- [ ] ApiKeyAuthMiddleware criado
- [ ] Email service testado
- [ ] Migrations aplicadas em dev
- [ ] Testes end-to-end
- [ ] Documentação atualizada

---

## 🚀 Como Testar

1. **Aplicar migrations**:
```bash
alembic upgrade head
```

2. **Instalar dependências**:
```bash
pip install -r requirements.txt
```

3. **Configurar `.env`** (copiar de `env.example.txt`)

4. **Rodar servidor**:
```bash
python main.py
```

5. **Testar endpoints** via `/docs`

---

*Última atualização: 2025-01-31*

