from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str

class BacktestRequest(BaseModel):
    """Request model for backtest endpoint."""
    ticker: str
    start_year: int
    initial_capital: float = Field(
        default=100000.0, 
        description="Initial capital for the backtest"
    )
    position_size: float = Field(
        default=10000.0, 
        description="Fixed dollar amount to invest on each positive sentiment signal"
    )
    unlimited_capital: bool = Field(
        default=False, 
        description="When enabled, uses the same fixed position_size for every trade regardless of capital constraints, simulating unlimited buying power"
    )

class BacktestResponse(BaseModel):
    """Response model for backtest endpoint."""
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None
