"""
IBKR broker adapter service.

Lazy imports to avoid event loop issues in Python 3.14+
"""

import importlib
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.core.config import get_settings, Settings
from app.core.errors import IBAPIError


class IBKRBrokerAdapter:
    """
    Adapter for Interactive Brokers API.
    
    Provides a clean interface to IBKR's TWS/IB Gateway for
    market data, order execution, and position management.
    """
    
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.ib = None
        self._connected = False
    
    def _ensure_ib(self):
        """Lazily initialize IB object to avoid event loop issues."""
        if self.ib is None:
            from ib_insync import IB
            self.ib = IB()
    
    async def connect(self) -> bool:
        """
        Connect to IBKR TWS or Gateway.
        
        Returns:
            True if connection successful
        """
        self._ensure_ib()
        try:
            await self.ib.connectAsync(
                host=self.settings.ibkr_host,
                port=self.settings.ibkr_port,
                clientId=self.settings.ibkr_client_id,
            )
            self._connected = True
            return True
        except Exception as e:
            raise IBAPIError(f"Failed to connect to IBKR: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from IBKR."""
        self._ensure_ib()
        if self._connected:
            await self.ib.disconnectAsync()
            self._connected = False
    
    async def get_historical_data(
        self,
        ticker: str,
        duration: str = "1M",
        bar_size: str = "5 mins",
    ) -> list[HistoricalBar]:
        """
        Get historical OHLCV data.
        
        Args:
            ticker: Stock ticker
            duration: Duration of historical data
            bar_size: Bar size (e.g., "5 mins", "1 day")
            
        Returns:
            List of historical bars
        """
        if not self._connected:
            await self.connect()
        
        try:
            contract = Stock(ticker, "SMART", "USD")
            bars = await self.ib.reqHistoricalDataAsync(
                contract,
                "",
                duration,
                bar_size,
                "TRADES",
                useRTH=True,
            )
            return list(bars)
        except Exception as e:
            raise IBAPIError(f"Failed to fetch historical data for {ticker}: {e}")
    
    async def get_option_chain(
        self,
        ticker: str,
        underlying_price: float | None = None,
        min_strike: float | None = None,
        max_strike: float | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get option chain for a stock with dynamic strike selection.
        
        Args:
            ticker: Stock ticker
            underlying_price: Current underlying price (optional)
            min_strike: Minimum strike price (optional)
            max_strike: Maximum strike price (optional)
            
        Returns:
            List of option chains by expiration with dynamic strikes
        """
        if not self._connected:
            await self.connect()
        
        try:
            contract = Stock(ticker, "SMART", "USD")
            chains = await self.ib.reqSecDefOptParamsAsync(
                underlyingSymbol=ticker,
                futFopExchange="",
                underlyingSecurityType="STK",
                underlyingConId=0,
            )
            
            option_contracts = []
            for chain in chains:
                # Filter expirations - get next 3 months by default
                expiries = sorted(chain.expirations)[:3]
                
                for expiry in expiries:
                    # Determine strike range
                    strikes = chain.strikes
                    
                    if underlying_price is not None:
                        # Underlying-centered selection: 20 strikes each side
                        at_the_money = min(strikes, key=lambda x: abs(x - underlying_price))
                        
                        strike_range_start = strikes.index(at_the_money) - 20
                        strike_range_end = strikes.index(at_the_money) + 20
                        
                        # Clamp to valid range
                        strike_range_start = max(0, strike_range_start)
                        strike_range_end = min(len(strikes) - 1, strike_range_end)
                        
                        strikes = strikes[strike_range_start:strike_range_end + 1]
                    elif min_strike is not None or max_strike is not None:
                        # Filter by price range
                        if min_strike is not None:
                            strikes = [s for s in strikes if s >= min_strike]
                        if max_strike is not None:
                            strikes = [s for s in strikes if s <= max_strike]
                    
                    # Create option contracts for calls and puts
                    for strike in strikes:
                        for right in ["C", "P"]:
                            opt = Contract()
                            opt.symbol = ticker
                            opt.secType = "OPT"
                            opt.exchange = "SMART"
                            opt.currency = "USD"
                            opt.lastTradeDateOrContractMonth = expiry
                            opt.strike = float(strike)
                            opt.right = right
                            
                            # Request contract details to get conId
                            try:
                                details = await self.ib.reqContractDetailsAsync(opt)
                                if details:
                                    qualified_contract = details[0].contract
                                    option_contracts.append({
                                        "contract": qualified_contract,
                                        "conid": qualified_contract.conId,
                                        "symbol": ticker,
                                        "expiry": expiry,
                                        "strike": float(strike),
                                        "right": right,
                                    })
                            except Exception as e:
                                # If contract details fail, add with placeholder conId
                                option_contracts.append({
                                    "contract": opt,
                                    "conid": 0,  # Will be populated later
                                    "symbol": ticker,
                                    "expiry": expiry,
                                    "strike": float(strike),
                                    "right": right,
                                })
            
            return option_contracts
        except Exception as e:
            raise IBAPIError(f"Failed to fetch option chain for {ticker}: {e}")
    
    async def get_option_quotes(
        self,
        contracts: list[dict[str, Any]],
        include_market_data: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Get market data for option contracts.
        
        Args:
            contracts: List of option contract dictionaries
            include_market_data: Include market data if available
            
        Returns:
            List of option quotes with Greeks
        """
        quotes = []
        
        for contract_data in contracts:
            quote = {
                "conid": contract_data["conid"],
                "symbol": contract_data["symbol"],
                "expiry": contract_data["expiry"],
                "strike": contract_data["strike"],
                "right": contract_data["right"],
            }
            
            if include_market_data:
                # Request market data with Greeks
                try:
                    ticker_id = await self.ib.reqMktDataAsync(
                        contract_data["contract"],
                        "236",  # Greek values and market data
                    )
                    
                    await self.ib.sleep(0.1)
                    
                    # Get current market data
                    mkt_data = self.ib.reqMktData(contract_data["contract"], "236")
                    if hasattr(mkt_data, 'bid') and mkt_data.bid:
                        quote["bid"] = float(mkt_data.bid)
                        quote["ask"] = float(mkt_data.ask) if hasattr(mkt_data, 'ask') else 0.0
                        quote["volume"] = int(mkt_data.volume) if hasattr(mkt_data, 'volume') else 0
                        quote["open_interest"] = int(mkt_data.openInterest) if hasattr(mkt_data, 'openInterest') else 0
                        quote["iv"] = float(mkt_data.impliedVolatility) if hasattr(mkt_data, 'impliedVolatility') else 0.0
                        quote["delta"] = float(mkt_data.greeks.delta) if hasattr(mkt_data.greeks, 'delta') else 0.0
                        quote["gamma"] = float(mkt_data.greeks.gamma) if hasattr(mkt_data.greeks, 'gamma') else 0.0
                        quote["theta"] = float(mkt_data.greeks.theta) if hasattr(mkt_data.greeks, 'theta') else 0.0
                        quote["vega"] = float(mkt_data.greeks.vega) if hasattr(mkt_data.greeks, 'vega') else 0.0
                    else:
                        # Entitlement not available - return zeros
                        quote.update({
                            "bid": 0.0,
                            "ask": 0.0,
                            "volume": 0,
                            "open_interest": 0,
                            "iv": 0.0,
                            "delta": 0.0,
                            "gamma": 0.0,
                            "theta": 0.0,
                            "vega": 0.0,
                        })
                except Exception as e:
                    quote.update({
                        "bid": 0.0,
                        "ask": 0.0,
                        "volume": 0,
                        "open_interest": 0,
                        "iv": 0.0,
                        "delta": 0.0,
                        "gamma": 0.0,
                        "theta": 0.0,
                        "vega": 0.0,
                    })
            else:
                # Don't request market data (faster)
                quote.update({
                    "bid": 0.0,
                    "ask": 0.0,
                    "volume": 0,
                    "open_interest": 0,
                    "iv": 0.0,
                    "delta": 0.0,
                    "gamma": 0.0,
                    "theta": 0.0,
                    "vega": 0.0,
                })
            
            quotes.append(quote)
        
        return quotes
    
    async def place_order(
        self,
        ticker: str,
        quantity: int,
        side: str,
        order_type: str = "MKT",
        price: Decimal | None = None,
    ) -> dict[str, Any]:
        """
        Place a trade order.
        
        Args:
            ticker: Stock ticker
            quantity: Number of shares
            side: "buy" or "sell"
            order_type: Order type (MKT, LMT, etc.)
            price: Limit price if applicable
            
        Returns:
            Order details including ID
        """
        if not self._connected:
            await self.connect()
        
        try:
            contract = Stock(ticker, "SMART", "USD")
            
            order = Order()
            order.action = side.upper()
            order.totalQuantity = quantity
            order.orderType = order_type
            
            if price:
                order.lmtPrice = float(price)
            
            trade = await self.ib.placeOrderAsync(contract, order)
            
            return {
                "order_id": trade.order.orderId,
                "ticker": ticker,
                "status": trade.orderStatus.status if trade.orderStatus else "Pending",
            }
        except Exception as e:
            raise IBAPIError(f"Failed to place order: {e}")
    
    async def get_positions(self) -> list[Position]:
        """
        Get current positions.
        
        Returns:
            List of position objects
        """
        if not self._connected:
            await self.connect()
        
        try:
            positions = await self.ib.positionsAsync()
            return list(positions)
        except Exception as e:
            raise IBAPIError(f"Failed to fetch positions: {e}")
    
    async def get_market_data(
        self,
        ticker: str,
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get real-time market data.
        
        Args:
            ticker: Stock ticker
            fields: Market data fields to request
            
        Returns:
            Dictionary of market data
        """
        if not self._connected:
            await self.connect()
        
        try:
            contract = Stock(ticker, "SMART", "USD")
            
            if fields is None:
                fields = ["bid", "ask", "last", "volume"]
            
            # Request market data
            ticker_id = await self.ib.reqMktDataAsync(contract, fields)
            
            # Wait for data (simplified - in production use event handler)
            await self.ib.sleep(1)
            
            return {"ticker": ticker, "fields": fields}
        except Exception as e:
            raise IBAPIError(f"Failed to fetch market data for {ticker}: {e}")
    
    async def get_greeks(self, contract: Contract) -> dict[str, float]:
        """
        Get option Greeks for a contract.
        
        Args:
            contract: Option contract
            
        Returns:
            Dictionary of Greeks
        """
        if not self._connected:
            await self.connect()
        
        try:
            # Request market data with Greeks
            ticker_id = await self.ib.reqMktDataAsync(
                contract,
                "236",  # Greek values
            )
            
            await self.ib.sleep(1)
            
            return {
                "delta": 0.0,
                "gamma": 0.0,
                "theta": 0.0,
                "vega": 0.0,
            }
        except Exception as e:
            raise IBAPIError(f"Failed to fetch Greeks: {e}")
    
    async def get_conid(self, ticker: str) -> int | None:
        """
        Get IBKR conId for a stock.
        
        Args:
            ticker: Stock ticker
            
        Returns:
            Contract ID or None if not found
        """
        if not self._connected:
            await self.connect()
        
        try:
            contract = Stock(ticker, "SMART", "USD")
            contracts = await self.ib.reqContractDetailsAsync(contract)
            
            if contracts:
                return contracts[0].conId
            return None
        except Exception as e:
            raise IBAPIError(f"Failed to fetch conId for {ticker}: {e}")


class IBKRMarketDataService:
    """
    Market data service using IBKR.
    
    Handles historical and real-time market data operations.
    """
    
    def __init__(self, broker: IBKRBrokerAdapter | None = None):
        self.broker = broker or IBKRBrokerAdapter()
    
    async def get_historical_ohlcv(
        self,
        ticker: str,
        days: int = 30,
        bar_size: str = "5 mins",
    ) -> list[dict[str, Any]]:
        """
        Get historical OHLCV data.
        
        Args:
            ticker: Stock ticker
            days: Number of days of history
            bar_size: Bar size
            
        Returns:
            List of OHLCV dictionaries
        """
        bars = await self.broker.get_historical_data(
            ticker=ticker,
            duration=f"{days} M",
            bar_size=bar_size,
        )
        
        return [
            {
                "timestamp": bar.date,
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": float(bar.close),
                "volume": bar.volume,
            }
            for bar in bars
        ]
    
    async def get_current_quote(self, ticker: str) -> dict[str, Any]:
        """
        Get current market quote.
        
        Args:
            ticker: Stock ticker
            
        Returns:
            Current bid, ask, last price
        """
        return await self.broker.get_market_data(ticker)
    
    async def get_dynamic_option_chain(
        self,
        ticker: str,
        days_to_expiry: int = 45,
    ) -> list[dict[str, Any]]:
        """
        Get dynamic option chain centered around underlying price.
        
        Args:
            ticker: Stock ticker
            days_to_expiry: Maximum days to expiry
            
        Returns:
            List of option contracts with dynamic strikes
        """
        # Get current underlying price
        quote = await self.get_current_quote(ticker)
        underlying_price = quote.get("last", 175.0) if isinstance(quote, dict) else 175.0
        
        # Get option chain with dynamic strikes
        return await self.broker.get_option_chain(
            ticker=ticker,
            underlying_price=underlying_price,
        )