import useSWR from 'swr';
import { apiClient } from '../services/api';
import { SentimentAnalysisResponse } from '../types';

export interface UseAnalysisProps {
  ticker: string;
  year?: number;
  enabled?: boolean;
}

export function useAnalysis({ ticker, year, enabled = true }: UseAnalysisProps) {
  // Build a SWR key only if the hook is enabled and we have a ticker
  const shouldFetch = enabled && !!ticker;
  const keyStr = shouldFetch ? `sentiment/${ticker}/${year || ''}` : null;
  
  // Create a fetcher function that ensures proper typing
  const fetcher = async () => {
    return apiClient.getSentiment(ticker, year) as Promise<SentimentAnalysisResponse>;
  };
  
  // Use SWR for data fetching with conditional fetching
  const { data, error, isLoading, mutate } = useSWR<SentimentAnalysisResponse>(
    shouldFetch ? keyStr : null,
    fetcher,
    {
      revalidateOnFocus: false,
      revalidateIfStale: false,
    }
  );

  return {
    data,
    error,
    isLoading,
    refresh: mutate
  };
} 