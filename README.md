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

- ✅ Multi-tenant (clientes isolados)
- ✅ JWT + Refresh Tokens
- ✅ Redis token storage
- ✅ Role-Based Access Control (RBAC)
- ✅ User management por cliente
- ✅ Frontend React TypeScript completo

## Próximos Passos

- Email Verification
- Two-Factor Authentication (2FA/MFA)
- Session Management
- Audit Logging
- OAuth2 Integration
- E muito mais...

