#!/bin/bash
echo "🚀 Starting Production Environment..."
echo ""
echo "⚠️  WARNING: You are about to start the PRODUCTION environment!"
echo "   Make sure you have:"
echo "   - Set all production secrets in .env.production"
echo "   - Configured SSL/HTTPS certificates"
echo "   - Set up proper backups"
echo "   - Configured monitoring (Sentry, etc.)"
echo ""
read -p "Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi
echo ""
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d
echo "✅ Production environment is running!"
echo ""
echo "📋 Useful commands:"
echo "   - View logs: ./scripts/logs.sh prod"
echo "   - Stop: ./scripts/down.sh"
echo ""

