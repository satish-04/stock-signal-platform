# Dockerfile for Stock Signal App

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-client \
    redis-tools \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files first for better caching
COPY pyproject.toml poetry.lock* ./

# Install Poetry dependencies
RUN if [ -f "poetry.lock" ]; then \
    poetry install --no-dev --no-interaction --no-ansi; \
    else \
    pip install --no-cache-dir fastapi uvicorn sqlmodel psycopg2-binary redis python-dotenv pydantic-settings asyncpg; \
    fi

# Copy application code
COPY app/ ./app/
COPY config/ ./config/

# Create non-root user for security
RUN useradd -m -s /bin/bash appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]