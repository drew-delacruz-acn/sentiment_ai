"""Financial Modeling Prep (FMP) service for fetching earnings call transcripts."""

import os
from typing import List, Dict, Optional
from datetime import datetime
import logging
import httpx

logger = logging.getLogger(__name__)

class FMPService:
    """Service for interacting with Financial Modeling Prep API."""
    
    BASE_URL = "https://financialmodelingprep.com/api/v3"
    
    def __init__(self, api_key: Optional[str] = None, http_client: Optional[httpx.AsyncClient] = None):
        """Initialize FMP service with API key."""
        self.api_key = api_key or os.getenv("FMP_API_KEY")
        if not self.api_key:
            raise ValueError("FMP API key not found. Set FMP_API_KEY environment variable.")
        self._http_client = http_client
    
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
        Fetch earnings call transcripts for a given ticker from a specific year.
        
        Args:
            ticker: Stock ticker symbol
            from_year: Start year for fetching transcripts
            
        Returns:
            List of transcripts with dates and content
        """
        if not self._http_client:
            raise RuntimeError("HTTP client not initialized")
            
        url = f"{self.BASE_URL}/earning_call_transcript/{ticker}"
        params = {
            "apikey": self.api_key,
            "year": from_year
        }
        
        try:
            response = await self._http_client.get(url, params=params)
            response.raise_for_status()
            transcripts = response.json()
            
            # Sort transcripts by date
            transcripts.sort(
                key=lambda x: self._parse_date(x.get("date", "1900-01-01")),
                reverse=True
            )
            
            return transcripts
            
        except Exception as e:
            logger.error(f"Error fetching transcripts for {ticker}: {str(e)}")
            raise
    
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
