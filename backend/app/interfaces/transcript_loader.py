from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd

class TranscriptLoader(ABC):
    """Abstract interface for loading transcript data."""
    
    @abstractmethod
    async def load_transcripts(self, ticker: str, from_year: Optional[int] = None) -> pd.DataFrame:
        """
        Load transcript data for a given ticker.
        
        Args:
            ticker: Stock ticker symbol
            from_year: Optional start year for fetching transcripts
            
        Returns:
            DataFrame with transcript data containing at least 'date' and 'content' columns
        """
        pass 