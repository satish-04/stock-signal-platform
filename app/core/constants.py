"""Constants for stock trading application."""

from enum import Enum
from typing import Final

# Timeframes
TIMEFRAME_1_MIN: Final[str] = "1min"
TIMEFRAME_5_MIN: Final[str] = "5min"
TIMEFRAME_15_MIN: Final[str] = "15min"
TIMEFRAME_1_HOUR: Final[str] = "1h"
TIMEFRAME_4_HOURS: Final[str] = "4h"
TIMEFRAME_1_DAY: Final[str] = "1d"

# Signal Types
SIGNAL_BULLISH: Final[str] = "bullish"
SIGNAL_BEARISH: Final[str] = "bearish"
SIGNAL_NEUTRAL: Final[str] = "neutral"

# Option Types
OPTION_CALL: Final[str] = "C"
OPTION_PUT: Final[str] = "P"

# Trade Directions
DIRECTION_LONG: Final[str] = "long"
DIRECTION_SHORT: Final[str] = "short"

# Order Types
ORDER_TYPE_MARKET: Final[str] = "MKT"
ORDER_TYPE_LIMIT: Final[str] = "LMT"
ORDER_TYPE_STOP: Final[str] = "STP"

# Position Status
POSITION_STATUS_OPEN: Final[str] = "open"
POSITION_STATUS_CLOSED: Final[str] = "closed"

# Trade Status
TRADE_STATUS_PENDING: Final[str] = "pending"
TRADE_STATUS_APPROVED: Final[str] = "approved"
TRADE_STATUS_EXECUTED: Final[str] = "executed"
TRADE_STATUS_FAILED: Final[str] = "failed"

# Confidence Scores
CONFIDENCE_HIGH: Final[float] = 0.8
CONFIDENCE_MEDIUM: Final[float] = 0.5
CONFIDENCE_LOW: Final[float] = 0.3

# Risk Constants
MAX_DAILY_LOSS_PERCENT: Final[float] = 2.0  # 2% daily loss limit
MAX_POSITION_PERCENT: Final[float] = 5.0  # 5% per position
RISK_REWARD_RATIO_MIN: Final[float] = 2.0  # Minimum 1:2 reward:risk

# IBKR Constants
IBKR_DEFAULT_CLIENT_ID: Final[int] = 1
IBKR_MIN_PORT: Final[int] = 7496
IBKR_MAX_PORT: Final[int] = 7499

# Market Hours (US Eastern Time)
MARKET_OPEN_HOUR: Final[int] = 9
MARKET_OPEN_MINUTE: Final[int] = 30
MARKET_CLOSE_HOUR: Final[float] = 16.5  # 4:30 PM

# Country Codes
US_COUNTRY_CODE: Final[str] = "USD"
NASDAQ_EXCHANGE: Final[str] = "ISLAND"

# Security Types
SECURITY_TYPE_STOCK: Final[str] = "STK"
SECURITY_TYPE_OPTION: Final[str] = "OPT"

# Data Sources
DATA_SOURCE_IBKR: Final[str] = "ibkr"
DATA_SOURCE_TRADINGVIEW: Final[str] = "tradingview"

# LLM Models
LLM_MODEL_CLAUDE_3_SONNET: Final[str] = "claude-3-sonnet"
LLM_MODEL_CLAUDE_3_5_SONNET: Final[str] = "claude-3-5-sonnet"

# Webhook Constants
WEBHOOK_SECRET_LENGTH: Final[int] = 32
