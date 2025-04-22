import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import yfinance as yf
from typing import Optional, Tuple
import asyncio

from app.core.forecast import PriceForecast
from app.services.prices import PriceService

async def get_price_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch historical price data for a given ticker and date range.
    
    Args:
        ticker (str): Stock ticker symbol
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        
    Returns:
        pd.DataFrame: DataFrame with historical prices
    """
    price_service = PriceService()
    df = await price_service.get_historical_prices(ticker, start_date, end_date)
    return df[['Close']]

async def create_forecast_plot(
    ticker: str,
    start_date: str,
    end_date: Optional[str] = None,
    forecast_days: int = 30
) -> None:
    """
    Create and display an interactive plot showing historical prices and forecast bands.
    
    Args:
        ticker (str): Stock ticker symbol
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str, optional): End date in YYYY-MM-DD format. Defaults to today.
        forecast_days (int, optional): Number of days to forecast. Defaults to 30.
    """
    # Set end date to today if not provided
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    # Get historical data
    historical_data = await get_price_data(ticker, start_date, end_date)
    
    # Create forecast
    forecaster = PriceForecast(min_samples=10)
    forecast_result = forecaster.create_forecast(historical_data, forecast_days)
    
    # Create the plot
    fig = go.Figure()
    
    # Plot historical prices with custom hover template
    fig.add_trace(go.Scatter(
        x=historical_data.index,
        y=historical_data['Close'],
        name='Historical Price',
        line=dict(color='#2E86C1', width=2),
        mode='lines',
        hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                      '<b>Price</b>: $%{y:.2f}<br>' +
                      '<extra></extra>'
    ))
    
    # Convert forecast dates
    forecast_dates = pd.to_datetime(forecast_result['dates'])
    
    # Add forecast bands with improved styling
    # P90 band (upper)
    fig.add_trace(go.Scatter(
        x=forecast_dates,
        y=forecast_result['bands']['P90'],
        name='90th Percentile',
        line=dict(color='rgba(231, 76, 60, 0.0)'),
        mode='lines',
        fillcolor='rgba(231, 76, 60, 0.1)',
        fill='tonexty',
        hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                      '<b>P90</b>: $%{y:.2f}<br>' +
                      '<extra></extra>'
    ))
    
    # P50 (median) line
    fig.add_trace(go.Scatter(
        x=forecast_dates,
        y=forecast_result['bands']['P50'],
        name='Median Forecast',
        line=dict(color='#E74C3C', width=2, dash='dash'),
        mode='lines',
        hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                      '<b>Median</b>: $%{y:.2f}<br>' +
                      '<extra></extra>'
    ))
    
    # P10 band (lower)
    fig.add_trace(go.Scatter(
        x=forecast_dates,
        y=forecast_result['bands']['P10'],
        name='10th Percentile',
        line=dict(color='rgba(231, 76, 60, 0.0)'),
        mode='lines',
        fillcolor='rgba(231, 76, 60, 0.1)',
        fill='tonexty',
        hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br>' +
                      '<b>P10</b>: $%{y:.2f}<br>' +
                      '<extra></extra>'
    ))
    
    # Update layout with improved styling
    fig.update_layout(
        title=dict(
            text=f'{ticker} Price Forecast',
            font=dict(size=24, color='#2C3E50'),
            x=0.5,
            y=0.95
        ),
        xaxis=dict(
            title='Date',
            title_font=dict(size=14),
            gridcolor='rgba(189, 195, 199, 0.2)',
            showgrid=True
        ),
        yaxis=dict(
            title='Price ($)',
            title_font=dict(size=14),
            gridcolor='rgba(189, 195, 199, 0.2)',
            showgrid=True,
            tickprefix='$',
            tickformat='.2f'
        ),
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor='rgba(255, 255, 255, 0.8)'
        ),
        template='plotly_white',
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(t=100, l=60, r=60, b=60)
    )
    
    # Add a shape to mark the transition from historical to forecast data
    fig.add_shape(
        type="line",
        x0=historical_data.index[-1],
        x1=historical_data.index[-1],
        y0=0,
        y1=1,
        yref="paper",
        line=dict(
            color="rgba(128, 128, 128, 0.4)",
            dash="dot",
        )
    )
    
    # Add annotation for forecast start
    fig.add_annotation(
        x=historical_data.index[-1],
        y=1,
        yref="paper",
        text="Forecast Start",
        showarrow=False,
        yshift=10,
        font=dict(size=12, color="rgba(128, 128, 128, 0.8)")
    )
    
    # Show the plot
    fig.show()

async def main():
    # Example usage
    ticker = "AAPL"
    start_date = "2024-01-01"
    end_date = "2024-03-20"
    
    await create_forecast_plot(ticker, start_date, end_date)

if __name__ == "__main__":
    asyncio.run(main())