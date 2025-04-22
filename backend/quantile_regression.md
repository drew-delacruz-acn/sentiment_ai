# Quantile Regression Implementation for Price Forecasting

## Overview
This document outlines the implementation of quantile regression for price forecasting in the sentiment analysis backtesting system. The implementation provides probability bands for price movements, helping investors understand potential price ranges with confidence levels.

## Implementation Components

### 1. Core Forecasting Class
```python
class PriceForecast:
    def __init__(self, min_samples: int = 10):
        self.min_samples = min_samples
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
       model = QuantReg(y, X)
       return model.fit(q=quantile)
   ```

3. **Forecasting**
   - Fit three models (P10, P50, P90)
   - Generate future dates
   - Create probability bands

### 2. Fallback Mechanism
For insufficient data (< 10 samples):
```python
def _fallback_to_ols(self, prices, horizon_days=90):
    # Use Linear Regression with standard error bands
    # Approximate quantiles using normal distribution
```

## Visualization Implementation

### 1. Backend Visualization Script
```python
async def create_forecast_plot(
    ticker: str,
    start_date: str,
    end_date: Optional[str] = None,
    forecast_days: int = 30
) -> None:
    """
    Create an interactive plot showing historical prices and forecast bands.
    """
    historical_data = await get_price_data(ticker, start_date, end_date)
    forecaster = PriceForecast(min_samples=10)
    forecast_result = forecaster.create_forecast(historical_data, forecast_days)
    
    fig = go.Figure()
    
    # Historical prices
    fig.add_trace(go.Scatter(
        x=historical_data.index,
        y=historical_data['Close'],
        name='Historical Price',
        line=dict(color='#2E86C1', width=2),
        mode='lines'
    ))
    
    # Forecast bands (P10, P50, P90)
    forecast_dates = pd.to_datetime(forecast_result['dates'])
    
    fig.add_trace(go.Scatter(
        x=forecast_dates,
        y=forecast_result['bands']['P90'],
        name='90th Percentile',
        line=dict(color='rgba(231, 76, 60, 0.0)'),
        fillcolor='rgba(231, 76, 60, 0.1)',
        fill='tonexty'
    ))
    
    fig.add_trace(go.Scatter(
        x=forecast_dates,
        y=forecast_result['bands']['P50'],
        name='Median Forecast',
        line=dict(color='#E74C3C', width=2, dash='dash')
    ))
    
    fig.add_trace(go.Scatter(
        x=forecast_dates,
        y=forecast_result['bands']['P10'],
        name='10th Percentile',
        fillcolor='rgba(231, 76, 60, 0.1)',
        fill='tonexty'
    ))
```

## Frontend Integration Plan

### 1. API Endpoint Implementation
```python
@router.get("/api/forecast")
async def get_forecast(
    ticker: str, 
    start_date: str, 
    end_date: str = None,
    forecast_days: int = 30
):
    """
    Endpoint to serve forecast data to the frontend.
    Returns both historical and forecast data in a format ready for plotting.
    """
    try:
        price_service = PriceService()
        historical_data = await price_service.get_historical_prices(
            ticker, start_date, end_date
        )
        
        forecaster = PriceForecast(min_samples=10)
        forecast_result = forecaster.create_forecast(
            historical_data[['Close']], 
            forecast_days
        )
        
        return {
            "historical": {
                "dates": historical_data.index.strftime('%Y-%m-%d').tolist(),
                "prices": historical_data['Close'].tolist()
            },
            "forecast": {
                "dates": forecast_result['dates'],
                "bands": forecast_result['bands']
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 2. React Component Structure
```typescript
// Types
interface ForecastData {
    historical: {
        dates: string[];
        prices: number[];
    };
    forecast: {
        dates: string[];
        bands: {
            P10: number[];
            P50: number[];
            P90: number[];
        };
    };
}

// Component
interface PriceForecastProps {
    ticker: string;
    startDate: string;
    endDate?: string;
}

const PriceForecast: React.FC<PriceForecastProps>
```

### 3. Frontend Implementation Steps

1. **Package Installation**
   ```bash
   cd frontend
   npm install react-plotly.js plotly.js
   ```

2. **Component Organization**
   ```
   frontend/
   ├── src/
   │   ├── components/
   │   │   ├── PriceForecast/
   │   │   │   ├── index.tsx
   │   │   │   ├── types.ts
   │   │   │   └── styles.css
   │   │   └── ...
   │   └── ...
   ```

3. **Integration Points**
   - Dashboard page
   - Analysis views
   - Comparison charts

4. **State Management**
   - Cache forecast results
   - Handle loading states
   - Error boundaries

### 4. Styling and UX Considerations

1. **Chart Customization**
   - Professional color scheme
   - Clear band separation
   - Interactive tooltips
   - Responsive design

2. **User Controls**
   - Date range selection
   - Forecast horizon adjustment
   - Export options
   - Zoom controls

3. **Performance Optimization**
   - Data caching
   - Lazy loading
   - Debounced updates

### 5. Testing Strategy

1. **Unit Tests**
   - Component rendering
   - Data transformations
   - Error handling

2. **Integration Tests**
   - API communication
   - State management
   - User interactions

3. **Visual Regression**
   - Chart appearance
   - Responsive behavior
   - Animation effects

## Deployment Considerations

1. **Backend**
   - API rate limiting
   - Cache invalidation
   - Error monitoring

2. **Frontend**
   - Bundle optimization
   - Lazy loading
   - Performance monitoring

3. **DevOps**
   - CI/CD pipeline
   - Environment configuration
   - Monitoring setup

## Next Steps

1. **Immediate Tasks**
   - Implement API endpoint
   - Create React component
   - Set up testing framework

2. **Future Enhancements**
   - Additional technical indicators
   - Custom visualization options
   - Advanced forecast settings

3. **Monitoring Plan**
   - User interaction tracking
   - Performance metrics
   - Error reporting

## Integration Points

### 1. Price Service Integration
```python
class PriceService:
    def __init__(self):
        self.forecaster = PriceForecast()
        
    async def get_price_analysis(self, ticker: str):
        prices = await self.get_historical_prices(ticker)
        forecast = self.forecaster.create_forecast(prices)
        return {
            'historical': prices.to_dict(),
            'forecast': forecast
        }
```

### 2. API Endpoint
```python
@app.get("/analyze/{ticker}")
async def analyze_ticker(ticker: str, horizon_days: int = 90):
    price_service = get_price_service()
    results = await price_service.get_price_analysis(
        ticker, horizon_days
    )
    return results
```

## Frontend Visualization

### 1. Data Structure for Charts
```typescript
interface ForecastData {
    dates: string[];
    bands: {
        P10: number[];
        P50: number[];
        P90: number[];
    };
}
```

### 2. React-Plotly Implementation
```typescript
const ForecastChart = ({ data }: { data: ForecastData }) => {
    return (
        <Plot
            data={[
                // Historical prices line
                {
                    x: data.historical_dates,
                    y: data.historical_prices,
                    type: 'scatter',
                    name: 'Historical'
                },
                // Median forecast
                {
                    x: data.forecast.dates,
                    y: data.forecast.bands.P50,
                    type: 'scatter',
                    name: 'Forecast',
                    line: { dash: 'dash' }
                },
                // Confidence band
                {
                    x: [...data.forecast.dates, ...data.forecast.dates.reverse()],
                    y: [...data.forecast.bands.P90, ...data.forecast.bands.P10.reverse()],
                    fill: 'tonexty',
                    type: 'scatter',
                    name: '80% Confidence'
                }
            ]}
        />
    );
};
```

## Future Enhancements

1. **Additional Features**
   - Technical indicators (MA, RSI)
   - Sentiment scores integration
   - Market indices correlation

2. **Model Improvements**
   - Non-linear transformations
   - Feature engineering
   - Cross-validation

3. **Performance Optimization**
   - Caching frequent calculations
   - Batch processing
   - Async computation

## Dependencies
- `statsmodels`: Quantile regression implementation
- `pandas`: Data manipulation
- `numpy`: Numerical operations
- `scikit-learn`: Fallback OLS implementation

## Testing Strategy
1. Unit tests for core forecasting
2. Integration tests with price service
3. Visual regression tests for charts
4. Performance benchmarks

## Error Handling
1. Insufficient data fallback
2. Invalid date ranges
3. API errors
4. Numerical instabilities

## Monitoring
1. Forecast accuracy metrics
2. Performance metrics
3. Error rates
4. Usage patterns