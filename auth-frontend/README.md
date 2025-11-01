# Auth System Frontend

Frontend React + TypeScript para o sistema de autenticação multi-tenant com **Arquitetura Hexagonal**.

## 🏗️ Arquitetura Hexagonal (Ports & Adapters)

Este projeto implementa **Hexagonal Architecture** no frontend, proporcionando:

### Benefícios:
- ✅ **Desacoplamento**: Camadas independentes e intercambiáveis
- ✅ **Testabilidade**: Testes unitários sem dependências externas
- ✅ **Manutenibilidade**: Código organizado e fácil de entender
- ✅ **Escalabilidade**: Adicionar features sem impactar outras camadas
- ✅ **Consistência**: Mesma arquitetura do backend

### Estrutura de Camadas:

```
src/
├── core/                       # 🎯 DOMAIN (Centro do Hexágono)
│   ├── domain/                # Entidades de negócio puras
│   │   ├── user.ts           # User domain model
│   │   └── token.ts          # Token domain model
│   ├── interfaces/
│   │   ├── primary/          # Portas de entrada (Use Cases)
│   │   │   └── IAuthService.ts
│   │   └── secondary/        # Portas de saída (Repositories)
│   │       ├── IAuthRepository.ts
│   │       ├── IHttpClient.ts
│   │       ├── IStorage.ts
│   │       └── ILogger.ts
│   └── services/             # Lógica de negócio
│       └── auth/
│           ├── authService.ts
│           └── __tests__/
│
├── infra/                     # 🔌 SECONDARY ADAPTERS
│   ├── api/
│   │   ├── dtos/             # Contratos da API
│   │   │   └── auth.dto.ts
│   │   ├── mappers/          # DTO ↔ Domain transformations
│   │   │   ├── user.mapper.ts
│   │   │   └── __tests__/
│   │   ├── repositories/     # Implementações HTTP
│   │   │   └── auth.repository.ts
│   │   └── http-client.ts    # HTTP client implementation
│   ├── storage/              # Storage implementations
│   │   └── local-storage.ts
│   └── logger/               # Logging infrastructure
│       └── console-logger.ts
│
└── app/                       # 🖥️ PRIMARY ADAPTERS
    ├── components/           # UI Components
    │   └── ui/              # shadcn/ui components
    │       ├── button.tsx
    │       ├── input.tsx
    │       ├── card.tsx
    │       ├── label.tsx
    │       ├── alert.tsx
    │       └── dialog.tsx
    ├── contexts/            # State management (React Context)
    │   └── AuthContext.tsx
    ├── pages/               # Route pages
    │   ├── Login.tsx
    │   ├── Register.tsx
    │   ├── Dashboard.tsx
    │   ├── ForgotPassword.tsx
    │   ├── ResetPassword.tsx
    │   └── __tests__/
    ├── hooks/               # Custom hooks
    │   ├── useAuthMutations.ts
    │   └── useCurrentUser.ts
    ├── schemas/             # Zod validation schemas
    │   └── auth.schema.ts
    ├── providers/           # React providers
    │   └── QueryProvider.tsx
    └── dicontainer/         # Dependency Injection Container
        └── container.ts
```

### Fluxo de Dados:

```
UI Component → Context → Service (via DI) → Repository → HTTP Client → API
    ↓             ↓          ↓                  ↓            ↓
  React      Adapter   Use Case          Adapter      Axios
```

---

## 🚀 Setup

### Pré-requisitos

- Node.js 18+
- npm ou yarn

### Instalação

1. **Instalar dependências**:
```bash
npm install
```

2. **Criar arquivo `.env`**:
```bash
cp .env.example .env
```

3. **Configurar variáveis no `.env`**:
```
VITE_API_BASE_URL=http://localhost:8080
```

4. **Executar em desenvolvimento**:
```bash
npm run dev
```

5. **Build para produção**:
```bash
npm run build
```

6. **Preview da build**:
```bash
npm run preview
```

---

## 🧪 Testing

### Executar Testes

```bash
# Rodar todos os testes
npm test

# Rodar com UI
npm run test:ui

# Rodar com coverage
npm run test:coverage
```

### Estrutura de Testes

Testes organizados por camada:

- **Domain Tests**: `src/core/domain/__tests__/` - Testa lógica de negócio
- **Service Tests**: `src/core/services/**/__tests__/` - Testa use cases com mocks
- **Mapper Tests**: `src/infra/api/mappers/__tests__/` - Testa transformações
- **Component Tests**: `src/app/pages/__tests__/` - Testa UI e interações

---

## 📦 Tecnologias

### Core
- **React 19** - UI Library
- **TypeScript 5.9** - Type safety
- **Vite 7** - Build tool & dev server

### Arquitetura
- **Dependency Injection** - Singleton container
- **Ports & Adapters** - Hexagonal architecture
- **DTOs & Mappers** - Data transformation

### State Management
- **React Context API** - Primary adapters
- **React Query 5** (@tanstack/react-query) - Server state
- **React Hook Form 7** - Form state
- **Zod 4** - Schema validation

### UI Components
- **Tailwind CSS 3.4** - Utility-first CSS
- **Radix UI** - Headless UI primitives
- **Lucide React** - Icon library
- **shadcn/ui** - Component patterns
- **@tanstack/react-table 8** - Table component
- **date-fns 3.6** - Date utilities

### HTTP & Data
- **Axios 1.13** - HTTP client with interceptors

### Testing
- **Vitest 4** - Test runner
- **@testing-library/react 16** - Component testing
- **happy-dom** - DOM environment

---

## 🎯 Funcionalidades

### Core Features
- ✅ Login/Registro com suporte multi-tenant
- ✅ Auto-refresh de tokens (interceptors)
- ✅ Rotas protegidas
- ✅ Context de autenticação global
- ✅ OAuth2 (Google, GitHub)
- ✅ Password reset flow
- ✅ Email verification
- ✅ Two-Factor Authentication (MFA)

### Advanced Features
- ✅ Form validation com Zod
- ✅ Server state caching com React Query
- ✅ Modern UI com Tailwind + shadcn/ui
- ✅ Type-safe com TypeScript
- ✅ Unit e integration testing
- ✅ Error handling por camada
- ✅ Logging infrastructure

---

## 🏛️ Dependency Injection

### Como Funciona

O **DI Container** gerencia todas as instâncias de serviços e suas dependências:

```typescript
// 1. Inicialização (main.tsx)
DIContainer.init('http://localhost:8080');

// 2. Uso em Contexts
const authService = DIContainer.getAuthService();

// 3. Uso em Hooks
const authService = DIContainer.getAuthService();
const user = await authService.login(credentials);

// 4. Reset (para testes)
DIContainer.reset();
```

### Benefícios do DI Container

- ✅ **Singleton pattern**: Uma única instância de cada serviço
- ✅ **Lazy initialization**: Instâncias criadas sob demanda
- ✅ **Testability**: Fácil de mockar serviços em testes
- ✅ **Dependency resolution**: Container resolve todas as dependências

---

## 🎨 UI Components (shadcn/ui)

### Componentes Disponíveis

- `<Button>` - Botões com variants (default, destructive, outline, etc.)
- `<Input>` - Inputs com labels e mensagens de erro
- `<Card>` - Cards para layout
- `<Label>` - Labels para formulários
- `<Alert>` - Alertas de sucesso/erro
- `<Dialog>` - Modais com Radix UI

### Exemplo de Uso

```tsx
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';

<Card>
  <CardHeader>
    <CardTitle>Título do Card</CardTitle>
  </CardHeader>
  <CardContent>
    <Input label="Email" type="email" {...register('email')} error={errors.email?.message} />
    <Button loading={isPending}>Enviar</Button>
  </CardContent>
</Card>
```

---

## 📋 Form Validation (React Hook Form + Zod)

### Exemplo Completo

```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { loginSchema, LoginFormData } from '../schemas/auth.schema';

const { register, handleSubmit, formState: { errors } } = useForm<LoginFormData>({
  resolver: zodResolver(loginSchema),
});

const onSubmit = (data: LoginFormData) => {
  loginMutation.mutate(data);
};

<form onSubmit={handleSubmit(onSubmit)}>
  <Input {...register('email')} error={errors.email?.message} />
  <Input type="password" {...register('password')} error={errors.password?.message} />
  <Button type="submit">Login</Button>
</form>
```

---

## 🔄 React Query Hooks

### Custom Hooks Disponíveis

```typescript
// Mutations
const loginMutation = useLogin();
const registerMutation = useRegister();
const logoutMutation = useLogout();
const forgotPasswordMutation = useForgotPassword();
const resetPasswordMutation = useResetPassword();

// Queries
const { data: user, isLoading } = useCurrentUser();
```

### Uso em Componentes

```tsx
const loginMutation = useLogin();

const handleLogin = async (data: LoginFormData) => {
  await loginMutation.mutateAsync(data);
  navigate('/dashboard');
};

<Button loading={loginMutation.isPending}>
  Login
</Button>

{loginMutation.isError && (
  <Alert variant="destructive">
    {loginMutation.error.message}
  </Alert>
)}
```

---

## 🧩 Padrões Arquiteturais

### 1. Domain Models (Entidades Puras)

```typescript
// core/domain/user.ts
export class User {
  constructor(
    public readonly id: string,
    public readonly email: string,
    // ...
  ) {}

  isAdmin(): boolean {
    return this.role === 'admin';
  }
}
```

### 2. DTOs (Contratos da API)

```typescript
// infra/api/dtos/auth.dto.ts
export interface UserResponseDTO {
  id: string;
  email: string;
  created_at: string; // API format
}
```

### 3. Mappers (Transformações)

```typescript
// infra/api/mappers/user.mapper.ts
export class UserMapper {
  static toDomain(dto: UserResponseDTO): User {
    return new User(
      dto.id,
      dto.email,
      new Date(dto.created_at) // Transform to Date
    );
  }
}
```

### 4. Repositories (Acesso a Dados)

```typescript
// infra/api/repositories/auth.repository.ts
export class AuthRepository implements IAuthRepository {
  constructor(private httpClient: IHttpClient) {}

  async login(credentials: LoginDTO): Promise<TokenResponseDTO> {
    return this.httpClient.post('/api/auth/login', credentials);
  }
}
```

### 5. Services (Lógica de Negócio)

```typescript
// core/services/auth/authService.ts
export class AuthService implements IAuthService {
  constructor(
    private repository: IAuthRepository,
    private storage: IStorage,
    private logger: ILogger
  ) {}

  async login(credentials: LoginDTO): Promise<User> {
    const response = await this.repository.login(credentials);
    const user = UserMapper.toDomain(response.user);
    this.storage.setItem('user', JSON.stringify(user));
    return user;
  }
}
```

---

## 📖 Guias Relacionados

Para entender melhor a arquitetura hexagonal e padrões implementados:

- **[08a-frontend-architecture.md](../colabora/guides%20%26%20docs/08a-frontend-architecture.md)** - Arquitetura hexagonal
- **[08b-state-management.md](../colabora/guides%20%26%20docs/08b-state-management.md)** - State management
- **[08c-react-best-practices.md](../colabora/guides%20%26%20docs/08c-react-best-practices.md)** - React best practices
- **[08d-ui-components.md](../colabora/guides%20%26%20docs/08d-ui-components.md)** - UI components
- **[08e-frontend-testing.md](../colabora/guides%20%26%20docs/08e-frontend-testing.md)** - Testing strategies

---

## 🔑 Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
VITE_API_BASE_URL=http://localhost:8080
```

---

## 🎨 Customização do Tailwind

Edite `tailwind.config.js` para personalizar cores, fontes, etc:

```javascript
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: '#3b82f6',
        // ...
      },
    },
  },
  plugins: [],
}
```

---

## 🐛 Debugging

### React Query Devtools

As devtools do React Query estão ativadas em desenvolvimento. Clique no ícone no canto inferior da tela para:
- Ver queries ativas
- Invalidar cache manualmente
- Debugar mutations
- Ver estado de loading

### Logger

O logger está configurado para mostrar logs no console em desenvolvimento:

```typescript
const logger = DIContainer.getLogger();
logger.info('Mensagem informativa');
logger.error('Erro', error);
logger.debug('Debug info'); // Apenas em dev
```

---

## 📊 Scripts Disponíveis

| Script | Descrição |
|--------|-----------|
| `npm run dev` | Inicia servidor de desenvolvimento |
| `npm run build` | Build para produção |
| `npm run preview` | Preview da build |
| `npm run lint` | Executa ESLint |
| `npm test` | Executa testes |
| `npm run test:ui` | Testes com UI interativa |
| `npm run test:coverage` | Testes com relatório de cobertura |

---

## 🔐 Segurança

### Token Refresh Automático

O HTTP Client possui interceptors que automaticamente:
1. Adicionam token de acesso a todas as requisições
2. Interceptam erros 401 (não autorizado)
3. Tentam renovar o token usando refresh token
4. Reenviam requisição original com novo token
5. Redirecionam para login se refresh falhar

### Storage Seguro

Tokens são armazenados em `localStorage` com:
- Limpeza automática no logout
- Validação antes de cada uso
- Remoção em caso de erro de autenticação

---

## 🎯 Boas Práticas

### 1. Sempre Use Interfaces

```typescript
// ❌ ERRADO: Depender de implementação concreta
const repository = new AuthRepository();

// ✅ CORRETO: Depender de interface
const repository: IAuthRepository = DIContainer.getAuthRepository();
```

### 2. Use Mappers Para Transformações

```typescript
// ❌ ERRADO: Usar DTO diretamente na UI
const user = apiResponse.user;

// ✅ CORRETO: Transformar DTO em Domain
const user = UserMapper.toDomain(apiResponse.user);
```

### 3. Validate com Zod

```typescript
// ❌ ERRADO: Validação manual
if (!email.includes('@')) { ... }

// ✅ CORRETO: Schema Zod
const schema = z.object({
  email: z.string().email(),
});
```

### 4. Use React Query Para Server State

```typescript
// ❌ ERRADO: useState para dados do servidor
const [user, setUser] = useState(null);

// ✅ CORRETO: React Query
const { data: user, isLoading } = useCurrentUser();
```

---

## 🔗 Integração com Backend

Este frontend se conecta ao backend em `auth-backend/` que também usa arquitetura hexagonal.

### Endpoints Disponíveis

Veja a documentação completa da API em:
- Swagger: `http://localhost:8080/docs`
- Backend README: `../auth-backend/README.md`

---

## 📚 Próximos Passos

1. Explore os arquivos em `src/core/domain/` para entender os modelos
2. Veja `src/core/services/` para entender a lógica de negócio
3. Verifique `src/infra/api/` para entender integração com API
4. Estude `src/app/pages/Login.tsx` para ver exemplo completo
5. Execute `npm test` para ver testes em ação

---

## 🤝 Contribuindo

Ao adicionar novas features, siga a arquitetura:

1. **Domain**: Defina entidade em `core/domain/`
2. **Interfaces**: Crie ports em `core/interfaces/`
3. **Service**: Implemente lógica em `core/services/`
4. **Repository**: Implemente em `infra/api/repositories/`
5. **DTO**: Defina contrato em `infra/api/dtos/`
6. **Mapper**: Crie transformações em `infra/api/mappers/`
7. **DI**: Adicione factory no `DIContainer`
8. **UI**: Crie componentes em `app/components/`
9. **Tests**: Adicione testes em `__tests__/`

---

## 📄 Licença

Este projeto é parte do sistema de autenticação multi-tenant.

---

## 🆘 Suporte

Para dúvidas sobre a arquitetura, consulte os guias em `../colabora/guides & docs/`.
