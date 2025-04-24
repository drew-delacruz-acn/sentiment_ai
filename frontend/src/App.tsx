import { useState, useEffect } from 'react'
import QueryForm from './components/QueryForm'
import Chart from './components/Chart'
import Metrics from './components/Metrics'
import PerformanceSummary from './components/PerformanceSummary'
import TranscriptTable from './components/TranscriptTable'
import { useAnalysis } from './hooks/useAnalysis'
import { useForecast } from './hooks/useForecast'
import { useBacktest } from './hooks/useBacktest'
import './App.css'
import Plot from 'react-plotly.js'

// Define the extended line type to include the dash property
type PlotlyLineType = {
  color: string;
  width: number;
  dash?: 'solid' | 'dot' | 'dash' | 'longdash' | 'dashdot' | 'longdashdot';
};

function App() {
  const [ticker, setTicker] = useState<string>('')
  const [analysisYears, setAnalysisYears] = useState<number>(1) // Default to 1 year analysis period
  const [isAnalysisEnabled, setIsAnalysisEnabled] = useState(false)
  const [developerMode, setDeveloperMode] = useState(false)
  const [isControlsOpen, setIsControlsOpen] = useState(true)
  const [unlimitedCapital, setUnlimitedCapital] = useState(false) 
  const [positionSize, setPositionSize] = useState(10000) // Default to $10,000 per trade

  // Calculate startYear dynamically based on current year and analysis period
  const currentYear = new Date().getFullYear()
  const startYear = currentYear - analysisYears

  // Fixed forecast horizon of 30 days
  const forecastDays = 30

  // Use data fetching hooks with conditional enabling
  const { data: sentimentData, isLoading: isLoadingSentiment } = useAnalysis({
    ticker,
    year: startYear,
    enabled: isAnalysisEnabled && ticker !== '',
  })

  // Make forecast start from beginning of the start year
  const startDate = startYear ? `${startYear}-01-01` : ''
  
  const { data: forecastData, isLoading: isLoadingForecast } = useForecast({
    ticker,
    startDate,
    forecastDays: forecastDays, // Fixed at 30 days
    enabled: isAnalysisEnabled && ticker !== '' && !!startDate,
  })

  const { data: backtestData, isLoading: isLoadingBacktest } = useBacktest({
    ticker,
    startYear: startYear, 
    initialCapital: 100000,
    positionSize: positionSize,
    unlimitedCapital: unlimitedCapital,
    enabled: isAnalysisEnabled && ticker !== '',
  })

  // Add debugging effect for sentiment data
  useEffect(() => {
    if (sentimentData && sentimentData.data && sentimentData.data.analysis) {
      console.log("App received sentiment data:", sentimentData);
      
      // Log transcript analyses data
      const transcriptAnalyses = sentimentData.data.analysis.results?.transcript_analyses || [];
      console.log("Transcript analyses length:", transcriptAnalyses.length);
      console.log("All transcript dates from sentiment data:", 
        transcriptAnalyses.map(t => t.date).sort().join(', '));
      
      // Check date range from the period property
      if (sentimentData.data.period) {
        console.log("API reported period:", sentimentData.data.period);
      }
      
      // Log all available properties for debugging
      console.log("All data properties:", Object.keys(sentimentData.data));
    }
  }, [sentimentData]);

  // Add debugging effect for backtest data
  useEffect(() => {
    if (backtestData && backtestData.data) {
      console.log("[DEBUG] App received backtest data:", backtestData);
      
      // Log equity curve data
      if (backtestData.data.equity_curve) {
        console.log("[DEBUG] Equity curve data points:", backtestData.data.equity_curve.dates.length);
        console.log("[DEBUG] Equity curve date range:", 
          backtestData.data.equity_curve.dates[0], 
          backtestData.data.equity_curve.dates[backtestData.data.equity_curve.dates.length - 1]);
      }
      
      // Log market comparison data
      if (backtestData.data.market_comparison) {
        console.log("[DEBUG] Market comparison data:", backtestData.data.market_comparison);
        console.log("[DEBUG] Market comparison keys:", Object.keys(backtestData.data.market_comparison));
        
        // Check for market index data
        if (backtestData.data.market_comparison.market_index) {
          console.log("[DEBUG] Market index data present:", 
            backtestData.data.market_comparison.market_index.ticker,
            backtestData.data.market_comparison.market_index.name);
          console.log("[DEBUG] Market index data points:", 
            backtestData.data.market_comparison.market_index.dates.length);
          
          // Log data for plot
          console.log("[DEBUG] Market index plot data:", {
            dates: backtestData.data.market_comparison.market_index.dates.length,
            values: backtestData.data.market_comparison.market_index.values.length,
            name: backtestData.data.market_comparison.market_index.name
          });
        } else {
          console.warn("[DEBUG] No market index data in the response");
        }
      } else {
        console.warn("[DEBUG] No market comparison data in the response");
      }
    }
  }, [backtestData]);

  // Effect to enforce unlimited capital in normal mode
  useEffect(() => {
    if (!developerMode) {
      setUnlimitedCapital(true);
    }
  }, [developerMode]);

  // Handle form submission
  const handleSubmit = (newTicker: string, newAnalysisYears: number, newUnlimitedCapital: boolean, newPositionSize: number) => {
    setTicker(newTicker)
    setAnalysisYears(newAnalysisYears)
    // In normal mode, always use unlimited capital; in developer mode use the checkbox value
    setUnlimitedCapital(developerMode ? newUnlimitedCapital : true)
    setPositionSize(newPositionSize)
    setIsAnalysisEnabled(true)
    setIsControlsOpen(false) // Close controls when analysis starts
  }

  const isLoading = isLoadingSentiment || isLoadingForecast || isLoadingBacktest
  const currentDate = new Date().toLocaleDateString('en-US', { 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  })

  return (
    <div className="min-h-screen bg-dark-900 text-white">
      <header className="border-b border-gray-800 py-4 px-6">
        <div className="container mx-auto">
          <div className="flex justify-between items-center">
            <div className="text-2xl font-bold">
              <span className="text-violet-500">ACN</span> | Sentiment Analysis
            </div>
            <div className="flex items-center space-x-4">
              <div className="px-4 py-2 rounded-md bg-dark-700">
                {currentDate}
              </div>
              <div className="flex items-center">
                <label className="flex items-center cursor-pointer">
                  <div className="relative">
                    <input 
                      type="checkbox" 
                      className="sr-only" 
                      checked={developerMode}
                      onChange={() => setDeveloperMode(!developerMode)} 
                    />
                    <div className={`block w-14 h-8 rounded-full ${developerMode ? 'bg-violet-500' : 'bg-gray-600'}`}></div>
                    <div className={`absolute left-1 top-1 bg-white w-6 h-6 rounded-full transition-transform ${developerMode ? 'transform translate-x-6' : ''}`}></div>
                  </div>
                  <div className={`ml-3 ${developerMode ? 'text-violet-500' : 'text-gray-300'}`}>Developer Mode</div>
                </label>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        <div className="bg-dark-800 rounded-xl shadow-lg p-6 mb-8">
          <div 
            className="flex justify-between items-center cursor-pointer"
            onClick={() => setIsControlsOpen(!isControlsOpen)}
          >
            <h2 className="text-xl font-semibold">Sentiment Analysis Controls</h2>
            <div className="text-gray-400">
              {isControlsOpen ? (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                </svg>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              )}
            </div>
          </div>
          
          <div 
            className={`overflow-hidden transition-all duration-300 ease-in-out ${
              isControlsOpen ? 'max-h-[1000px] opacity-100 mt-4' : 'max-h-0 opacity-0'
            }`}
          >
            <p className="text-gray-400 mb-6">Process earnings call transcripts to analyze sentiment patterns</p>
            
            <QueryForm 
              onSubmit={handleSubmit}
              isLoading={isLoading}
              developerMode={developerMode}
            />
            
            {developerMode && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6 mt-6">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Embedding API:
                  </label>
                  <select className="w-full bg-dark-700 border border-gray-700 rounded-md px-4 py-2 text-white">
                    <option>OpenAI</option>
                    <option>Claude/Anthropic</option>
                    <option>Grok</option>
                    <option>Cohere</option>
                    <option>Mistral</option>
                    <option>Deep Seek</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    LLM API:
                  </label>
                  <select className="w-full bg-dark-700 border border-gray-700 rounded-md px-4 py-2 text-white">
                    <option>OpenAI</option>
                    <option>Claude/Anthropic</option>
                    <option>Grok</option>
                    <option>Cohere</option>
                    <option>Mistral</option>
                    <option>Deep Seek</option>
                  </select>
                </div>
              </div>
            )}
            
            {developerMode && (
              <div className="mt-4">
                <button
                  type="button"
                  onClick={() => {
                    const form = document.querySelector('form');
                    if (form) form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
                  }}
                  disabled={isLoading}
                  className="px-4 py-2 bg-violet-600 text-white font-medium rounded-md hover:bg-violet-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-violet-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? 'Loading...' : 'Analyze'}
                </button>
              </div>
            )}
          </div>
          
          {!isControlsOpen && isAnalysisEnabled && (
            <div className="mt-2 flex items-center">
              <div className="flex-1 text-gray-400">
                {ticker ? (
                  <span>
                    Analyzing <span className="font-semibold text-white">{ticker}</span> from <span className="font-semibold text-white">{startYear}</span> to <span className="font-semibold text-white">{currentYear}</span>
                  </span>
                ) : "No ticker selected"}
              </div>
              <button
                onClick={() => setIsControlsOpen(true)}
                className="ml-4 px-4 py-2 text-sm bg-dark-700 hover:bg-dark-600 rounded-md text-gray-300"
              >
                Edit
              </button>
            </div>
          )}
        </div>
        
        {/* Performance Summary - Full Width */}
        {isAnalysisEnabled && (
          <PerformanceSummary 
            backtestData={backtestData}
            isLoading={isLoading} 
          />
        )}
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="lg:col-span-1">
            <Chart 
              sentimentData={sentimentData} 
              forecastData={forecastData}
              isLoading={isLoading} 
              startYear={startYear}
            />
            
            {backtestData && backtestData.data && backtestData.data.equity_curve && (
              <div className="bg-dark-800 rounded-xl shadow-lg p-6 mt-6">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-xl font-semibold text-white">Equity Curve</h2>
                  
                  {/* Add Transcript Toggle Button when transcripts are available */}
                  {sentimentData?.data?.analysis?.results?.transcript_analyses && 
                   sentimentData.data.analysis.results.transcript_analyses.length > 0 && (
                    <div className="lg:hidden">
                      <button 
                        onClick={() => document.getElementById('right-transcript-table')?.scrollIntoView({ behavior: 'smooth' })}
                        className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded text-white text-sm"
                      >
                        View Transcripts
                      </button>
                    </div>
                  )}
                </div>
                
                <Plot
                  data={[
                    {
                      x: backtestData.data.equity_curve.dates,
                      y: backtestData.data.equity_curve.values,
                      type: 'scatter',
                      mode: 'lines',
                      name: 'Portfolio Value',
                      line: { color: 'rgb(16, 185, 129)', width: 3 },
                      fill: 'tozeroy',
                      fillcolor: 'rgba(16, 185, 129, 0.1)',
                    },
                    // Add market index line if data is available
                    ...(backtestData.data.market_comparison?.market_index ? [{
                      x: backtestData.data.market_comparison.market_index.dates,
                      y: backtestData.data.market_comparison.market_index.values,
                      type: 'scatter',
                      mode: 'lines',
                      name: `${backtestData.data.market_comparison.market_index.name}`,
                      line: { color: 'rgba(79, 70, 229, 0.8)', width: 2, dash: 'dash' } as PlotlyLineType
                    }] : [])
                  ]}
                  layout={{
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
                  }}
                  config={{
                    displayModeBar: true,
                    responsive: true,
                    displaylogo: false
                  }}
                  className="w-full"
                  onInitialized={(figure) => console.log("[DEBUG] Equity curve plot initialized:", figure)}
                  onError={(err) => console.error("[DEBUG] Equity curve plot error:", err)}
                />
              </div>
            )}
          </div>
          
          <div className="lg:col-span-1">
            <Metrics 
              backtestData={backtestData}
              isLoading={isLoading}
              hideEquityCurve={true}
            />
            
            {/* Keep only one TranscriptTable here and make it visible on all screen sizes */}
            {sentimentData && sentimentData.data && sentimentData.data.analysis && sentimentData.data.analysis.results && (
              <div id="right-transcript-table" className="mt-6" style={{ minHeight: '490px' }}>
                <TranscriptTable 
                  transcripts={sentimentData.data.analysis.results.transcript_analyses || []} 
                  startYear={startYear}
                />
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="bg-gray-800 text-white py-4 mt-12">
        <div className="container mx-auto px-4 text-center">
          <p className="text-sm">&copy; {new Date().getFullYear()} Sentiment AI Backtesting MVP</p>
          <p className="text-xs mt-1 text-gray-400">
            Data period: {startYear && ticker ? `${startYear} to ${currentYear}` : 'No data loaded'}
          </p>
        </div>
      </footer>
    </div>
  )
}

export default App
