from typing import Optional
from httpx import AsyncClient
from .services.transcript_loaders import FMPTranscriptLoader
from .services.sentiment_analyzer import SentimentAnalyzer
from .interfaces.transcript_loader import TranscriptLoader

async def create_sentiment_analyzer(http_client: AsyncClient) -> SentimentAnalyzer:
    """
    Factory function to create a configured SentimentAnalyzer instance.
    
    Args:
        http_client: AsyncClient instance for making HTTP requests
        
    Returns:
        Configured SentimentAnalyzer instance
    """
    # Create transcript loader
    transcript_loader = FMPTranscriptLoader(http_client)
    
    # Create and return analyzer with dependencies
    return SentimentAnalyzer(transcript_loader=transcript_loader) 