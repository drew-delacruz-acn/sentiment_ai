"""Financial Modeling Prep (FMP) service for fetching earnings call transcripts."""

import os
from typing import List, Dict, Optional
from datetime import datetime
import logging
import httpx
from httpx import HTTPError, RequestError
import polars as pl
from ..interfaces.transcript_loader import TranscriptLoader

logger = logging.getLogger(__name__)

class FMPService(TranscriptLoader):
    """Service for interacting with Financial Modeling Prep API."""
    
    BASE_URL = "https://financialmodelingprep.com/api/v4"
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize FMP service with API key."""
        self.api_key = api_key or os.getenv("FMP_API_KEY")
        if not self.api_key:
            raise ValueError("FMP API key not found. Set FMP_API_KEY environment variable.")
        self._http_client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    async def initialize(self) -> None:
        """Initialize the HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)

    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None
    
    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        """Parse date string from FMP API."""
        try:
            # Try ISO format first
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            try:
                # Try date-only format
                return datetime.strptime(date_str.split()[0], "%Y-%m-%d")
            except ValueError as e:
                logger.error(f"Failed to parse date: {date_str}")
                raise ValueError(f"Invalid date format: {date_str}") from e
    
    async def get_earnings_call_transcripts(
        self, 
        ticker: str, 
        from_year: int
    ) -> List[Dict]:
        """
        Fetch earnings call transcripts for a given ticker from a specific year onwards.
        
        Args:
            ticker: Stock ticker symbol
            from_year: Start year for fetching transcripts
            
        Returns:
            List of transcripts with dates and content
        """
        if not self._http_client:
            await self.initialize()
            
        url = f"{self.BASE_URL}/batch_earning_call_transcript/{ticker}"
        current_year = datetime.now().year
        all_transcripts = []
        
        logger.info(f"--------------------------------")
        logger.info(f"Fetching transcripts for {ticker} from {from_year} to {current_year}")
        logger.info(f"--------------------------------")
        
        # Fetch transcripts for each year in the range
        for year in range(from_year, current_year + 1):
            params = {
                "apikey": self.api_key,
                "year": year
            }
            
            try:
                logger.info(f"Fetching transcripts for year {year}")
                response = await self._http_client.get(url, params=params)
                response.raise_for_status()
                year_transcripts = response.json()
                
                if isinstance(year_transcripts, list) and year_transcripts:
                    logger.info(f"Found {len(year_transcripts)} transcripts for {ticker} in {year}")
                    all_transcripts.extend(year_transcripts)
                else:
                    logger.warning(f"No transcripts found for {ticker} in {year}")
                    
            except Exception as e:
                logger.warning(f"Error fetching {year} transcripts for {ticker}: {str(e)}")
                continue
        
        # Sort all transcripts by date
        all_transcripts.sort(
            key=lambda x: self._parse_date(x.get("date", "1900-01-01")),
            reverse=True
        )
        
        logger.info(f"Total transcripts found for {ticker}: {len(all_transcripts)}")
        return all_transcripts
    
    async def get_latest_transcript(self, ticker: str) -> Optional[Dict]:
        """
        Fetch the most recent earnings call transcript for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Most recent transcript or None if not found
        """
        current_year = datetime.now().year
        transcripts = await self.get_earnings_call_transcripts(ticker, current_year)
        return transcripts[0] if transcripts else None

    async def load_transcripts(self, ticker: str, from_year: Optional[int] = None) -> pl.DataFrame:
        """
        Load transcript data for a given ticker.
        
        Args:
            ticker: Stock ticker symbol
            from_year: Optional start year for fetching transcripts
            
        Returns:
            Polars DataFrame with transcript data containing at least 'date' and 'content' columns
        """
        try:
            # Use current year if from_year not provided
            year = from_year or datetime.now().year
            
            # Fetch transcripts
            transcripts = await self.get_earnings_call_transcripts(ticker, year)
            
            if not transcripts:
                logger.warning(f"No transcripts found for {ticker} from year {year}")
                return pl.DataFrame(schema={'date': pl.Datetime, 'content': pl.Utf8})
            
            # Convert to Polars DataFrame
            df = pl.DataFrame(transcripts)
            
            # Ensure required columns exist
            if 'date' not in df.columns or 'content' not in df.columns:
                logger.error(f"Missing required columns in transcript data for {ticker}")
                return pl.DataFrame(schema={'date': pl.Datetime, 'content': pl.Utf8})
            
            # Convert dates to datetime using a more flexible approach
            try:
                # First try parsing as datetime with time
                df = df.with_columns([
                    pl.col('date').str.to_datetime('%Y-%m-%d %H:%M:%S', strict=False)
                ])
            except Exception:
                try:
                    # Then try parsing as date only
                    df = df.with_columns([
                        pl.col('date').str.to_datetime('%Y-%m-%d', strict=False)
                    ])
                except Exception as e:
                    logger.error(f"Failed to parse dates: {e}")
                    return pl.DataFrame(schema={'date': pl.Datetime, 'content': pl.Utf8})
            
            # Sort by date descending
            df = df.sort('date', descending=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading transcripts for {ticker}: {str(e)}")
            # Return empty DataFrame on error
            return pl.DataFrame(schema={'date': pl.Datetime, 'content': pl.Utf8})
