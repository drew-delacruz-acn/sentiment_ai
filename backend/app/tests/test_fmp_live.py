"""Live testing script for FMP service with real API calls."""

import asyncio
import os
from dotenv import load_dotenv
from app.services.fmp import FMPService
import httpx

async def test_live_fmp():
    """Test FMP service with real API calls."""
    # Load environment variables
    load_dotenv()
    
    # Create HTTP client
    async with httpx.AsyncClient(
        timeout=30.0,
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
    ) as client:
        # Initialize service
        service = FMPService()
        service._http_client = client  # Directly set client for testing
        
        try:
            # Test with AAPL
            print("\nFetching latest transcript for AAPL...")
            transcript = await service.get_latest_transcript("AAPL")
            if transcript:
                print(f"Found transcript from {transcript.get('date')}")
                print(f"Quarter: Q{transcript.get('quarter')} {transcript.get('year')}")
                print(f"Content preview: {transcript.get('content')[:200]}...")
            else:
                print("No transcript found")
                
            # Test with MSFT from 2023
            print("\nFetching 2023 transcripts for MSFT...")
            transcripts = await service.get_earnings_call_transcripts("MSFT", 2023)
            print(f"Found {len(transcripts)} transcripts")
            for t in transcripts[:2]:  # Show first two
                print(f"- {t.get('date')}: Q{t.get('quarter')} {t.get('year')}")
                
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_live_fmp()) 