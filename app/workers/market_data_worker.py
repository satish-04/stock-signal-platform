"""
Market data worker.
"""

import asyncio
from datetime import datetime

from app.core.config import get_settings


class MarketDataWorker:
    """
    Background worker for market data collection.
    
    Collects and processes real-time market data
    from various sources.
    """
    
    def __init__(self, settings: get_settings | None = None):
        self.settings = settings or get_settings()
        self.running = False
    
    async def start(self) -> None:
        """Start the market data worker."""
        self.running = True
        print(f"[{datetime.utcnow()}] MarketDataWorker started")
        
        while self.running:
            try:
                # Collect market data
                await self._collect_market_data()
                
                # Wait before next collection
                await asyncio.sleep(60)  # Collect every 60 seconds
                
            except Exception as e:
                print(f"[{datetime.utcnow()}] Error collecting market data: {e}")
                await asyncio.sleep(10)
    
    async def _collect_market_data(self) -> None:
        """Collect market data for tracked tickers."""
        # Placeholder - would fetch from IBKR or other sources
        print(f"[{datetime.utcnow()}] Collecting market data...")
    
    async def stop(self) -> None:
        """Stop the market data worker."""
        self.running = False
        print(f"[{datetime.utcnow()}] MarketDataWorker stopped")
