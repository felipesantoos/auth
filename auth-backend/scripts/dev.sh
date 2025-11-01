#!/bin/bash
echo "🚀 Starting Development Environment..."

# Export environment variables from .env.development
set -a
source .env.development
set +a

docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
echo "✅ Development environment is running!"
echo ""
echo "📝 Services:"
echo "   - API: http://localhost:8080"
echo "   - API Docs: http://localhost:8080/docs"
echo "   - PostgreSQL: localhost:5432"
echo "   - Redis: localhost:6379"
echo ""
echo "📋 Useful commands:"
echo "   - View logs: ./scripts/logs.sh"
echo "   - Stop: ./scripts/down.sh"
echo "   - Access database: docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec postgres psql -U postgres -d auth_system"
echo "   - Run migrations: source .env.development && docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec api alembic upgrade head"
echo ""

