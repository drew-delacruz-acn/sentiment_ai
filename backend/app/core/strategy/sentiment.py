"""Sentiment-based trading strategy implementation."""

from typing import Dict, Any
import pandas as pd
from .base import BaseStrategy

class EarningsSentimentStrategy(BaseStrategy):
    """Trading strategy based on earnings call sentiment."""
    
    def __init__(
        self,
        position_size: float = 10000.0,
        percentage_allocation: float = 0.10,
        entry_price_type: str = 'next_day_open',
        initial_capital: float = 100000.0,
        unlimited_capital: bool = False
    ):
        """
        Initialize sentiment strategy.
        
        Args:
            position_size: Fixed position size per trade (used if percentage_allocation is None)
            percentage_allocation: Percentage of available capital to allocate per trade (default: 10%)
            entry_price_type: Price type for entry ('next_day_open' or 'next_day_close')
            initial_capital: Starting capital
            unlimited_capital: If True, ignore capital constraints
        """
        super().__init__(initial_capital)
        self.position_size = position_size
        self.percentage_allocation = percentage_allocation
        self.entry_price_type = entry_price_type
        self.unlimited_capital = unlimited_capital
        
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Generate trading signals from sentiment data.
        
        Args:
            data: Dictionary with 'prices' and 'sentiment' DataFrames
            
        Returns:
            DataFrame with signals
        """
        prices_df = data['prices']
        sentiment_df = data['sentiment']
        
        # Generate signals based on optimistic sentiment
        signals = pd.DataFrame(index=sentiment_df.index)
        signals['signal'] = (sentiment_df['sentiment'] == 'optimistic').astype(int)
        
        return signals
        
    def calculate_position_size(self, signal: Dict[str, Any]) -> float:
        """
        Calculate position size for a trade.
        
        Args:
            signal: Signal information
            
        Returns:
            Position size in currency units
        """
        # If unlimited capital, use fixed position size
        if self.unlimited_capital:
            return self.position_size
        
        # Calculate position size as a percentage of current capital
        if self.percentage_allocation is not None:
            # Use percentage of available capital
            allocated_amount = self.current_capital * self.percentage_allocation
            # Log the allocation calculation
            print(f"Allocating {self.percentage_allocation:.1%} of ${self.current_capital:.2f} = ${allocated_amount:.2f}")
        else:
            # Fall back to fixed position size if percentage_allocation is None
            allocated_amount = self.position_size
            
        # Use the minimum of allocated amount and available capital
        return min(allocated_amount, self.current_capital) 