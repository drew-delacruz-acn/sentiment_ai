"""Demo script for sentiment-based backtesting strategy."""

import os
import sys
import asyncio
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
import logging
from dotenv import load_dotenv
import httpx
import polars as pl

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, project_root)

# Load environment variables
load_dotenv(os.path.join(project_root, ".env"))

from backend.app.core.strategy.sentiment import EarningsSentimentStrategy
from backend.app.core.backtest.engine import BacktestEngine
from backend.app.services.prices import PriceService
from backend.app.services.fmp import FMPService
from backend.app.services.sentiment_analyzer import SentimentAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backtest_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def fetch_data(
    ticker: str,
    start_year: int,
    price_service: PriceService,
    fmp_service: FMPService,
    sentiment_analyzer: SentimentAnalyzer
) -> Dict[str, pd.DataFrame]:
    """Fetch and prepare data for backtesting."""
    logger.info(f"Fetching data for {ticker} from {start_year}")
    
    try:
        # Initialize FMP service if needed
        if not fmp_service._http_client:
            await fmp_service.initialize()
        
        # Get price data
        start_date = datetime(start_year, 1, 1)
        prices_df = await price_service.get_historical_prices(
            ticker=ticker,
            start_date=start_date
        )
        
        if prices_df.empty:
            raise ValueError(f"No price data found for {ticker}")
        
        # Log price data summary
        logger.info(f"Price data range: {prices_df.index.min().date()} to {prices_df.index.max().date()}")
        logger.info(f"Price data stats: Low=${prices_df['Close'].min():.2f}, High=${prices_df['Close'].max():.2f}, Mean=${prices_df['Close'].mean():.2f}")
        
        # Get transcripts and analyze sentiment
        sentiment_results = await sentiment_analyzer.analyze_stock_sentiment(
            ticker=ticker,
            from_year=start_year
        )
        
        if not sentiment_results or sentiment_results['status'] == 'error':
            logger.error(f"Sentiment analysis failed: {sentiment_results.get('message', 'Unknown error')}")
            raise ValueError(f"Failed to analyze sentiment for {ticker}")
            
        # Log the sentiment results structure
        logger.info(f"Transcript analyses: {sentiment_results['data']['analysis']['results']['transcript_analyses']}")
        sentiment_df = pl.DataFrame(sentiment_results['data']['analysis']['results']['transcript_analyses'])
        
        # Convert Polars DataFrame to pandas and log the columns
        sentiment_df = sentiment_df.to_pandas()
        logger.info(f"Sentiment DataFrame columns: {sentiment_df.columns.tolist()}")
        
        # Set the date as index for both DataFrames
        sentiment_df.set_index('date', inplace=True)
        prices_df.set_index(prices_df.index.date, inplace=True)
        
        # Log sentiment data summary
        logger.info(f"Sentiment data range: {sentiment_df.index.min()} to {sentiment_df.index.max()}")
        logger.info(f"Sentiment distribution: {sentiment_df['sentiment'].value_counts().to_dict()}")
        
        # Analyze correlation between sentiment and subsequent price movements
        analyze_sentiment_price_correlation(sentiment_df, prices_df)
        
        return {
            'prices': prices_df,
            'sentiment': sentiment_df
        }
    except Exception as e:
        logger.error(f"Error in fetch_data: {str(e)}")
        logger.error("Full sentiment_results:", exc_info=True)
        raise

def analyze_sentiment_price_correlation(sentiment_df: pd.DataFrame, prices_df: pd.DataFrame) -> None:
    """Analyze and log correlation between sentiment and subsequent price movements."""
    try:
        results = []
        
        for date, row in sentiment_df.iterrows():
            sentiment = row['sentiment']
            
            # Get price on sentiment date
            if date in prices_df.index:
                base_price = prices_df.loc[date, 'Close']
                
                # Get prices 30, 60, 90 days later
                for days in [30, 60, 90]:
                    target_date = pd.Timestamp(date) + pd.Timedelta(days=days)
                    target_dates = [d for d in prices_df.index if pd.Timestamp(d) >= target_date]
                    
                    if target_dates:
                        future_date = target_dates[0]
                        future_price = prices_df.loc[future_date, 'Close']
                        price_change_pct = (future_price - base_price) / base_price * 100
                        
                        results.append({
                            'sentiment_date': date,
                            'sentiment': sentiment,
                            'future_date': future_date,
                            'days_later': days,
                            'price_change_pct': price_change_pct
                        })
        
        if results:
            results_df = pd.DataFrame(results)
            # Group by sentiment and days_later
            grouped = results_df.groupby(['sentiment', 'days_later'])['price_change_pct'].agg(['mean', 'median', 'count'])
            
            logger.info("=== SENTIMENT PREDICTIVE POWER ANALYSIS ===")
            logger.info(f"\n{grouped}")
            
            # Check if optimistic sentiment is actually a good indicator
            optimistic_perf = results_df[results_df['sentiment'] == 'optimistic'].groupby('days_later')['price_change_pct'].mean()
            logger.info(f"\nMean price change after optimistic sentiment:\n{optimistic_perf}")
            
            # Analyze all sentiments
            for sentiment_type in results_df['sentiment'].unique():
                avg_changes = results_df[results_df['sentiment'] == sentiment_type].groupby('days_later')['price_change_pct'].mean()
                logger.info(f"\nMean price change after {sentiment_type} sentiment:\n{avg_changes}")
        else:
            logger.warning("No data available for sentiment-price correlation analysis")
            
    except Exception as e:
        logger.error(f"Error in sentiment-price correlation analysis: {str(e)}", exc_info=True)

def create_results_plots(results: Dict[str, Any], save_dir: str) -> None:
    """Create and save visualization plots."""
    # Ensure save directory exists
    os.makedirs(save_dir, exist_ok=True)
    
    # Portfolio value plot with buy points
    portfolio_fig = go.Figure()
    portfolio_fig.add_trace(go.Scatter(
        x=results['portfolio_value_history']['dates'],
        y=results['portfolio_value_history']['values'],
        name='Portfolio Value',
        line=dict(color='blue')
    ))
    
    # Add buy points as markers
    trades_df = pd.DataFrame(results['trades'])
    if not trades_df.empty:
        # Filter only entry trades
        entry_trades = trades_df[trades_df['type'] == 'entry']
        if not entry_trades.empty:
            portfolio_fig.add_trace(go.Scatter(
                x=entry_trades['date'],
                y=[results['portfolio_value_history']['values'][
                    results['portfolio_value_history']['dates'].index(date)] 
                    if date in results['portfolio_value_history']['dates'] 
                    else None for date in entry_trades['date']],
                mode='markers',
                name='Buy Points',
                marker=dict(
                    size=10,
                    color='green',
                    symbol='triangle-up'
                )
            ))
    
    portfolio_fig.update_layout(
        title='Portfolio Value Over Time with Buy Points',
        xaxis_title='Date',
        yaxis_title='Value ($)',
        showlegend=True
    )
    portfolio_fig.write_html(os.path.join(save_dir, 'portfolio_value.html'))
    portfolio_fig.write_image(os.path.join(save_dir, 'portfolio_value.png'))
    
    # Trade analysis plot
    if not trades_df.empty:
        trades_fig = go.Figure()
        # Add price line
        price_dates = results.get('price_history', {}).get('dates', [])
        price_values = results.get('price_history', {}).get('values', [])
        if price_dates and price_values:
            trades_fig.add_trace(go.Scatter(
                x=price_dates,
                y=price_values,
                name='Stock Price',
                line=dict(color='gray', width=1)
            ))
            
        # Add trade markers
        trades_fig.add_trace(go.Scatter(
            x=trades_df['date'],
            y=trades_df.apply(lambda x: x.get('entry_price', x.get('exit_price')), axis=1),
            mode='markers',
            name='Trades',
            marker=dict(
                size=10,
                color=['green' if t.get('type') == 'entry' else 'red' for t in results['trades']],
                symbol=['triangle-up' if t.get('type') == 'entry' else 'triangle-down' for t in results['trades']]
            )
        ))
        trades_fig.update_layout(
            title='Trade Points and Stock Price',
            xaxis_title='Date',
            yaxis_title='Price ($)',
            showlegend=True
        )
        trades_fig.write_html(os.path.join(save_dir, 'trades.html'))
        trades_fig.write_image(os.path.join(save_dir, 'trades.png'))

def print_results_summary(results: Dict[str, Any]) -> None:
    """Print formatted summary of backtest results."""
    metrics = results['performance_metrics']
    
    print("\n=== Backtest Results Summary ===")
    print(f"Total Return: {metrics['total_return']:.2%}")
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"Sortino Ratio: {metrics['sortino_ratio']:.2f}")
    print(f"Maximum Drawdown: {metrics['max_drawdown']:.2%}")
    print(f"Number of Trades: {metrics['number_of_trades']}")
    
    logger.info("\n=== Backtest Results Summary ===")
    logger.info(f"Total Return: {metrics['total_return']:.2%}")
    logger.info(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    logger.info(f"Sortino Ratio: {metrics['sortino_ratio']:.2f}")
    logger.info(f"Maximum Drawdown: {metrics['max_drawdown']:.2%}")
    logger.info(f"Number of Trades: {metrics['number_of_trades']}")
    
    if results['trades']:
        trades_df = pd.DataFrame(results['trades'])
        print("\nTrade Analysis:")
        print(f"First Trade Date: {min(trades_df['date'])}")
        print(f"Last Trade Date: {max(trades_df['date'])}")
        print(f"Average Trade Size: ${trades_df['quantity'].mean() * trades_df['entry_price'].mean():,.2f}")
        
        logger.info("\nTrade Analysis:")
        logger.info(f"First Trade Date: {min(trades_df['date'])}")
        logger.info(f"Last Trade Date: {max(trades_df['date'])}")
        logger.info(f"Average Trade Size: ${trades_df['quantity'].mean() * trades_df['entry_price'].mean():,.2f}")
        
        # Analyze individual trades
        logger.info("\n=== Detailed Trade Analysis ===")
        trade_values = []
        current_value = results['performance_metrics'].get('initial_capital', 100000)
        
        for idx, trade in trades_df.iterrows():
            trade_date = trade['date']
            trade_type = trade['type']
            trade_price = trade.get('entry_price', trade.get('exit_price'))
            trade_qty = trade['quantity']
            trade_value = trade_price * trade_qty
            
            if trade_type == 'entry':
                position_change = -trade_value  # Money spent on buying
            else:
                position_change = trade_value   # Money gained from selling
                
            current_value += position_change
            trade_values.append(current_value)
            
            logger.info(f"Trade #{idx+1}: {trade_date} - {trade_type.upper()} - "
                        f"Price: ${trade_price:.2f} - Qty: {trade_qty} - "
                        f"Value: ${trade_value:.2f} - Portfolio: ${current_value:.2f}")
        
        # Check if portfolio value matches expected from trades
        logger.info(f"\nFinal portfolio value from trade analysis: ${trade_values[-1]:.2f}")
        logger.info(f"Final portfolio value from results: ${results['portfolio_value_history']['values'][-1]:.2f}")
    
    print("\n=== Strategy Settings ===")
    print("Type: Earnings Call Sentiment")
    print("Entry: On Optimistic Sentiment")
    print("Exit: Hold Position")
    
    logger.info("\n=== Strategy Settings ===")
    logger.info("Type: Earnings Call Sentiment")
    logger.info("Entry: On Optimistic Sentiment")
    logger.info("Exit: Hold Position")

async def run_demo(
    ticker: str = 'AAPL',
    start_year: int = 2023,
    initial_capital: float = 100000.0,
    position_size: float = 10000.0,  # Fixed position size of $10k
    unlimited_capital: bool = False,
    plots_dir: str = 'backtest_results'
) -> None:
    """Run complete backtesting demo."""
    logger.info(f"Starting demo for {ticker}")
    logger.info(f"Parameters: start_year={start_year}, initial_capital=${initial_capital:,.2f}, position_size=${position_size:,.2f}, unlimited_capital={unlimited_capital}")
    
    try:
        # Initialize services
        price_service = PriceService()
        fmp_service = FMPService()  # Will be used with async context manager
        sentiment_analyzer = SentimentAnalyzer(fmp_service)
        
        # Fetch data
        data = await fetch_data(
            ticker=ticker,
            start_year=start_year,
            price_service=price_service,
            fmp_service=fmp_service,
            sentiment_analyzer=sentiment_analyzer
        )
        
        # Initialize strategy and engine
        strategy = EarningsSentimentStrategy(
            initial_capital=initial_capital,
            position_size=position_size,  # Use fixed position size
            percentage_allocation=None,  # Disable percentage allocation
            unlimited_capital=unlimited_capital
        )
        engine = BacktestEngine(strategy=strategy)
        
        # Monkey patch the strategy to log decisions
        original_generate_signals = strategy.generate_signals
        
        def logged_generate_signals(data):
            signals = original_generate_signals(data)
            
            # Log each signal
            for date, row in signals.iterrows():
                signal_value = row['signal']
                price_data = data['prices'].loc[date] if date in data['prices'].index else None
                sentiment_data = data['sentiment'].loc[date] if date in data['sentiment'].index else None
                
                close_price = price_data['Close'] if price_data is not None else 'N/A'
                sentiment_value = sentiment_data['sentiment'] if sentiment_data is not None else 'N/A'
                
                logger.info(f"Signal generated for {date}: {signal_value} - "
                           f"Price: ${close_price}, "
                           f"Sentiment: {sentiment_value}, "
                           f"Cash: ${strategy.current_capital:,.2f}")
            
            return signals
        
        strategy.generate_signals = logged_generate_signals
        
        # Run backtest
        logger.info("Starting backtest execution")
        results = await engine.run(
            price_data=data['prices'],
            sentiment_data=data['sentiment']
        )
        
        # Print results
        print_results_summary(results)
        
        # Create and save plots
        create_results_plots(results, plots_dir)
        logger.info(f"Plots saved to {plots_dir}")
        
        # Analyze market performance without strategy
        analyze_market_performance(data['prices'], results)
        
    except Exception as e:
        logger.error(f"Error running demo: {str(e)}", exc_info=True)
        raise

def analyze_market_performance(price_data: pd.DataFrame, backtest_results: Dict[str, Any]) -> None:
    """Analyze how the market performed compared to our strategy."""
    try:
        start_date = price_data.index.min()
        end_date = price_data.index.max()
        start_price = price_data.loc[start_date, 'Close']
        end_price = price_data.loc[end_date, 'Close']
        market_return = (end_price / start_price) - 1
        
        strategy_return = backtest_results['performance_metrics']['total_return']
        
        logger.info("\n=== Market vs Strategy Analysis ===")
        logger.info(f"Market Return ({start_date} to {end_date}): {market_return:.2%}")
        logger.info(f"Strategy Return: {strategy_return:.2%}")
        logger.info(f"Outperformance: {strategy_return - market_return:.2%}")
        
        # Calculate buy and hold performance
        initial_capital = backtest_results['performance_metrics'].get('initial_capital', 100000)
        shares_bought = initial_capital / start_price
        final_market_value = shares_bought * end_price
        
        logger.info(f"Buy & Hold Initial: ${initial_capital:,.2f}")
        logger.info(f"Buy & Hold Final: ${final_market_value:,.2f}")
        logger.info(f"Buy & Hold Return: {(final_market_value / initial_capital) - 1:.2%}")
        
    except Exception as e:
        logger.error(f"Error analyzing market performance: {str(e)}", exc_info=True)

async def main():
    """Main demo execution function."""
    # Demo parameters
    params = {
        'ticker': 'AAPL',
        'start_year': 2023,
        'initial_capital': 100000.0,
        'position_size': 10000.0,  # Fixed $10k per trade
        'unlimited_capital': False,
        'plots_dir': 'backtest_results'
    }
    
    try:
        await run_demo(**params)
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 