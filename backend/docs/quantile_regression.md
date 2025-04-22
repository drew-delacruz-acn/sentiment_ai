# Quantile Regression Implementation for Price Forecasting

## Overview
This document outlines the implementation of quantile regression for price forecasting in the sentiment analysis backtesting system. The implementation provides probability bands for price movements, helping investors understand potential price ranges with confidence levels.

## Implementation Components

### 1. Core Forecasting Class
```python
class PriceForecast:
    def __init__(self, min_samples: int = 10):
        self.min_samples = min_samples
        self.quantiles = [0.1, 0.5, 0.9]  # P10, P50, P90
```

### 2. Data Structure
#### Input
```python
prices_df = {
    'Date': datetime,    # Index
    'Close': float      # Target variable for forecasting
}
```

#### Output
```python
forecast_result = {
    'dates': ['2024-04-01', '2024-04-02', ...],  # Future dates
    'bands': {
        'P10': [180.5, 181.2, ...],  # Lower band
        'P50': [190.2, 191.1, ...],  # Median forecast
        'P90': [200.1, 201.3, ...]   # Upper band
    }
}
```

## Technical Implementation

### 1. Quantile Regression Process
1. **Data Preparation**
   ```python
   def _prepare_data(self, prices: pd.DataFrame):
       X = np.arange(len(prices)).reshape(-1, 1)  # Time feature
       y = prices['Close'].values                 # Target prices
       return X, y
   ```

2. **Model Fitting**
   ```python
   def _fit_quantile_regression(self, X, y, quantile):
       model = QuantReg(y, self._add_intercept(X))
       return model.fit(q=quantile)
   ```

3. **Forecasting**
   ```python
   def create_forecast(self, price_data: pd.DataFrame, horizon_days: int = 30) -> Dict:
       """Create price forecast with confidence bands."""
       X, y = self._prepare_data(price_data)
       
       # Generate predictions for P10, P50, P90
       forecast_steps = np.arange(len(X), len(X) + horizon_days)
       forecast_features = forecast_steps.reshape(-1, 1)
       
       try:
           if len(price_data) < self.min_samples:
               raise ValueError("Insufficient samples for quantile regression")

           # Fit models for different quantiles
           q10_model = self._fit_quantile_regression(X, y, quantile=0.1)
           q50_model = self._fit_quantile_regression(X, y, quantile=0.5)
           q90_model = self._fit_quantile_regression(X, y, quantile=0.9)

           # Generate predictions
           p10 = self._predict_with_intercept(q10_model, forecast_features)
           p50 = self._predict_with_intercept(q50_model, forecast_features)
           p90 = self._predict_with_intercept(q90_model, forecast_features)
       except Exception:
           # Fallback to OLS with confidence intervals
           model = self._fallback_to_ols(X, y)
           p50 = model.predict(forecast_features)
           residuals = y - model.predict(X)
           std_dev = np.std(residuals)
           p10 = p50 - 1.28 * std_dev
           p90 = p50 + 1.28 * std_dev

       return {
           'dates': forecast_dates.strftime('%Y-%m-%d').tolist(),
           'bands': {
               'P10': p10.tolist(),
               'P50': p50.tolist(),
               'P90': p90.tolist()
           }
       }
   ```

### 2. API Integration
```python
@app.get("/api/forecast/{ticker}")
async def forecast_price(
    ticker: str,
    start_date: str,
    forecast_days: int = 30
):
    """Generate price forecast for a given ticker."""
    try:
        # Validate start date
        start = datetime.strptime(start_date, "%Y-%m-%d")
        if start > datetime.now():
            raise HTTPException(status_code=400, detail="Future start date not allowed")
            
        # Get historical prices
        historical_data = await price_service.get_historical_prices(ticker, start_date)
        
        if len(historical_data) < 30:
            raise HTTPException(status_code=400, detail="Insufficient historical data")
            
        # Generate forecast
        forecaster = PriceForecast()
        forecast_result = forecaster.create_forecast(historical_data, forecast_days)
        
        return {
            "historical": {
                "dates": historical_data.index.strftime("%Y-%m-%d").tolist(),
                "prices": historical_data["Close"].tolist()
            },
            "forecast": forecast_result,
            "metadata": {
                "ticker": ticker,
                "forecast_days": forecast_days
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Testing Implementation

### 1. Test Setup
```python
@pytest.fixture
def client():
    """Create a test client with mocked services."""
    global_state.price_service = MagicMock(spec=PriceService)
    return TestClient(app)

@pytest.fixture
def mock_price_data():
    """Create realistic test price data."""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    trend = np.linspace(100, 200, 100)
    seasonality = 10 * np.sin(np.linspace(0, 4*np.pi, 100))
    noise = np.random.normal(0, 5, 100)
    
    return pd.DataFrame({
        'Close': trend + seasonality + noise
    }, index=dates)
```

### 2. Test Cases
```python
@pytest.mark.asyncio
async def test_forecast_endpoint_success(client, mock_price_data):
    """Test successful forecast generation."""
    with patch.object(global_state.price_service, 'get_historical_prices', 
                     return_value=mock_price_data):
        response = client.get(
            "/api/forecast/AAPL",
            params={
                "start_date": "2024-01-01",
                "forecast_days": 30
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "historical" in data
        assert "forecast" in data
        assert "metadata" in data
```

### 3. Error Cases
```python
@pytest.mark.asyncio
async def test_forecast_endpoint_insufficient_data(client):
    """Test rejection of insufficient historical data."""
    small_data = pd.DataFrame({
        'Close': np.linspace(100, 110, 5)
    }, index=pd.date_range(start='2024-01-01', periods=5))
    
    with patch.object(global_state.price_service, 'get_historical_prices', 
                     return_value=small_data):
        response = client.get("/api/forecast/AAPL")
        assert response.status_code == 400
        assert "Insufficient historical data" in response.json()["detail"]
```

## Dependencies
- `statsmodels`: Quantile regression implementation
- `pandas`: Data manipulation
- `numpy`: Numerical operations
- `scikit-learn`: Fallback OLS implementation
- `pytest`: Testing framework
- `pytest-asyncio`: Async test support
- `httpx`: Async HTTP client

## Error Handling
1. Input Validation
   - Invalid date formats (422)
   - Future start dates (400)
   - Insufficient data (400)
2. Service Errors
   - Price service unavailable (503)
   - No data found (404)
3. Processing Errors
   - Forecast generation failures (500)
   - Model fitting errors (500)

## Next Steps
1. Performance optimization
   - Caching frequent calculations
   - Batch processing
2. Enhanced features
   - Multiple forecast horizons
   - Additional technical indicators
3. Monitoring
   - Forecast accuracy metrics
   - API performance tracking