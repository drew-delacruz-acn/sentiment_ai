import { BacktestResponse } from '../types';
import Plot from 'react-plotly.js';
import { useEffect } from 'react';

// Define the extended line type to include the dash property
type PlotlyLineType = {
  color: string;
  width: number;
  dash?: 'solid' | 'dot' | 'dash' | 'longdash' | 'dashdot' | 'longdashdot';
};

interface MetricsProps {
  backtestData?: BacktestResponse;
  isLoading?: boolean;
  hideEquityCurve?: boolean;
}

export default function Metrics({ backtestData, isLoading = false, hideEquityCurve = false }: MetricsProps) {
  const metrics = backtestData?.data?.performance_metrics;
  const equityCurve = backtestData?.data?.equity_curve;
  const comparison = backtestData?.data?.market_comparison;
  
  // Add debug logging when component receives data
  useEffect(() => {
    if (backtestData) {
      console.log('[Metrics] Received backtest data:', backtestData);
      console.log('[Metrics] Equity curve data:', equityCurve);
      console.log('[Metrics] Performance metrics:', metrics);
      console.log('[Metrics] Market comparison:', comparison);
      
      // Validate essential data
      if (!equityCurve) {
        console.warn('[Metrics] Missing equity curve data in backtest response');
      } else {
        console.log('[Metrics] Equity curve points:', equityCurve.dates.length);
        console.log('[Metrics] First point:', equityCurve.dates[0], equityCurve.values[0]);
        console.log('[Metrics] Last point:', 
          equityCurve.dates[equityCurve.dates.length-1], 
          equityCurve.values[equityCurve.values.length-1]
        );
      }
    }
  }, [backtestData, equityCurve, metrics, comparison]);
  
  // Format number as percentage
  const formatPercent = (value: number | undefined | null) => {
    if (value === undefined || value === null) return 'N/A';
    return `${(value * 100).toFixed(2)}%`;
  };
  
  // Format number as currency
  const formatCurrency = (value: number | undefined | null) => {
    if (value === undefined || value === null) return 'N/A';
    return new Intl.NumberFormat('en-US', { 
      style: 'currency', 
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2 
    }).format(value);
  };
  
  // Format currency in a more compact way for display in limited space
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
  
  // Format number with 2 decimal places
  const formatNumber = (value: number | undefined | null) => {
    if (value === undefined || value === null) return 'N/A';
    return value.toFixed(2);
  };
  
  // Get color for value (green for positive, red for negative)
  const getValueColor = (value: number | undefined | null) => {
    if (value === undefined || value === null) return 'text-gray-500';
    return value >= 0 ? 'text-emerald-600 font-extrabold' : 'text-red-600 font-extrabold';
  };
  
  // Prepare equity curve data for the main chart
  const equityCurveData = equityCurve ? [{
    x: equityCurve.dates,
    y: equityCurve.values,
    type: 'scatter',
    mode: 'lines',
    name: 'Portfolio Value',
    line: {
      color: 'rgb(16, 185, 129)',
      width: 3
    },
    fill: 'tozeroy',
    fillcolor: 'rgba(16, 185, 129, 0.1)',
  }] : [];
  
  console.log('[Metrics] Prepared equity curve plot data:', equityCurveData);
  
  // Equity curve layout
  const equityCurveLayout = {
    title: 'Equity Curve - Portfolio Value Over Time',
    autosize: true,
    height: 400,
    margin: { l: 50, r: 50, b: 50, t: 80 },
    xaxis: {
      title: 'Date',
      gridcolor: '#293548',
      linecolor: '#293548',
      tickfont: { color: '#cbd5e1' }
    },
    yaxis: {
      title: 'Portfolio Value ($)',
      gridcolor: '#293548',
      linecolor: '#293548',
      tickfont: { color: '#cbd5e1' }
    },
    legend: {
      orientation: 'h',
      y: -0.2,
      font: { color: '#cbd5e1' }
    },
    plot_bgcolor: '#1A2235',
    paper_bgcolor: '#1A2235',
    font: { color: '#cbd5e1' },
    hovermode: 'closest'
  };
  
  // Chart config
  const chartConfig = {
    displayModeBar: true,
    responsive: true,
    displaylogo: false
  };
  
  // Small sparkline for the metrics panel
  const sparklineData = equityCurve ? [{
    x: equityCurve.dates,
    y: equityCurve.values,
    type: 'scatter',
    mode: 'lines',
    line: {
      color: 'rgb(16, 185, 129)',
      width: 2
    },
    fill: 'tozeroy',
    fillcolor: 'rgba(16, 185, 129, 0.1)',
    showlegend: false
  }] : [];
  
  // Sparkline layout
  const sparklineLayout = {
    autosize: true,
    height: 120,
    width: 280,
    margin: { l: 0, r: 0, b: 0, t: 0, pad: 0 },
    xaxis: {
      showticklabels: false,
      showgrid: false,
      zeroline: false
    },
    yaxis: {
      showticklabels: false,
      showgrid: false,
      zeroline: false
    },
    plot_bgcolor: '#1A2235',
    paper_bgcolor: '#1A2235'
  };
  
  // Sparkline config
  const sparklineConfig = {
    displayModeBar: false,
    responsive: true
  };
  
  // Log whenever rendering state changes
  console.log('[Metrics] Rendering with state:', { 
    isLoading, 
    hasData: !!metrics,
    equityCurvePoints: equityCurve?.dates.length || 0,
    plotTraces: equityCurveData.length 
  });
  
  return (
    <div className="bg-dark-800 rounded-xl shadow-lg p-6">
      {isLoading ? (
        <div className="flex justify-center items-center h-32">
          <p className="text-gray-400">Loading metrics data...</p>
        </div>
      ) : !metrics ? (
        <div className="flex justify-center items-center h-32">
          <p className="text-gray-400">No data available. Please run an analysis first.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Main Equity Curve Chart - Only show if hideEquityCurve is false */}
          {!hideEquityCurve && equityCurveData.length > 0 && (
            <div className="mb-8">
              <h3 className="text-lg font-bold mb-4 text-gray-300 border-b border-gray-700 pb-2 text-center">Equity Curve</h3>
              <Plot
                data={equityCurveData}
                layout={equityCurveLayout}
                config={chartConfig}
                className="w-full"
                onInitialized={(figure) => console.log('[Metrics] Plot initialized:', figure)}
                onUpdate={(figure) => console.log('[Metrics] Plot updated:', figure)}
                onError={(err) => console.error('[Metrics] Plot error:', err)}
              />
            </div>
          )}

          <div>
            <h3 className="text-lg font-bold mb-4 text-gray-300 border-b border-gray-700 pb-2">Performance Metrics</h3>
            
            <div className="overflow-x-auto">
              <table className="min-w-full table-fixed border-collapse border border-gray-700">
                <thead>
                  <tr className="bg-gradient-to-r from-purple-700 to-blue-700 text-white">
                    <th className="py-3 px-4 text-left text-xs font-semibold uppercase tracking-wider border border-gray-700 w-1/4">Metric</th>
                    <th className="py-3 px-4 text-right text-xs font-semibold uppercase tracking-wider border border-gray-700 w-1/4">Value</th>
                    <th className="py-3 px-4 text-left text-xs font-semibold uppercase tracking-wider border border-gray-700 hidden md:table-cell w-2/4">Description</th>
                  </tr>
                </thead>
                <tbody className="bg-dark-700">
                  <tr>
                    <td className="py-2 px-4 text-sm font-medium text-gray-300 border border-gray-700">Sharpe Ratio</td>
                    <td className={`py-2 px-4 text-sm font-bold text-right border border-gray-700 ${getValueColor(metrics.sharpe_ratio)}`}>{formatNumber(metrics.sharpe_ratio)}</td>
                    <td className="py-2 px-4 text-sm text-gray-400 border border-gray-700 hidden md:table-cell">Return adjusted for risk (higher is better)</td>
                  </tr>
                  <tr className="bg-dark-600">
                    <td className="py-2 px-4 text-sm font-medium text-gray-300 border border-gray-700">Sortino Ratio</td>
                    <td className={`py-2 px-4 text-sm font-bold text-right border border-gray-700 ${getValueColor(metrics.sortino_ratio)}`}>{formatNumber(metrics.sortino_ratio)}</td>
                    <td className="py-2 px-4 text-sm text-gray-400 border border-gray-700 hidden md:table-cell">Return adjusted for downside risk</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-4 text-sm font-medium text-gray-300 border border-gray-700">Total Return</td>
                    <td className={`py-2 px-4 text-sm font-bold text-right border border-gray-700 ${getValueColor(metrics.total_return)}`}>{formatPercent(metrics.total_return)}</td>
                    <td className="py-2 px-4 text-sm text-gray-400 border border-gray-700 hidden md:table-cell">Overall percentage gain/loss</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-4 text-sm font-medium text-gray-300 border border-gray-700">Max Drawdown</td>
                    <td className="py-2 px-4 text-sm font-bold text-right border border-gray-700 text-red-500">{formatPercent(metrics.max_drawdown)}</td>
                    <td className="py-2 px-4 text-sm text-gray-400 border border-gray-700 hidden md:table-cell">Largest percentage drop from peak</td>
                  </tr>
                  <tr className="bg-dark-600">
                    <td className="py-2 px-4 text-sm font-medium text-gray-300 border border-gray-700">Win Rate</td>
                    <td className={`py-2 px-4 text-sm font-bold text-right border border-gray-700 ${getValueColor(metrics.win_rate)}`}>{formatPercent(metrics.win_rate)}</td>
                    <td className="py-2 px-4 text-sm text-gray-400 border border-gray-700 hidden md:table-cell">Percentage of profitable trades</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          
          {/* Market Comparison */}
          {comparison && (
            <div>
              <h3 className="text-lg font-bold mb-4 text-gray-300 border-b border-gray-700 pb-2">Market Comparison</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full table-fixed border-collapse border border-gray-700">
                  <thead>
                    <tr className="bg-gradient-to-r from-red-600 to-orange-500 text-white">
                      <th className="py-3 px-4 text-left text-xs font-semibold uppercase tracking-wider border border-gray-700 w-1/2">Metric</th>
                      <th className="py-3 px-4 text-right text-xs font-semibold uppercase tracking-wider border border-gray-700 w-1/2">Value</th>
                    </tr>
                  </thead>
                  <tbody className="bg-dark-700">
                    <tr>
                      <td className="py-2 px-4 text-sm font-medium text-gray-300 border border-gray-700">Strategy Return</td>
                      <td className={`py-2 px-4 text-sm font-extrabold text-right border border-gray-700 ${getValueColor(comparison.strategy_return)}`}>{formatPercent(comparison.strategy_return)}</td>
                    </tr>
                    
                    {/* Add Market Index Return if available */}
                    {comparison.market_index && (
                      <tr className="bg-dark-600">
                        <td className="py-2 px-4 text-sm font-medium text-gray-300 border border-gray-700">{comparison.market_index.name} Return</td>
                        <td className={`py-2 px-4 text-sm font-extrabold text-right border border-gray-700 ${getValueColor(comparison.market_index.return)}`}>{formatPercent(comparison.market_index.return)}</td>
                      </tr>
                    )}
                    
                    <tr className={comparison.market_index ? '' : 'bg-dark-600'}>
                      <td className="py-2 px-4 text-sm font-medium text-gray-300 border border-gray-700">Market Return</td>
                      <td className={`py-2 px-4 text-sm font-extrabold text-right border border-gray-700 ${getValueColor(comparison.market_return)}`}>{formatPercent(comparison.market_return)}</td>
                    </tr>
                    
                    <tr className={comparison.market_index ? 'bg-dark-600' : ''}>
                      <td className="py-2 px-4 text-sm font-medium text-gray-300 border border-gray-700">Outperformance</td>
                      <td className={`py-2 px-4 text-sm font-extrabold text-right border border-gray-700 ${getValueColor(comparison.outperformance)}`}>{formatPercent(comparison.outperformance)}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
} 