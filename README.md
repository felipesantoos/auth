# Auth System

Sistema completo de autenticação e autorização multi-tenant com backend Python (FastAPI) e frontend React TypeScript.

## Estrutura do Projeto

```
auth/
├── auth-backend/    # Backend Python FastAPI
└── auth-frontend/   # Frontend React TypeScript
```

## Backend

Ver [auth-backend/README.md](auth-backend/README.md) para instruções do backend.

## Frontend

Ver [auth-frontend/README.md](auth-frontend/README.md) para instruções do frontend.

## Quick Start

### Backend

```bash
cd auth-backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Configure suas variáveis
alembic upgrade head
python main.py
```

### Frontend

```bash
cd auth-frontend
npm install
cp .env.example .env  # Configure VITE_API_BASE_URL
npm run dev
```

## Features

### Core Features ✅
- ✅ Multi-tenant (clientes isolados)
- ✅ JWT + Refresh Tokens
- ✅ Redis token storage
- ✅ Role-Based Access Control (RBAC)
- ✅ User management por cliente
- ✅ OAuth2 Integration (Google, GitHub)
- ✅ Frontend React TypeScript completo

### Advanced Authentication Features ✅ NOVO!
- ✅ **Email Verification** - Verificação de email com tokens seguros
- ✅ **Two-Factor Authentication (MFA/2FA)** - TOTP + QR codes + backup codes
- ✅ **Session Management** - Tracking multi-device com logout remoto
- ✅ **Audit Logging** - 70+ tipos de eventos de segurança
- ✅ **Account Lockout** - Proteção contra brute-force
- ✅ **API Keys** - Personal Access Tokens com scoped permissions
- ✅ **Passwordless Auth** - Magic links via email
- ✅ **Suspicious Activity Detection** - Alertas automáticos

### Enterprise Features (Estrutura Pronta) ⏳
- ⏳ WebAuthn/Passkeys (biometric auth)
- ⏳ SAML 2.0 (Enterprise SSO)
- ⏳ OIDC (OpenID Connect)
- ⏳ LDAP/Active Directory

---

## 🚀 Quick Start

**NOVO**: Leia [`auth-backend/START_HERE.md`](auth-backend/START_HERE.md) para setup em 3 passos!

---

## 📊 Status da Implementação

**Backend**: 90% completo (todas features core funcionais)  
**Frontend**: Básico implementado  
**Total Endpoints**: 29  
**Total Services**: 6 enterprise-grade  
**Documentação**: 11 documentos completos

Veja [`auth-backend/FINAL_IMPLEMENTATION.md`](auth-backend/FINAL_IMPLEMENTATION.md) para detalhes completos.

