"""Tests for technical indicators."""

import pytest

from app.services.indicators.engine import (
    ATR,
    BollingerBands,
    EMA,
    MACD,
    RSI,
    SMA,
    IndicatorEngine,
)


class TestIndicators:
    """Tests for individual indicators."""
    
    def test_ema_calculation(self):
        """Test EMA calculation."""
        import pandas as pd
        
        prices = pd.Series([100, 101, 102, 103, 104])
        ema = EMA(period=3)
        
        result = ema.calculate(prices)
        
        assert len(result) == len(prices)
        assert not result.isna().all()
    
    def test_sma_calculation(self):
        """Test SMA calculation."""
        import pandas as pd
        
        prices = pd.Series([100, 101, 102, 103, 104])
        sma = SMA(period=3)
        
        result = sma.calculate(prices)
        
        assert len(result) == len(prices)
        assert result.iloc[2] == 101.0  # Average of first 3 prices
    
    def test_rsi_calculation(self):
        """Test RSI calculation."""
        import pandas as pd
        
        # More data points needed for RSI calculation with period=3
        prices = pd.Series([100 + i * 0.5 for i in range(20)])
        rsi = RSI(period=3)
        
        result = rsi.calculate(prices)
        
        assert len(result) == len(prices)
        # RSI should be between 0 and 100 (ignore NaN values at start)
        non_nan = result.dropna()
        if len(non_nan) > 0:
            assert (non_nan >= 0).all()
            assert (non_nan <= 100).all()
    
    def test_macd_calculation(self):
        """Test MACD calculation."""
        import pandas as pd
        
        prices = pd.Series([100 + i * 0.5 for i in range(30)])
        macd = MACD(fast=12, slow=26, signal=9)
        
        result = macd.calculate(prices)
        
        assert "macd" in result.columns
        assert "macd_signal" in result.columns
        assert "macd_histogram" in result.columns
    
    def test_atr_calculation(self):
        """Test ATR calculation."""
        import pandas as pd
        
        prices = pd.Series([100 + i * 0.5 for i in range(20)])
        atr = ATR(period=14)
        
        result = atr.calculate(prices)
        
        assert len(result) == len(prices)
    
    def test_bollinger_bands_calculation(self):
        """Test Bollinger Bands calculation."""
        import pandas as pd
        
        prices = pd.Series([100 + i * 0.5 for i in range(30)])
        bb = BollingerBands()
        
        result = bb.calculate_with_deviation(prices)
        
        assert "bollinger_upper" in result.columns
        assert "bollinger_middle" in result.columns
        assert "bollinger_lower" in result.columns


class TestIndicatorEngine:
    """Tests for indicator engine."""
    
    @pytest.fixture
    def indicator_engine(self):
        """Create an indicator engine instance."""
        return IndicatorEngine()
    
    @pytest.mark.asyncio
    async def test_compute_all(self, indicator_engine):
        """Test computing all indicators."""
        import pandas as pd
        
        prices = pd.Series([100 + i * 0.5 for i in range(50)])
        volumes = pd.Series([1000 + i * 10 for i in range(50)])
        
        indicators = await indicator_engine.compute_all(prices, volumes)
        
        # Check for expected indicators
        assert "ema_9" in indicators
        assert "ema_20" in indicators
        assert "rsi" in indicators
        assert "macd" in indicators
        assert "atr" in indicators
    
    @pytest.mark.asyncio
    async def test_indicator_engine_without_volume(self, indicator_engine):
        """Test computing indicators without volume data."""
        import pandas as pd
        
        prices = pd.Series([100 + i * 0.5 for i in range(50)])
        
        indicators = await indicator_engine.compute_all(prices)
        
        # VWAP requires volume
        assert "vwap" not in indicators or indicators["vwap"] is None
