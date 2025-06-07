import React from 'react';
import { CheckCircle, Clock, AlertCircle, Loader } from 'lucide-react';
import { ProcessStage } from '../types/api';

interface ProgressTrackerProps {
  stage: ProcessStage;
  progress: number;
  statusMessage: string;
  author: string;
}

export const ProgressTracker: React.FC<ProgressTrackerProps> = ({ 
  stage, 
  progress, 
  statusMessage, 
  author 
}) => {
  const stages = [
    { key: 'scraping', label: 'Scraping Publications', description: 'Collecting publication data' },
    { key: 'resolving', label: 'Resolving DOIs', description: 'Verifying publication identifiers' },
    { key: 'extracting', label: 'Extracting Content', description: 'Processing publication content' },
    { key: 'analyzing', label: 'AI Analysis / Plagiarism Analysis', description: 'Running integrity checks' },
  ];

  const getStageIcon = (stageKey: string, currentStage: ProcessStage) => {
    const stageIndex = stages.findIndex(s => s.key === stageKey);
    const currentIndex = stages.findIndex(s => s.key === currentStage);

    if (stage === 'error') {
      return <AlertCircle className="w-5 h-5 text-red-500" />;
    }

    if (stageIndex < currentIndex || stage === 'completed') {
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    }

    if (stageIndex === currentIndex && stage !== 'completed') {
      return <Loader className="w-5 h-5 text-blue-500 animate-spin" />;
    }

    return <Clock className="w-5 h-5 text-gray-300" />;
  };

  const getStageStatus = (stageKey: string, currentStage: ProcessStage) => {
    const stageIndex = stages.findIndex(s => s.key === stageKey);
    const currentIndex = stages.findIndex(s => s.key === currentStage);

    if (stage === 'error') return 'error';
    if (stageIndex < currentIndex || stage === 'completed') return 'completed';
    if (stageIndex === currentIndex && stage !== 'completed') return 'active';
    return 'pending';
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Analyzing: {author}
          </h2>
          <p className="text-gray-600">{statusMessage}</p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">Progress</span>
            <span className="text-sm font-medium text-gray-700">{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div 
              className={`h-3 rounded-full transition-all duration-500 ${
                stage === 'error' ? 'bg-red-500' : 
                stage === 'completed' ? 'bg-green-500' : 'bg-blue-500'
              }`}
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>

        {/* Stage Indicators */}
        <div className="space-y-4">
          {stages.map((stageItem, index) => {
            const status = getStageStatus(stageItem.key, stage);
            
            return (
              <div 
                key={stageItem.key}
                className={`flex items-center p-4 rounded-lg border transition-all duration-200 ${
                  status === 'completed' ? 'bg-green-50 border-green-200' :
                  status === 'active' ? 'bg-blue-50 border-blue-200' :
                  status === 'error' ? 'bg-red-50 border-red-200' :
                  'bg-gray-50 border-gray-200'
                }`}
              >
                <div className="flex-shrink-0 mr-4">
                  {getStageIcon(stageItem.key, stage)}
                </div>
                <div className="flex-grow">
                  <h3 className={`font-semibold ${
                    status === 'completed' ? 'text-green-800' :
                    status === 'active' ? 'text-blue-800' :
                    status === 'error' ? 'text-red-800' :
                    'text-gray-500'
                  }`}>
                    {stageItem.label}
                  </h3>
                  <p className={`text-sm ${
                    status === 'completed' ? 'text-green-600' :
                    status === 'active' ? 'text-blue-600' :
                    status === 'error' ? 'text-red-600' :
                    'text-gray-400'
                  }`}>
                    {stageItem.description}
                  </p>
                </div>
                <div className="flex-shrink-0">
                  {status === 'completed' && (
                    <span className="text-xs font-medium text-green-600 bg-green-100 px-2 py-1 rounded-full">
                      Complete
                    </span>
                  )}
                  {status === 'active' && (
                    <span className="text-xs font-medium text-blue-600 bg-blue-100 px-2 py-1 rounded-full">
                      Processing
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {stage === 'error' && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center">
              <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
              <span className="text-red-800 font-medium">Analysis Failed</span>
            </div>
            <p className="text-red-600 text-sm mt-1">
              There was an error during the analysis process. Please try again.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};