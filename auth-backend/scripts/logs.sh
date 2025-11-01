#!/bin/bash
ENV=${1:-dev}

if [ "$ENV" = "dev" ]; then
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f
elif [ "$ENV" = "staging" ]; then
    docker-compose -f docker-compose.yml -f docker-compose.staging.yml logs -f
elif [ "$ENV" = "prod" ]; then
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
else
    echo "Usage: ./scripts/logs.sh [dev|staging|prod]"
    echo "Default: dev"
    exit 1
fi

