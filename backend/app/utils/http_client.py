"""HTTP client utilities."""

from fastapi import Depends, Request
from httpx import AsyncClient
from typing import Optional

async def get_http_client(request: Request) -> AsyncClient:
    """
    Dependency for getting the shared HTTP client.
    
    Args:
        request: FastAPI request object
        
    Returns:
        AsyncClient: The global HTTP client instance
    
    Raises:
        RuntimeError: If the HTTP client is not initialized
    """
    app = request.app
    
    if not hasattr(app.state, "http_client") or app.state.http_client is None:
        raise RuntimeError("HTTP client not initialized")
    
    return app.state.http_client 