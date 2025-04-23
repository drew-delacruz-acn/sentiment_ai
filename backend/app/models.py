from pydantic import BaseModel
from typing import Optional, Dict, Any

class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str

class BacktestRequest(BaseModel):
    """Request model for backtest endpoint."""
    ticker: str
    start_year: int
    initial_capital: float = 100000.0
    position_size: float = 10000.0
    unlimited_capital: bool = False

class BacktestResponse(BaseModel):
    """Response model for backtest endpoint."""
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None
