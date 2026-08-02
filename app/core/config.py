"""
Application configuration management.
"""

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Trading Configuration
    trading_mode: str = "paper"  # paper, live
    market_data_mode: str = "mock"  # mock, real
    enable_order_submission: bool = False  # Safety switch
    enable_live_trading: bool = False  # Kill switch
    
    # IBKR Configuration
    ibkr_host: str = "localhost"
    ibkr_port: int = 7496
    ibkr_client_id: int = 1
    
    # Claude AI Configuration
    anthropic_api_key: str = ""
    ai_mode: str = "mock"  # mock, claude
    ai_model: str = "claude-3-5-sonnet"
    
    # Database Configuration
    database_url: str = "postgresql://postgres:password@localhost:5432/stock_signal_app"
    database_pool_size: int = 10
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    
    # TradingView Webhook
    webhook_secret: str = ""
    webhook_port: int = 8000
    
    # Logging
    log_level: str = "INFO"
    
    @property
    def is_paper_mode(self) -> bool:
        """Check if paper trading mode is enabled."""
        return self.trading_mode == "paper"
    
    @property
    def is_live_trading_enabled(self) -> bool:
        """Check if live trading is explicitly enabled."""
        return self.enable_live_trading and not self.is_paper_mode
    
    @property
    def is_order_submission_enabled(self) -> bool:
        """Check if order submission is enabled."""
        return self.enable_order_submission and self.is_live_trading_enabled
    
    @property
    def is_mock_mode(self) -> bool:
        """Check if market data mode is mock."""
        return self.market_data_mode == "mock"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
