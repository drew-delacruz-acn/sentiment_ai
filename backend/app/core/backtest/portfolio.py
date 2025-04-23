"""Portfolio management for backtesting."""

from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Portfolio:
    """Manages positions and tracks portfolio value."""
    
    def __init__(self, initial_capital: float = 100000.0, unlimited_capital: bool = False):
        """
        Initialize portfolio.
        
        Args:
            initial_capital: Starting capital
            unlimited_capital: If True, ignore capital constraints and allow unlimited position entries
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.unlimited_capital = unlimited_capital
        self.positions: Dict[str, float] = {}  # ticker -> quantity
        self.trades: List[Dict] = []
        self.portfolio_values: List[Dict] = []
        
    def enter_position(
        self,
        ticker: str,
        quantity: float,
        price: float,
        date: datetime,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Enter a new position.
        
        Args:
            ticker: Stock symbol
            quantity: Number of shares
            price: Entry price
            date: Trade date
            metadata: Additional trade information
            
        Returns:
            True if trade successful
        """
        cost = quantity * price
        if not self.unlimited_capital and cost > self.current_capital:
            return False
            
        # Record trade
        trade = {
            'ticker': ticker,
            'quantity': quantity,
            'entry_price': price,
            'date': date,
            'type': 'entry',
            'metadata': metadata or {}
        }
        self.trades.append(trade)
        
        # Update position
        if ticker not in self.positions:
            self.positions[ticker] = 0
        self.positions[ticker] += quantity
        
        # Update capital only if not in unlimited mode
        if not self.unlimited_capital:
            self.current_capital -= cost
        return True
        
    def exit_position(
        self,
        ticker: str,
        quantity: float,
        price: float,
        date: datetime,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Exit an existing position.
        
        Args:
            ticker: Stock symbol
            quantity: Number of shares
            price: Exit price
            date: Trade date
            metadata: Additional trade information
            
        Returns:
            True if trade successful
        """
        if ticker not in self.positions or self.positions[ticker] < quantity:
            return False
            
        # Record trade
        trade = {
            'ticker': ticker,
            'quantity': -quantity,
            'exit_price': price,
            'date': date,
            'type': 'exit',
            'metadata': metadata or {}
        }
        self.trades.append(trade)
        
        # Update position
        self.positions[ticker] -= quantity
        if self.positions[ticker] == 0:
            del self.positions[ticker]
            
        # Update capital only if not in unlimited mode
        if not self.unlimited_capital:
            self.current_capital += quantity * price
        return True
        
    def update_portfolio_value(self, date: datetime, prices: Dict[str, float]) -> None:
        """
        Update portfolio value based on current prices.
        
        Args:
            date: Valuation date
            prices: Dictionary of current prices by ticker
        """
        logger.info(f"\n=== Updating Portfolio Value ({date}) ===")
        
        # Calculate total value of all positions
        position_values = {}
        position_value = 0
        
        for ticker, quantity in self.positions.items():
            if ticker in prices:
                value = quantity * prices[ticker]
                position_values[ticker] = value
                position_value += value
                logger.info(f"Position Value - {ticker}: {quantity:.2f} shares × ${prices[ticker]:.2f} = ${value:.2f}")
        
        if self.unlimited_capital:
            # In unlimited capital mode, portfolio value is just the current position value
            total_value = position_value
            logger.info(f"Position Value: ${position_value:.2f}")
            logger.info(f"Total Portfolio Value: ${total_value:.2f}")
        else:
            total_value = self.current_capital + position_value
            logger.info(f"Cash: ${self.current_capital:.2f}")
            logger.info(f"Position Value: ${position_value:.2f}")
            logger.info(f"Total Portfolio Value: ${total_value:.2f}")
        
        self.portfolio_values.append({
            'date': date,
            'cash': 0 if self.unlimited_capital else self.current_capital,
            'positions': position_value,
            'total': total_value
        })
        
    def get_portfolio_history(self) -> pd.DataFrame:
        """
        Get historical portfolio values.
        
        Returns:
            DataFrame of portfolio value history
        """
        return pd.DataFrame(self.portfolio_values) 