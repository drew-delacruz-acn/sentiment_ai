import asyncio
import time
from datetime import datetime, timedelta
import yfinance as yf
from backend.app.services.prices import PriceService

# Test with a diverse set of tickers across sectors
TICKERS = [
    # Tech
    "AAPL", "MSFT", "GOOGL", "META", "NVDA",
    # Finance
    "JPM", "BAC", "GS", "V", "MA",
    # Healthcare
    "JNJ", "PFE", "UNH", "ABBV", "MRK",
    # Consumer
    "AMZN", "WMT", "PG", "KO", "PEP",
    # Industrial
    "CAT", "BA", "GE", "MMM", "HON"
]

def sync_get_prices(tickers, start_date, end_date):
    """Synchronous price fetching"""
    results = {}
    for ticker in tickers:
        try:
            ticker_obj = yf.Ticker(ticker)
            df = ticker_obj.history(start=start_date, end=end_date)
            results[ticker] = df
        except Exception as e:
            print(f"Error fetching {ticker}: {str(e)}")
            results[ticker] = None
    return results

async def benchmark():
    print(f"\nBenchmarking with {len(TICKERS)} tickers, 3 runs each...")
    service = PriceService()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    async_times = []
    sync_times = []
    
    for i in range(3):
        print(f"\nRun {i+1}/3:")
        
        # Benchmark async implementation
        start_time = time.time()
        await service.get_batch_prices(TICKERS, start_date, end_date)
        async_time = time.time() - start_time
        async_times.append(async_time)
        print(f"Async time: {async_time:.2f}s")
        
        # Benchmark sync implementation
        start_time = time.time()
        sync_get_prices(TICKERS, start_date, end_date)
        sync_time = time.time() - start_time
        sync_times.append(sync_time)
        print(f"Sync time: {sync_time:.2f}s")
        
        # Small delay between runs
        await asyncio.sleep(1)
    
    # Calculate averages
    avg_async = sum(async_times) / len(async_times)
    avg_sync = sum(sync_times) / len(sync_times)
    speedup = avg_sync / avg_async
    
    print("\nResults:")
    print(f"Average Async time: {avg_async:.2f}s")
    print(f"Average Sync time: {avg_sync:.2f}s")
    print(f"Speedup factor: {speedup:.2f}x")
    
    # Calculate per-request times
    print("\nPer-request times:")
    print(f"Async: {(avg_async/len(TICKERS)):.2f}s per request")
    print(f"Sync: {(avg_sync/len(TICKERS)):.2f}s per request")
    
    return {
        "async_times": async_times,
        "sync_times": sync_times,
        "avg_async": avg_async,
        "avg_sync": avg_sync,
        "speedup": speedup,
        "tickers": TICKERS
    }

if __name__ == "__main__":
    asyncio.run(benchmark()) 