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
        
        # Calculate total return differently for unlimited capital mode
        if getattr(self.strategy, 'unlimited_capital', False):
            non_zero_values = [v for v in portfolio_history['total'] if v > 0]
            if non_zero_values:
                first_value = non_zero_values[0]
                logger.info(f"Using first non-zero value (${first_value:.2f}) as base for return calculation")
                total_return = portfolio_history['total'].iloc[-1] / first_value - 1
            else:
                logger.warning("No non-zero portfolio values found, setting return to 0")
                total_return = 0.0
        else:
            total_return = portfolio_history['total'].iloc[-1] / self.portfolio.initial_capital - 1
        
        logger.info(f"Total Return: {total_return:.2%}")
        logger.info(f"Number of Trades: {len(self.portfolio.trades)}")

        self.results = {
            'performance_metrics': {
                'total_return': float(total_return),
                'sharpe_ratio': float(calculate_sharpe_ratio(returns)),
                'sortino_ratio': float(calculate_sortino_ratio(returns)),
                'max_drawdown': float(calculate_max_drawdown(returns)),
                'number_of_trades': len(self.portfolio.trades)
            },
            'trades': self.portfolio.trades,
            'portfolio_value_history': {
                'dates': portfolio_history['date'].tolist(),
                'values': portfolio_history['total'].tolist()
            }
        }
        
        logger.info("\n=== Backtest Complete ===")
        logger.info(f"Final Results: {self.results['performance_metrics']}")
        return self.results