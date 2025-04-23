"""Base strategy class for backtesting."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd

class BaseStrategy(ABC):
    """Abstract base class for all trading strategies."""
    
    def __init__(self, initial_capital: float = 100000.0):
        """
        Initialize base strategy.
        
        Args:
            initial_capital: Starting capital for the strategy
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions: Dict[str, float] = {}  # ticker -> quantity
        self.trades: list[Dict[str, Any]] = []
        
    @abstractmethod
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Generate trading signals from input data.
        
        Args:
            data: Dictionary of DataFrames with market data
            
        Returns:
            DataFrame with signals
        """
        pass
        
    @abstractmethod
    def calculate_position_size(self, signal: Dict[str, Any]) -> float:
        """
        Calculate position size for a trade.
        
        Args:
            signal: Signal information
            
        Returns:
            Position size in currency units
        """
        pass
    
    def update_portfolio(self, trade: Dict[str, Any]) -> None:
        """
        Update portfolio after a trade.
        
        Args:
            trade: Trade information
        """
        self.trades.append(trade)
        # Update positions and capital
        ticker = trade['ticker']
        quantity = trade['quantity']
        cost = trade['price'] * quantity
        
        if ticker not in self.positions:
            self.positions[ticker] = 0
        self.positions[ticker] += quantity
        
        # Only update capital if we're not using unlimited capital
        if not getattr(self, 'unlimited_capital', False):
            self.current_capital -= cost 