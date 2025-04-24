# Market Index Comparison Implementation Plan

This document outlines the plan to replace the current simplified buy & hold comparison line with a full market index comparison in the equity curve visualization.

## Problem
Currently, the buy & hold comparison is displayed as a straight line connecting only two points: the initial investment value and the final value. This creates a misleading visualization when the return is negative, as it shows a continuously declining line that doesn't reflect actual market movements.

## Solution
Implement a proper market index comparison that shows the actual historical performance of an index (like S&P 500) over the same time period as the backtest. This will provide a more realistic benchmark for strategy evaluation.

## Implementation Steps

### 1. Backend Changes

#### Step 1.1: Add Market Index Service
Create a new service file to handle fetching market index data:

```python
# backend/app/services/market_index.py
import yfinance as yf
import pandas as pd
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def fetch_market_index(ticker="^GSPC", start_date=None, end_date=None):
    """
    Fetch market index data using yfinance.
    
    Args:
        ticker: Index ticker symbol (default: ^GSPC for S&P 500)
        start_date: Start date for data in YYYY-MM-DD format
        end_date: End date for data in YYYY-MM-DD format
        
    Returns:
        DataFrame with index data
    """
    try:
        # Convert string dates to datetime if needed
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
        logger.info(f"Fetching {ticker} index data from {start_date} to {end_date}")
        
        # Download market data
        index_data = yf.download(
            ticker, 
            start=start_date, 
            end=end_date,
            progress=False
        )
        
        if index_data.empty:
            logger.warning(f"No data returned for {ticker}")
            return pd.DataFrame()
            
        logger.info(f"Successfully fetched {len(index_data)} data points for {ticker}")
        return index_data
        
    except Exception as e:
        logger.error(f"Error fetching market index data: {str(e)}")
        return pd.DataFrame()
```

#### Step 1.2: Update Market Performance Analysis
Modify the `analyze_market_performance` function in `backend/app/api/backtest.py`:

```python
async def analyze_market_performance(price_data, backtest_results):
    """Analyze market performance compared to strategy."""
    try:
        start_date = price_data.index.min()
        end_date = price_data.index.max()
        start_price = price_data.loc[start_date, 'Close']
        end_price = price_data.loc[end_date, 'Close']
        market_return = (end_price / start_price) - 1
        
        strategy_return = backtest_results['performance_metrics']['total_return']
        initial_capital = backtest_results['performance_metrics'].get('initial_capital', 100000)
        
        # Calculate buy and hold performance (keep for backward compatibility)
        shares_bought = initial_capital / start_price
        final_market_value = shares_bought * end_price
        buy_hold_return = (final_market_value / initial_capital) - 1
        
        # Fetch market index data
        from app.services.market_index import fetch_market_index
        index_ticker = "^GSPC"  # S&P 500 by default
        index_data = await fetch_market_index(
            ticker=index_ticker,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        # Prepare result with base comparison data
        result = {
            'period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            },
            'market_return': float(market_return),
            'strategy_return': float(strategy_return),
            'outperformance': float(strategy_return - market_return),
            'buy_hold': {
                'initial_value': float(initial_capital),
                'final_value': float(final_market_value),
                'return': float(buy_hold_return)
            }
        }
        
        # Add market index data if available
        if not index_data.empty:
            # Normalize index to initial capital
            initial_index_value = index_data['Close'].iloc[0]
            
            # Calculate normalized index values
            index_values = [float(v * initial_capital / initial_index_value) for v in index_data['Close']]
            index_dates = [d.strftime('%Y-%m-%d') for d in index_data.index]
            
            # Calculate index return
            index_return = (index_data['Close'].iloc[-1] / index_data['Close'].iloc[0]) - 1
            
            # Add to response
            result['market_index'] = {
                'ticker': index_ticker,
                'name': 'S&P 500',
                'initial_value': float(initial_capital),
                'final_value': float(index_values[-1]),
                'return': float(index_return),
                'dates': index_dates,
                'values': index_values
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing market performance: {str(e)}")
        return {'error': str(e)}
```

### 2. Frontend Changes

#### Step 2.1: Update Equity Curve Visualization
Modify the plot component in `frontend/src/App.tsx`:

```javascript
<Plot
  data={[
    // Strategy line (unchanged)
    {
      x: backtestData.data.equity_curve.dates,
      y: backtestData.data.equity_curve.values,
      type: 'scatter',
      mode: 'lines',
      name: 'Portfolio Value',
      line: { color: 'rgb(16, 185, 129)', width: 3 },
      fill: 'tozeroy',
      fillcolor: 'rgba(16, 185, 129, 0.1)',
    },
    
    // Market index line (new)
    ...(backtestData.data.market_comparison?.market_index ? [{
      x: backtestData.data.market_comparison.market_index.dates,
      y: backtestData.data.market_comparison.market_index.values,
      type: 'scatter',
      mode: 'lines',
      name: `${backtestData.data.market_comparison.market_index.name}`,
      line: { color: 'rgba(79, 70, 229, 0.8)', width: 2, dash: 'dash' } as PlotlyLineType
    }] : []),
    
    // Buy & hold line (keep but make optional or hide)
    ...(backtestData.data.market_comparison?.buy_hold && !backtestData.data.market_comparison?.market_index ? [{
      x: [
        backtestData.data.equity_curve.dates[0], 
        backtestData.data.equity_curve.dates[backtestData.data.equity_curve.dates.length - 1]
      ],
      y: [
        backtestData.data.market_comparison.buy_hold.initial_value, 
        backtestData.data.market_comparison.buy_hold.final_value
      ],
      type: 'scatter',
      mode: 'lines',
      name: 'Buy & Hold',
      line: { color: 'rgba(79, 70, 229, 0.8)', width: 2, dash: 'dash' } as PlotlyLineType
    }] : []),
    
    // Initial capital line (unchanged)
    {
      x: backtestData.data.equity_curve.dates,
      y: Array(backtestData.data.equity_curve.dates.length).fill(
        backtestData.data.performance_metrics.initial_capital
      ),
      type: 'scatter',
      mode: 'lines',
      name: 'Initial Capital',
      line: { color: 'rgba(209, 213, 219, 0.5)', width: 1, dash: 'dot' } as PlotlyLineType
    }
  ]}
  // Rest of the component remains unchanged
  {...}
/>
```

#### Step 2.2: Update the Metrics Component
Modify the market comparison table in `frontend/src/components/Metrics.tsx`:

```jsx
{/* Market Comparison */}
{comparison && (
  <div className="mt-6">
    <h3 className="text-lg font-medium mb-4 text-gray-300 border-b border-gray-700 pb-2">Market Comparison</h3>
    <div className="bg-dark-700 p-4 rounded-md">
      <table className="w-full">
        <thead>
          <tr>
            <th className="py-2 px-4 text-left text-sm font-medium text-gray-400 border border-gray-700">METRIC</th>
            <th className="py-2 px-4 text-right text-sm font-medium text-gray-400 border border-gray-700">VALUE</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-700">
          <tr>
            <td className="py-2 px-4 text-sm font-medium text-gray-300 border border-gray-700">Strategy Return</td>
            <td className={`py-2 px-4 text-sm font-extrabold text-right border border-gray-700 ${getValueColor(comparison.strategy_return)}`}>{formatPercent(comparison.strategy_return)}</td>
          </tr>
          
          {/* Add Market Index Return */}
          {comparison.market_index && (
            <tr className="bg-dark-600">
              <td className="py-2 px-4 text-sm font-medium text-gray-300 border border-gray-700">{comparison.market_index.name} Return</td>
              <td className={`py-2 px-4 text-sm font-extrabold text-right border border-gray-700 ${getValueColor(comparison.market_index.return)}`}>{formatPercent(comparison.market_index.return)}</td>
            </tr>
          )}
          
          {/* Keep Buy & Hold Return */}
          <tr className="bg-dark-600">
            <td className="py-2 px-4 text-sm font-medium text-gray-300 border border-gray-700">Buy & Hold Return</td>
            <td className={`py-2 px-4 text-sm font-extrabold text-right border border-gray-700 ${getValueColor(comparison.buy_hold.return)}`}>{formatPercent(comparison.buy_hold.return)}</td>
          </tr>
          
          <tr>
            <td className="py-2 px-4 text-sm font-medium text-gray-300 border border-gray-700">Outperformance</td>
            <td className={`py-2 px-4 text-sm font-extrabold text-right border border-gray-700 ${getValueColor(comparison.outperformance)}`}>{formatPercent(comparison.outperformance)}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
)}
```

### 3. Testing Plan

1. **Unit Tests**
   - Create unit tests for the `fetch_market_index` function
   - Test with different date ranges and index tickers
   - Verify error handling with invalid inputs

2. **Integration Tests**
   - Test the API endpoint with real data
   - Verify the response format includes market index data
   - Check normalization logic produces expected values

3. **Manual Testing**
   - Verify market index line appears properly in the UI
   - Check that the values match expectations for known periods
   - Test with different stocks and time periods

### 4. Future Enhancements

1. **Configurable Indices**
   - Allow users to select different market indices for comparison (SPY, DIA, QQQ, etc.)
   - Add a dropdown in the UI to switch between indices

2. **Index Data Caching**
   - Implement Redis caching for index data to reduce API calls
   - Set appropriate TTL for cached data

3. **Multiple Comparisons**
   - Allow multiple indices to be displayed simultaneously
   - Add legend toggles to show/hide different comparison lines

4. **Relative Performance View**
   - Add option to normalize all lines to 100% at start date
   - Display relative performance rather than absolute values

## Timeline

- **Day 1**: Implement backend changes and test
- **Day 2**: Implement frontend changes and test
- **Day 3**: Integrate, test end-to-end, and document 