"""Shared pytest fixtures for testing the Sentiment AI Backtesting API."""

import pytest
from fastapi.testclient import TestClient
import httpx
from backend.app.main import app, GlobalState

@pytest.fixture(autouse=True)
async def setup_http_client():
    """Setup and teardown the global HTTP client for each test."""
    GlobalState.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(30.0),
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
    )
    yield
    await GlobalState.http_client.aclose()
    GlobalState.http_client = None

@pytest.fixture
def client():
    """Create a test client for synchronous API testing."""
    with TestClient(app) as test_client:
        yield test_client 