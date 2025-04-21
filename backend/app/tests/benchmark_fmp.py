"""Benchmark script comparing async vs sync performance for FMP API calls."""

import asyncio
import time
import os
from dotenv import load_dotenv
import httpx
from app.services.fmp import FMPService

# Test with a variety of companies from different sectors
TICKERS = [
    # Tech
    "AAPL", "MSFT", "GOOGL", "META", "NVDA", "ADBE", "CRM", "INTC",
    # Finance
    "JPM", "BAC", "GS", "MS",
    # Healthcare
    "JNJ", "PFE", "UNH", "ABBV",
    # Consumer
    "AMZN", "WMT", "PG", "KO",
]

async def fetch_async():
    """Fetch transcripts using async approach."""
    async with httpx.AsyncClient(
        timeout=30.0,
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
    ) as client:
        service = FMPService(http_client=client)
        
        # Create tasks for all fetches
        tasks = [
            service.get_latest_transcript(ticker)
            for ticker in TICKERS
        ]
        
        # Run all tasks concurrently
        return await asyncio.gather(*tasks)

def fetch_sync():
    """Fetch transcripts using synchronous approach."""
    results = []
    api_key = os.getenv("FMP_API_KEY")
    with httpx.Client(timeout=30.0) as client:
        for ticker in TICKERS:
            url = f"{FMPService.BASE_URL}/earning_call_transcript/{ticker}"
            response = client.get(url, params={
                "apikey": api_key,
                "year": 2024
            })
            response.raise_for_status()
            transcripts = response.json()
            results.append(transcripts[0] if transcripts else None)
    return results

async def run_benchmark(num_runs: int = 3):
    """Run the benchmark multiple times and average the results."""
    print(f"\nBenchmarking with {len(TICKERS)} tickers, {num_runs} runs each...")
    
    async_times = []
    sync_times = []
    
    for i in range(num_runs):
        print(f"\nRun {i + 1}/{num_runs}:")
        
        # Benchmark async
        start = time.time()
        results_async = await fetch_async()
        async_time = time.time() - start
        async_times.append(async_time)
        print(f"Async time: {async_time:.2f}s")
        
        # Brief pause between tests
        await asyncio.sleep(1)
        
        # Benchmark sync
        start = time.time()
        results_sync = fetch_sync()
        sync_time = time.time() - start
        sync_times.append(sync_time)
        print(f"Sync time: {sync_time:.2f}s")
        
        # Verify results match
        assert len(results_async) == len(results_sync) == len(TICKERS)
    
    # Calculate averages
    avg_async = sum(async_times) / len(async_times)
    avg_sync = sum(sync_times) / len(sync_times)
    
    print("\nResults:")
    print(f"Average Async time: {avg_async:.2f}s")
    print(f"Average Sync time: {avg_sync:.2f}s")
    print(f"Speedup factor: {avg_sync/avg_async:.2f}x")
    
    # Show per-request times
    print(f"\nPer-request times:")
    print(f"Async: {avg_async/len(TICKERS):.2f}s per request")
    print(f"Sync: {avg_sync/len(TICKERS):.2f}s per request")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(run_benchmark()) 