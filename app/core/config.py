from functools import lru_cache
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)
    app_env: str = "local"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    database_url: str = "postgresql+asyncpg://signals:signals@postgres:5432/signals"
    redis_url: str = "redis://redis:6379/0"
    trading_mode: Literal["paper", "live"] = "paper"
    market_data_mode: Literal["mock", "ibkr"] = "mock"
    tradingview_webhook_secret: str = Field(min_length=16)
    ai_mode: Literal["mock", "claude"] = "mock"
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-5"
    ibkr_host: str = "host.docker.internal"
    ibkr_port: int = 7497
    ibkr_client_id: int = 41
    ibkr_account: str = ""
    ibkr_news_providers: str = ""
    max_risk_per_trade_pct: float = 0.50
    risk_account_equity: float = 100000.0
    risk_available_funds: float = 50000.0
    max_position_value_pct: float = 2.0
    max_option_contracts: int = 5
    max_option_spread_pct: float = 5.0
    minimum_option_open_interest: int = 1000
    minimum_option_volume: int = 250
    minimum_reward_risk_ratio: float = 2.0
    option_stop_loss_pct: float = 20.0
    option_first_target_pct: float = 40.0
    option_second_target_pct: float = 80.0
    max_daily_loss_pct: float = 1.50
    max_open_positions: int = 5
    signal_ttl_seconds: int = 120
    signal_review_threshold: float = 65.0
    signal_actionable_threshold: float = 80.0
    enable_order_submission: bool = False
    enable_live_trading: bool = False

    def validate_safety(self) -> None:
        if self.signal_review_threshold >= self.signal_actionable_threshold:
            raise RuntimeError("SIGNAL_REVIEW_THRESHOLD must be lower than SIGNAL_ACTIONABLE_THRESHOLD")
        if self.trading_mode == "live" and not self.enable_live_trading:
            raise RuntimeError("Live mode requires ENABLE_LIVE_TRADING=true")
        if self.trading_mode == "live" and not self.enable_order_submission:
            raise RuntimeError("Live mode requires ENABLE_ORDER_SUBMISSION=true")

@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_safety()
    return settings
