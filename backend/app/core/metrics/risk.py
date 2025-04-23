"""Risk metric calculation functions."""

import numpy as np
import pandas as pd
from typing import Optional

def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.02,
    periods_per_year: int = 252
) -> float:
    """
    Calculate the Sharpe ratio for a series of returns.
    
    Args:
        returns: Series of returns
        risk_free_rate: Annual risk-free rate
        periods_per_year: Number of periods in a year
        
    Returns:
        Sharpe ratio
    """
    if returns.empty:
        return 0.0
        
    excess_returns = returns - risk_free_rate / periods_per_year
    return np.sqrt(periods_per_year) * (excess_returns.mean() / excess_returns.std())

def calculate_sortino_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.02,
    periods_per_year: int = 252
) -> float:
    """
    Calculate the Sortino ratio for a series of returns.
    
    Args:
        returns: Series of returns
        risk_free_rate: Annual risk-free rate
        periods_per_year: Number of periods in a year
        
    Returns:
        Sortino ratio
    """
    if returns.empty:
        return 0.0
        
    excess_returns = returns - risk_free_rate / periods_per_year
    downside_returns = excess_returns[excess_returns < 0]
    
    if downside_returns.empty:
        return np.inf if excess_returns.mean() > 0 else 0.0
        
    return np.sqrt(periods_per_year) * (excess_returns.mean() / downside_returns.std())

def calculate_max_drawdown(returns: pd.Series) -> float:
    """
    Calculate the maximum drawdown from a series of returns.
    
    Args:
        returns: Series of returns
        
    Returns:
        Maximum drawdown as a positive percentage
    """
    if returns.empty:
        return 0.0
        
    cumulative = (1 + returns).cumprod()
    rolling_max = cumulative.expanding().max()
    drawdowns = cumulative / rolling_max - 1
    
    return abs(drawdowns.min()) 