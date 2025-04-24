"""Main FastAPI application module."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import httpx
from typing import Optional
import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
# First try the backend-specific .env file
backend_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(backend_env_path):
    load_dotenv(backend_env_path)
else:
    # Fallback to the project root .env file
    project_root_env = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), ".env")
    if os.path.exists(project_root_env):
        load_dotenv(project_root_env)
    else:
        # If no specific .env file is found, try default behavior (current directory)
        load_dotenv()

from app.models import HealthResponse
from app.services import init_services, get_sentiment_analyzer
from app.services.prices import PriceService
from app.core.forecast import PriceForecast
from app.api import backtest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Shared HTTP client for async requests
class GlobalState:
    http_client: Optional[httpx.AsyncClient] = None
    price_service: Optional[PriceService] = None

global_state = GlobalState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for async resources."""
    # Initialize shared HTTP client
    http_client = httpx.AsyncClient(
        timeout=30.0,  # 30 second timeout
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
    )
    logger.info("Starting up async HTTP client")
    
    # Store in both global state (for backwards compatibility) and app.state
    global_state.http_client = http_client
    app.state.http_client = http_client
    
    # Initialize services with HTTP client
    init_services(http_client)
    
    # Initialize price service with default settings (not http_client)
    global_state.price_service = PriceService()
    logger.info("Initialized services with HTTP client")
    
    yield  # Server is running and handling requests here
    
    # Cleanup
    if http_client:
        await http_client.aclose()
        logger.info("Closed async HTTP client")
    
    # Reset state
    global_state.http_client = None
    app.state.http_client = None

app = FastAPI(
    title="Sentiment AI Backtesting API",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Check if the API is operational by verifying the HTTP client is initialized.
    """
    try:
        if global_state.http_client is None:
            raise HTTPException(status_code=503, detail="Service unhealthy: HTTP client not initialized")
        
        return HealthResponse(status="healthy")
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Sentiment AI Backtesting API",
        "version": "0.1.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "analyze": "/analyze",
            "forecast": "/api/forecast/{ticker}",
            "backtest": "/api/backtest/{ticker}"
        }
    }

@app.get("/analyze/{ticker}")
async def analyze_ticker(ticker: str, from_year: Optional[int] = None):
    """
    Analyze sentiment for a given ticker's earnings call transcripts.
    
    Args:
        ticker: Stock ticker symbol
        from_year: Optional start year to filter transcripts (defaults to all years)
    """
    try:
        if global_state.http_client is None:
            raise HTTPException(status_code=503, detail="Service unavailable: HTTP client not initialized")
            
        # Get the initialized sentiment analyzer
        analyzer = get_sentiment_analyzer()
        results = await analyzer.analyze_stock_sentiment(ticker, from_year)
        
        if results["status"] == "error":
            raise HTTPException(status_code=500, detail=results["message"])
            
        return results
        
    except Exception as e:
        logger.error(f"Error analyzing {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/api/forecast/{ticker}")
async def forecast_price(
    ticker: str,
    start_date: str,
    forecast_days: int = 30
):
    """Generate price forecast for a given ticker.
    
    Args:
        ticker: Stock ticker symbol
        start_date: Start date for historical data in YYYY-MM-DD format
        forecast_days: Number of days to forecast (default: 30)
    """
    try:
        if global_state.price_service is None:
            raise HTTPException(status_code=503, detail="Service unavailable: Price service not initialized")
        
        # Validate start date
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            if start > datetime.now():
                raise HTTPException(status_code=400, detail="Future start date not allowed")
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Get historical prices
        historical_data = await global_state.price_service.get_historical_prices(ticker, start_date)
        
        if historical_data.empty:
            raise HTTPException(status_code=404, detail="No price data found")
            
        if len(historical_data) < 30:  # Require at least 30 days of data
            raise HTTPException(status_code=400, detail="Insufficient historical data")
            
        # Generate forecast
        forecaster = PriceForecast()
        forecast_result = forecaster.create_forecast(historical_data, forecast_days)
        
        # Prepare OHLC data for candlestick chart
        ohlc_data = None
        if 'Open' in historical_data.columns and 'High' in historical_data.columns and 'Low' in historical_data.columns:
            ohlc_data = {
                'open': historical_data['Open'].tolist(),
                'high': historical_data['High'].tolist(),
                'low': historical_data['Low'].tolist(),
                'close': historical_data['Close'].tolist(),
            }
        
        return {
            "historical": {
                "dates": historical_data.index.strftime("%Y-%m-%d").tolist(),
                "prices": historical_data["Close"].tolist(),
                "ohlc": ohlc_data  # Add OHLC data for candlestick chart
            },
            "forecast": {
                "dates": forecast_result["dates"],
                "bands": forecast_result["bands"]
            },
            "metadata": {
                "ticker": ticker,
                "forecast_days": forecast_days
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error forecasting {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Forecast failed: {str(e)}")

# Include routers
app.include_router(backtest.router, prefix="/api/backtest", tags=["backtest"])

# Error handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.error(f"HTTP error occurred: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unexpected error occurred: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "status_code": 500}
    )
