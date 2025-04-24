// Health check response
export interface HealthResponse {
  status: string;
}

// Sentiment analysis response
export interface SentimentResult {
  date: string;
  quarter: string;
  sentiment: 'negative' | 'neutral' | 'optimistic';
  score: number;
  summary: string;
  fullText: string; // Changed from optional to required since backend will always provide it
}

export interface SentimentAnalysisResponse {
  status: string;
  message: string;
  data: {
    ticker: string;
    period: {
      from: string;
      to: string;
    };
    analysis: {
      results: {
        transcript_analyses: SentimentResult[];
      };
      summary: {
        overall_sentiment: string;
        sentiment_distribution: {
          negative: number;
          neutral: number;
          optimistic: number;
        };
      };
    };
  };
}

// Price forecast response
export interface ForecastResponse {
  historical: {
    dates: string[];
    prices: number[];
    ohlc?: {
      open: number[];
      high: number[];
      low: number[];
      close: number[];
    };
  };
  forecast: {
    dates: string[];
    bands: {
      p10: number[];
      p50: number[];
      p90: number[];
    };
  };
  metadata: {
    ticker: string;
    forecast_days: number;
  };
}

// Backtest response
export interface PerformanceMetrics {
  initial_capital: number;
  final_capital: number;
  total_return: number;
  annualized_return: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown: number;
  win_rate: number;
  // Unlimited capital mode metrics
  unlimited_mode?: boolean;
  total_investment?: number;
  position_size_per_trade?: number;
  number_of_trades?: number;
}

export interface Trade {
  date: string;
  action: 'buy' | 'sell';
  price: number;
  shares: number;
  value: number;
  sentiment: string;
}

export interface BacktestResponse {
  status: string;
  message: string;
  data: {
    performance_metrics: PerformanceMetrics;
    trades: Trade[];
    equity_curve: {
      dates: string[];
      values: number[];
    };
    market_comparison: {
      period: {
        start_date: string;
        end_date: string;
      };
      market_return: number;
      strategy_return: number;
      outperformance: number;
      buy_hold: {
        initial_value: number;
        final_value: number;
        return: number;
      };
      market_index?: {
        ticker: string;
        name: string;
        initial_value: number;
        final_value: number;
        return: number;
        dates: string[];
        values: number[];
      };
    };
  };
} 