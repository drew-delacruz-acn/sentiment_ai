"""Backtesting engine implementation."""

from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime
from ..strategy.base import BaseStrategy
from .portfolio import Portfolio
from ..metrics import (
    calculate_returns,
    calculate_cumulative_returns,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_max_drawdown
)
import logging

logger = logging.getLogger(__name__)

class BacktestEngine:
    """Engine for running backtests."""
    
    def __init__(
        self,
        strategy: BaseStrategy,
        initial_capital: float = 100000.0
    ):
        """
        Initialize backtesting engine.
        
        Args:
            strategy: Trading strategy to test
            initial_capital: Starting capital
        """
        self.strategy = strategy
        unlimited_capital = getattr(strategy, 'unlimited_capital', False)
        logger.info(f"\n=== Initializing Backtest Engine ===")
        logger.info(f"Strategy: {strategy.__class__.__name__}")
        logger.info(f"Unlimited Capital Mode: {unlimited_capital}")
        logger.info(f"Initial Capital: ${initial_capital:.2f}")
        
        self.portfolio = Portfolio(
            initial_capital=initial_capital,
            unlimited_capital=unlimited_capital
        )
        self.results: Optional[Dict] = None
        
    async def run(
        self,
        price_data: pd.DataFrame,
        sentiment_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Run backtest.
        
        Args:
            price_data: DataFrame of price history
            sentiment_data: DataFrame of sentiment signals
            
        Returns:
            Dictionary of backtest results
        """
        logger.info("\n=== Starting Backtest Run ===")
        logger.info(f"Price data range: {price_data.index[0]} to {price_data.index[-1]}")
        logger.info(f"Sentiment data range: {sentiment_data.index.min()} to {sentiment_data.index.max()}")
        
        # Generate trading signals
        signals = self.strategy.generate_signals({
            'prices': price_data,
            'sentiment': sentiment_data
        })
        logger.info(f"Generated {len(signals[signals['signal'] == 1])} buy signals")
        if not isinstance(sentiment_data.index, pd.DatetimeIndex):
            sentiment_data.index = pd.to_datetime(sentiment_data.index)
        # Convert index to datetime.date
        sentiment_data.index = sentiment_data.index.date
        # Print price data index information
        print('--------------------------------')
        logger.info(f"Sentiment data: {sentiment_data}")
        logger.info(f"Sentiment data columns: {sentiment_data.columns.tolist()}")
        logger.info(f"Sentiment data index: {sentiment_data.index}")
        logger.info(f"Sentiment data index type: {type(sentiment_data.index[0])}")
        logger.info(f"Sentiment data sample:\n{sentiment_data.head()}")
        print('--------------------------------')
        
        # Process signals chronologically
        # Sort signals by date ascending (earliest to latest)
        signals = signals.sort_index(ascending=True)
        
        # Log the sorted signals
        logger.info(f"Processing signals in chronological order (earliest to latest): {signals.index.tolist()}")
        
        for date, row in signals.iterrows():
            date = pd.to_datetime(date).date()
            logger.info(f"\n=== Processing Date: {date} ===")
            
            try:
                if row['signal'] == 1:  # Buy signal
                    if date not in price_data.index:
                        logger.warning(f"Date {date} not found in price data index, skipping position entry")
                        continue
                    
                    # Ensure strategy current_capital matches portfolio current_capital
                    self.strategy.current_capital = self.portfolio.current_capital
                    
                    close_price = price_data.loc[date, 'Close']
                    position_size = self.strategy.calculate_position_size({
                        'date': date,
                        'price': close_price,
                        'signal': row['signal']
                    })
                    
                    quantity = position_size / close_price
                    logger.info(f"Buy Signal - Size: ${position_size:.2f}, Quantity: {quantity:.2f}, Price: ${close_price:.2f}")
                    
                    self.portfolio.enter_position(
                        ticker=price_data.index.name or 'UNKNOWN',
                        quantity=quantity,
                        price=close_price,
                        date=date,
                        metadata={'sentiment': sentiment_data.loc[date, 'sentiment']}
                    )
                
                # Update portfolio value
                self.portfolio.update_portfolio_value(
                    date=date,
                    prices={price_data.index.name or 'UNKNOWN': price_data.loc[date, 'Close']}
                )
                
            except Exception as e:
                logger.error(f"Error processing date {date}: {str(e)}", exc_info=True)
                raise
            
        # Calculate performance metrics
        logger.info("\n=== Calculating Performance Metrics ===")
        portfolio_history = self.portfolio.get_portfolio_history()
        returns = calculate_returns(portfolio_history['total'])
        
        # Calculate total investment and returns differently for unlimited capital mode
        if getattr(self.strategy, 'unlimited_capital', False):
            # In unlimited capital mode, calculate total investment (sum of all buys)
            total_investment = sum(
                abs(trade['quantity']) * trade.get('entry_price', 0)
                for trade in self.portfolio.trades
                if trade['type'] == 'entry'
            )
            
            # Get final portfolio value
            final_portfolio_value = portfolio_history['total'].iloc[-1]
            
            # Calculate ROI
            if total_investment > 0:
                roi = (final_portfolio_value / total_investment) - 1
            else:
                roi = 0.0
                
            logger.info(f"Unlimited Capital Mode - Total Investment: ${total_investment:.2f}")
            logger.info(f"Final Portfolio Value: ${final_portfolio_value:.2f}")
            logger.info(f"Return on Investment: {roi:.2%}")
            
            total_return = roi
        else:
            total_return = portfolio_history['total'].iloc[-1] / self.portfolio.initial_capital - 1
            logger.info(f"Total Return: {total_return:.2%}")
        
        logger.info(f"Number of Trades: {len(self.portfolio.trades)}")

        # Format the trades for API response
        formatted_trades = []
        for trade in self.portfolio.trades:
            formatted_trades.append({
                'date': trade['date'].strftime('%Y-%m-%d'),
                'action': 'buy' if trade['type'] == 'entry' else 'sell',
                'price': float(trade.get('entry_price', trade.get('exit_price', 0))),
                'shares': float(abs(trade['quantity'])),
                'value': float(abs(trade['quantity']) * trade.get('entry_price', trade.get('exit_price', 0))),
                'sentiment': trade.get('metadata', {}).get('sentiment', 'unknown')
            })

        # Prepare equity curve data
        dates = [d.strftime('%Y-%m-%d') for d in portfolio_history['date']]
        values = [float(v) for v in portfolio_history['total']]
        
        # Log equity curve data details for debugging
        logger.info(f"Creating equity curve data with {len(dates)} data points")
        logger.info(f"First date: {dates[0] if dates else 'N/A'}, Last date: {dates[-1] if dates else 'N/A'}")
        logger.info(f"First value: {values[0] if values else 'N/A'}, Last value: {values[-1] if values else 'N/A'}")
        
        # Create the final results dictionary with additional metrics for unlimited capital mode
        results = {
            'performance_metrics': {
                'initial_capital': float(self.portfolio.initial_capital),
                'final_capital': float(portfolio_history['total'].iloc[-1]),
                'total_return': float(total_return),
                'sharpe_ratio': float(calculate_sharpe_ratio(returns)),
                'sortino_ratio': float(calculate_sortino_ratio(returns)),
                'max_drawdown': float(calculate_max_drawdown(returns)),
                'win_rate': 0.6,  # Placeholder - should be calculated from actual trade results
            },
            'trades': formatted_trades,
            'equity_curve': {
                'dates': dates,
                'values': values
            }
        }
        
        # Add unlimited capital mode specific metrics
        if getattr(self.strategy, 'unlimited_capital', False):
            results['performance_metrics']['unlimited_mode'] = True
            results['performance_metrics']['total_investment'] = float(total_investment)
            results['performance_metrics']['position_size_per_trade'] = float(self.strategy.position_size)
            results['performance_metrics']['number_of_trades'] = len(self.portfolio.trades)
        
        logger.info("\n=== Backtest Complete ===")
        logger.info(f"Final Results: {results['performance_metrics']}")
        logger.info(f"Equity Curve Data Points: {len(results['equity_curve']['dates'])}")
        
        self.results = results
        return results