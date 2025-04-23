from fastapi import APIRouter, HTTPException, Depends, Query
from httpx import AsyncClient
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import pandas as pd

from ..utils.http_client import get_http_client
from ..services.prices import PriceService
from ..services.fmp import FMPService
from ..services.sentiment_analyzer import SentimentAnalyzer
from ..core.strategy.sentiment import EarningsSentimentStrategy
from ..core.backtest.engine import BacktestEngine
from ..models import BacktestRequest, BacktestResponse
from ..services.transcript_loaders import FMPTranscriptLoader

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/run", response_model=BacktestResponse)
async def run_backtest(
    request: BacktestRequest,
    http_client: AsyncClient = Depends(get_http_client)
) -> BacktestResponse:
    """
    Run a backtest for a given ticker using sentiment analysis strategy.
    
    Args:
        request: Backtest parameters
        http_client: Injected HTTP client
        
    Returns:
        Backtest results including performance metrics and trade history
    """
    try:
        logger.info(f"Starting backtest for {request.ticker} from {request.start_year}")
        
        # Initialize services
        price_service = PriceService()
        fmp_service = FMPService()
        transcript_loader = FMPTranscriptLoader(http_client)
        sentiment_analyzer = SentimentAnalyzer(transcript_loader)
        
        # Fetch data
        data = await fetch_data(
            ticker=request.ticker,
            start_year=request.start_year,
            price_service=price_service,
            sentiment_analyzer=sentiment_analyzer
        )
        
        # Initialize strategy and engine
        strategy = EarningsSentimentStrategy(
            initial_capital=request.initial_capital,
            position_size=request.position_size,
            percentage_allocation=None,
            unlimited_capital=request.unlimited_capital
        )
        engine = BacktestEngine(strategy=strategy)
        
        # Run backtest
        logger.info(f"Executing backtest for {request.ticker}")
        results = await engine.run(
            price_data=data['prices'],
            sentiment_data=data['sentiment']
        )
        
        # Add market comparison
        market_comparison = analyze_market_performance(data['prices'], results)
        results['market_comparison'] = market_comparison
        
        return BacktestResponse(
            status="success",
            message=f"Backtest completed for {request.ticker}",
            data=results
        )
        
    except Exception as e:
        logger.error(f"Error running backtest: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Backtest failed: {str(e)}"
        )

@router.get("/{ticker}", response_model=BacktestResponse)
async def backtest_ticker(
    ticker: str,
    start_year: int = Query(..., description="Start year for backtest data"),
    initial_capital: float = Query(100000.0, description="Initial capital for backtest"),
    position_size: float = Query(10000.0, description="Position size per trade"),
    unlimited_capital: bool = Query(False, description="Whether to use unlimited capital mode"),
    http_client: AsyncClient = Depends(get_http_client)
) -> BacktestResponse:
    """
    Run a backtest for a given ticker using GET method.
    
    Args:
        ticker: Stock ticker symbol
        start_year: Start year for backtest data
        initial_capital: Initial capital for backtest
        position_size: Position size per trade
        unlimited_capital: Whether to use unlimited capital mode
        http_client: Injected HTTP client
        
    Returns:
        Backtest results including performance metrics and trade history
    """
    request = BacktestRequest(
        ticker=ticker,
        start_year=start_year,
        initial_capital=initial_capital,
        position_size=position_size,
        unlimited_capital=unlimited_capital
    )
    
    return await run_backtest(request, http_client)

async def fetch_data(
    ticker: str,
    start_year: int,
    price_service: PriceService,
    sentiment_analyzer: SentimentAnalyzer
) -> Dict[str, Any]:
    """Fetch and prepare data for backtesting."""
    logger.info(f"Fetching data for {ticker} from {start_year}")
    
    try:
        # Get price data
        start_date = datetime(start_year, 1, 1)
        prices_df = await price_service.get_historical_prices(
            ticker=ticker,
            start_date=start_date
        )
        
        if prices_df.empty:
            raise ValueError(f"No price data found for {ticker}")
        
        # Get transcripts and analyze sentiment
        sentiment_results = await sentiment_analyzer.analyze_stock_sentiment(
            ticker=ticker,
            from_year=start_year
        )
        
        if not sentiment_results or sentiment_results['status'] == 'error':
            logger.error(f"Sentiment analysis failed: {sentiment_results.get('message', 'Unknown error')}")
            raise ValueError(f"Failed to analyze sentiment for {ticker}")
            
        # Extract transcript analyses
        sentiment_df = pd.DataFrame(sentiment_results['data']['analysis']['results']['transcript_analyses'])
        
        # Set the date as index for both DataFrames
        sentiment_df.set_index('date', inplace=True)
        prices_df.set_index(prices_df.index.date, inplace=True)
        
        return {
            'prices': prices_df,
            'sentiment': sentiment_df
        }
    except Exception as e:
        logger.error(f"Error in fetch_data: {str(e)}")
        raise

def analyze_market_performance(price_data, backtest_results):
    """Analyze market performance compared to strategy."""
    try:
        start_date = price_data.index.min()
        end_date = price_data.index.max()
        start_price = price_data.loc[start_date, 'Close']
        end_price = price_data.loc[end_date, 'Close']
        market_return = (end_price / start_price) - 1
        
        strategy_return = backtest_results['performance_metrics']['total_return']
        initial_capital = backtest_results['performance_metrics'].get('initial_capital', 100000)
        
        # Calculate buy and hold performance
        shares_bought = initial_capital / start_price
        final_market_value = shares_bought * end_price
        buy_hold_return = (final_market_value / initial_capital) - 1
        
        return {
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
        
    except Exception as e:
        logger.error(f"Error analyzing market performance: {str(e)}")
        return {'error': str(e)} 