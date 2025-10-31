# Auth System Frontend

Frontend React TypeScript para o sistema de autenticação multi-tenant.

## Setup

1. Instalar dependências:
```bash
npm install
```

2. Criar arquivo `.env`:
```bash
cp .env.example .env
```

3. Configurar variáveis no `.env`:
```
VITE_API_BASE_URL=http://localhost:8080
```

4. Executar em desenvolvimento:
```bash
npm run dev
```

## Estrutura

```
src/
├── core/
│   ├── domain/          # Modelos TypeScript
│   ├── repositories/    # Chamadas API
│   └── services/        # Lógica de negócio
└── app/
    ├── components/      # Componentes React
    ├── contexts/        # Context providers
    ├── pages/          # Páginas
    └── hooks/          # Custom hooks
```

## Funcionalidades

- Login/Registro com suporte multi-tenant
- Auto-refresh de tokens
- Rotas protegidas
- Context de autenticação global
