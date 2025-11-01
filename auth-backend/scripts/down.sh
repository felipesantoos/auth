#!/bin/bash
echo "🛑 Stopping all environments..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down 2>/dev/null || true
docker-compose -f docker-compose.yml -f docker-compose.staging.yml down 2>/dev/null || true
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down 2>/dev/null || true
echo "✅ All environments stopped!"

