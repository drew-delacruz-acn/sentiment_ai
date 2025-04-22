"""Tests for the quantile regression forecasting functionality."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.core.forecast import PriceForecast

pytestmark = pytest.mark.asyncio

@pytest.fixture(scope="function")
def sample_price_data():
    """Create sample price data for testing with a clear trend and some noise."""
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    # Create a trend with some seasonality and noise
    trend = np.linspace(100, 200, 100)  # Linear trend from 100 to 200
    seasonality = 10 * np.sin(np.linspace(0, 4*np.pi, 100))  # Seasonal component
    noise = np.random.normal(0, 5, 100)  # Random noise
    
    prices = pd.DataFrame({
        'Close': trend + seasonality + noise
    }, index=dates)
    
    return prices

@pytest.fixture(scope="function")
def minimal_price_data():
    """Create minimal price data (less than min_samples) for testing fallback behavior."""
    dates = pd.date_range(start='2023-01-01', periods=5, freq='D')
    prices = pd.DataFrame({
        'Close': np.linspace(100, 110, 5)  # Simple linear trend
    }, index=dates)
    
    return prices

@pytest.fixture(scope="function")
def constant_price_data():
    """Create price data with constant values to test edge cases."""
    dates = pd.date_range(start='2023-01-01', periods=20, freq='D')
    prices = pd.DataFrame({
        'Close': [100] * 20  # Constant price
    }, index=dates)
    
    return prices

async def test_prepare_data_valid_input(sample_price_data):
    """Test data preparation with valid price data."""
    forecaster = PriceForecast(min_samples=10)
    X, y = forecaster._prepare_data(sample_price_data)
    
    assert isinstance(X, np.ndarray), "X should be a numpy array"
    assert isinstance(y, np.ndarray), "y should be a numpy array"
    assert X.shape[0] == len(sample_price_data), "X should have same length as input data"
    assert y.shape[0] == len(sample_price_data), "y should have same length as input data"
    assert X.shape[1] == 1, "X should have single feature (time)"
    assert np.all(np.isfinite(X)) and np.all(np.isfinite(y)), "Data should not contain inf/nan values"

async def test_prepare_data_empty_input():
    """Test handling of empty price data."""
    forecaster = PriceForecast(min_samples=10)
    empty_df = pd.DataFrame(columns=['Close'])
    
    with pytest.raises(ValueError, match="Empty price data provided"):
        forecaster._prepare_data(empty_df)

async def test_prepare_data_missing_values():
    """Test handling of price data with missing values."""
    dates = pd.date_range(start='2023-01-01', periods=20, freq='D')
    prices = pd.DataFrame({
        'Close': np.random.normal(100, 10, 20)
    }, index=dates)
    prices.loc[prices.index[5:8], 'Close'] = np.nan
    
    forecaster = PriceForecast(min_samples=10)
    with pytest.raises(ValueError, match="Price data contains missing values"):
        forecaster._prepare_data(prices)

async def test_quantile_regression_fit(sample_price_data):
    """Test basic quantile regression fitting."""
    forecaster = PriceForecast(min_samples=10)
    X, y = forecaster._prepare_data(sample_price_data)
    
    # Test median (q=0.5) regression
    model = forecaster._fit_quantile_regression(X, y, quantile=0.5)
    predictions = forecaster._predict_with_intercept(model, X)
    
    assert len(predictions) == len(sample_price_data), "Predictions length should match input length"
    assert all(np.isfinite(predictions)), "Predictions should be finite numbers"
    
    # Basic sanity checks for the fit
    assert np.mean(predictions > y) > 0.4, "Around 50% predictions should be above actual values"
    assert np.mean(predictions > y) < 0.6, "Around 50% predictions should be below actual values"

async def test_multiple_quantile_levels(sample_price_data):
    """Test P10, P50, P90 quantile predictions."""
    forecaster = PriceForecast(min_samples=10)
    X, y = forecaster._prepare_data(sample_price_data)
    
    # Fit models for different quantiles
    q10_model = forecaster._fit_quantile_regression(X, y, quantile=0.1)
    q50_model = forecaster._fit_quantile_regression(X, y, quantile=0.5)
    q90_model = forecaster._fit_quantile_regression(X, y, quantile=0.9)
    
    q10 = forecaster._predict_with_intercept(q10_model, X)
    q50 = forecaster._predict_with_intercept(q50_model, X)
    q90 = forecaster._predict_with_intercept(q90_model, X)
    
    # Check quantile ordering
    assert np.all(q10 <= q50), "P10 should be less than or equal to P50"
    assert np.all(q50 <= q90), "P50 should be less than or equal to P90"
    
    # Check approximate quantile proportions
    assert 0.05 <= np.mean(y < q10) <= 0.15, "~10% values should be below P10"
    assert 0.85 <= np.mean(y < q90) <= 0.95, "~90% values should be below P90"

async def test_fallback_insufficient_data(minimal_price_data):
    """Test OLS fallback when samples < min_samples."""
    forecaster = PriceForecast(min_samples=10)
    result = forecaster.create_forecast(minimal_price_data, horizon_days=30)
    
    assert isinstance(result, dict), "Result should be a dictionary"
    assert 'dates' in result, "Result should have dates"
    assert 'bands' in result, "Result should have bands"
    assert all(key in result['bands'] for key in ['P10', 'P50', 'P90']), "Should have all quantile bands"
    
    # Check forecast length
    assert len(result['dates']) == 30, "Should forecast requested horizon"
    assert all(len(result['bands'][q]) == 30 for q in ['P10', 'P50', 'P90']), "All bands should have same length"
    
    # Check band ordering
    assert all(
        result['bands']['P10'][i] <= result['bands']['P50'][i] <= result['bands']['P90'][i]
        for i in range(30)
    ), "Quantile bands should maintain proper ordering"

async def test_create_forecast_complete(sample_price_data):
    """Test end-to-end forecast creation with sufficient data."""
    forecaster = PriceForecast(min_samples=10)
    horizon_days = 30
    result = forecaster.create_forecast(sample_price_data, horizon_days)
    
    # Check structure
    assert isinstance(result, dict), "Result should be a dictionary"
    assert 'dates' in result, "Result should contain dates"
    assert 'bands' in result, "Result should contain bands"
    assert all(q in result['bands'] for q in ['P10', 'P50', 'P90']), "Should have all quantile bands"
    
    # Check dimensions
    assert len(result['dates']) == horizon_days, "Should have correct forecast horizon"
    assert all(len(result['bands'][q]) == horizon_days for q in ['P10', 'P50', 'P90']), "All bands should have same length"
    
    # Check forecast starts after last historical date
    last_historical = sample_price_data.index[-1]
    first_forecast = pd.to_datetime(result['dates'][0])
    assert first_forecast > last_historical, "Forecast should start after historical data"
    
    # Check band ordering
    assert all(
        result['bands']['P10'][i] <= result['bands']['P50'][i] <= result['bands']['P90'][i]
        for i in range(horizon_days)
    ), "Quantile bands should maintain proper ordering"

async def test_handle_constant_prices(constant_price_data):
    """Test handling of non-varying price series."""
    forecaster = PriceForecast(min_samples=10)
    result = forecaster.create_forecast(constant_price_data, horizon_days=30)
    
    # In case of constant prices, all quantiles should be very close to the constant value
    constant_value = constant_price_data['Close'].iloc[0]
    for q in ['P10', 'P50', 'P90']:
        assert np.allclose(
            result['bands'][q], 
            [constant_value] * 30, 
            rtol=1e-2
        ), f"{q} should be close to constant value"

async def test_handle_extreme_values():
    """Test handling of extreme price values."""
    dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
    prices = pd.DataFrame({
        'Close': [1e6] * 25 + [1e-6] * 25  # Extreme high and low values
    }, index=dates)
    
    forecaster = PriceForecast(min_samples=10)
    result = forecaster.create_forecast(prices, horizon_days=30)
    
    # Check that the forecast handles extreme values without numerical issues
    assert all(np.isfinite(v) for q in ['P10', 'P50', 'P90'] for v in result['bands'][q]), \
        "Forecast should handle extreme values without producing inf/nan" 