"""Sentiment analysis service."""

import asyncio
from typing import List, Dict, Any, Optional
import polars as pl
from datetime import datetime
import json
from .async_llm_client import async_llm_batch, DEFAULT_LLM_API
from ..utils.logging import setup_logger
from ..interfaces.transcript_loader import TranscriptLoader
import logging
import pandas as pd

logger = setup_logger(__name__)

class AnalysisProgress:
    """Tracks progress of sentiment analysis."""
    def __init__(self, total_items: int):
        self.total = int(total_items)  # Convert to standard Python int
        self.completed = 0
        self.current_task = "Initializing"
        self.status = "in_progress"
        self.results = None
        self.error = None

    def update(self, completed: int, current_task: str):
        self.completed = int(completed)  # Convert to standard Python int
        self.current_task = current_task

    def complete(self, results: Dict):
        self.completed = int(self.total)  # Convert to standard Python int
        self.current_task = "Complete"
        self.status = "complete"
        # Convert any numpy types in results to standard Python types
        if isinstance(results, dict):
            self.results = {k: int(v) if hasattr(v, 'dtype') else v for k, v in results.items()}
        else:
            self.results = results

    def fail(self, error: str):
        self.status = "failed"
        self.error = error

    def to_dict(self) -> Dict:
        return {
            "total": int(self.total),  # Ensure standard Python int
            "completed": int(self.completed),  # Ensure standard Python int
            "current_task": self.current_task,
            "status": self.status,
            "results": self.results,
            "error": self.error
        }

class SentimentAnalyzer:
    """Class for analyzing sentiment in earnings call transcripts."""
    
    def __init__(self, transcript_loader: TranscriptLoader):
        """
        Initialize the SentimentAnalyzer.
        
        Args:
            transcript_loader: Implementation of TranscriptLoader interface
        """
        self.transcript_loader = transcript_loader
        self.logger = logging.getLogger(__name__)
        self._progress_trackers = {}
        self._cached_transcripts = {}  # Add cache for transcripts

    async def analyze_stock_sentiment(
        self, 
        ticker: str,
        from_year: Optional[int] = None
    ) -> Dict:
        """
        Analyze sentiment for a given stock ticker.
        
        Args:
            ticker: Stock ticker symbol
            from_year: Optional start year for analysis
            
        Returns:
            Dict containing sentiment analysis results
        """
        try:
            self.logger.info(f"Starting sentiment analysis for {ticker}, from_year={from_year}")
            
            # Load transcript data using the provided loader within context
            self.logger.info(f"Loading transcripts for {ticker}")
            
            # Load and cache transcript data
            df = await self.load_transcript_data(ticker, from_year)
            if df is None or df.height == 0:
                self.logger.error(f"No transcripts found for {ticker}")
                return {
                    "status": "error",
                    "message": f"No transcripts found for {ticker}",
                    "data": None
                }
            
            # Log detailed information about loaded transcripts
            self.logger.info(f"Loaded {df.height} transcripts for {ticker}")
            
            if isinstance(df, pl.DataFrame):
                # Log the date range of the transcripts
                min_date = df.select(pl.col("date").min()).item()
                max_date = df.select(pl.col("date").max()).item()
                self.logger.info(f"Transcript date range: {min_date} to {max_date}")
                
                # Log all dates for debugging
                dates_list = df.select("date").to_series().to_list()
                self.logger.info(f"All transcript dates: {sorted(dates_list)}")
            
            # Cache the loaded transcripts
            self._cached_transcripts[ticker] = df
            
            # Initialize progress tracking
            progress = AnalysisProgress(df.height)
            self._progress_trackers[ticker] = progress
            
            # Analyze transcripts in batches
            self.logger.info(f"Starting batch analysis for {ticker}")
            analysis_results = await self.analyze_transcript(ticker)
            self.logger.info(f"Completed batch analysis for {ticker}")
            
            # Log the results
            num_analyses = len(analysis_results.get('results', {}).get('transcript_analyses', []))
            self.logger.info(f"Generated {num_analyses} transcript analysis results")
            
            if 'results' in analysis_results and 'transcript_analyses' in analysis_results['results']:
                # Log all sentiment result dates
                result_dates = [item['date'] for item in analysis_results['results']['transcript_analyses']]
                self.logger.info(f"Analysis result dates: {sorted(result_dates)}")
            
            # Prepare response
            response = {
                "status": "success",
                "message": "Sentiment analysis completed",
                "data": {
                    "ticker": ticker,
                    "num_transcripts": df.height,
                    "date_range": [
                        df.select(pl.col("date").min()).item(),
                        df.select(pl.col("date").max()).item()
                    ],
                    "analysis": analysis_results
                }
            }
            
            self.logger.info(f"Analysis complete for {ticker} with {num_analyses} results")
            return response
            
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment for {ticker}: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to analyze sentiment: {str(e)}",
                "data": None
            }

    async def analyze_transcript(self, ticker: str, batch_size: int = 5) -> Dict:
        """Analyze sentiment of transcripts with progress tracking."""
        # Initialize progress before any operations
        progress = AnalysisProgress(0)  # Initialize with 0 until we know the total
        self._progress_trackers[ticker] = progress  # Store the tracker
        
        try:
            # Use cached data instead of making a new API call
            df = self._cached_transcripts.get(ticker)
            if df is None:
                raise ValueError(f"No cached transcript data found for ticker {ticker}")

            # Convert to Polars if needed
            if not isinstance(df, pl.DataFrame):
                df = pl.from_pandas(df)
            
            total_transcripts = df.height
            self.logger.info(f"DEBUG: Processing {total_transcripts} transcripts for sentiment analysis")
            
            progress = AnalysisProgress(total_transcripts)  # Re-initialize with actual total
            self._progress_trackers[ticker] = progress  # Update the tracker with actual total
            
            results = []
            
            # Log the data structure before processing
            self.logger.info(f"DEBUG: DataFrame schema: {df.schema}")
            if 'date' in df.columns:
                self.logger.info(f"DEBUG: Date column type: {df.schema['date']}")
                
                # Log all dates in the DataFrame
                dates = sorted([d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d) 
                           for d in df.select("date").to_series().to_list()])
                self.logger.info(f"DEBUG: All dates in DataFrame: {dates}")
            
            # *** IMPORTANT FIX: No LIMIT on batch processing ***
            # IMPORTANT: Process ALL transcripts, not just the first few batches
            batch_count = (total_transcripts + batch_size - 1) // batch_size
            self.logger.info(f"DEBUG: Will process {batch_count} batches with batch_size={batch_size}")
            
            # Process in batches
            for i in range(0, total_transcripts, batch_size):
                # Get batch using Polars slice
                batch = df.slice(i, min(batch_size, total_transcripts - i))
                self.logger.info(f"DEBUG: Processing batch {i//batch_size + 1}/{batch_count} with {batch.height} transcripts")
                
                # Print the dates in this batch for debugging
                if 'date' in df.columns:
                    batch_dates = [d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d) 
                                   for d in batch.select("date").to_series().to_list()]
                    self.logger.info(f"DEBUG: Batch {i//batch_size + 1} dates: {batch_dates}")
                
                # Prepare prompts for the batch
                prompts = []
                for row in batch.iter_rows(named=True):
                    if DEFAULT_LLM_API == "GoogleAI":
                        prompt = f"""You are a financial analyst tasked with analyzing the sentiment of an earnings call transcript.
        
Based on the following transcript excerpts, determine the overall sentiment of the call.
Classify the sentiment as one of: optimistic, neutral, or pessimistic.

Also provide a brief summary (2-3 sentences) of the key points that justify your sentiment classification.

Transcript excerpts:
{row['content'][:2000]}

Output your response in the following format:
Sentiment: [optimistic/neutral/pessimistic]
Summary: [your brief summary]"""
                        prompts.append([{"content": prompt}])
                    else:
                        prompts.append([
                            {"role": "system", "content": "You are a financial analyst tasked with analyzing earnings call transcripts."},
                            {"role": "user", "content": f"""Based on the following transcript excerpts, determine the overall sentiment of the call.
Classify the sentiment as one of: optimistic, neutral, or pessimistic.

Also provide a brief summary (2-3 sentences) of the key points that justify your sentiment classification.

Transcript excerpts:
{row['content'][:2000]}

Output your response in the following format:
Sentiment: [optimistic/neutral/pessimistic]
Summary: [your brief summary]"""}
                        ])

                # Process batch
                progress.update(i, f"Analyzing batch {i//batch_size + 1} of {(total_transcripts + batch_size - 1)//batch_size}")
                batch_results = await async_llm_batch(prompts, temperature=0.3)
                
                # Parse results and convert numeric values
                for idx, result in enumerate(batch_results):
                    try:
                        # Extract sentiment and summary using string parsing
                        content = result['content']
                        sentiment = None
                        summary = None
                        
                        for line in content.split('\n'):
                            if line.startswith('Sentiment:'):
                                sentiment = line.replace('Sentiment:', '').strip().lower()
                            elif line.startswith('Summary:'):
                                summary = line.replace('Summary:', '').strip()
                        
                        if sentiment and summary:
                            row_data = batch.row(idx, named=True)
                            
                            # Log the row data being processed
                            date_str = row_data['date'].strftime('%Y-%m-%d') if 'date' in row_data and hasattr(row_data['date'], 'strftime') else str(row_data.get('date', 'unknown'))
                            self.logger.info(f"Processing transcript from {date_str} with sentiment: {sentiment}")
                            
                            results.append({
                                'sentiment': sentiment,
                                'summary': summary,
                                'date': date_str,
                                'fullText': row_data['content'] if 'content' in row_data else None  # Add full transcript text
                            })
                    except Exception as e:
                        logger.error(f"Error parsing result: {str(e)}")
                        continue

            # IMPORTANT: Make sure we have results from all batches
            self.logger.info(f"DEBUG: Completed processing all {batch_count} batches")
            self.logger.info(f"DEBUG: Total results collected: {len(results)}")
            self.logger.info(f"DEBUG: Expected results: {total_transcripts}")
            
            if len(results) < total_transcripts:
                self.logger.error(f"DEBUG: Missing results! Collected {len(results)} out of {total_transcripts}")
            
            # Calculate aggregate statistics
            if results:
                # Convert sentiment to numeric for stats
                sentiment_map = {'pessimistic': -1, 'neutral': 0, 'optimistic': 1}
                sentiment_scores = [sentiment_map[r['sentiment']] for r in results if r['sentiment'] in sentiment_map]
                
                if sentiment_scores:
                    # Create distribution count of sentiments
                    sentiment_counts = {
                        'optimistic': sum(1 for r in results if r['sentiment'] == 'optimistic'),
                        'neutral': sum(1 for r in results if r['sentiment'] == 'neutral'),
                        'pessimistic': sum(1 for r in results if r['sentiment'] == 'pessimistic')
                    }
                    self.logger.info(f"Sentiment distribution: {sentiment_counts}")
                    
                    # Sort results by date in descending order before returning
                    results.sort(key=lambda x: x['date'], reverse=True)
                    
                    # Log the final sorted list of dates
                    final_result_dates = [r['date'] for r in results]
                    self.logger.info(f"Final sorted result dates: {final_result_dates}")
                    
                    # IMPORTANT: Make sure we're returning ALL transcripts
                    self.logger.info(f"DEBUG: Returning exactly {len(results)} out of {total_transcripts} transcript analyses")
                    
                    stats = {
                        'mean_sentiment': float(sum(sentiment_scores) / len(sentiment_scores)),
                        'sentiment_counts': sentiment_counts,
                        'total_analyzed': len(results),
                        'transcript_analyses': [
                            {
                                'date': r['date'],
                                'sentiment': r['sentiment'],
                                'summary': r['summary'],
                                'fullText': r['fullText']
                            } for r in results
                        ]
                    }
                    
                    # Log the number of results being returned
                    self.logger.info(f"Returning {len(stats['transcript_analyses'])} transcript analyses")
                    
                    # Verify one more time that all transcripts have been analyzed and included
                    if len(stats['transcript_analyses']) != total_transcripts:
                        self.logger.error(f"DEBUG: CRITICAL - Missing transcripts in final response! Returning {len(stats['transcript_analyses'])} out of {total_transcripts}")
                        
                    progress.complete(stats)
                else:
                    progress.fail("No valid sentiment scores found in results")
            else:
                progress.fail("No valid results obtained from analysis")

            return progress.to_dict()

        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}", exc_info=True)
            progress.fail(str(e))
            return progress.to_dict()

    def get_progress(self, ticker: str) -> Optional[Dict]:
        """Get the current progress of sentiment analysis for a ticker."""
        if ticker in self._progress_trackers:
            return self._progress_trackers[ticker].to_dict()
        return None

    def cleanup_tracker(self, ticker: str):
        """Remove the progress tracker for a completed analysis."""
        if ticker in self._progress_trackers:
            del self._progress_trackers[ticker]

    async def load_transcript_data(self, ticker: str, from_year: Optional[int] = None) -> Optional[pl.DataFrame]:
        """Load transcript data for a ticker."""
        try:
            # Check cache first
            if ticker in self._cached_transcripts:
                return self._cached_transcripts[ticker]

            async with self.transcript_loader as loader:
                df = await loader.load_transcripts(ticker, from_year)
                if df is None or (isinstance(df, pl.DataFrame) and df.height == 0):
                    self.logger.warning(f"No transcript data found for {ticker}")
                    return None
                
                # Cache the results
                self._cached_transcripts[ticker] = df
                return df
        except Exception as e:
            self.logger.error(f"Error loading transcript data for {ticker}: {str(e)}")
            return None 