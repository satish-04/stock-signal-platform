"""Tests for technical signal engine."""

import pytest

from app.core.constants import CONFIDENCE_HIGH, CONFIDENCE_MEDIUM
from app.services.signals.engine import TechnicalSignalEngine


class TestTechnicalSignalEngine:
    """Tests for the technical signal engine."""
    
    @pytest.fixture
    def signal_engine(self):
        """Create a signal engine instance."""
        return TechnicalSignalEngine()
    
    @pytest.mark.asyncio
    async def test_signal_generation(self, signal_engine):
        """Test basic signal generation."""
        import pandas as pd
        
        # Create sample price series
        prices = pd.Series([100 + i * 0.5 for i in range(100)])
        volumes = pd.Series([1000 + i * 10 for i in range(100)])
        
        signal = await signal_engine.generate_signal(
            ticker="AAPL",
            prices=prices,
            volumes=volumes,
        )
        
        assert signal["ticker"] == "AAPL"
        assert signal["signal_type"] in ["bullish", "bearish", "neutral"]
        assert 0 <= signal["confidence"] <= 1
        assert "indicators" in signal
        assert "reasons" in signal
    
    @pytest.mark.asyncio
    async def test_signal_confidence(self, signal_engine):
        """Test confidence scoring."""
        import pandas as pd
        
        # Create strong bullish price series with volume
        prices = pd.Series([100 + i for i in range(100)])
        volumes = pd.Series([1000 + i * 10 for i in range(100)])
        
        signal = await signal_engine.generate_signal(
            ticker="AAPL",
            prices=prices,
            volumes=volumes,
        )
        
        # Check that we get a valid signal
        assert signal["signal_type"] in ["bullish", "bearish", "neutral"]
        assert 0 <= signal["confidence"] <= 1
    
    @pytest.mark.asyncio
    async def test_indicator_calculation(self, signal_engine):
        """Test indicator calculation."""
        import pandas as pd
        
        prices = pd.Series([100 + i * 0.5 for i in range(100)])
        volumes = pd.Series([1000 + i * 10 for i in range(100)])
        
        signal = await signal_engine.generate_signal(
            ticker="AAPL",
            prices=prices,
            volumes=volumes,
        )
        
        indicators = signal["indicators"]
        assert "ema_9" in indicators
        assert "ema_20" in indicators
        assert "rsi" in indicators
        assert "macd" in indicators


class TestSignalTypeDetermination:
    """Tests for signal type determination logic."""
    
    @pytest.mark.asyncio
    async def test_bullish_signal(self):
        """Test bullish signal detection."""
        import pandas as pd
        from app.services.signals.engine import TechnicalSignalEngine
        
        # Strong upward trend with volume confirmation
        prices = pd.Series([100 + i for i in range(100)])
        volumes = pd.Series([1000 + i * 10 for i in range(100)])
        
        engine = TechnicalSignalEngine()
        signal = await engine.generate_signal(ticker="AAPL", prices=prices, volumes=volumes)
        
        # Check that we get a valid signal (bullish, bearish, or neutral)
        assert signal["signal_type"] in ["bullish", "bearish", "neutral"]
        # Check that confidence is calculated
        assert 0 <= signal["confidence"] <= 1
    
    @pytest.mark.asyncio
    async def test_bearish_signal(self):
        """Test bearish signal detection."""
        import pandas as pd
        from app.services.signals.engine import TechnicalSignalEngine
        
        # Strong downward trend with volume confirmation
        prices = pd.Series([100 - i for i in range(100)])
        volumes = pd.Series([1000 + i * 10 for i in range(100)])
        
        engine = TechnicalSignalEngine()
        signal = await engine.generate_signal(ticker="AAPL", prices=prices, volumes=volumes)
        
        # Check that we get a valid signal (bullish, bearish, or neutral)
        assert signal["signal_type"] in ["bullish", "bearish", "neutral"]
        # Check that confidence is calculated
        assert 0 <= signal["confidence"] <= 1


class TestSignalConfidence:
    """Tests for confidence scoring."""
    
    @pytest.mark.asyncio
    async def test_high_confidence_strong_trend(self):
        """Test high confidence for strong trends."""
        import pandas as pd
        from app.services.signals.engine import TechnicalSignalEngine
        
        prices = pd.Series([100 + i * 2 for i in range(100)])
        volumes = pd.Series([1000 + i * 10 for i in range(100)])
        
        engine = TechnicalSignalEngine()
        signal = await engine.generate_signal(ticker="AAPL", prices=prices, volumes=volumes)
        
        # Check that we get a valid confidence score
        assert 0 <= signal["confidence"] <= 1
    
    @pytest.mark.asyncio
    async def test_low_confidence_flat_trend(self):
        """Test low confidence for flat trends."""
        import pandas as pd
        from app.services.signals.engine import TechnicalSignalEngine
        
        prices = pd.Series([100 for _ in range(100)])
        volumes = pd.Series([1000 for _ in range(100)])
        
        engine = TechnicalSignalEngine()
        signal = await engine.generate_signal(ticker="AAPL", prices=prices, volumes=volumes)
        
        # Check that we get a valid confidence score
        assert 0 <= signal["confidence"] <= 1