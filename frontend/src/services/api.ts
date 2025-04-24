// frontend/src/services/api.ts

// Base URL for API requests - use environment variable for flexibility
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Interface for backtest parameters
export interface BacktestParams {
  ticker: string;
  start_year: number;
  initial_capital?: number;
  position_size?: number;
  unlimited_capital?: boolean;
}

/**
 * API client for connecting to the backend
 */
export const apiClient = {
  /**
   * Generic GET request
   */
  async get<T>(endpoint: string): Promise<T> {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `API error: ${response.status}`);
      }
      
      return await response.json() as T;
    } catch (error) {
      console.error(`GET request failed for ${endpoint}:`, error);
      throw error;
    }
  },
  
  /**
   * Generic POST request
   */
  async post<T>(endpoint: string, data: any): Promise<T> {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `API error: ${response.status}`);
      }
      
      return await response.json() as T;
    } catch (error) {
      console.error(`POST request failed for ${endpoint}:`, error);
      throw error;
    }
  },
  
  /**
   * Health check endpoint
   */
  async checkHealth() {
    return this.get<{ status: string }>('/health');
  },
  
  /**
   * Get sentiment analysis for a ticker
   */
  async getSentiment(ticker: string, year?: number) {
    const queryParam = year ? `?from_year=${year}` : '';
    return this.get(`/analyze/${ticker}${queryParam}`);
  },
  
  /**
   * Get price forecast for a ticker
   */
  async getForecast(ticker: string, startDate: string, forecastDays: number = 30) {
    return this.get(`/api/forecast/${ticker}?start_date=${startDate}&forecast_days=${forecastDays}`);
  },
  
  /**
   * Run a backtest with POST method
   */
  async runBacktest(params: BacktestParams) {
    return this.post('/api/backtest/run', params);
  },
  
  /**
   * Run a backtest with GET method
   */
  async getBacktest(
    ticker: string, 
    startYear: number, 
    initialCapital: number = 100000, 
    positionSize: number = 10000,
    unlimitedCapital: boolean = false
  ) {
    return this.get(
      `/api/backtest/${ticker}?start_year=${startYear}&initial_capital=${initialCapital}&position_size=${positionSize}&unlimited_capital=${unlimitedCapital}`
    );
  }
}; 