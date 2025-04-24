import { BacktestResponse } from '../types';

interface PerformanceSummaryProps {
  backtestData?: BacktestResponse;
  isLoading?: boolean;
}

export default function PerformanceSummary({ backtestData, isLoading = false }: PerformanceSummaryProps) {
  const metrics = backtestData?.data?.performance_metrics;
  
  // Format number as percentage
  const formatPercent = (value: number | undefined | null) => {
    if (value === undefined || value === null) return 'N/A';
    return `${(value * 100).toFixed(2)}%`;
  };
  
  // Format number as compact currency
  const formatCompactCurrency = (value: number | undefined | null) => {
    if (value === undefined || value === null) return 'N/A';
    
    // For values over 1000, use compact notation
    if (Math.abs(value) >= 10000) {
      return new Intl.NumberFormat('en-US', { 
        style: 'currency', 
        currency: 'USD',
        notation: 'compact',
        minimumFractionDigits: 0,
        maximumFractionDigits: 1
      }).format(value);
    }
    
    // Otherwise use standard formatting
    return new Intl.NumberFormat('en-US', { 
      style: 'currency', 
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };
  
  // Get color for value (green for positive, red for negative)
  const getValueColor = (value: number | undefined | null) => {
    if (value === undefined || value === null) return 'text-gray-500';
    return value >= 0 ? 'text-emerald-600 font-extrabold' : 'text-red-600 font-extrabold';
  };

  // Check if unlimited capital mode is being used
  const isUnlimitedMode = metrics?.unlimited_mode === true;
  
  return (
    <div className="bg-dark-800 rounded-xl shadow-lg p-6 mb-6 w-full">
      <h2 className="text-xl font-semibold mb-4 text-white">
        Performance Summary
        {isUnlimitedMode && (
          <span className="ml-2 text-sm bg-indigo-600 text-white px-2 py-1 rounded">Unlimited Mode</span>
        )}
      </h2>
      
      {isLoading ? (
        <div className="flex justify-center items-center h-32">
          <p className="text-gray-400">Loading metrics data...</p>
        </div>
      ) : !metrics ? (
        <div className="flex justify-center items-center h-32">
          <p className="text-gray-400">No data available. Please run an analysis first.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {isUnlimitedMode ? (
            // Unlimited capital mode metrics
            <>
              <div className="bg-dark-700 p-4 rounded-lg flex flex-col h-full">
                <h4 className="text-gray-400 text-sm mb-1">Total Investment</h4>
                <p className="text-white text-lg md:text-xl font-bold truncate hover:text-clip hover:overflow-visible">
                  {formatCompactCurrency(metrics.total_investment)}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  {metrics.number_of_trades || 0} trades @ {formatCompactCurrency(metrics.position_size_per_trade)} each
                </p>
              </div>
              <div className="bg-dark-700 p-4 rounded-lg flex flex-col h-full">
                <h4 className="text-gray-400 text-sm mb-1">Final Portfolio Value</h4>
                <p className={`text-lg md:text-xl font-bold truncate hover:text-clip hover:overflow-visible ${getValueColor(metrics.final_capital)}`}>
                  {formatCompactCurrency(metrics.final_capital)}
                </p>
              </div>
              <div className="bg-dark-700 p-4 rounded-lg flex flex-col h-full">
                <h4 className="text-gray-400 text-sm mb-1">Return on Investment</h4>
                <div className={`${getValueColor(metrics.total_return)}`}>
                  <span className="text-lg md:text-xl font-bold">{formatPercent(metrics.total_return)}</span>
                  <div className="text-sm font-medium truncate hover:text-clip hover:overflow-visible">
                    ({formatCompactCurrency(metrics.final_capital - (metrics.total_investment || 0))})
                  </div>
                </div>
              </div>
            </>
          ) : (
            // Standard mode metrics
            <>
              <div className="bg-dark-700 p-4 rounded-lg flex flex-col h-full">
                <h4 className="text-gray-400 text-sm mb-1">Initial Capital</h4>
                <p className="text-white text-lg md:text-xl font-bold truncate hover:text-clip hover:overflow-visible">
                  {formatCompactCurrency(metrics.initial_capital)}
                </p>
              </div>
              <div className="bg-dark-700 p-4 rounded-lg flex flex-col h-full">
                <h4 className="text-gray-400 text-sm mb-1">Current Value</h4>
                <p className={`text-lg md:text-xl font-bold truncate hover:text-clip hover:overflow-visible ${getValueColor(metrics.final_capital)}`}>
                  {formatCompactCurrency(metrics.final_capital)}
                </p>
              </div>
              <div className="bg-dark-700 p-4 rounded-lg flex flex-col h-full">
                <h4 className="text-gray-400 text-sm mb-1">Profit/Loss</h4>
                <div className={`${getValueColor(metrics.total_return)}`}>
                  <span className="text-lg md:text-xl font-bold">{formatPercent(metrics.total_return)}</span>
                  <div className="text-sm font-medium truncate hover:text-clip hover:overflow-visible">
                    ({formatCompactCurrency(metrics.final_capital - metrics.initial_capital)})
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
} 