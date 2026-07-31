from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from app.api.routes import (
    ai,
    analysis,
    dev,
    health,
    historical,
    options,
    signals,
    technical_signals,
    webhooks,
)
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import engine
from app.models import entities  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(title="Stock Signal Platform", version="0.2.0", lifespan=lifespan)
app.include_router(health.router)
app.include_router(webhooks.router)
app.include_router(dev.router)
app.include_router(signals.router)
app.include_router(historical.router)
app.include_router(analysis.router)
app.include_router(technical_signals.router)
app.include_router(ai.router)
app.include_router(options.router)
app.mount("/metrics", make_asgi_app())
