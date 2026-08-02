"""
Order execution service.
"""

from datetime import datetime
from decimal import Decimal

from app.core.config import get_settings, Settings


class OrderExecutor:
    """
    Executes trades through the broker.
    
    Handles order placement, monitoring, and fill processing
    for both paper and live trading modes.
    """
    
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.paper_mode = True  # Default to paper trading
        self.execution_log: list[dict] = []
    
    async def place_order(
        self,
        ticker: str,
        quantity: int,
        side: str,  # "buy" or "sell"
        order_type: str = "market",
        price: Decimal | None = None,
    ) -> dict:
        """
        Place a trade order.
        
        Args:
            ticker: Stock ticker symbol
            quantity: Number of shares/options
            side: "buy" or "sell"
            order_type: Order type ("market", "limit")
            price: Limit price (required for limit orders)
            
        Returns:
            Order details with status and ID
        """
        # Safety checks
        if not self.settings.is_paper_mode:
            raise ValueError("Not in paper mode")
        
        if not self.settings.enable_order_submission:
            raise ValueError("Order submission is disabled")
        
        # Build order object
        order = {
            "ticker": ticker,
            "quantity": quantity,
            "side": side,
            "order_type": order_type,
            "price": float(price) if price else None,
            "status": "pending",
            "placed_at": datetime.utcnow(),
            "order_id": self._generate_order_id(),
        }
        
        if self.settings.is_live_trading_enabled:
            # Real order execution (mocked for demo)
            order["status"] = "executed"
            order["filled_qty"] = quantity
            order["avg_fill_price"] = float(price) if price else 175.0
            order["filled_at"] = datetime.utcnow()
        else:
            # Paper trading execution
            order = await self._execute_paper_order(order)
        
        self.execution_log.append(order)
        
        return order
    
    async def _execute_paper_order(self, order: dict) -> dict:
        """
        Execute a paper trading order.
        
        Simulates order execution without real broker interaction.
        
        Args:
            order: Order dictionary
            
        Returns:
            Executed order with fill details
        """
        # Simulate execution delay
        await self._simulate_delay()
        
        order["status"] = "executed"
        order["filled_qty"] = order["quantity"]
        
        # Determine fill price based on side
        if order["side"] == "buy":
            order["avg_fill_price"] = 175.23  # Simulated fill
        else:
            order["avg_fill_price"] = 175.00
        
        order["filled_at"] = datetime.utcnow()
        
        return order
    
    async def _simulate_delay(self) -> None:
        """Simulate network delay for realistic execution."""
        import asyncio
        await asyncio.sleep(0.1)  # 100ms delay
    
    def _generate_order_id(self) -> str:
        """Generate unique order ID."""
        import uuid
        return f"ORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    
    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel a pending order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if cancellation successful
        """
        return False  # Placeholder
    
    async def get_order_status(self, order_id: str) -> dict:
        """
        Get current status of an order.
        
        Args:
            order_id: Order ID
            
        Returns:
            Order status information
        """
        return {"order_id": order_id, "status": "unknown"}


class PositionManager:
    """
    Manages positions and portfolio.
    
    Tracks open positions, calculates P&L, and manages
    position sizing.
    """
    
    def __init__(self):
        self.positions: dict[str, dict] = {}
        self.portfolio_value = 100000.0
        self.cash_balance = 50000.0
    
    async def open_position(
        self,
        ticker: str,
        quantity: int,
        entry_price: Decimal,
        side: str = "buy",
    ) -> dict:
        """
        Open a new position.
        
        Args:
            ticker: Ticker symbol
            quantity: Number of shares/options
            entry_price: Entry price per share
            side: "buy" or "sell"
            
        Returns:
            New position record
        """
        if ticker in self.positions:
            # Update existing position
            pos = self.positions[ticker]
            old_qty = pos["quantity"]
            old_cost = pos["avg_cost"]
            
            if side == "buy":
                new_qty = old_qty + quantity
                new_cost = ((old_qty * old_cost) + (quantity * float(entry_price))) / new_qty
            else:
                new_qty = old_qty - quantity
            
            pos["quantity"] = new_qty
            pos["avg_cost"] = Decimal(str(new_cost)) if side == "buy" else old_cost
        else:
            # Create new position
            self.positions[ticker] = {
                "ticker": ticker,
                "quantity": quantity if side == "buy" else -quantity,
                "avg_cost": float(entry_price),
                "entry_price": float(entry_price),
                "side": side,
            }
        
        return self.positions[ticker]
    
    async def close_position(self, ticker: str, quantity: int | None = None) -> dict:
        """
        Close a position.
        
        Args:
            ticker: Ticker symbol
            quantity: Quantity to close (None = all)
            
        Returns:
            Closed position record with P&L
        """
        if ticker not in self.positions:
            raise ValueError(f"No position for {ticker}")
        
        pos = self.positions[ticker]
        
        if quantity is None or quantity >= abs(pos["quantity"]):
            # Close entire position
                pnl = self._calculate_pnl(pos)
                
                del self.positions[ticker]
                
                return {**pos, "pnl": pnl}
        else:
            # Partial close
            pos["quantity"] -= quantity if pos["quantity"] > 0 else -quantity
        
        return self.positions[ticker]
    
    def _calculate_pnl(self, position: dict) -> float:
        """
        Calculate P&L for a position.
        
        Args:
            position: Position dictionary
            
        Returns:
            P&L value
        """
        current_price = self._get_current_price(position["ticker"])
        
        if position["side"] == "buy":
            pnl = (current_price - position["avg_cost"]) * position["quantity"]
        else:
            pnl = (position["avg_cost"] - current_price) * abs(position["quantity"])
        
        return round(pnl, 2)
    
    def _get_current_price(self, ticker: str) -> float:
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
    
    def get_portfolio_summary(self) -> dict:
        """
        Get portfolio summary.
        
        Returns:
            Portfolio statistics
        """
        total_positions_value = sum(
            pos["quantity"] * self._get_current_price(pos["ticker"])
            for pos in self.positions.values()
        )
        
        return {
            "total_equity": self.portfolio_value,
            "cash_balance": self.cash_balance,
            "total_positions_value": total_positions_value,
            "positions_count": len(self.positions),
        }
