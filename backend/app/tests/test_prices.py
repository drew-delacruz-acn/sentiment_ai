import pytest
import pandas as pd
from datetime import datetime, timedelta
from app.services.prices import PriceService

@pytest.mark.asyncio
async def test_get_historical_prices():
    service = PriceService()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Test single ticker
    df = await service.get_historical_prices('AAPL', start_date, end_date)
    assert not df.empty
    assert all(col in df.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume'])
    
@pytest.mark.asyncio
async def test_get_batch_prices():
    service = PriceService()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    tickers = ['AAPL', 'MSFT', 'GOOGL']
    
    # Test multiple tickers
    results = await service.get_batch_prices(tickers, start_date, end_date)
    assert len(results) == len(tickers)
    assert all(isinstance(df, pd.DataFrame) for df in results.values())
    assert all(not df.empty for df in results.values())
    
@pytest.mark.asyncio
async def test_get_latest_price():
    service = PriceService()
    
    # Test latest price
    price = await service.get_latest_price('AAPL')
    assert price is not None
    assert isinstance(price, float)
    
@pytest.mark.asyncio
async def test_invalid_ticker():
    service = PriceService()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Test invalid ticker
    df = await service.get_historical_prices('INVALID_TICKER', start_date, end_date)
    assert df.empty 