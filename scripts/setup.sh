#!/bin/bash

# Setup script for Stock Signal App
set -e

echo "🚀 Setting up Stock Signal App..."

# Create necessary directories
mkdir -p app/core app/db app/models app/schemas app/services app/workers
mkdir -p tests/unit tests/integration config/docs scripts

# Install dependencies if poetry is available
if command -v poetry &> /dev/null; then
    echo "📦 Installing dependencies..."
    poetry install
fi

# Copy .env.example to .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📄 Creating .env file from .env.example..."
    cp .env.example .env
fi

# Create database if using Docker
if [ -f docker-compose.yml ]; then
    echo "🐳 Starting Docker containers..."
    docker-compose up -d postgres redis
fi

echo "✅ Setup complete!"
echo "📝 Edit .env with your credentials"
echo "🚀 Run: docker-compose up -d"
