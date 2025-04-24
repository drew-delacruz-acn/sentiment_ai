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
from ..services.market_index import fetch_market_index
from ..core.strategy.sentiment import EarningsSentimentStrategy
from ..core.backtest.engine import BacktestEngine
from ..models import BacktestRequest, BacktestResponse
from ..factory import create_transcript_loader

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
        
        # Use the ticker-specific transcript loader
        transcript_loader = create_transcript_loader(http_client, request.ticker)
        logger.info(f"Using {transcript_loader.__class__.__name__} for ticker {request.ticker}")
        
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
        market_comparison = await analyze_market_performance(data['prices'], results)
        results['market_comparison'] = market_comparison
        
        # Debug logging
        logger.info(f"Backtest results keys: {results.keys()}")
        if 'equity_curve' in results:
            logger.info(f"Equity curve data found with {len(results['equity_curve']['dates'])} data points")
            logger.info(f"Equity curve date range: {results['equity_curve']['dates'][0]} to {results['equity_curve']['dates'][-1]}")
        else:
            logger.error(f"No equity_curve data found in backtest results")
            
        if 'performance_metrics' in results:
            logger.info(f"Performance metrics: {results['performance_metrics']}")
        
        # Check if trades are properly formatted
        if 'trades' in results:
            logger.info(f"Number of trades: {len(results['trades'])}")
            if results['trades']:
                logger.info(f"Sample trade: {results['trades'][0]}")
        
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
    position_size: float = Query(10000.0, description="Fixed dollar amount to invest on each positive sentiment signal"),
    unlimited_capital: bool = Query(False, description="When enabled, uses the same fixed position_size for every trade regardless of capital constraints, simulating unlimited buying power"),
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

async def analyze_market_performance(price_data, backtest_results):
    """Analyze market performance compared to strategy."""
    try:
        logger.info("[DEBUG] Starting market performance analysis")
        start_date = price_data.index.min()
        end_date = price_data.index.max()
        start_price = price_data.loc[start_date, 'Close']
        end_price = price_data.loc[end_date, 'Close']
        market_return = (end_price / start_price) - 1
        
        logger.info(f"[DEBUG] Price data date range: {start_date} to {end_date}")
        logger.info(f"[DEBUG] Price data first value: {start_price}, last value: {end_price}")
        
        strategy_return = backtest_results['performance_metrics']['total_return']
        initial_capital = backtest_results['performance_metrics'].get('initial_capital', 100000)
        
        logger.info(f"[DEBUG] Strategy return: {strategy_return:.2%}, Initial capital: {initial_capital}")
        
        # Calculate buy and hold performance (keep for backward compatibility)
        shares_bought = initial_capital / start_price
        final_market_value = shares_bought * end_price
        buy_hold_return = (final_market_value / initial_capital) - 1
        
        logger.info(f"[DEBUG] Buy & hold return: {buy_hold_return:.2%}")
        
        # Find all buy trade dates to match S&P 500 investments
        buy_trade_dates = []
        trade_buy_amounts = {}
        if 'trades' in backtest_results and backtest_results['trades']:
            # Get all buy trades
            for trade in backtest_results['trades']:
                if trade['action'] == 'buy':
                    trade_date = datetime.strptime(trade['date'], '%Y-%m-%d').date()
                    buy_trade_dates.append(trade_date)
                    
                    # Store the actual amount invested in each trade
                    if trade_date in trade_buy_amounts:
                        trade_buy_amounts[trade_date] += trade['value']
                    else:
                        trade_buy_amounts[trade_date] = trade['value']
            
            buy_trade_dates = sorted(buy_trade_dates)
            logger.info(f"[DEBUG] Found {len(buy_trade_dates)} buy trade dates")
            logger.info(f"[DEBUG] Buy trade dates: {buy_trade_dates}")
        else:
            logger.info(f"[DEBUG] No trades found in backtest results")
        
        # Use the first trade date for comparison if no buy trades found
        if not buy_trade_dates and 'trades' in backtest_results and backtest_results['trades']:
            # Sort trades by date to ensure we get the earliest
            sorted_trades = sorted(backtest_results['trades'], key=lambda x: x['date'])
            first_trade = sorted_trades[0]
            first_trade_date = datetime.strptime(first_trade['date'], '%Y-%m-%d').date()
            buy_trade_dates = [first_trade_date]
            trade_buy_amounts[first_trade_date] = 10000.0
            logger.info(f"[DEBUG] No buy trades found, using first trade date: {first_trade_date}")
        elif not buy_trade_dates:
            # If no trades at all, use the start date of price data
            buy_trade_dates = [start_date]
            trade_buy_amounts[start_date] = 10000.0
            logger.info(f"[DEBUG] No trades found, using price data start date: {start_date}")
        
        # Fetch market index data for the entire period
        index_ticker = "^GSPC"  # S&P 500 by default
        logger.info(f"[DEBUG] Fetching market index '{index_ticker}' data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        index_data = await fetch_market_index(
            ticker=index_ticker,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        logger.info(f"[DEBUG] Received index data with shape: {index_data.shape if not index_data.empty else 'Empty DataFrame'}")
        
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
        if not index_data.empty and buy_trade_dates:
            try:
                # Handle MultiIndex columns (ticker, field)
                if isinstance(index_data.columns, pd.MultiIndex):
                    # Access Close column with ticker '^GSPC'
                    close_prices = index_data[('Close', '^GSPC')]
                else:
                    # Standard columns
                    close_prices = index_data['Close']
                
                # Create a daily equity curve for the S&P 500, investing $10K on each buy trade date
                market_index_dates = []
                market_index_values = []
                
                # Track shares bought at each investment point
                total_shares = 0.0
                total_investment = 0.0
                
                # First, build a map of dates to index values for easy lookup
                index_by_date = {}
                for i, date in enumerate(index_data.index):
                    date_str = date.date().strftime('%Y-%m-%d')
                    index_by_date[date_str] = close_prices.iloc[i]
                
                # For each date in the price dataset
                for date in sorted(price_data.index):
                    date_str = date.strftime('%Y-%m-%d')
                    
                    # Check if this date or the next trading day exists in the index data
                    if date_str not in index_by_date:
                        continue
                    
                    # Check if this is a buy date - if yes, add more shares
                    if date in buy_trade_dates:
                        # Invest $10K in S&P 500 shares
                        investment_amount = 10000.0
                        index_price = index_by_date[date_str]
                        shares_bought = investment_amount / index_price
                        
                        logger.info(f"[DEBUG] Buying {shares_bought:.2f} S&P 500 shares at ${index_price:.2f} on {date_str}")
                        
                        total_shares += shares_bought
                        total_investment += investment_amount
                    
                    # Calculate total value for this date
                    index_price = index_by_date[date_str]
                    market_value = total_shares * index_price
                    
                    market_index_dates.append(date_str)
                    market_index_values.append(float(market_value))
                
                # Calculate market index return
                if len(market_index_values) > 1 and total_investment > 0:
                    index_return = (market_index_values[-1] / total_investment) - 1
                else:
                    index_return = 0.0
                
                logger.info(f"[DEBUG] Market index starts with value: $0")
                logger.info(f"[DEBUG] Total invested in S&P 500: ${total_investment:.2f}")
                logger.info(f"[DEBUG] Final market index value: ${market_index_values[-1]:.2f}")
                logger.info(f"[DEBUG] Market index return: {index_return:.2%}")
                logger.info(f"[DEBUG] Market index data points: {len(market_index_dates)}")
                
                # Add to response
                result['market_index'] = {
                    'ticker': index_ticker,
                    'name': 'S&P 500',
                    'initial_value': 0.0,  # Starts at 0 since we build up investments over time
                    'final_value': float(market_index_values[-1]),
                    'return': float(index_return),
                    'dates': market_index_dates,
                    'values': market_index_values,
                    'total_investment': float(total_investment)
                }
                
                # Log index data
                logger.info(f"[DEBUG] Added market index data: {index_ticker}, {len(market_index_dates)} data points")
                logger.info(f"[DEBUG] Market index structure: {list(result['market_index'].keys())}")
            except Exception as e:
                logger.error(f"[DEBUG] Error processing market index data: {str(e)}")
                import traceback
                logger.error(f"[DEBUG] Index data processing error: {traceback.format_exc()}")
        else:
            logger.warning(f"[DEBUG] No market index data available for {index_ticker} or no buy trades found")
        
        logger.info(f"[DEBUG] Final result keys: {list(result.keys())}")
        return result
        
    except Exception as e:
        logger.error(f"[DEBUG] Error analyzing market performance: {str(e)}")
        import traceback
        logger.error(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return {'error': str(e)} 