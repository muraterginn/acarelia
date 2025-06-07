import React from 'react';
import { SearchForm } from './components/SearchForm';
import { ProgressTracker } from './components/ProgressTracker';
import { ResultsDisplay } from './components/ResultsDisplay';
import { useAnalysisJob } from './hooks/useAnalysisJob';
import { AlertCircle } from 'lucide-react';

function App() {
  const {
    stage,
    progress,
    statusMessage,
    jobData,
    error,
    isLoading,
    startAnalysis,
    reset
  } = useAnalysisJob();

  const renderContent = () => {
    if (stage === 'completed' && jobData) {
      return <ResultsDisplay jobData={jobData} onNewSearch={reset} />;
    }

    if (stage !== 'idle') {
      return (
        <ProgressTracker 
          stage={stage}
          progress={progress}
          statusMessage={statusMessage}
          author={jobData?.author || ''}
        />
      );
    }

    return <SearchForm onSubmit={startAnalysis} isLoading={isLoading} />;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">acarelia.com</h1>
        </div>

        {/* Error Display */}
        {error && (
          <div className="max-w-2xl mx-auto mb-8">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center">
                <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
                <span className="text-red-800 font-medium">Error</span>
              </div>
              <p className="text-red-600 text-sm mt-1">{error}</p>
              <button
                onClick={reset}
                className="mt-3 text-red-600 hover:text-red-800 text-sm font-medium underline"
              >
                Try Again
              </button>
            </div>
          </div>
        )}

        {/* Main Content */}
        <div className="flex justify-center">
          {renderContent()}
        </div>

        {/* Footer */}
        <div className="text-center mt-16 text-gray-500 text-sm">
          <p>© 2025 acarelia.com</p>
        </div>
      </div>
    </div>
  );
}

export default App;