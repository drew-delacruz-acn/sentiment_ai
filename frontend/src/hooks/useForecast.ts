import useSWR from 'swr';
import { apiClient } from '../services/api';
import { ForecastResponse } from '../types';

export interface UseForecastProps {
  ticker: string;
  startDate: string;
  forecastDays?: number;
  enabled?: boolean;
}

export function useForecast({ 
  ticker, 
  startDate, 
  forecastDays = 30, 
  enabled = true 
}: UseForecastProps) {
  // Build a SWR key only if the hook is enabled and we have required params
  const shouldFetch = enabled && !!ticker && !!startDate;
  const keyStr = shouldFetch 
    ? `forecast/${ticker}/${startDate}/${forecastDays}` 
    : null;
  
  // Create a fetcher function that ensures proper typing
  const fetcher = async () => {
    const response = await apiClient.getForecast(ticker, startDate, forecastDays) as any;
    
    // Fix case sensitivity issue with bands - backend returns "P10", "P50", "P90" but frontend expects "p10", "p50", "p90"
    if (response?.forecast?.bands) {
      const { P10, P50, P90 } = response.forecast.bands;
      
      // Transform to expected lowercase format
      response.forecast.bands = {
        p10: P10 || [],
        p50: P50 || [],
        p90: P90 || []
      };
    }
    
    return response as ForecastResponse;
  };
  
  // Use SWR for data fetching with conditional fetching
  const { data, error, isLoading, mutate } = useSWR<ForecastResponse>(
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