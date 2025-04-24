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
        df = df[df['symbol'] == 'ACN']
        
        # Filter by year if specified
        if year:
            df = df[df['year'] == year]
            
        # Transform data to match FMP API response format
        transcripts = []
        for _, row in df.iterrows():
            # Convert date to string format if it's a datetime
            date_str = row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else str(row['date'])
            
            transcript = {
                'ticker': 'ACN',
                'date': date_str,
                'quarter': f"Q{row.get('quarter', '')}",
                'year': row.get('year', ''),
                'content': row['content'],
                # Add other fields that match FMP response structure
            }
            transcripts.append(transcript)
            
        return transcripts
        
    except Exception as e:
        print(f"Error loading ACN transcripts from parquet: {e}")
        # Fallback to empty list in case of errors
        return [] 