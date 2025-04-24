import { useEffect } from 'react';
import { BacktestResponse } from '../types';

interface MarketComparisonProps {
  backtestData?: BacktestResponse;
  isLoading?: boolean;
}

export default function MarketComparison({ backtestData, isLoading = false }: MarketComparisonProps) {
  const comparison = backtestData?.data?.market_comparison;
  
  // Add debug logging when component receives data
  useEffect(() => {
    if (backtestData && backtestData.data) {
      console.log('[MarketComparison] Received backtest data:', backtestData);
      console.log('[MarketComparison] Market comparison data:', comparison);
    }
  }, [backtestData, comparison]);
  
  // Format number as percentage
  const formatPercent = (value: number | undefined | null) => {
    if (value === undefined || value === null) return 'N/A';
    return `${(value * 100).toFixed(2)}%`;
  };
  
  // Get color for value (green for positive, red for negative)
  const getValueColor = (value: number | undefined | null) => {
    if (value === undefined || value === null) return 'text-gray-500';
    return value >= 0 ? 'text-emerald-600 font-extrabold' : 'text-red-600 font-extrabold';
  };
  
  if (isLoading) {
    return (
      <div className="bg-dark-800 rounded-xl shadow-lg p-6 mt-6">
        <div className="flex justify-center items-center h-20">
          <p className="text-gray-400">Loading comparison data...</p>
        </div>
      </div>
    );
  }
  
  if (!comparison) {
    return (
      <div className="bg-dark-800 rounded-xl shadow-lg p-6 mt-6">
        <div className="flex justify-center items-center h-20">
          <p className="text-gray-400">No comparison data available</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="bg-dark-800 rounded-xl shadow-lg p-6 mt-6">
      <h3 className="text-lg font-bold mb-4 text-gray-300 border-b border-gray-700 pb-2">Market Comparison</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Strategy Return */}
        <div className="bg-dark-700 p-4 rounded-lg">
          <h4 className="text-sm text-gray-300 mb-1">Strategy Return</h4>
          <p className={`text-xl font-bold ${getValueColor(comparison.strategy_return)}`}>
            {formatPercent(comparison.strategy_return)}
          </p>
        </div>
        
        {/* S&P 500 Return */}
        <div className="bg-dark-700 p-4 rounded-lg">
          <h4 className="text-sm text-gray-300 mb-1">S&P 500 Return</h4>
          <p className={`text-xl font-bold ${getValueColor(comparison.market_index?.return)}`}>
            {formatPercent(comparison.market_index?.return)}
          </p>
        </div>
        
        {/* Market Return */}
        <div className="bg-dark-700 p-4 rounded-lg">
          <h4 className="text-sm text-gray-300 mb-1">Market Return</h4>
          <p className={`text-xl font-bold ${getValueColor(comparison.market_return)}`}>
            {formatPercent(comparison.market_return)}
          </p>
        </div>
        
        {/* Outperformance */}
        <div className="bg-dark-700 p-4 rounded-lg">
          <h4 className="text-sm text-gray-300 mb-1">Outperformance</h4>
          <p className={`text-xl font-bold ${getValueColor(comparison.outperformance)}`}>
            {formatPercent(comparison.outperformance)}
          </p>
        </div>
      </div>
    </div>
  );
} 