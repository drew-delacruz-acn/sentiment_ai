from datetime import datetime
import polars as pl
from typing import Optional
import httpx
from ...interfaces.transcript_loader import TranscriptLoader
from ..fmp import FMPService
from ...utils.logging import setup_logger

logger = setup_logger(__name__)

class FMPTranscriptLoader(TranscriptLoader):
    """FMP implementation of transcript loading."""
    
    def __init__(self, http_client: Optional[httpx.AsyncClient] = None):
        """Initialize with HTTP client."""
        self._http_client = http_client
        self._owns_client = False
        self.fmp_service = None
    
    async def __aenter__(self):
        """Set up async resources."""
        if not self._http_client:
            self._http_client = httpx.AsyncClient()
            self._owns_client = True
        if not self.fmp_service:
            # Initialize FMP service with API key from environment variables
            self.fmp_service = FMPService()
            # Make sure FMP service has its HTTP client initialized
            await self.fmp_service.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up async resources."""
        if self._owns_client and self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None
        
        # Clean up FMP service if we created it
        if self.fmp_service:
            await self.fmp_service.cleanup()
    
    async def load_transcripts(self, ticker: str, from_year: Optional[int] = None) -> pl.DataFrame:
        """Load transcripts for a given ticker."""
        try:
            if not self.fmp_service:
                raise RuntimeError("FMP service not initialized. Use async context manager.")
            
            # Use provided from_year or default to current year
            current_year = datetime.now().year
            start_year = from_year if from_year is not None else current_year
            
            transcripts = await self.fmp_service.get_earnings_call_transcripts(
                ticker, start_year
            )
            
            if not transcripts:
                logger.warning(f"No transcripts found for {ticker}")
                return pl.DataFrame()
            
            df = pl.DataFrame(transcripts)
            
            # Validate and process DataFrame
            required_columns = ['date', 'content']
            if not all(col in df.columns for col in required_columns):
                missing = [col for col in required_columns if col not in df.columns]
                raise ValueError(f"Missing required columns: {missing}")
            
            df = df.with_columns(pl.col('date').str.strptime(pl.Datetime))
            return df.sort('date', descending=True)
            
        except Exception as e:
            logger.error(f"Error loading transcript data for {ticker}: {str(e)}")
            return pl.DataFrame() 