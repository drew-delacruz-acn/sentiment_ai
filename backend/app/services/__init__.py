"""Services initialization module."""

from .async_llm_client import async_llm_call, async_llm_batch
from .async_embedding_client import async_embed, async_embed_batch
from .sentiment_analyzer import SentimentAnalyzer
from .fmp import FMPService
from .transcript_loaders.fmp_loader import FMPTranscriptLoader

# Services will be initialized with HTTP client in main.py
_fmp_service = None
_transcript_loader = None
_sentiment_analyzer = None

def init_services(http_client):
    """Initialize services with HTTP client."""
    global _fmp_service, _transcript_loader, _sentiment_analyzer
    
    _fmp_service = FMPService(http_client=http_client)
    _transcript_loader = FMPTranscriptLoader(http_client)
    _sentiment_analyzer = SentimentAnalyzer(_transcript_loader)

def get_sentiment_analyzer():
    """Get the initialized sentiment analyzer."""
    if _sentiment_analyzer is None:
        raise RuntimeError("Services not initialized. Call init_services first.")
    return _sentiment_analyzer

__all__ = [
    'async_llm_call',
    'async_llm_batch',
    'async_embed',
    'async_embed_batch',
    'SentimentAnalyzer',
    'FMPService',
    'FMPTranscriptLoader',
    'init_services',
    'get_sentiment_analyzer'
]
