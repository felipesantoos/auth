# Auth System API

Multi-tenant Authentication and Authorization System built with FastAPI.

## Features

- Multi-tenant architecture (clients with isolated users)
- JWT authentication with refresh tokens
- Role-based access control (RBAC)
- User management per client
- Redis caching
- PostgreSQL database
- Structured logging

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
auth/
├── alembic/              # Database migrations
├── app/                  # Application layer
│   └── api/             # API routes, DTOs, middlewares
├── config/              # Configuration (settings, logging)
├── core/                # Core business logic
│   ├── domain/         # Domain models
│   ├── interfaces/     # Port interfaces
│   └── services/       # Business services
├── infra/              # Infrastructure
│   ├── database/       # Database models, repositories
│   └── redis/         # Redis client and cache
└── main.py            # Application entry point
```

## Architecture

This project follows Hexagonal Architecture (Ports & Adapters) principles:

- **Domain Layer**: Pure business logic, no dependencies
- **Service Layer**: Business use cases, depends on interfaces
- **Infrastructure Layer**: Database, Redis, external services
- **API Layer**: HTTP endpoints, DTOs, validation

