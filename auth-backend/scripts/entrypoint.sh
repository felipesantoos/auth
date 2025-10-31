#!/bin/bash
set -e

echo "================================================"
echo "Auth System API - Starting..."
echo "================================================"

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable is not set"
    exit 1
fi

echo "Environment: ${ENVIRONMENT:-development}"
echo "Database URL: ${DATABASE_URL%%@*}@***"  # Hide password in logs

# Wait for database to be ready
echo "Waiting for database to be ready..."
python << END
import sys
import time
import psycopg2
from urllib.parse import urlparse

db_url = "${DATABASE_URL}".replace("postgresql+asyncpg://", "postgresql://").replace("postgresql+psycopg2://", "postgresql://")
result = urlparse(db_url)

max_attempts = 30
attempt = 0

while attempt < max_attempts:
    try:
        conn = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port or 5432
        )
        conn.close()
        print("Database is ready!")
        sys.exit(0)
    except psycopg2.OperationalError as e:
        attempt += 1
        if attempt >= max_attempts:
            print(f"ERROR: Could not connect to database after {max_attempts} attempts")
            print(f"Error: {e}")
            sys.exit(1)
        print(f"Database not ready yet (attempt {attempt}/{max_attempts}), waiting...")
        time.sleep(2)
END

# Check wait-for-db exit code
if [ $? -ne 0 ]; then
    echo "Failed to connect to database"
    exit 1
fi

# Run database migrations
echo ""
echo "Running database migrations..."
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✓ Migrations completed successfully"
else
    echo "✗ Migration failed!"
    exit 1
fi

echo ""
echo "================================================"
echo "Starting application..."
echo "================================================"
echo ""

# Execute the main command (passed as arguments to the script)
exec "$@"

