"""Strategy module for backtesting implementations."""

from .base import BaseStrategy
from .sentiment import EarningsSentimentStrategy

__all__ = ['BaseStrategy', 'EarningsSentimentStrategy'] 