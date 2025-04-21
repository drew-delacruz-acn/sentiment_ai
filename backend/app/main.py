"""Main FastAPI application module."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import httpx
from typing import Optional
import asyncio
from backend.app.models import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Shared HTTP client for async requests
class GlobalState:
    http_client: Optional[httpx.AsyncClient] = None

global_state = GlobalState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for async resources."""
    # Initialize shared HTTP client
    global_state.http_client = httpx.AsyncClient(
        timeout=30.0,  # 30 second timeout
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
    )
    logger.info("Starting up async HTTP client")
    
    yield  # Server is running and handling requests here
    
    # Cleanup
    if global_state.http_client:
        await global_state.http_client.aclose()
        logger.info("Closed async HTTP client")

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
            "analyze": "/analyze"  # To be implemented
        }
    }

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
