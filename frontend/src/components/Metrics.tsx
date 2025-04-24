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

export default function Metrics({ backtestData, isLoading = false, hideEquityCurve = true }: MetricsProps) {
  const metrics = backtestData?.data?.performance_metrics;
  const equityCurve = backtestData?.data?.equity_curve;
  
  // Add debug logging when component receives data
  useEffect(() => {
    if (backtestData) {
      console.log('[Metrics] Received backtest data:', backtestData);
      console.log('[Metrics] Equity curve data:', equityCurve);
      console.log('[Metrics] Performance metrics:', metrics);
    }
  }, [backtestData, equityCurve, metrics]);
  
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
    equityCurvePoints: equityCurve?.dates.length || 0
  });
  
  return (
    <div className="bg-dark-800 rounded-xl shadow-lg p-6 h-full flex flex-col">
      {isLoading ? (
        <div className="flex justify-center items-center h-32">
          <p className="text-gray-400">Loading metrics data...</p>
        </div>
      ) : !metrics ? (
        <div className="flex justify-center items-center h-32">
          <p className="text-gray-400">No data available. Please run an analysis first.</p>
        </div>
      ) : (
        <div className="flex flex-col h-full">
          <h3 className="text-lg font-bold mb-3 text-gray-300 border-b border-gray-700 pb-2">Performance Metrics</h3>
          
          <div className="flex-grow">
            <table className="w-full h-full table-fixed border-collapse">
              <thead>
                <tr>
                  <th className="bg-gradient-to-r from-purple-700 to-violet-600 text-white text-left px-6 py-4 text-xs font-semibold uppercase tracking-wider">METRIC</th>
                  <th className="bg-gradient-to-r from-violet-600 to-blue-700 text-white text-right px-6 py-4 text-xs font-semibold uppercase tracking-wider">VALUE</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                <tr style={{ height: '20%' }}>
                  <td className="px-6 py-4 bg-dark-700 text-center text-sm font-medium text-gray-300">Sharpe Ratio</td>
                  <td className={`px-6 py-4 bg-dark-700 text-right text-sm font-bold ${getValueColor(metrics.sharpe_ratio)}`}>{formatNumber(metrics.sharpe_ratio)}</td>
                </tr>
                <tr style={{ height: '20%' }}>
                  <td className="px-6 py-4 bg-dark-600 text-center text-sm font-medium text-gray-300">Sortino Ratio</td>
                  <td className={`px-6 py-4 bg-dark-600 text-right text-sm font-bold ${getValueColor(metrics.sortino_ratio)}`}>{formatNumber(metrics.sortino_ratio)}</td>
                </tr>
                <tr style={{ height: '20%' }}>
                  <td className="px-6 py-4 bg-dark-700 text-center text-sm font-medium text-gray-300">Total Return</td>
                  <td className={`px-6 py-4 bg-dark-700 text-right text-sm font-bold ${getValueColor(metrics.total_return)}`}>{formatPercent(metrics.total_return)}</td>
                </tr>
                <tr style={{ height: '20%' }}>
                  <td className="px-6 py-4 bg-dark-600 text-center text-sm font-medium text-gray-300">Max Drawdown</td>
                  <td className="px-6 py-4 bg-dark-600 text-right text-sm font-bold text-red-500">{formatPercent(metrics.max_drawdown)}</td>
                </tr>
                <tr style={{ height: '20%' }}>
                  <td className="px-6 py-4 bg-dark-700 text-center text-sm font-medium text-gray-300">Win Rate</td>
                  <td className={`px-6 py-4 bg-dark-700 text-right text-sm font-bold ${getValueColor(metrics.win_rate)}`}>{formatPercent(metrics.win_rate)}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
} 