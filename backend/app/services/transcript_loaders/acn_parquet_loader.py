"""ACN Parquet Loader for fetching ACN transcripts from local parquet file."""

import os
import logging
from typing import Optional
import pandas as pd
import polars as pl
from datetime import datetime
from pathlib import Path
from ...interfaces.transcript_loader import TranscriptLoader
from ...config import settings
from ...utils.logging import setup_logger

logger = setup_logger(__name__)

class ACNParquetLoader(TranscriptLoader):
    """Loader for ACN transcripts from local parquet file."""
    
    def __init__(self, parquet_path: Optional[str] = None):
        """Initialize ACN parquet loader with file path."""
        self.parquet_path = parquet_path or settings.ACN_PARQUET_PATH
        
        if not os.path.exists(self.parquet_path):
            logger.warning(f"ACN parquet file not found at {self.parquet_path}")
    
    async def __aenter__(self):
        """Async context manager entry - no initialization needed."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - no cleanup needed."""
        pass
    
    async def load_transcripts(self, ticker: str, from_year: Optional[int] = None) -> pl.DataFrame:
        """
        Load ACN transcript data from parquet file.
        
        Args:
            ticker: Stock ticker symbol (should be 'ACN')
            from_year: Optional start year for filtering transcripts
            
        Returns:
            Polars DataFrame with transcript data
        """
        # Only process for ACN ticker
        if ticker.upper() != 'ACN':
            logger.warning(f"ACNParquetLoader only supports ACN ticker, not {ticker}")
            return pl.DataFrame(schema={'date': pl.Datetime, 'content': pl.Utf8})
        
        try:
            logger.info(f"Loading ACN transcripts from parquet file: {self.parquet_path} with from_year={from_year}")
            
            # Read the parquet file using pandas first (which handles date conversion better)
            pdf = pd.read_parquet(self.parquet_path)
            logger.info(f"Initial parquet load: {len(pdf)} records")
            
            # Log the years available in the dataset
            if 'year' in pdf.columns:
                years = sorted(pdf['year'].unique())
                logger.info(f"Years available in the dataset: {years}")
            elif 'date' in pdf.columns:
                if pd.api.types.is_datetime64_any_dtype(pdf['date']):
                    years = sorted(pdf['date'].dt.year.unique())
                else:
                    # Try to convert to datetime first
                    try:
                        dates = pd.to_datetime(pdf['date'])
                        years = sorted(dates.dt.year.unique())
                    except:
                        years = ["unknown - could not parse dates"]
                logger.info(f"Years available in the dataset based on dates: {years}")
            
            # Filter for ACN ticker if multiple tickers exist
            if 'symbol' in pdf.columns:
                original_count = len(pdf)
                pdf = pdf[pdf['symbol'] == 'ACN']
                logger.info(f"Filtered for ACN symbol: {original_count} -> {len(pdf)} records")
            
            # Log all dates before year filtering
            if 'date' in pdf.columns and len(pdf) > 0:
                if pd.api.types.is_datetime64_any_dtype(pdf['date']):
                    all_dates = sorted(pdf['date'].dt.strftime('%Y-%m-%d').tolist())
                else:
                    all_dates = sorted(pdf['date'].astype(str).tolist())
                logger.info(f"All dates before year filtering: {all_dates}")
            
            # Filter by year if specified
            if from_year is not None:
                logger.info(f"Filtering transcripts from year >= {from_year}")
                
                # Check if we have a year column
                if 'year' in pdf.columns:
                    original_count = len(pdf)
                    
                    # Log the distribution of years before filtering
                    year_counts = pdf['year'].value_counts().sort_index()
                    logger.info(f"Year distribution before filtering: {year_counts.to_dict()}")
                    
                    # Apply the filter
                    pdf = pdf[pdf['year'] >= from_year]
                    
                    # Log the effect of the filter
                    logger.info(f"Filtered by year >= {from_year}: {original_count} -> {len(pdf)} records")
                
                # If no year column but we have a date column, filter by the date
                elif 'date' in pdf.columns:
                    original_count = len(pdf)
                    
                    # Try to extract the year from the date
                    if pd.api.types.is_datetime64_any_dtype(pdf['date']):
                        # Already datetime
                        pdf = pdf[pdf['date'].dt.year >= from_year]
                    else:
                        # Try to convert to datetime first
                        try:
                            # Convert to datetime
                            pdf['date'] = pd.to_datetime(pdf['date'])
                            pdf = pdf[pdf['date'].dt.year >= from_year]
                        except Exception as e:
                            logger.error(f"Could not filter by year: {e}")
                    
                    # Log the effect of the filter
                    logger.info(f"Filtered by date.year >= {from_year}: {original_count} -> {len(pdf)} records")
            
            # Log all dates after year filtering
            if 'date' in pdf.columns and len(pdf) > 0:
                if pd.api.types.is_datetime64_any_dtype(pdf['date']):
                    filtered_dates = sorted(pdf['date'].dt.strftime('%Y-%m-%d').tolist())
                else:
                    filtered_dates = sorted(pdf['date'].astype(str).tolist())
                logger.info(f"All dates after year filtering: {filtered_dates}")
            
            # Ensure date is in datetime format
            if 'date' in pdf.columns:
                # Convert date column to datetime if it's not already
                if not pd.api.types.is_datetime64_any_dtype(pdf['date']):
                    try:
                        logger.info("Converting date column to datetime format")
                        pdf['date'] = pd.to_datetime(pdf['date'])
                    except Exception as e:
                        logger.warning(f"Failed to convert dates: {e}")
                        # Create dates from year as fallback
                        if 'year' in pdf.columns:
                            logger.info("Using year column as fallback for dates")
                            pdf['date'] = pd.to_datetime(pdf['year'].astype(str) + '-01-01')
            else:
                # Create date from year if date column doesn't exist
                if 'year' in pdf.columns:
                    logger.info("Creating date column from year column")
                    pdf['date'] = pd.to_datetime(pdf['year'].astype(str) + '-01-01')
                else:
                    logger.error("No date or year column found in ACN parquet file")
                    return pl.DataFrame(schema={'date': pl.Datetime, 'content': pl.Utf8})
            
            # Add ticker column if it doesn't exist
            if 'ticker' not in pdf.columns:
                pdf['ticker'] = 'ACN'
            
            # Convert to polars DataFrame
            df = pl.from_pandas(pdf)
            
            # Sort by date
            df = df.sort('date', descending=True)
            
            # Log the final output
            if df.height > 0:
                min_date = df.select(pl.col('date').min()).item()
                max_date = df.select(pl.col('date').max()).item()
                logger.info(f"Final date range after all processing: {min_date} to {max_date}")
                
                all_dates = df.select('date').sort('date').to_series().to_list()
                logger.info(f"All final dates (sorted): {all_dates}")
            
            logger.info(f"Loaded {df.height} ACN transcripts from parquet file")
            return df
            
        except Exception as e:
            logger.error(f"Error loading ACN transcripts from parquet: {e}", exc_info=True)
            # Return empty DataFrame on error
            return pl.DataFrame(schema={'date': pl.Datetime, 'content': pl.Utf8}) 