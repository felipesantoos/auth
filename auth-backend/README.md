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

