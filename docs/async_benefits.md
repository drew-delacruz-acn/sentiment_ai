# Async vs Sync Performance Benchmark Results

## Test Configuration
- **Number of Companies:** 20
- **Sectors Tested:** Technology (8), Finance (4), Healthcare (4), Consumer (4)
- **Companies Tested:**
  - **Tech:** AAPL, MSFT, GOOGL, META, NVDA, ADBE, CRM, INTC
  - **Finance:** JPM, BAC, GS, MS
  - **Healthcare:** JNJ, PFE, UNH, ABBV
  - **Consumer:** AMZN, WMT, PG, KO
- **Number of Runs:** 3
- **Date Tested:** Current

## Benchmark Results

### Individual Run Times
| Run | Async Time | Sync Time |
|-----|------------|-----------|
| 1   | 1.60s     | 2.92s     |
| 2   | 1.09s     | 2.31s     |
| 3   | 0.87s     | 2.33s     |

### Summary Statistics
- **Average Async Time:** 1.19s
- **Average Sync Time:** 2.52s
- **Speedup Factor:** 2.13x

### Per-Request Performance
- **Async:** 0.06s per request
- **Sync:** 0.13s per request

## Analysis

### Performance Benefits
1. **Concurrent Processing:** The async implementation processes requests more than twice as fast as the synchronous version.
2. **Scalability:** The benefits are clearly visible with 20 concurrent requests, showing good scaling with increased load.
3. **Consistency:** While the sync implementation shows more consistent timing (2.31s - 2.92s), the async implementation, despite more variance (0.87s - 1.60s), is consistently faster.

### Implementation Details
- Uses `httpx.AsyncClient` for async requests
- Leverages `asyncio.gather()` for concurrent execution
- Maintains connection pooling with `max_keepalive_connections=5`
- Sets appropriate timeouts (30s) to handle slower responses

### Conclusions
The async implementation demonstrates significant performance benefits for concurrent API requests, making it well-suited for the sentiment analysis application where multiple company transcripts need to be processed simultaneously. 