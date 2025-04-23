import asyncio
import pytest
from datetime import datetime
from app.core.strategy import EarningsSentimentStrategy
from app.services.prices import PriceService
from app.services.sentiment_analyzer import SentimentAnalyzer
from app.services.fmp import FMPService
import os

@pytest.mark.asyncio
async def test_backtest_strategy():
    """Test the backtesting strategy with real data."""
    
    # Initialize services
    price_service = PriceService()
    fmp_service = FMPService(api_key=os.getenv("FMP_API_KEY"))
    sentiment_analyzer = SentimentAnalyzer(transcript_loader=fmp_service)
    
    # Create strategy
    strategy = EarningsSentimentStrategy(
        price_service=price_service,
        sentiment_analyzer=sentiment_analyzer,
        initial_capital=100000.0,
        position_size=10000.0,
        entry_price_type='next_day_open'
    )
    
    # Run backtest
    results = await strategy.backtest(
        ticker="AAPL",
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2024, 1, 1)
    )
    
    # Assert results structure
    assert results["status"] == "success"
    assert "data" in results
    assert "trades" in results["data"]
    assert "portfolio_value" in results["data"]
    assert "metrics" in results["data"]
    
    # Print detailed results
    print("\nBacktest Results:")
    print(f"Number of trades: {len(results['data']['trades'])}")
    print(f"Metrics: {results['data']['metrics']}")
    
    return results

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_backtest_strategy()) 