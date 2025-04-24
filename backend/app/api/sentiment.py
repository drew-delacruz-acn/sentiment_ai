from fastapi import APIRouter, HTTPException, Depends
from httpx import AsyncClient
from typing import Optional
import logging

from ..factory import create_sentiment_analyzer
from ..utils.logging import setup_logger
from ..utils.http_client import get_http_client

router = APIRouter()
logger = setup_logger(__name__)

@router.get("/analyze/{ticker}")
async def analyze_sentiment(
    ticker: str,
    from_year: Optional[int] = None,
    http_client: AsyncClient = Depends(get_http_client)
):
    """
    Analyze sentiment for a given stock ticker.
    
    Args:
        ticker: Stock ticker symbol
        from_year: Optional start year to analyze from
        http_client: Injected HTTP client
        
    Returns:
        Dict containing sentiment analysis results
    """
    try:
        logger.info(f"Received sentiment analysis request for ticker={ticker}, from_year={from_year}")
        
        # Create analyzer instance using factory
        analyzer = await create_sentiment_analyzer(http_client)
        
        # Perform sentiment analysis
        logger.info(f"Calling sentiment analyzer for {ticker} from year {from_year}")
        result = await analyzer.analyze_stock_sentiment(
            ticker=ticker,
            from_year=from_year
        )
        
        if result["status"] == "error":
            logger.error(f"Error analyzing sentiment for {ticker}: {result['message']}")
            raise HTTPException(
                status_code=500,
                detail=result["message"]
            )
        
        # Log the response size and content summary
        transcript_count = len(result.get("data", {}).get("analysis", {}).get("results", {}).get("transcript_analyses", []))
        date_range = result.get("data", {}).get("date_range", ["unknown", "unknown"])
        
        logger.info(f"Returning {transcript_count} transcript analyses for {ticker} from {date_range[0]} to {date_range[1]}")
        
        # If transcript count is low, log dates for debugging
        if transcript_count < 25:
            transcripts = result.get("data", {}).get("analysis", {}).get("results", {}).get("transcript_analyses", [])
            if transcripts:
                dates = [t.get("date") for t in transcripts]
                logger.info(f"Returning transcript dates: {sorted(dates)}")
            
        return result
        
    except Exception as e:
        logger.error(f"Failed to analyze sentiment for {ticker}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze sentiment: {str(e)}"
        ) 