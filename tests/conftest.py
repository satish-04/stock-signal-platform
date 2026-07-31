import os

os.environ.setdefault("TRADINGVIEW_WEBHOOK_SECRET", "test-webhook-secret-123456")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://signals:signals@postgres:5432/signals")
os.environ.setdefault("REDIS_URL", "redis://redis:6379/0")
