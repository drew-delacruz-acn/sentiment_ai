from typing import Optional
from httpx import AsyncClient
from .services.transcript_loaders import FMPTranscriptLoader, ACNParquetLoader
from .services.sentiment_analyzer import SentimentAnalyzer
from .interfaces.transcript_loader import TranscriptLoader

def create_transcript_loader(http_client: AsyncClient, ticker: Optional[str] = None) -> TranscriptLoader:
    """
    Factory function to create the appropriate transcript loader based on ticker.
    
    Args:
        http_client: AsyncClient instance for making HTTP requests
        ticker: Optional ticker symbol to determine which loader to use
        
    Returns:
        Appropriate TranscriptLoader instance
    """
    # Use ACNParquetLoader for ACN ticker
    if ticker and ticker.upper() == 'ACN':
        return ACNParquetLoader()
        
    # Default to FMPTranscriptLoader for other tickers
    return FMPTranscriptLoader(http_client)

async def create_sentiment_analyzer(http_client: AsyncClient) -> SentimentAnalyzer:
    """
    Factory function to create a configured SentimentAnalyzer instance.
    
    Args:
        http_client: AsyncClient instance for making HTTP requests
        
    Returns:
        Configured SentimentAnalyzer instance
    """
    # Create default transcript loader (will be switched based on ticker at runtime)
    transcript_loader = FMPTranscriptLoader(http_client)
    
    # Create and return analyzer with dependencies
    return SentimentAnalyzer(transcript_loader=transcript_loader) 