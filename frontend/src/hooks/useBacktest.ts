import useSWR from 'swr';
import { apiClient } from '../services/api';
import { BacktestResponse } from '../types';

export interface UseBacktestProps {
  ticker: string;
  startYear: number;
  initialCapital?: number;
  positionSize?: number;
  unlimitedCapital?: boolean;
  enabled?: boolean;
}

export function useBacktest({ 
  ticker, 
  startYear, 
  initialCapital = 100000, 
  positionSize = 10000,
  unlimitedCapital = false,
  enabled = true 
}: UseBacktestProps) {
  // Build a SWR key only if the hook is enabled and we have required params
  const shouldFetch = enabled && !!ticker && !!startYear;
  const keyStr = shouldFetch 
    ? `backtest/${ticker}/${startYear}/${initialCapital}/${positionSize}/${unlimitedCapital}` 
    : null;
  
  // Create a fetcher function that ensures proper typing
  const fetcher = async () => {
    return apiClient.getBacktest(
      ticker, 
      startYear, 
      initialCapital, 
      positionSize, 
      unlimitedCapital
    ) as Promise<BacktestResponse>;
  };
  
  // Use SWR for data fetching with conditional fetching
  const { data, error, isLoading, mutate } = useSWR<BacktestResponse>(
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