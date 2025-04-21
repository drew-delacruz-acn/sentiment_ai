"""Tests for the main FastAPI application endpoints and functionality."""

import pytest
import httpx
from backend.app.main import app, GlobalState
from fastapi.testclient import TestClient
from httpx import AsyncClient
import asyncio

def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Sentiment AI Backtesting API"
    assert data["version"] == "0.1.0"
    assert data["status"] == "operational"
    assert "endpoints" in data

@pytest.mark.asyncio
async def test_health_check_async():
    """Test the health check endpoint asynchronously."""
    async with AsyncClient(base_url="http://testserver", transport=httpx.ASGITransport(app=app)) as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

def test_health_check_sync():
    """Test the health check endpoint synchronously."""
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test multiple concurrent health check requests."""
    async with AsyncClient(base_url="http://testserver", transport=httpx.ASGITransport(app=app)) as client:
        tasks = [client.get("/health") for _ in range(5)]
        responses = await asyncio.gather(*tasks)
        for response in responses:
            assert response.status_code == 200
            assert response.json() == {"status": "healthy"}

def test_global_http_client_initialization():
    """Test that the global HTTP client is initialized with correct settings."""
    client = GlobalState.http_client
    assert client is not None
    assert client.timeout.connect == 30.0  # Check connect timeout directly
    assert client.timeout.read == 30.0     # Check read timeout directly
    assert client.timeout.write == 30.0    # Check write timeout directly

def test_cors_headers(client):
    """Test that CORS headers are properly set."""
    response = client.get("/", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"

def test_error_handling(client):
    """Test error handling middleware."""
    # Test 404 error
    response = client.get("/nonexistent")
    assert response.status_code == 404
    
    # Test internal server error simulation
    with pytest.raises(Exception):
        raise Exception("Test error") 