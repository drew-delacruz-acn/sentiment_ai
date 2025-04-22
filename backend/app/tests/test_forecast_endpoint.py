"""Tests for the forecast API endpoint (MVP version)."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

from app.main import app, global_state
from app.core.forecast import PriceForecast
from app.services.prices import PriceService

@pytest.fixture
def client():
    """Create a test client."""
    # Mock the price service
    global_state.price_service = MagicMock(spec=PriceService)
    return TestClient(app)

@pytest.fixture
def mock_price_data():
    """Create realistic test price data with sufficient samples."""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    # Create a trend with some seasonality and noise
    trend = np.linspace(100, 200, 100)
    seasonality = 10 * np.sin(np.linspace(0, 4*np.pi, 100))
    noise = np.random.normal(0, 5, 100)
    
    return pd.DataFrame({
        'Close': trend + seasonality + noise
    }, index=dates)

@pytest.mark.asyncio
async def test_forecast_endpoint_success(client, mock_price_data):
    """Test successful forecast generation."""
    with patch.object(global_state.price_service, 'get_historical_prices', return_value=mock_price_data):
        response = client.get(
            "/api/forecast/AAPL",
            params={
                "start_date": "2024-01-01",
                "forecast_days": 30
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "historical" in data
        assert "forecast" in data
        assert "metadata" in data
        
        # Check historical data
        assert len(data["historical"]["dates"]) == len(mock_price_data)
        assert len(data["historical"]["prices"]) == len(mock_price_data)
        
        # Check forecast data
        assert len(data["forecast"]["dates"]) == 30
        assert all(band in data["forecast"]["bands"] for band in ["P10", "P50", "P90"])
        assert all(len(data["forecast"]["bands"][band]) == 30 for band in ["P10", "P50", "P90"])
        
        # Check metadata
        assert data["metadata"]["ticker"] == "AAPL"
        assert data["metadata"]["forecast_days"] == 30

@pytest.mark.asyncio
async def test_forecast_endpoint_insufficient_data(client):
    """Test rejection of insufficient historical data."""
    small_data = pd.DataFrame({
        'Close': np.linspace(100, 110, 5)
    }, index=pd.date_range(start='2024-01-01', periods=5))
    
    with patch.object(global_state.price_service, 'get_historical_prices', return_value=small_data):
        response = client.get(
            "/api/forecast/AAPL",
            params={"start_date": "2024-01-01"}
        )
        
        assert response.status_code == 400
        assert "Insufficient historical data" in response.json()["detail"]

@pytest.mark.asyncio
async def test_forecast_endpoint_no_data(client):
    """Test behavior when no historical data is found."""
    with patch.object(global_state.price_service, 'get_historical_prices', return_value=pd.DataFrame()):
        response = client.get(
            "/api/forecast/INVALID",
            params={"start_date": "2024-01-01"}
        )
        
        assert response.status_code == 404
        assert "No price data found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_forecast_endpoint_invalid_dates(client):
    """Test handling of invalid date formats."""
    response = client.get(
        "/api/forecast/AAPL",
        params={"start_date": "invalid-date"}
    )
    
    assert response.status_code == 422  # FastAPI validation error

@pytest.mark.asyncio
async def test_forecast_endpoint_future_start_date(client):
    """Test handling of future start dates."""
    future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    response = client.get(
        "/api/forecast/AAPL",
        params={"start_date": future_date}
    )
    
    assert response.status_code == 400
    assert "Future start date" in response.json()["detail"]

@pytest.mark.asyncio
async def test_forecast_endpoint_band_ordering(client, mock_price_data):
    """Test that forecast bands maintain proper ordering (P10 ≤ P50 ≤ P90)."""
    with patch.object(global_state.price_service, 'get_historical_prices', return_value=mock_price_data):
        response = client.get(
            "/api/forecast/AAPL",
            params={"start_date": "2024-01-01"}
        )
        
        assert response.status_code == 200
        data = response.json()
        bands = data["forecast"]["bands"]
        
        # Check band ordering for each forecast point
        for i in range(len(bands["P10"])):
            assert bands["P10"][i] <= bands["P50"][i] <= bands["P90"][i] 