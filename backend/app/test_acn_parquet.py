import asyncio
import sys
import os
import traceback

# Add the parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.acn_parquet import load_acn_transcripts

async def test_parquet_loader():
    """Test the ACN parquet loader with the specified path."""
    parquet_path = "/Users/andrewdelacruz/sentiment_ai/backend/app/data/trx_raw_ACN.parquet"
    
    print(f"Testing ACN parquet loader with path: {parquet_path}")
    
    try:
        # Load all transcripts
        all_transcripts = await load_acn_transcripts(parquet_path)
        print(f"Total transcripts loaded: {len(all_transcripts)}")
        
        # Show sample of first transcript if available
        if all_transcripts:
            first = all_transcripts[0]
            print("\nSample transcript data:")
            print(f"Ticker: {first.get('ticker')}")
            print(f"Date: {first.get('date')}")
            print(f"Quarter: {first.get('quarter')}")
            print(f"Year: {first.get('year')}")
            print(f"Content preview: {first.get('content')[:200]}...")
        
            # Test year filtering
            year = first.get('year')
            if year:
                print(f"\nTesting year filter for {year}:")
                year_transcripts = await load_acn_transcripts(parquet_path, year=year)
                print(f"Transcripts for {year}: {len(year_transcripts)}")
        else:
            print("No transcripts were loaded. Check for errors above.")
    
    except Exception as e:
        print(f"Error in test: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_parquet_loader()) 