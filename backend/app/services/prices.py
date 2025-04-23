from typing import Dict, List, Optional
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
import requests
import time
from asyncio import Semaphore
import random

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, max_requests: int = 2, time_window: float = 1.0):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        self.semaphore = Semaphore(max_requests)
    
    async def acquire(self):
        """Acquire permission to make a request with rate limiting."""
        await self.semaphore.acquire()
        
        # Clean up old requests
        current_time = time.time()
        self.requests = [t for t in self.requests if current_time - t < self.time_window]
        
        if len(self.requests) >= self.max_requests:
            # Wait until enough time has passed
            sleep_time = self.requests[0] + self.time_window - current_time
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        self.requests.append(current_time)
    
    def release(self):
        """Release the rate limiter."""
        self.semaphore.release()

class PriceService:
    def __init__(self, max_workers: int = 5, max_retries: int = 3):
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._rate_limiter = RateLimiter(max_requests=2, time_window=1.0)  # 2 requests per second
        self.max_retries = max_retries
        
    async def get_historical_prices(
        self,
        ticker: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Asynchronously fetch historical price data for a given ticker.
        
        Args:
            ticker: Stock symbol (e.g., 'AAPL')
            start_date: Start date for historical data
            end_date: End date for historical data (defaults to today)
            interval: Data interval ('1d' for daily, '1wk' for weekly, etc.)
            
        Returns:
            DataFrame with columns: Open, High, Low, Close, Volume, Dividends, Stock Splits
            Index: DatetimeIndex with the dates of the price data
        """
        retries = 0
        while retries < self.max_retries:
            try:
                await self._rate_limiter.acquire()
                df = await asyncio.get_event_loop().run_in_executor(
                    self._executor,
                    self._download_prices,
                    ticker,
                    start_date,
                    end_date or datetime.now(),
                    interval
                )
                
                if df.empty:
                    logger.warning(f"No price data found for {ticker} between {start_date} and {end_date}")
                    return pd.DataFrame()
                
                # Ensure the index is a DatetimeIndex
                if not isinstance(df.index, pd.DatetimeIndex):
                    df.index = pd.to_datetime(df.index)
                    
                return df
                
            except Exception as e:
                retries += 1
                if "Too Many Requests" in str(e):
                    # Exponential backoff
                    wait_time = (2 ** retries) + (random.random() * 0.1)
                    logger.warning(f"Rate limit hit for {ticker}, waiting {wait_time:.2f}s (attempt {retries}/{self.max_retries})")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Error fetching prices for {ticker}: {str(e)}")
                    if retries == self.max_retries:
                        return pd.DataFrame()
            finally:
                self._rate_limiter.release()
                
        return pd.DataFrame()
            
    def _download_prices(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        interval: str
    ) -> pd.DataFrame:
        """
        Download price data using yfinance (blocking operation).
        """
        try:
            ticker_obj = yf.Ticker(ticker)
            
            # First check if the ticker exists by attempting to get info
            try:
                ticker_obj.info
            except (ValueError, requests.exceptions.HTTPError) as e:
                if "404" in str(e):
                    logger.warning(f"Invalid ticker symbol: {ticker}")
                    return pd.DataFrame()
                raise
                
            df = ticker_obj.history(
                start=start_date,
                end=end_date,
                interval=interval
            )
            return df
            
        except Exception as e:
            logger.error(f"Error in _download_prices for {ticker}: {str(e)}")
            raise  # Re-raise for retry logic in get_historical_prices
        
    async def get_batch_prices(
        self,
        tickers: List[str],
        start_date: datetime,
        end_date: Optional[datetime] = None,
        interval: str = "1d",
        chunk_size: int = 5  # Process tickers in smaller chunks
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical prices for multiple tickers concurrently.
        
        Args:
            tickers: List of stock symbols
            start_date: Start date for historical data
            end_date: End date for historical data
            interval: Data interval
            chunk_size: Number of concurrent requests
            
        Returns:
            Dict mapping tickers to their respective price DataFrames
        """
        price_data = {}
        
        # Process tickers in chunks to avoid overwhelming the API
        for i in range(0, len(tickers), chunk_size):
            chunk = tickers[i:i + chunk_size]
            tasks = [
                self.get_historical_prices(ticker, start_date, end_date, interval)
                for ticker in chunk
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for ticker, result in zip(chunk, results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to fetch prices for {ticker}: {str(result)}")
                    price_data[ticker] = pd.DataFrame()
                else:
                    price_data[ticker] = result
            
            # Small delay between chunks
            if i + chunk_size < len(tickers):
                await asyncio.sleep(0.5)
                
        return price_data

    async def get_latest_price(self, ticker: str) -> Optional[float]:
        """
        Get the most recent closing price for a ticker.
        
        Args:
            ticker: Stock symbol
            
        Returns:
            Latest closing price or None if not available
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5)  # Get last 5 days in case of holidays
        
        try:
            df = await self.get_historical_prices(ticker, start_date, end_date)
            if not df.empty:
                return df['Close'].iloc[-1]
            return None
            
        except Exception as e:
            logger.error(f"Error fetching latest price for {ticker}: {str(e)}")
            return None
