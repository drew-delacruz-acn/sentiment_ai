"""Return calculation functions."""

import numpy as np
import pandas as pd
from typing import List, Dict

def calculate_returns(prices: pd.Series) -> pd.Series:
    """
    Calculate period returns from price series.
    
    Args:
        prices: Series of prices
        
    Returns:
        Series of returns
    """
    return prices.pct_change().fillna(0)

def calculate_cumulative_returns(returns: pd.Series) -> pd.Series:
    """
    Calculate cumulative returns from return series.
    
    Args:
        returns: Series of returns
        
    Returns:
        Series of cumulative returns
    """
    return (1 + returns).cumprod() - 1

def calculate_trade_returns(trades: List[Dict]) -> pd.Series:
    """
    Calculate returns from trade history.
    
    Args:
        trades: List of trade dictionaries
        
    Returns:
        Series of trade returns
    """
    if not trades:
        return pd.Series()
        
    trade_returns = []
    dates = []
    
    for trade in trades:
        entry_price = trade['entry_price']
        exit_price = trade.get('exit_price', entry_price)  # Use entry price if not closed
        trade_return = (exit_price - entry_price) / entry_price
        trade_returns.append(trade_return)
        dates.append(trade['date'])
        
    return pd.Series(trade_returns, index=dates) 