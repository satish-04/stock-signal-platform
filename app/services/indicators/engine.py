"""
Base class for technical indicators.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal

import pandas as pd


class Indicator(ABC):
    """
    Base class for technical indicators.
    
    All indicator implementations should inherit from this class
    and implement the calculate method.
    """
    
    def __init__(self, period: int = 14):
        self.period = period
        self.name = self.__class__.__name__.lower()
    
    @abstractmethod
    def calculate(self, prices: pd.Series) -> pd.Series:
        """
        Calculate indicator values for price series.
        
        Args:
            prices: Price series (typically close prices)
            
        Returns:
            Series of indicator values
        """
        pass
    
    def calculate_with_timestamps(
        self,
        prices: pd.Series,
        timestamps: pd.DatetimeIndex | None = None,
    ) -> pd.DataFrame:
        """
        Calculate indicator with timestamps.
        
        Args:
            prices: Price series
            timestamps: Optional timestamps
            
        Returns:
            DataFrame with timestamp and indicator value columns
        """
        values = self.calculate(prices)
        
        if timestamps is not None:
            df = pd.DataFrame({
                "timestamp": timestamps,
                f"{self.name}": values,
            })
        else:
            df = pd.DataFrame({
                "timestamp": prices.index,
                f"{self.name}": values,
            })
        
        return df.dropna()


class MovingAverage(Indicator):
    """Base class for moving average indicators."""
    
    @abstractmethod
    def calculate(self, prices: pd.Series) -> pd.Series:
        pass


class EMA(MovingAverage):
    """Exponential Moving Average indicator."""
    
    def calculate(self, prices: pd.Series) -> pd.Series:
        return prices.ewm(span=self.period, adjust=False).mean()


class SMA(MovingAverage):
    """Simple Moving Average indicator."""
    
    def calculate(self, prices: pd.Series) -> pd.Series:
        return prices.rolling(window=self.period).mean()


class RSI(Indicator):
    """Relative Strength Index indicator."""
    
    def calculate(self, prices: pd.Series) -> pd.Series:
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=self.period).mean()
        avg_loss = loss.rolling(window=self.period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi


class MACD(Indicator):
    """MACD (Moving Average Convergence Divergence) indicator."""
    
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        self.fast = fast
        self.slow = slow
        self.signal = signal
        self.name = "macd"
    
    def calculate(self, prices: pd.Series) -> pd.DataFrame:
        ema_fast = prices.ewm(span=self.fast, adjust=False).mean()
        ema_slow = prices.ewm(span=self.slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return pd.DataFrame({
            "macd": macd_line,
            "macd_signal": signal_line,
            "macd_histogram": histogram,
        })


class ATR(Indicator):
    """Average True Range indicator."""
    
    def calculate(self, prices: pd.Series) -> pd.Series:
        # For simplicity, assuming prices is close series
        # In production, would need high/low data
        return prices.rolling(window=self.period).std()


class VWAP(Indicator):
    """Volume Weighted Average Price indicator."""
    
    def calculate(self, prices: pd.Series) -> pd.Series:
        """
        Calculate VWAP (returns NaN since volume is required).
        
        Args:
            prices: Price series
            
        Returns:
            NaN Series (VWAP requires volume)
        """
        return pd.Series([float('nan')] * len(prices))
    
    def calculate_with_volume(
        self,
        prices: pd.Series,
        volumes: pd.Series,
    ) -> pd.Series:
        """
        Calculate VWAP with volume data.
        
        Args:
            prices: Price series
            volumes: Volume series
            
        Returns:
            VWAP values
        """
        cumprod = (prices * volumes).cumsum()
        cumvol = volumes.cumsum()
        
        return cumprod / cumvol


class BollingerBands(Indicator):
    """Bollinger Bands indicator."""
    
    def calculate(self, prices: pd.Series) -> pd.Series:
        """
        Calculate Bollinger Bands.
        
        Args:
            prices: Price series
            
        Returns:
            Middle band (SMA)
        """
        return prices.rolling(window=20).mean()
    
    def calculate_with_deviation(
        self,
        prices: pd.Series,
        ma: pd.Series | None = None,
        num_std: float = 2.0,
    ) -> pd.DataFrame:
        """
        Calculate Bollinger Bands.
        
        Args:
            prices: Price series
            ma: Optional moving average (defaults to 20-period SMA)
            num_std: Number of standard deviations
            
        Returns:
            DataFrame with upper, middle, and lower bands
        """
        if ma is None:
            ma = prices.rolling(window=20).mean()
        
        std_dev = prices.rolling(window=20).std()
        
        upper = ma + (num_std * std_dev)
        lower = ma - (num_std * std_dev)
        
        return pd.DataFrame({
            "bollinger_upper": upper,
            "bollinger_middle": ma,
            "bollinger_lower": lower,
        })


class IndicatorEngine:
    """
    Engine for computing multiple technical indicators.
    
    Computes all configured indicators and returns a combined
    DataFrame of indicator values.
    """
    
    def __init__(self):
        self.indicators: dict[str, Indicator] = {
            "ema_9": EMA(period=9),
            "ema_20": EMA(period=20),
            "ema_50": EMA(period=50),
            "ema_200": EMA(period=200),
            "sma_20": SMA(period=20),
            "rsi_14": RSI(period=14),
            "macd": MACD(fast=12, slow=26, signal=9),
            "atr_14": ATR(period=14),
            "vwap": VWAP(),
            "bollinger": BollingerBands(),
        }
    
    async def compute_all(
        self,
        prices: pd.Series,
        volumes: pd.Series | None = None,
    ) -> dict[str, Any]:
        """
        Compute all indicators for a price series.
        
        Args:
            prices: Price series (close prices)
            volumes: Optional volume series
            
        Returns:
            Dictionary of indicator values
        """
        results = {}
        
        # Moving averages
        for name, indicator in self.indicators.items():
            if isinstance(indicator, (EMA, SMA)):
                value = indicator.calculate(prices)
                results[f"{name}"] = float(value.iloc[-1]) if len(value) > 0 else None
        
        # RSI
        rsi = self.indicators["rsi_14"].calculate(prices)
        results["rsi"] = float(rsi.iloc[-1]) if len(rsi) > 0 else None
        
        # MACD
        macd = self.indicators["macd"].calculate(prices)
        results["macd"] = float(macd["macd"].iloc[-1]) if len(macd) > 0 else None
        results["macd_signal"] = float(macd["macd_signal"].iloc[-1]) if len(macd) > 0 else None
        results["macd_histogram"] = float(macd["macd_histogram"].iloc[-1]) if len(macd) > 0 else None
        
        # ATR
        atr = self.indicators["atr_14"].calculate(prices)
        results["atr"] = float(atr.iloc[-1]) if len(atr) > 0 else None
        
        # Bollinger Bands
        bb = self.indicators["bollinger"].calculate_with_deviation(prices)
        results["bb_upper"] = float(bb["bollinger_upper"].iloc[-1]) if len(bb) > 0 else None
        results["bb_middle"] = float(bb["bollinger_middle"].iloc[-1]) if len(bb) > 0 else None
        results["bb_lower"] = float(bb["bollinger_lower"].iloc[-1]) if len(bb) > 0 else None
        
        # VWAP
        if volumes is not None:
            vwap = self.indicators["vwap"].calculate_with_volume(prices, volumes)
            results["vwap"] = float(vwap.iloc[-1]) if len(vwap) > 0 else None
        
        return results
