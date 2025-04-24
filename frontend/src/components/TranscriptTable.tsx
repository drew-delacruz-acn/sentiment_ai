import { useState, useEffect, useMemo } from 'react';
import { SentimentResult } from '../types';

// Modal component for displaying full transcript
interface TranscriptModalProps {
  isOpen: boolean;
  onClose: () => void;
  transcript: {
    date: string;
    sentiment: string;
    fullText: string;
  } | null;
}

function TranscriptModal({ isOpen, onClose, transcript }: TranscriptModalProps) {
  if (!isOpen || !transcript) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50 p-4 overflow-y-auto">
      <div className="bg-dark-900 rounded-xl shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        <div className="flex justify-between items-center border-b border-gray-700 p-4 sticky top-0 bg-dark-900 z-10">
          <h3 className="text-lg sm:text-xl font-semibold text-white">
            Earnings Call Transcript - {new Date(transcript.date).toLocaleDateString()}
          </h3>
          <div className="flex items-center space-x-3">
            <span className={`px-2 py-1 rounded-full text-xs sm:text-sm ${
              transcript.sentiment === 'optimistic' ? 'bg-green-900 text-green-200' :
              transcript.sentiment === 'negative' ? 'bg-red-900 text-red-200' :
              'bg-gray-700 text-gray-200'
            }`}>
              {transcript.sentiment.charAt(0).toUpperCase() + transcript.sentiment.slice(1)}
            </span>
            <button 
              onClick={onClose}
              className="text-gray-400 hover:text-white p-2"
              aria-label="Close modal"
            >
              ✕
            </button>
          </div>
        </div>
        <div className="overflow-y-auto p-4 sm:p-6 flex-grow">
          <div className="whitespace-pre-wrap text-gray-200 text-sm sm:text-base">
            {transcript.fullText}
          </div>
        </div>
      </div>
    </div>
  );
}

interface TranscriptTableProps {
  transcripts: SentimentResult[];
  startYear?: number; // Add startYear prop
}

export default function TranscriptTable({ transcripts, startYear }: TranscriptTableProps) {
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedTranscript, setSelectedTranscript] = useState<{
    date: string;
    sentiment: string;
    fullText: string;
  } | null>(null);

  // Calculate the effective startYear - if not provided, use current year - 1
  const effectiveStartYear = startYear || (new Date().getFullYear() - 1);

  // Filter transcripts based on startYear
  const filteredTranscripts = useMemo(() => {
    return transcripts.filter(transcript => {
      const transcriptDate = new Date(transcript.date.substring(0, 10));
      const transcriptYear = transcriptDate.getFullYear();
      
      // Only include transcripts from startYear up to current year + 1 (to include near-future forecasts)
      return transcriptYear >= effectiveStartYear && transcriptYear <= new Date().getFullYear() + 1;
    });
  }, [transcripts, effectiveStartYear]);

  // Add useEffect to log transcript data when it changes
  useEffect(() => {
    console.log("TranscriptTable received transcripts:", transcripts);
    console.log("Filtered transcripts based on year:", filteredTranscripts.length);
    console.log("Using date filter from year:", effectiveStartYear);
    
    if (filteredTranscripts && filteredTranscripts.length > 0) {
      console.log("First transcript:", filteredTranscripts[0]);
      console.log("Total transcripts:", filteredTranscripts.length);
      console.log("All transcript dates:", filteredTranscripts.map(t => t.date).sort());
    }
  }, [transcripts, filteredTranscripts, effectiveStartYear]);

  const openTranscriptModal = (transcript: SentimentResult) => {
    setSelectedTranscript({
      date: transcript.date,
      sentiment: transcript.sentiment,
      fullText: transcript.fullText || transcript.summary
    });
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
  };

  const truncateText = (text: string, maxLength = 100) => {
    if (!text) return '';
    return text.length > maxLength ? `${text.substring(0, maxLength)}...` : text;
  };

  if (!filteredTranscripts || filteredTranscripts.length === 0) {
    return (
      <div className="bg-dark-800 rounded-xl shadow-lg p-4 sm:p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Earnings Call Transcripts</h2>
        <p className="text-gray-400">No transcript data available for the selected date range</p>
      </div>
    );
  }

  return (
    <div className="bg-dark-800 rounded-xl shadow-lg p-4 sm:p-6 flex flex-col h-full">
      <div className="flex justify-center items-center mb-4">
        <h2 className="text-xl font-semibold text-white">Earnings Call Transcripts</h2>
      </div>
      
      {/* Improved scrolling container */}
      <div className="overflow-hidden flex-grow h-full relative" style={{ minHeight: '360px' }}>
        <div className="absolute inset-0 overflow-y-auto overflow-x-hidden">
          <table className="min-w-full bg-dark-900 rounded-lg border border-gray-800">
            <thead className="bg-gray-800 sticky top-0 z-10">
              <tr>
                <th className="px-3 sm:px-4 py-3 text-left text-xs sm:text-sm font-medium text-gray-300">Date</th>
                <th className="px-3 sm:px-4 py-3 text-left text-xs sm:text-sm font-medium text-gray-300">Sentiment</th>
                <th className="px-3 sm:px-4 py-3 text-left text-xs sm:text-sm font-medium text-gray-300">Transcript</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {filteredTranscripts.map((transcript, index) => (
                <tr 
                  key={index} 
                  className="hover:bg-dark-700 cursor-pointer transition-colors"
                  onClick={() => openTranscriptModal(transcript)}
                >
                  <td className="px-3 sm:px-4 py-2 sm:py-3 text-xs sm:text-sm text-gray-300 whitespace-nowrap">
                    {new Date(transcript.date).toLocaleDateString()}
                  </td>
                  <td className="px-3 sm:px-4 py-2 sm:py-3 text-xs sm:text-sm">
                    <span className={`inline-block px-2 py-1 rounded-full text-xs ${
                      transcript.sentiment === 'optimistic' ? 'bg-green-900 text-green-200' :
                      transcript.sentiment === 'negative' ? 'bg-red-900 text-red-200' :
                      'bg-gray-700 text-gray-200'
                    }`}>
                      {transcript.sentiment.charAt(0).toUpperCase() + transcript.sentiment.slice(1)}
                    </span>
                  </td>
                  <td className="px-3 sm:px-4 py-2 sm:py-3 text-xs sm:text-sm text-gray-300">
                    {truncateText(transcript.summary)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <TranscriptModal 
        isOpen={modalOpen}
        onClose={closeModal}
        transcript={selectedTranscript}
      />
    </div>
  );
} 