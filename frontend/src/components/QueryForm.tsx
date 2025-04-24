import { useState, FormEvent } from 'react';

interface QueryFormProps {
  onSubmit: (ticker: string, analysisYears: number, unlimitedCapital: boolean, positionSize: number) => void;
  isLoading?: boolean;
  developerMode?: boolean;
}

export default function QueryForm({ onSubmit, isLoading = false, developerMode = false }: QueryFormProps) {
  const [ticker, setTicker] = useState('');
  const [analysisYears, setAnalysisYears] = useState<number>(1); // Default to 1 year analysis period
  const [unlimitedCapital, setUnlimitedCapital] = useState(false);
  const [positionSize, setPositionSize] = useState(10000); // Default position size

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (ticker.trim()) {
      onSubmit(ticker.toUpperCase(), analysisYears, unlimitedCapital, positionSize);
    }
  };

  // Analysis period options (years)
  const analysisYearsOptions = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

  return (
    <form onSubmit={handleSubmit}>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="ticker" className="block text-sm font-medium text-gray-300 mb-1">
            Stock Ticker
          </label>
          <input
            id="ticker"
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            placeholder="AAPL"
            className="w-full px-3 py-2 bg-dark-700 border border-gray-700 rounded-md shadow-sm focus:outline-none focus:ring-violet-500 focus:border-violet-500 text-white"
            required
          />
        </div>
        
        <div>
          <label htmlFor="analysisYears" className="block text-sm font-medium text-gray-300 mb-1">
            Historical Analysis Period (years)
          </label>
          <select
            id="analysisYears"
            value={analysisYears}
            onChange={(e) => setAnalysisYears(Number(e.target.value))}
            className="w-full px-3 py-2 bg-dark-700 border border-gray-700 rounded-md shadow-sm focus:outline-none focus:ring-violet-500 focus:border-violet-500 text-white"
          >
            {analysisYearsOptions.map((years) => (
              <option key={years} value={years}>
                {years} {years === 1 ? 'year' : 'years'}
              </option>
            ))}
          </select>
          <p className="text-xs text-gray-500 mt-1">
            Data will be analyzed from {new Date().getFullYear() - analysisYears} to present
          </p>
        </div>
        
        <div>
          <label htmlFor="positionSize" className="block text-sm font-medium text-gray-300 mb-1">
            Position Size ($)
          </label>
          <input
            id="positionSize"
            type="number"
            min="1000"
            step="1000"
            value={positionSize}
            onChange={(e) => setPositionSize(Number(e.target.value))}
            className="w-full px-3 py-2 bg-dark-700 border border-gray-700 rounded-md shadow-sm focus:outline-none focus:ring-violet-500 focus:border-violet-500 text-white"
          />
          <p className="text-xs text-gray-500 mt-1">
            Fixed dollar amount to invest on each positive signal
          </p>
        </div>
        
        {developerMode && (
          <div className="flex items-center md:mt-6">
            <div className="flex items-center h-5">
              <input
                id="unlimitedCapital"
                type="checkbox"
                checked={unlimitedCapital}
                onChange={(e) => setUnlimitedCapital(e.target.checked)}
                className="h-4 w-4 border-gray-700 rounded text-violet-600 focus:ring-violet-500 bg-dark-700"
              />
            </div>
            <div className="ml-3 text-sm">
              <label htmlFor="unlimitedCapital" className="font-medium text-gray-300">
                Unlimited Capital Mode
              </label>
              <p className="text-xs text-gray-500">
                Invest the same amount on every positive sentiment signal, regardless of capital constraints
              </p>
            </div>
          </div>
        )}
      </div>
      
      {!developerMode && (
        <div className="mt-4">
          <button
            type="submit"
            disabled={isLoading || !ticker.trim()}
            className="px-4 py-2 bg-violet-600 text-white font-medium rounded-md hover:bg-violet-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-violet-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Loading...' : 'Analyze'}
          </button>
        </div>
      )}
    </form>
  );
} 