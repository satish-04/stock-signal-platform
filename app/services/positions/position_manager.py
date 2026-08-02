"""
Position management service.
"""

from decimal import Decimal

from app.core.config import get_settings
from app.services.order_execution.executor import OrderExecutor


class PositionManager:
    """
    Manages trading positions and portfolio.
    
    Handles position creation, updates, closures,
    and performance tracking.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.order_executor = OrderExecutor(self.settings)
        self.positions: dict[str, dict] = {}
    
    async def create_position(
        self,
        ticker: str,
        quantity: int,
        entry_price: Decimal,
        side: str = "buy",
    ) -> dict:
        """
        Create a new position.
        
        Args:
            ticker: Stock/option symbol
            quantity: Number of contracts/shares
            entry_price: Entry price per unit
            side: "buy" or "sell"
            
        Returns:
            Created position record
        """
        position = {
            "ticker": ticker,
            "quantity": quantity if side == "buy" else -quantity,
            "avg_cost": float(entry_price),
            "entry_price": float(entry_price),
            "side": side,
            "status": "open",
        }
        
        self.positions[ticker] = position
        return position
    
    async def update_position(self, ticker: str) -> dict:
        """
        Update position with current market data.
        
        Args:
            ticker: Position ticker symbol
            
        Returns:
            Updated position with current values
        """
        if ticker not in self.positions:
            raise ValueError(f"Position for {ticker} not found")
        
        position = self.positions[ticker]
        current_price = await self._get_current_price(ticker)
        
        position["current_price"] = current_price
        
        if position["side"] == "buy":
            position["unrealized_pnl"] = (current_price - position["avg_cost"]) * abs(position["quantity"])
            position["pnl_percent"] = ((current_price - position["avg_cost"]) / position["avg_cost"]) * 100
        else:
            position["unrealized_pnl"] = (position["avg_cost"] - current_price) * abs(position["quantity"])
            position["pnl_percent"] = ((position["avg_cost"] - current_price) / position["avg_cost"]) * 100
        
        return position
    
    async def close_position(
        self,
        ticker: str,
        quantity: int | None = None,
    ) -> dict:
        """
        Close all or part of a position.
        
        Args:
            ticker: Position ticker symbol
            quantity: Quantity to close (None = all)
            
        Returns:
            Closed position with execution details
        """
        if ticker not in self.positions:
            raise ValueError(f"Position for {ticker} not found")
        
        position = self.positions[ticker]
        
        if quantity is None:
            quantity_to_close = abs(position["quantity"])
        else:
            quantity_to_close = min(quantity, abs(position["quantity"]))
        
        # Execute the closing order
        side = "sell" if position["side"] == "buy" else "buy"
        
        execution = await self.order_executor.place_order(
            ticker=ticker,
            quantity=quantity_to_close,
            side=side,
        )
        
        # Update position
        old_qty = abs(position["quantity"])
        remaining_qty = old_qty - quantity_to_close
        
        position["realized_pnl"] = execution.get("total_pnl", 0)
        position["status"] = "closed" if remaining_qty == 0 else "open"
        
        if remaining_qty == 0:
            del self.positions[ticker]
        else:
            position["quantity"] = remaining_qty if position["side"] == "buy" else -remaining_qty
        
        return execution
    
    async def _get_current_price(self, ticker: str) -> float:
        """
        Get current market price for a ticker.
        
        Args:
            ticker: Ticker symbol
            
        Returns:
            Current price
        """
        # Placeholder - would fetch from market data service
        prices = {"AAPL": 175.23, "GOOGL": 140.50, "MSFT": 375.80}
        return prices.get(ticker, 100.0)
    
    def get_positions(self) -> list[dict]:
        """
        Get all positions.
        
        Returns:
            List of position records
        """
        return list(self.positions.values())
    
    def get_positions_by_ticker(self, ticker: str) -> dict | None:
        """
        Get a specific position by ticker.
        
        Args:
            ticker: Ticker symbol
            
        Returns:
            Position record or None
        """
        return self.positions.get(ticker)
    
    def get_portfolio_summary(self) -> dict:
        """
        Get portfolio summary.
        
        Returns:
            Portfolio statistics
        """
        positions = self.get_positions()
        
        total_value = 0
        total_pnl = 0
        
        for pos in positions:
            current_price = pos.get("current_price", pos["avg_cost"])
            
            if pos["side"] == "buy":
                total_value += current_price * abs(pos["quantity"])
            else:
                total_value -= current_price * abs(pos["quantity"])
            
            if "unrealized_pnl" in pos:
                total_pnl += pos["unrealized_pnl"]
        
        return {
            "positions_count": len(positions),
            "total_value": total_value,
            "total_pnl": total_pnl,
        }


class PositionExitMonitor:
    """
    Monitors positions for exit conditions.
    
    Tracks stop loss, take profit, and other exit
    criteria for active positions.
    """
    
    def __init__(self):
        self.monitored_positions: dict[str, dict] = {}
    
    def add_position(
        self,
        ticker: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
    ) -> None:
        """
        Add a position to the exit monitor.
        
        Args:
            ticker: Position ticker
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
        """
        self.monitored_positions[ticker] = {
            "ticker": ticker,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "status": "active",
        }
    
    def check_exit_conditions(self, ticker: str, current_price: float) -> dict | None:
        """
        Check if exit conditions are met.
        
        Args:
            ticker: Position ticker
            current_price: Current market price
            
        Returns:
            Exit signal if conditions met, None otherwise
        """
        if ticker not in self.monitored_positions:
            return None
        
        position = self.monitored_positions[ticker]
        
        # Check stop loss
        if current_price <= position["stop_loss"]:
            return {
                "action": "exit",
                "reason": "stop_loss_hit",
                "current_price": current_price,
            }
        
        # Check take profit
        if current_price >= position["take_profit"]:
            return {
                "action": "exit",
                "reason": "take_profit_hit",
                "current_price": current_price,
            }
        
        return None
    
    def remove_position(self, ticker: str) -> bool:
        """
        Remove a position from monitoring.
        
        Args:
            ticker: Position ticker
            
        Returns:
            True if removed successfully
        """
        if ticker in self.monitored_positions:
            del self.monitored_positions[ticker]
            return True
        return False
