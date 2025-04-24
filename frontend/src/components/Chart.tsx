import { useEffect, useRef, useState } from 'react';
import Plot from 'react-plotly.js';
import { SentimentAnalysisResponse, ForecastResponse } from '../types';

interface ChartProps {
  sentimentData?: SentimentAnalysisResponse;
  forecastData?: ForecastResponse;
  isLoading?: boolean;
  startYear?: number;
}

type SentimentMarker = {
  date: string;
  sentiment: 'negative' | 'neutral' | 'optimistic';
  color: string;
  summary: string;
  score: number;
};

type SentimentTypeData = {
  x: string[];
  y: number[];
  text: string[];
  marker: {
    color: string;
    size: number;
    symbol: string;
  };
};

type ChartType = 'line' | 'candlestick';

export default function Chart({ sentimentData, forecastData, isLoading = false, startYear }: ChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const [chartType, setChartType] = useState<ChartType>('line');

  // Debug: Log data when it changes
  useEffect(() => {
    if (forecastData) {
      console.log('Forecast Data Structure:', forecastData);
      console.log('Historical dates range:', 
        forecastData.historical.dates[0], 
        'to', 
        forecastData.historical.dates[forecastData.historical.dates.length - 1]
      );
    }
    
    if (sentimentData) {
      console.log('Sentiment Data:', sentimentData);
      const transcripts = sentimentData?.data?.analysis?.results?.transcript_analyses || [];
      console.log('Transcript dates:', transcripts.map(t => t.date).join(', '));
    }
  }, [forecastData, sentimentData]);

  // Calculate the effective startYear - if not provided, use current year - 1
  const effectiveStartYear = startYear || (new Date().getFullYear() - 1);
  
  // Prepare sentiment markers - FILTERED based on startYear
  const sentimentMarkers: SentimentMarker[] = sentimentData?.data?.analysis?.results?.transcript_analyses
    ?.filter(item => {
      // Extract date from the transcript
      const transcriptDate = new Date(item.date.substring(0, 10));
      const transcriptYear = transcriptDate.getFullYear();
      
      // Only include transcripts from startYear up to current year + 1 (to include near-future forecasts)
      return transcriptYear >= effectiveStartYear && transcriptYear <= new Date().getFullYear() + 1;
    })
    ?.map(item => {
      const color = item.sentiment === 'negative' 
        ? 'red' 
        : item.sentiment === 'optimistic' 
          ? 'green' 
          : 'gray';
          
      return {
        date: item.date,
        sentiment: item.sentiment,
        color,
        summary: item.summary,
        score: item.score || 0
      };
    }) || [];
  
  console.log('Sentiment markers created:', sentimentMarkers.length);
  console.log('Using date filter from year:', effectiveStartYear);

  // Prepare plot data
  const plotData: any[] = [];
  
  // Add historical price data if available
  if (forecastData?.historical) {
    if (chartType === 'line') {
      plotData.push({
        x: forecastData.historical.dates,
        y: forecastData.historical.prices,
        type: 'scatter',
        mode: 'lines',
        name: 'Historical Price',
        line: {
          color: 'blue',
          width: 2
        }
      });
    } else if (chartType === 'candlestick') {
      // Use real OHLC data if available, otherwise create synthetic data
      if (forecastData.historical.ohlc) {
        plotData.push({
          x: forecastData.historical.dates,
          open: forecastData.historical.ohlc.open,
          high: forecastData.historical.ohlc.high,
          low: forecastData.historical.ohlc.low,
          close: forecastData.historical.ohlc.close,
          increasing: {line: {color: '#26a69a'}, fillcolor: '#26a69a'},
          decreasing: {line: {color: '#ef5350'}, fillcolor: '#ef5350'},
          type: 'candlestick',
          name: 'Price'
        });
      } else if (forecastData.historical.prices) {
        // Fallback to synthetic OHLC data based on close prices
        const ohlc = forecastData.historical.prices.map(price => ({
          open: price,
          high: price * 1.005, // Approximation for demo purposes
          low: price * 0.995,  // Approximation for demo purposes
          close: price
        }));
        
        plotData.push({
          x: forecastData.historical.dates,
          open: ohlc.map(d => d.open),
          high: ohlc.map(d => d.high),
          low: ohlc.map(d => d.low),
          close: ohlc.map(d => d.close),
          increasing: {line: {color: '#26a69a'}, fillcolor: '#26a69a'},
          decreasing: {line: {color: '#ef5350'}, fillcolor: '#ef5350'},
          type: 'candlestick',
          name: 'Price'
        });
      }
    }
  }
  
  // Add forecast bands if available
  if (forecastData?.forecast?.bands) {
    // Add P50 (median) forecast line
    if (Array.isArray(forecastData.forecast.bands.p50)) {
      plotData.push({
        x: forecastData.forecast.dates,
        y: forecastData.forecast.bands.p50,
        type: 'scatter',
        mode: 'lines',
        name: 'Median Forecast (P50)',
        line: {
          color: 'rgb(44, 160, 44)',
          width: 2,
          dash: 'dash'
        }
      });
    }
    
    // Add P10-P90 confidence band as a filled area
    if (Array.isArray(forecastData.forecast.bands.p90) && Array.isArray(forecastData.forecast.bands.p10)) {
      plotData.push({
        x: [...forecastData.forecast.dates, ...forecastData.forecast.dates.slice().reverse()],
        y: [...forecastData.forecast.bands.p90, ...forecastData.forecast.bands.p10.slice().reverse()],
        fill: 'toself',
        fillcolor: 'rgba(0, 100, 80, 0.2)',
        line: { color: 'transparent' },
        name: 'Forecast Range (P10-P90)',
        showlegend: true,
        type: 'scatter'
      });
    }
  }
  
  // Add sentiment markers if available
  if (sentimentMarkers.length > 0 && forecastData?.historical) {
    const sentimentsByType: Record<string, SentimentTypeData> = {
      negative: { x: [], y: [], text: [], marker: { color: 'red', size: 10, symbol: 'triangle-down' } },
      neutral: { x: [], y: [], text: [], marker: { color: 'gray', size: 10, symbol: 'circle' } },
      optimistic: { x: [], y: [], text: [], marker: { color: 'green', size: 10, symbol: 'triangle-up' } }
    };
    
    // Convert historical dates to Date objects for easier comparison
    const historicalDates = forecastData.historical.dates.map(dateStr => new Date(dateStr));
    
    // Process each sentiment marker
    sentimentMarkers.forEach(marker => {
      try {
        // Extract date portion and convert to Date object
        const markerDate = new Date(marker.date.substring(0, 10));
        
        // Find the closest date in historical data
        let closestDateIndex = -1;
        let minTimeDiff = Infinity;
        
        historicalDates.forEach((date, index) => {
          const timeDiff = Math.abs(date.getTime() - markerDate.getTime());
          if (timeDiff < minTimeDiff) {
            minTimeDiff = timeDiff;
            closestDateIndex = index;
          }
        });
        
        // If we found a reasonably close date (within 5 days), use its price
        const daysDifference = minTimeDiff / (1000 * 60 * 60 * 24);
        
        if (closestDateIndex >= 0) {
          const price = forecastData.historical.prices[closestDateIndex];
          const dateStr = forecastData.historical.dates[closestDateIndex];
          const sentimentType = marker.sentiment as keyof typeof sentimentsByType;
          
          // Use the original marker date for display but position at the closest price point
          sentimentsByType[sentimentType].x.push(dateStr);
          sentimentsByType[sentimentType].y.push(price);
          
          // Add information about date approximation to the tooltip if dates aren't exact
          let tooltipText = marker.summary;
          if (daysDifference > 1) {
            tooltipText += `<br>(Earnings call: ${marker.date.substring(0, 10)})`;
          }
          
          sentimentsByType[sentimentType].text.push(tooltipText);
          
          console.log(`Matched sentiment from ${marker.date.substring(0, 10)} to price point at ${dateStr} (${daysDifference.toFixed(1)} days diff)`);
        } else {
          console.log(`No matching date found for ${marker.date.substring(0, 10)}`);
        }
      } catch (error) {
        console.error('Error processing sentiment marker:', error);
      }
    });
    
    // Log summary of matched sentiment markers
    Object.entries(sentimentsByType).forEach(([sentiment, data]) => {
      console.log(`${sentiment} sentiment markers: ${data.x.length}`);
    });
    
    // Add each sentiment type as a separate scatter trace
    Object.entries(sentimentsByType).forEach(([sentiment, data]) => {
      if (data.x.length > 0) {
        plotData.push({
          x: data.x,
          y: data.y,
          text: data.text,
          mode: 'markers',
          type: 'scatter',
          name: `${sentiment.charAt(0).toUpperCase() + sentiment.slice(1)} Sentiment`,
          marker: data.marker,
          hoverinfo: 'text+y'
        });
      }
    });
  }

  const layout = {
    title: forecastData?.metadata?.ticker 
      ? `Price History and Forecast: ${forecastData.metadata.ticker}`
      : 'Price History and Forecast',
    autosize: true,
    height: 500,
    margin: { l: 50, r: 50, b: 50, t: 80 },
    xaxis: {
      title: 'Date',
      rangeslider: { visible: false },
      gridcolor: '#293548',
      linecolor: '#293548',
      tickfont: { color: '#cbd5e1' }
    },
    yaxis: {
      title: 'Price ($)',
      autorange: true,
      gridcolor: '#293548',
      linecolor: '#293548',
      tickfont: { color: '#cbd5e1' }
    },
    legend: {
      orientation: 'h',
      y: -0.2,
      font: { color: '#cbd5e1' }
    },
    hovermode: 'closest',
    plot_bgcolor: '#1A2235',
    paper_bgcolor: '#1A2235',
    font: { color: '#cbd5e1' }
  };

  const config = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false
  };

  // Toggle chart type handler
  const toggleChartType = () => {
    setChartType(prev => prev === 'line' ? 'candlestick' : 'line');
  };

  return (
    <div ref={chartRef} className="bg-dark-800 rounded-xl shadow-lg p-6 mb-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-white">Price Analysis and Forecast</h2>
        {plotData.length > 0 && (
          <button
            onClick={toggleChartType}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            {chartType === 'line' ? 'Switch to Candlestick' : 'Switch to Line Chart'}
          </button>
        )}
      </div>
      
      {isLoading ? (
        <div className="flex justify-center items-center h-64">
          <p className="text-gray-400">Loading chart data...</p>
        </div>
      ) : plotData.length === 0 ? (
        <div className="flex justify-center items-center h-64">
          <p className="text-gray-400">No data available. Please run an analysis first.</p>
        </div>
      ) : (
        <div className="flex justify-center">
          <Plot 
            data={plotData} 
            layout={{...layout, autosize: true}}
            config={config}
            className="w-full"
            style={{margin: '0 auto'}}
          />
        </div>
      )}
    </div>
  );
} 