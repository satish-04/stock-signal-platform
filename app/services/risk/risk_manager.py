"""
Risk management service.
"""

from decimal import Decimal

from app.core.config import get_settings
from app.core.constants import (
    MAX_DAILY_LOSS_PERCENT,
    MAX_POSITION_PERCENT,
    RISK_REWARD_RATIO_MIN,
)


class RiskManager:
    """
    Manages trading risk and safety controls.
    
    Implements position sizing, stop loss calculation,
    daily loss limits, and other risk controls.
    """
    
    def __init__(self, settings: get_settings | None = None):
        self.settings = settings or get_settings()
    
    def calculate_position_size(
        self,
        account_balance: float,
        risk_percent: float = 1.0,  # Risk % per trade
    ) -> int:
        """
        Calculate position size based on risk.
        
        Args:
            account_balance: Total account balance
            risk_percent: Risk percentage per trade
            
        Returns:
            Recommended position size (number of shares)
        """
        risk_amount = account_balance * (risk_percent / 100.0)
        
        # Assuming $2 stop loss per share as default
        max_loss_per_share = 2.0
        
        position_size = int(risk_amount / max_loss_per_share)
        
        # Apply maximum position limit
        max_position = int(account_balance * (MAX_POSITION_PERCENT / 100.0))
        
        return min(position_size, max_position)
    
    def calculate_stop_loss(
        self,
        entry_price: float,
        volatility: float = 0.02,  # 2% default
    ) -> float:
        """
        Calculate stop loss level.
        
        Args:
            entry_price: Entry price per share
            volatility: Volatility percentage (0.02 = 2%)
            
        Returns:
            Stop loss price
        """
        # ATR-based stop (3x average true range)
        atr_stop = entry_price * volatility
        
        # Minimum $1 stop or 2% (whichever is greater)
        min_stop = max(1.0, entry_price * 0.02)
        
        return entry_price - max(atr_stop, min_stop)
    
    def calculate_reward_ratio(
        self,
        entry_price: float,
        target_price: float,
        stop_loss: float,
    ) -> Decimal:
        """
        Calculate reward:risk ratio.
        
        Args:
            entry_price: Entry price
            target_price: Target price
            stop_loss: Stop loss price
            
        Returns:
            Reward:risk ratio
        """
        reward = target_price - entry_price
        risk = entry_price - stop_loss
        
        if risk == 0:
            return Decimal("0")
        
        return Decimal(str(reward / abs(risk)))
    
    def validate_trade(
        self,
        entry_price: float,
        stop_loss: float,
        target_price: float,
        position_size: int,
        account_balance: float,
    ) -> dict:
        """
        Validate trade against risk limits.
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            target_price: Target price
            position_size: Position size
            account_balance: Account balance
            
        Returns:
            Validation results with recommendations
        """
        reward_risk = self.calculate_reward_ratio(
            entry_price, target_price, stop_loss
        )
        
        daily_risk = position_size * abs(entry_price - stop_loss)
        daily_risk_percent = (daily_risk / account_balance) * 100 if account_balance > 0 else 100
        
        violations = []
        
        # Check reward:risk ratio
        if reward_risk < RISK_REWARD_RATIO_MIN:
            violations.append(
                f"Reward:risk ratio ({reward_risk:.2f}) below minimum ({RISK_REWARD_RATIO_MIN})"
            )
        
        # Check daily risk limit
        if daily_risk_percent > MAX_DAILY_LOSS_PERCENT:
            violations.append(
                f"Daily risk ({daily_risk_percent:.2f}%) exceeds limit ({MAX_DAILY_LOSS_PERCENT}%)"
            )
        
        # Check position size
        max_position_value = account_balance * (MAX_POSITION_PERCENT / 100.0)
        position_value = position_size * entry_price
        
        if position_value > max_position_value:
            violations.append(
                f"Position value (${position_value:,.2f}) exceeds limit (${max_position_value:,.2f})"
            )
        
        return {
            "valid": len(violations) == 0,
            "reward_risk_ratio": reward_risk,
            "daily_risk_percent": daily_risk_percent,
            "violations": violations,
            "recommendation": "approved" if len(violations) == 0 else "rejected",
        }
    
    def check_daily_loss_limit(self, daily_pnl: float) -> dict:
        """
        Check if daily loss limit is exceeded.
        
        Args:
            daily_pnl: Current day's P&L
            
        Returns:
            Limit status and recommended action
        """
        loss_amount = abs(daily_pnl)
        loss_percent = (loss_amount / 100000.0) * 100 if daily_pnl < 0 else 0
        
        exceeded = loss_percent > MAX_DAILY_LOSS_PERCENT
        
        return {
            "daily_pnl": daily_pnl,
            "loss_percent": loss_percent,
            "limit_exceeded": exceeded,
            "remaining_loss_allowance": MAX_DAILY_LOSS_PERCENT - loss_percent if not exceeded else 0,
            "action": "stop_trading" if exceeded else "continue",
        }


class SafetyControls:
    """
    Implements safety controls and kill switches.
    
    Provides emergency stop mechanisms and safety
    limits for automated trading.
    """
    
    def __init__(self, settings: get_settings | None = None):
        self.settings = settings or get_settings()
    
    async def check_position_limit(self, position_size: int) -> bool:
        """
        Check if position size exceeds limits.
        
        Args:
            position_size: Position size to check
            
        Returns:
            True if within limits
        """
        max_position = int(100000 * (MAX_POSITION_PERCENT / 100.0))
        return position_size <= max_position
    
    async def check_daily_loss_limit(self, daily_pnl: float) -> bool:
        """
        Check if daily loss limit is exceeded.
        
        Args:
            daily_pnl: Current day's P&L
            
        Returns:
            True if limit exceeded
        """
        return daily_pnl < -1000  # $1,000 loss limit
    
    async def kill_switch(self) -> bool:
        """
        Emergency kill switch.
        
        Returns:
            True if kill switch is active
        """
        return not self.settings.enable_order_submission
    
    async def get_safety_status(self) -> dict:
        """
        Get current safety status.
        
        Returns:
            Safety status information
        """
        return {
            "kill_switch_active": await self.kill_switch(),
            "paper_mode": True,
            "order_submission_enabled": self.settings.enable_order_submission,
            "live_trading_enabled": self.settings.enable_live_trading,
        }
