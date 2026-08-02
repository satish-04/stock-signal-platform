"""
Stock Signal App - Main Application.

A local-first, paper-trading-by-default platform that combines
TradingView technical alerts, IBKR market/options data,
Claude AI news interpretation, deterministic options selection,
and risk controls.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware

from app.core.config import get_settings, Settings
from app.core.errors import AppError


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    settings = get_settings()
    print(f"[{settings.trading_mode.upper()} MODE] Starting Stock Signal App")
    
    yield
    
    # Shutdown
    print("Shutting down Stock Signal App")


app = FastAPI(
    title="Stock Signal App",
    description="""
A local-first, paper-trading-by-default platform that combines
TradingView technical alerts, IBKR market/options data,
Claude AI news interpretation, deterministic options selection,
and risk controls.
""",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check(settings: Settings = get_settings()):
    """
    Health check endpoint.
    
    Returns the status of all system components.
    """
    return {
        "status": "healthy",
        "trading_mode": settings.trading_mode,
        "market_data_mode": settings.market_data_mode,
    }


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.
    
    Returns basic application information.
    """
    return {
        "name": "Stock Signal App",
        "version": "0.1.0",
        "description": """
        AI-powered automated trading platform.
        
        Note: This is a paper-trading platform by default.
        No real orders will be submitted without explicit configuration.
        """,
    }


# Include API routers
from app.api.v1 import signals, options, portfolio, trades, scanner

app.include_router(signals.router)
app.include_router(options.router)
app.include_router(portfolio.router)
app.include_router(trades.router)
app.include_router(scanner.router)


@app.exception_handler(AppError)
async def app_exception_handler(request, exc: AppError):
    """
    Handle application errors.
    
    Converts custom exceptions to proper HTTP responses.
    """
    return {
        "error": True,
        "error_type": exc.__class__.__name__,
        "message": str(exc),
    }


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.log_level == "DEBUG",
    )