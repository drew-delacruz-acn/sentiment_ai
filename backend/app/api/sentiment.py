from fastapi import APIRouter, HTTPException, Depends
from httpx import AsyncClient
from typing import Optional

from ..factory import create_sentiment_analyzer
from ..utils.http_client import get_http_client

router = APIRouter()

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
        # Create analyzer instance using factory
        analyzer = await create_sentiment_analyzer(http_client)
        
        # Perform sentiment analysis
        result = await analyzer.analyze_stock_sentiment(
            ticker=ticker,
            from_year=from_year
        )
        
        if result["status"] == "error":
            raise HTTPException(
                status_code=500,
                detail=result["message"]
            )
            
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze sentiment: {str(e)}"
        ) 