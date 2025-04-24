import yfinance as yf
import pandas as pd
import logging
from datetime import datetime
from typing import Optional, Union

logger = logging.getLogger(__name__)

async def fetch_market_index(ticker: str = "^GSPC", start_date: Optional[Union[str, datetime]] = None, end_date: Optional[Union[str, datetime]] = None) -> pd.DataFrame:
    """
    Fetch market index data using yfinance.
    
    Args:
        ticker: Index ticker symbol (default: ^GSPC for S&P 500)
        start_date: Start date for data in YYYY-MM-DD format or datetime
        end_date: End date for data in YYYY-MM-DD format or datetime
        
    Returns:
        DataFrame with index data
    """
    try:
        # Convert string dates to datetime if needed
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
        logger.info(f"[DEBUG] Fetching {ticker} index data from {start_date} to {end_date}")
        
        # Download market data
        index_data = yf.download(
            ticker, 
            start=start_date, 
            end=end_date,
            progress=False
        )
        
        if index_data.empty:
            logger.warning(f"[DEBUG] No data returned for {ticker}")
            return pd.DataFrame()
        
        logger.info(f"[DEBUG] Successfully fetched {len(index_data)} data points for {ticker}")
        logger.info(f"[DEBUG] Index data first 3 rows: {index_data.head(3)}")
        logger.info(f"[DEBUG] Index data last 3 rows: {index_data.tail(3)}")
        logger.info(f"[DEBUG] Index columns: {index_data.columns.tolist()}")
        return index_data
        
    except Exception as e:
        logger.error(f"[DEBUG] Error fetching market index data: {str(e)}")
        import traceback
        logger.error(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return pd.DataFrame()

class MarketIndexService:
    """Service for fetching and processing market index data."""
    
    def __init__(self):
        """Initialize the market index service."""
        self.default_index = "^GSPC"  # S&P 500 by default
        
    async def get_index_data(self, start_date: Union[str, datetime], end_date: Optional[Union[str, datetime]] = None, 
                            ticker: str = "^GSPC") -> pd.DataFrame:
        """
        Get market index data for a specified period.
        
        Args:
            start_date: Start date for fetching data
            end_date: Optional end date (defaults to current date)
            ticker: Index ticker symbol (default: ^GSPC for S&P 500)
            
        Returns:
            DataFrame with market index data
        """
        return await fetch_market_index(ticker=ticker, start_date=start_date, end_date=end_date)
    
    def get_index_info(self, ticker: str = "^GSPC") -> dict:
        """
        Get information about a market index.
        
        Args:
            ticker: Index ticker symbol
            
        Returns:
            Dict with index information
        """
        index_info = {
            "^GSPC": {"name": "S&P 500", "description": "Standard & Poor's 500 Index"},
            "^DJI": {"name": "Dow Jones Industrial Average", "description": "Dow Jones Industrial Average"},
            "^IXIC": {"name": "NASDAQ Composite", "description": "NASDAQ Composite Index"},
            "^RUT": {"name": "Russell 2000", "description": "Russell 2000 Small Cap Index"},
        }
        
        return index_info.get(ticker, {"name": ticker, "description": f"Market Index {ticker}"}) 