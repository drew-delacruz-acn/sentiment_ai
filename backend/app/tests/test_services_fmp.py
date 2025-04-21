"""Tests for the Financial Modeling Prep (FMP) service."""

import pytest
from datetime import datetime
import os
from unittest.mock import patch, MagicMock
from backend.app.services.fmp import FMPService
from backend.app.main import global_state
import httpx

# Sample test data
MOCK_TRANSCRIPTS = [
    {
        "symbol": "AAPL",
        "date": "2024-01-15",
        "quarter": 4,
        "year": 2023,
        "content": "This is a test transcript content..."
    },
    {
        "symbol": "AAPL",
        "date": "2023-10-15",
        "quarter": 3,
        "year": 2023,
        "content": "Another test transcript..."
    }
]

@pytest.fixture
def fmp_service():
    """Create an FMP service instance with test API key."""
    with patch.dict(os.environ, {"FMP_API_KEY": "test_key"}):
        return FMPService()

@pytest.mark.asyncio
async def test_get_earnings_call_transcripts(fmp_service):
    """Test fetching earnings call transcripts."""
    # Mock the HTTP response
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_TRANSCRIPTS
    mock_response.raise_for_status.return_value = None
    
    # Mock the HTTP client get method
    with patch.object(global_state.http_client, 'get', 
                     return_value=mock_response) as mock_get:
        transcripts = await fmp_service.get_earnings_call_transcripts("AAPL", 2023)
        
        # Verify the call was made correctly
        mock_get.assert_called_once()
        url = mock_get.call_args[0][0]
        params = mock_get.call_args[1]['params']
        
        assert "earning_call_transcript/AAPL" in url
        assert params['apikey'] == "test_key"
        assert params['year'] == 2023
        
        # Verify response processing
        assert len(transcripts) == 2
        assert transcripts[0]['date'] == "2024-01-15"  # Should be sorted newest first
        assert transcripts[1]['date'] == "2023-10-15"

@pytest.mark.asyncio
async def test_get_latest_transcript(fmp_service):
    """Test fetching the most recent transcript."""
    # Mock the get_earnings_call_transcripts method
    with patch.object(fmp_service, 'get_earnings_call_transcripts', 
                     return_value=MOCK_TRANSCRIPTS) as mock_get:
        transcript = await fmp_service.get_latest_transcript("AAPL")
        
        # Verify we got the most recent transcript
        assert transcript == MOCK_TRANSCRIPTS[0]
        assert transcript['date'] == "2024-01-15"

@pytest.mark.asyncio
async def test_missing_api_key():
    """Test service initialization with missing API key."""
    with patch.dict(os.environ, clear=True):
        with pytest.raises(ValueError, match="FMP API key not found"):
            FMPService()

@pytest.mark.asyncio
async def test_api_error_handling(fmp_service):
    """Test handling of API errors."""
    # Mock an HTTP error response
    with patch.object(global_state.http_client, 'get', 
                     side_effect=httpx.HTTPError("API Error")) as mock_get:
        with pytest.raises(httpx.HTTPError):
            await fmp_service.get_earnings_call_transcripts("AAPL", 2023) 