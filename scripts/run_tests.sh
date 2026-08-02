#!/bin/bash

# Test runner script for Stock Signal App
# Run tests using Docker Compose or directly with pytest

set -e

echo "=========================================="
echo "Stock Signal App Test Runner"
echo "=========================================="

# Parse arguments
RUN_INTEGRATION=false
RUN_UNIT=true

for arg in "$@"; do
    case $arg in
        --integration)
            RUN_INTEGRATION=true
            ;;
    esac
done

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "⚠️ Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Start services if running integration tests
if [ "$RUN_INTEGRATION" = true ]; then
    echo "🚀 Starting Docker services..."
    docker-compose up -d postgres redis
    
    # Wait for services to be ready
    echo "⏳ Waiting for services..."
    sleep 5
    
    # Run database migrations
    echo "🔄 Running database migrations..."
    docker-compose exec -T api python -m app.db.migrate
fi

# Run tests using Docker Compose
echo "🧪 Running tests..."
docker-compose run --rm api pytest tests/

# Cleanup
if [ "$RUN_INTEGRATION" = true ]; then
    echo "🛑 Stopping services..."
    docker-compose down -v
fi

echo "=========================================="
echo "✅ Tests completed!"
echo "=========================================="
