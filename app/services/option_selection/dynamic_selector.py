"""
Dynamic option selection service.
"""

from datetime import date
from decimal import Decimal

from app.core.constants import OPTION_CALL, OPTION_PUT


class DynamicOptionSelector:
    """
    Dynamically select options based on market conditions.
    
    Uses underlying price, volatility, and technical signals
    to determine optimal options for trading strategies.
    """
    
    def __init__(
        self,
        underlying_price: Decimal,
        volatility: Decimal | None = None,
    ):
        self.underlying_price = underlying_price
        self.volatility = volatility or Decimal("0.30")
    
    def select_otm_calls(
        self,
        moneyness_range: tuple[Decimal, Decimal] = (Decimal("1.02"), Decimal("1.10")),
    ) -> list[dict]:
        """
        Select out-of-the-money call options.
        
        Args:
            moneyness_range: Range of strike prices relative to underlying
                            (e.g., 1.02 = 2% OTM, 1.10 = 10% OTM)
                            
        Returns:
            List of call options
        """
        min_strike = self.underlying_price * moneyness_range[0]
        max_strike = self.underlying_price * moneyness_range[1]
        
        strikes = []
        strike = min_strike
        while strike <= max_strike:
            strikes.append({
                "strike_price": float(strike),
                "right": OPTION_CALL,
                "moneyness": float(strike / self.underlying_price),
            })
            strike += Decimal("2.5")  # Default $2.50 strike increments
        
        return strikes
    
    def select_otm_puts(
        self,
        moneyness_range: tuple[Decimal, Decimal] = (Decimal("0.90"), Decimal("0.98")),
    ) -> list[dict]:
        """
        Select out-of-the-money put options.
        
        Args:
            moneyness_range: Range of strike prices relative to underlying
            
        Returns:
            List of put options
        """
        min_strike = self.underlying_price * moneyness_range[0]
        max_strike = self.underlying_price * moneyness_range[1]
        
        strikes = []
        strike = min_strike
        while strike <= max_strike:
            strikes.append({
                "strike_price": float(strike),
                "right": OPTION_PUT,
                "moneyness": float(strike / self.underlying_price),
            })
            strike += Decimal("2.5")
        
        return strikes
    
    def find_straddles(
        self,
        delta_range: tuple[Decimal, Decimal] = (Decimal("0.30"), Decimal("0.50")),
    ) -> list[dict]:
        """
        Find at-the-money straddle options.
        
        Args:
            delta_range: Delta range for ATM options
            
        Returns:
            List of straddle combinations
        """
        # Find strikes closest to underlying price
        call_strike = float(self.underlying_price)
        put_strike = float(self.underlying_price)
        
        return [{
            "strike_price": call_strike,
            "call": {
                "right": OPTION_CALL,
                "strike": call_strike,
            },
            "put": {
                "right": OPTION_PUT,
                "strike": put_strike,
            },
            "total_cost": 0,  # Calculated from options
        }]
    
    def find_strangles(
        self,
        call_moneyness: Decimal = Decimal("1.05"),
        put_moneyness: Decimal = Decimal("0.95"),
    ) -> list[dict]:
        """
        Find out-of-the-money strangle options.
        
        Args:
            call_moneyness: OTM percentage for calls
            put_moneyness: OTM percentage for puts
            
        Returns:
            List of strangle combinations
        """
        call_strike = float(self.underlying_price * call_moneyness)
        put_strike = float(self.underlying_price * put_moneyness)
        
        return [{
            "call_strike": call_strike,
            "put_strike": put_strike,
            "call_right": OPTION_CALL,
            "put_right": OPTION_PUT,
        }]
    
    def rank_options(
        self,
        options: list[dict],
        criteria: dict[str, float],
    ) -> list[dict]:
        """
        Rank options based on multiple criteria.
        
        Args:
            options: List of option dictionaries
            criteria: Weighted criteria for ranking
            
        Returns:
            Ranked list of options
        """
        # Placeholder implementation
        return sorted(
            options,
            key=lambda x: x.get("implied_volatility", 0),
            reverse=True,
        )


class OptionChainService:
    """
    Service for managing option chains.
    
    Handles option chain discovery, filtering, and
    selection for trading strategies.
    """
    
    def __init__(self):
        self.selector = DynamicOptionSelector(Decimal("175.0"))
    
    async def build_option_chain(
        self,
        ticker: str,
        underlying_price: Decimal,
    ) -> dict:
        """
        Build complete option chain for a ticker.
        
        Args:
            ticker: Stock ticker
            underlying_price: Current price of underlying
            
        Returns:
            Complete option chain structure
        """
        # Get expirations
        expirations = await self._get_expirations(ticker)
        
        # Get strikes for each expiration
        chain = {
            "ticker": ticker,
            "underlying_price": float(underlying_price),
            "expirations": {},
        }
        
        for expiry in expirations:
            chain["expirations"][expiry] = {
                "calls": self.selector.select_otm_calls(),
                "puts": self.selector.select_otm_puts(),
            }
        
        return chain
    
    async def _get_expirations(self, ticker: str) -> list[str]:
        """Get available expirations for a ticker."""
        # Placeholder - would call IBKR API
        return ["2024-01-19", "2024-02-16", "2024-03-15"]
