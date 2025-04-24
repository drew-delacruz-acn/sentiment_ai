# ACN Transcript Parquet Loading Workflow

This document outlines the implementation approach for loading ACN earnings call transcripts from a local parquet file instead of downloading them from Financial Modeling Prep (FMP) API.

## Overview

For the ACN ticker specifically, the system will load transcript data from a parquet file rather than making API calls to FMP. This approach:

1. Reduces API usage and potential costs
2. Speeds up data retrieval for ACN analysis
3. Allows for offline analysis of ACN data
4. Can serve as a template for other high-priority tickers

## Implementation Details

### Backend Changes

#### 1. Create ACN Parquet Loader Service

```python
# backend/app/services/acn_parquet.py

import pandas as pd
from pathlib import Path

async def load_acn_transcripts(parquet_path, year=None):
    """
    Load ACN transcripts from parquet file.
    
    Parameters:
    -----------
    parquet_path : str
        Path to the parquet file containing ACN transcripts
    year : int, optional
        Filter transcripts to a specific year
        
    Returns:
    --------
    list
        Transcript data in the same format as returned by FMP API
    """
    try:
        # Load parquet file
        df = pd.read_parquet(parquet_path)
        
        # Filter for ACN ticker if multiple tickers exist in the file
        df = df[df['ticker'] == 'ACN']
        
        # Filter by year if specified
        if year:
            df = df[df['date'].dt.year == year]
            
        # Transform data to match FMP API response format
        transcripts = []
        for _, row in df.iterrows():
            transcript = {
                'ticker': 'ACN',
                'date': row['date'].strftime('%Y-%m-%d'),
                'quarter': row.get('quarter', ''),
                'content': row['content'],
                # Add other fields that match FMP response structure
            }
            transcripts.append(transcript)
            
        return transcripts
        
    except Exception as e:
        print(f"Error loading ACN transcripts from parquet: {e}")
        # Fallback to empty list in case of errors
        return []
```

#### 2. Modify FMP Service to Use Parquet for ACN

```python
# backend/app/services/fmp.py

from .acn_parquet import load_acn_transcripts
from ..config import settings

async def get_earnings_transcripts(client, ticker, year):
    """
    Get earnings call transcripts, using parquet for ACN and API for others.
    """
    # Special case for ACN ticker
    if ticker.upper() == 'ACN':
        return await load_acn_transcripts(
            settings.ACN_PARQUET_PATH,
            year=year
        )
    
    # Original FMP API call for other tickers
    # [existing code...]
```

#### 3. Add Configuration Settings

```python
# backend/app/config.py

from pydantic import BaseSettings

class Settings(BaseSettings):
    # Existing settings...
    
    # Path to ACN parquet file
    ACN_PARQUET_PATH: str = "./data/acn_transcripts.parquet"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### Workflow Steps

1. **Prepare Parquet File**:
   - Ensure the parquet file contains all necessary ACN transcript data
   - Follow the expected schema (ticker, date, content, quarter, etc.)
   - Store it in the location specified in your configuration

2. **System Behavior**:
   - When a user selects ACN ticker for analysis, the backend will automatically load data from the parquet file
   - The API response format will be identical regardless of the data source
   - The frontend requires no changes as this is handled transparently in the backend

3. **Configuration**:
   - Set `ACN_PARQUET_PATH` in your .env file to override the default location
   - Example: `ACN_PARQUET_PATH=/path/to/acn_transcripts.parquet`

## Parquet File Requirements

The parquet file should include these columns:
- `ticker`: Stock ticker (should be 'ACN' for our specific case)
- `date`: Date of the earnings call in datetime format
- `content`: Full text transcript of the earnings call
- `quarter`: Quarter information (e.g., 'Q1', 'Q2', etc.)

Additional columns may be included but these are the minimum required.

## Error Handling

If the parquet file cannot be read or the ACN data is not found:
1. Error will be logged
2. System will attempt to fallback to FMP API as a recovery mechanism
3. If both fail, appropriate error responses will be returned to the client

## Extending to Other Tickers

This approach can be extended to other tickers by:
1. Creating a more generic parquet loader that handles multiple tickers
2. Updating the configuration to specify which tickers should use parquet files
3. Modifying the service to check against a list of "parquet-enabled" tickers

## Testing

To test this implementation:
1. Create a test parquet file with sample ACN transcript data
2. Run tests to verify the parquet loader correctly reads and formats the data
3. Verify the system falls back to FMP API if the parquet file is unavailable 