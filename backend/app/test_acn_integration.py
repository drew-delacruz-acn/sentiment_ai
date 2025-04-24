"""Integration test for ACN parquet loading."""

import asyncio
import sys
import os
import logging
import httpx
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from app
from app.factory import create_transcript_loader
from app.services.sentiment_analyzer import SentimentAnalyzer
from app.config import settings

async def test_acn_integration():
    """Test ACN parquet loader integration with sentiment analyzer."""
    
    # Verify config settings
    logger.info(f"ACN_PARQUET_PATH from settings: {settings.ACN_PARQUET_PATH}")
    
    # Create HTTP client for non-ACN loaders
    async with httpx.AsyncClient(timeout=30.0) as http_client:
        # Test ACN ticker (should use parquet)
        logger.info("\n=== Testing ACN ticker (should use parquet) ===")
        acn_loader = create_transcript_loader(http_client, ticker="ACN")
        logger.info(f"Created loader for ACN: {acn_loader.__class__.__name__}")
        
        # Verify it's using the correct loader class
        assert "ACNParquetLoader" in acn_loader.__class__.__name__, "Wrong loader type for ACN"
        
        # Load transcripts
        acn_transcripts = await acn_loader.load_transcripts(ticker="ACN", from_year=2007)
        logger.info(f"Loaded {len(acn_transcripts)} ACN transcripts from parquet")
        
        # Basic validation
        if len(acn_transcripts) > 0:
            logger.info(f"First ACN transcript date: {acn_transcripts[0]['date']}")
        
        # Test another ticker (should use FMP)
        logger.info("\n=== Testing AAPL ticker (should use FMP API) ===")
        aapl_loader = create_transcript_loader(http_client, ticker="AAPL")
        logger.info(f"Created loader for AAPL: {aapl_loader.__class__.__name__}")
        
        # Verify it's using the correct loader class
        assert "FMP" in aapl_loader.__class__.__name__, "Wrong loader type for AAPL"
        
        # Test sentiment analyzer with ACN
        logger.info("\n=== Testing sentiment analyzer with ACN ===")
        analyzer = SentimentAnalyzer(acn_loader)
        
        try:
            # This won't actually call the LLM API but will check if data loading works
            sentiment_results = await analyzer.analyze_stock_sentiment(ticker="ACN", from_year=2007)
            
            # Check if we got transcript data from parquet
            logger.info(f"Sentiment analysis status: {sentiment_results.get('status', 'unknown')}")
            if sentiment_results.get('status') == 'success':
                analysis = sentiment_results.get('data', {}).get('analysis', {})
                transcript_count = len(analysis.get('results', {}).get('transcript_analyses', []))
                logger.info(f"Analyzed {transcript_count} ACN transcripts")
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            
        logger.info("\n=== Test complete ===")

if __name__ == "__main__":
    asyncio.run(test_acn_integration()) 