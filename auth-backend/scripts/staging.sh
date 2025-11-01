#!/bin/bash
echo "🚀 Starting Staging Environment..."
docker-compose -f docker-compose.yml -f docker-compose.staging.yml --env-file .env.staging up -d
echo "✅ Staging environment is running!"
echo ""
echo "📋 Useful commands:"
echo "   - View logs: ./scripts/logs.sh staging"
echo "   - Stop: ./scripts/down.sh"
echo ""

