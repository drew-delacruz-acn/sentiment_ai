import pandas as pd

def check_parquet_structure():
    """Check the structure of the ACN parquet file"""
    parquet_path = "/Users/andrewdelacruz/sentiment_ai/backend/app/data/trx_raw_ACN.parquet"
    
    try:
        # Read the parquet file
        df = pd.read_parquet(parquet_path)
        
        # Print basic information
        print(f"Parquet file loaded successfully")
        print(f"Shape: {df.shape}")
        print("\nColumns:")
        for col in df.columns:
            print(f"- {col}")
        
        # Print sample data (first row)
        if len(df) > 0:
            print("\nSample data (first row):")
            for col in df.columns:
                print(f"{col}: {df[col].iloc[0]}")
    
    except Exception as e:
        print(f"Error reading parquet file: {e}")

if __name__ == "__main__":
    check_parquet_structure() 