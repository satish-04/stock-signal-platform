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
    order_intent_store: Literal["memory", "redis"] = "redis"
    order_intent_key_prefix: str = "stock-signal:order-intents"
    order_intent_ttl_seconds: int = 604800
    order_intent_lock_ttl_seconds: int = 300
    order_execution_key_prefix: str = "stock-signal:order-executions"
    order_execution_ttl_seconds: int = 604800
    order_execution_lock_ttl_seconds: int = 300
    position_store: Literal["memory", "redis"] = "redis"
    position_key_prefix: str = "stock-signal:positions"
    position_ttl_seconds: int = 2592000
    position_fill_lock_ttl_seconds: int = 300
    position_exit_store: Literal["memory", "redis"] = "redis"
    position_exit_key_prefix: str = "stock-signal:position-exits"
    position_exit_ttl_seconds: int = 2592000
    position_exit_lock_ttl_seconds: int = 300
    position_stop_loss_pct: float = 20.0
    position_first_target_pct: float = 40.0
    position_second_target_pct: float = 80.0
    position_first_target_exit_pct: float = 50.0
    position_trailing_stop_enabled: bool = True
    position_trailing_activation_pct: float = 30.0
    position_trailing_distance_pct: float = 15.0
    position_max_holding_hours: int = 120
    position_expiration_exit_days: int = 2
    position_stale_mark_seconds: int = 300
    trading_workflow_store: Literal["memory", "redis"] = "redis"
    trading_workflow_key_prefix: str = "stock-signal:trading-workflows"
    trading_workflow_ttl_seconds: int = 2592000
    trading_workflow_lock_ttl_seconds: int = 300
    paper_workflow_auto_create_intent: bool = True
    paper_workflow_require_manual_approval: bool = True
    paper_workflow_auto_submit: bool = False
    paper_workflow_max_attempts: int = 3
    paper_workflow_retry_delay_seconds: int = 30
    background_job_store: Literal["memory", "redis"] = "redis"
    background_job_key_prefix: str = "stock-signal:background-jobs"
    background_job_ttl_seconds: int = 604800
    background_job_lock_ttl_seconds: int = 300
    worker_queue_name: str = "paper-trading"
    worker_max_retries: int = 3
    worker_retry_delay_seconds: int = 30
    workflow_reconciliation_interval_seconds: int = 60
    execution_reconciliation_interval_seconds: int = 30
    position_reconciliation_interval_seconds: int = 30
    exit_monitoring_interval_seconds: int = 60
    stale_workflow_cleanup_interval_seconds: int = 300
    background_automation_enabled: bool = True
    background_sweep_batch_size: int = 100
    background_sweep_stale_workflow_seconds: int = 900
    background_sweep_index_ttl_seconds: int = 2592000
    signal_review_threshold: float = 65.0
    signal_actionable_threshold: float = 80.0
    enable_order_submission: bool = False
    enable_live_trading: bool = False

    def validate_safety(self) -> None:
        if self.background_sweep_batch_size <= 0:
            raise RuntimeError("BACKGROUND_SWEEP_BATCH_SIZE must be greater than zero")
        if self.background_sweep_stale_workflow_seconds <= 0:
            raise RuntimeError("BACKGROUND_SWEEP_STALE_WORKFLOW_SECONDS must be greater than zero")
        if self.background_sweep_index_ttl_seconds <= 0:
            raise RuntimeError("BACKGROUND_SWEEP_INDEX_TTL_SECONDS must be greater than zero")
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
