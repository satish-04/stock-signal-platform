"""Tests for API endpoints."""

import pytest

from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health endpoint."""
    
    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "trading_mode" in data
        assert "market_data_mode" in data


class TestRootEndpoint:
    """Tests for root endpoint."""
    
    def test_root(self, client):
        """Test the root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert data["name"] == "Stock Signal App"
        assert "version" in data


class TestSignalsAPI:
    """Tests for signals API."""
    
    def test_get_signals_empty(self, client):
        """Test getting signals when none exist."""
        response = client.get("/v1/signals/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_signal(self, client):
        """Test creating a signal."""
        signal_data = {
            "ticker": "AAPL",
            "signal_type": "bullish",
            "confidence": 0.85,
            "technical_score": 0.92,
        }
        
        response = client.post("/v1/signals/", json=signal_data)
        
        assert response.status_code == 201 or response.status_code == 200
        data = response.json()
        assert data["ticker"] == "AAPL"
        assert data["signal_type"] == "bullish"


class TestOptionsAPI:
    """Tests for options API."""
    
    def test_get_option_chain(self, client):
        """Test getting option chain for a ticker."""
        response = client.get("/v1/options/AAPL")
        
        assert response.status_code == 200
        data = response.json()
        assert "ticker" in data
    
    def test_get_multiple_option_chains(self, client):
        """Test getting option chains for multiple tickers."""
        response = client.get("/v1/options/", params={"ticker_list": ["AAPL", "MSFT"]})
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2


class TestTradesAPI:
    """Tests for trades API."""
    
    def test_get_trades_empty(self, client):
        """Test getting trades when none exist."""
        response = client.get("/v1/trades/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
