"""
Options pricing and Greeks calculation.
"""

from datetime import date
from decimal import Decimal

import numpy as np


class OptionsService:
    """
    Service for options pricing and Greeks calculation.
    
    Implements Black-Scholes model for European options
    and calculates all major Greeks.
    """
    
    def __init__(self):
        self.risk_free_rate = Decimal("0.05")  # 5% annual
    
    def black_scholes_price(
        self,
        spot: Decimal,
        strike: Decimal,
        time_to_expiry: float,  # in years
        volatility: float,
        option_type: str,  # "call" or "put"
    ) -> Decimal:
        """
        Calculate Black-Scholes option price.
        
        Args:
            spot: Current underlying price
            strike: Strike price
            time_to_expiry: Time to expiry in years
            volatility: Implied volatility (decimal)
            option_type: "call" or "put"
            
        Returns:
            Option price
        """
        S = float(spot)
        K = float(strike)
        T = time_to_expiry
        sigma = volatility
        
        if T <= 0:
            # Option expired
            if option_type == "call":
                return max(0, S - K)
            else:
                return max(0, K - S)
        
        d1 = (np.log(S / K) + (self.risk_free_rate + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if option_type == "call":
            price = S * self._norm_cdf(d1) - K * np.exp(-self.risk_free_rate * T) * self._norm_cdf(d2)
        else:
            price = K * np.exp(-self.risk_free_rate * T) * self._norm_cdf(-d2) - S * self._norm_cdf(-d1)
        
        return Decimal(str(price))
    
    def calculate_greeks(
        self,
        spot: Decimal,
        strike: Decimal,
        time_to_expiry: float,
        volatility: float,
        option_type: str,
    ) -> dict[str, float]:
        """
        Calculate all Greeks for an option.
        
        Args:
            spot: Current underlying price
            strike: Strike price
            time_to_expiry: Time to expiry in years
            volatility: Implied volatility
            option_type: "call" or "put"
            
        Returns:
            Dictionary of Greeks (delta, gamma, theta, vega, rho)
        """
        S = float(spot)
        K = float(strike)
        T = time_to_expiry
        sigma = volatility
        
        if T <= 0:
            return {"delta": 0, "gamma": 0, "theta": 0, "vega": 0, "rho": 0}
        
        d1 = (np.log(S / K) + (self.risk_free_rate + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        # Delta
        if option_type == "call":
            delta = self._norm_cdf(d1)
        else:
            delta = self._norm_cdf(d1) - 1
        
        # Gamma (same for calls and puts)
        gamma = self._norm_pdf(d1) / (S * sigma * np.sqrt(T))
        
        # Theta
        term1 = -S * self._norm_pdf(d1) * sigma / (2 * np.sqrt(T))
        if option_type == "call":
            theta = term1 - self.risk_free_rate * K * np.exp(-self.risk_free_rate * T) * self._norm_cdf(d2)
        else:
            theta = term1 + self.risk_free_rate * K * np.exp(-self.risk_free_rate * T) * self._norm_cdf(-d2)
        
        # Vega (same for calls and puts)
        vega = S * self._norm_pdf(d1) * np.sqrt(T)
        
        # Rho
        if option_type == "call":
            rho = K * T * np.exp(-self.risk_free_rate * T) * self._norm_cdf(d2)
        else:
            rho = -K * T * np.exp(-self.risk_free_rate * T) * self._norm_cdf(-d2)
        
        return {
            "delta": round(delta, 4),
            "gamma": round(gamma, 4),
            "theta": round(theta / 365, 4),  # Daily theta
            "vega": round(vega / 100, 4),  # Per 1% vol change
            "rho": round(rho / 100, 4),  # Per 1% rate change
        }
    
    def _norm_cdf(self, x: float) -> float:
        """Cumulative distribution function for standard normal."""
        return 0.5 * (1 + np.math.erf(x / np.sqrt(2)))
    
    def _norm_pdf(self, x: float) -> float:
        """Probability density function for standard normal."""
        return np.exp(-0.5 * x ** 2) / np.sqrt(2 * np.pi)


class OptionChainService:
    """
    Service for managing option chains.
    
    Handles complete option chain data and calculations.
    """
    
    def __init__(self):
        self.pricer = OptionsService()
    
    async def get_option_price(
        self,
        spot: Decimal,
        strike: Decimal,
        expiry_date: date,
        volatility: float,
        option_type: str,
    ) -> dict:
        """
        Get complete option pricing information.
        
        Args:
            spot: Current underlying price
            strike: Strike price
            expiry_date: Option expiration date
            volatility: Implied volatility
            option_type: "call" or "put"
            
        Returns:
            Complete pricing information including Greeks
        """
        time_to_expiry = (expiry_date - date.today()).days / 365.0
        
        price = self.pricer.black_scholes_price(spot, strike, time_to_expiry, volatility, option_type)
        greeks = self.pricer.calculate_greeks(spot, strike, time_to_expiry, volatility, option_type)
        
        return {
            "strike": float(strike),
            "expiry_date": str(expiry_date),
            "option_type": option_type,
            "price": float(price),
            "greeks": greeks,
        }
    
    async def build_option_chain(
        self,
        spot: Decimal,
        expirations: list[date],
        strikes: list[Decimal],
        volatility: float,
    ) -> dict:
        """
        Build complete option chain.
        
        Args:
            spot: Current underlying price
            expirations: List of expiration dates
            strikes: List of strike prices
            volatility: Implied volatility
            
        Returns:
            Complete option chain structure
        """
        chain = {}
        
        for expiry in expirations:
            chain[str(expiry)] = {
                "calls": [],
                "puts": [],
            }
            
            for strike in strikes:
                # Add calls
                call_price = await self.get_option_price(
                    spot, strike, expiry, volatility, "call"
                )
                chain[str(expiry)]["calls"].append(call_price)
                
                # Add puts
                put_price = await self.get_option_price(
                    spot, strike, expiry, volatility, "put"
                )
                chain[str(expiry)]["puts"].append(put_price)
        
        return chain
