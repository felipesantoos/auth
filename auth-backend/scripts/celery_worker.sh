#!/bin/bash
# Celery Worker Script
# Starts Celery worker for background email tasks

set -e

echo "🚀 Starting Celery Worker..."

# Navigate to project root
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start Celery worker
celery -A infra.celery.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --max-tasks-per-child=100 \
    --prefetch-multiplier=1

echo "✅ Celery Worker stopped"

