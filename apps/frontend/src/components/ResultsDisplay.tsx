import React from 'react';
import { ExternalLink, CheckCircle, XCircle, AlertTriangle, FileText, Calendar, Quote } from 'lucide-react';
import { JobData, Article } from '../types/api';

interface ResultsDisplayProps {
  jobData: JobData;
  onNewSearch: () => void;
}

export const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ jobData, onNewSearch }) => {
  const verifiedArticles = jobData.results.filter(article => article.verified);
  
  const getAILabelColor = (label: string) => {
    return label === 'real' ? 'text-green-600 bg-green-100' : 'text-red-600 bg-red-100';
  };

  const getAILabelIcon = (label: string) => {
    return label === 'real' ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />;
  };

  const getPlagiarismColor = (score: number) => {
    if (score === 0) return 'text-green-600 bg-green-100';
    if (score < 15) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const formatConfidenceScore = (score: number) => {
    return `${(score * 100).toFixed(1)}%`;
  };

  return (
    <div className="w-full max-w-6xl mx-auto">
      <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-8 py-6 text-white">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-3xl font-bold mb-2">Analysis Results</h2>
              <p className="text-blue-100">Author: {jobData.author}</p>
              <p className="text-blue-100 text-sm">
                {verifiedArticles.length} verified publications found
              </p>
            </div>
            <button
              onClick={onNewSearch}
              className="bg-white text-blue-600 hover:bg-blue-50 px-6 py-2 rounded-lg font-semibold transition-colors duration-200"
            >
              New Search
            </button>
          </div>
        </div>

        {/* Results */}
        <div className="p-8">
          {verifiedArticles.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-600 mb-2">No Verified Publications Found</h3>
              <p className="text-gray-500">No verified publications were found for this author.</p>
            </div>
          ) : (
            <div className="space-y-6">
              {verifiedArticles.map((article, index) => (
                <div key={index} className="border border-gray-200 rounded-xl p-6 hover:shadow-lg transition-shadow duration-200">
                  {/* Article Header */}
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-xl font-semibold text-gray-900 leading-tight flex-grow pr-4">
                      {article.title}
                    </h3>
                    {article.open_access && (
                      <span className="flex-shrink-0 bg-green-100 text-green-800 text-xs font-medium px-2 py-1 rounded-full">
                        Open Access
                      </span>
                    )}
                  </div>

                  {/* Article Metadata */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div className="flex items-center text-gray-600">
                      <Calendar className="w-4 h-4 mr-2" />
                      <span className="text-sm">
                        {article.year || 'Year not specified'}
                      </span>
                    </div>
                    <div className="flex items-center text-gray-600">
                      <Quote className="w-4 h-4 mr-2" />
                      <span className="text-sm">
                        {article.citations !== null ? `${article.citations} citations` : 'Citations not available'}
                      </span>
                    </div>
                    {article.doi && (
                      <div className="flex items-center text-gray-600">
                        <ExternalLink className="w-4 h-4 mr-2" />
                        <a 
                          href={`https://doi.org/${article.doi}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-blue-600 hover:text-blue-800 hover:underline truncate"
                        >
                          {article.doi}
                        </a>
                      </div>
                    )}
                  </div>

                  {/* AI Analysis & Plagiarism Results */}
                  {(article.ai_analyzer_label || article.plagiarism_checker_results) && (
                    <div className="border-t border-gray-100 pt-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* AI Analysis */}
                        {article.ai_analyzer_label && article.ai_analyzer_score !== undefined && (
                          <div className="bg-gray-50 rounded-lg p-4">
                            <h4 className="font-semibold text-gray-800 mb-2 flex items-center">
                              <AlertTriangle className="w-4 h-4 mr-2" />
                              AI Authenticity Analysis
                            </h4>
                            <div className="flex items-center justify-between">
                              <div className="flex items-center">
                                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getAILabelColor(article.ai_analyzer_label)}`}>
                                  {getAILabelIcon(article.ai_analyzer_label)}
                                  <span className="ml-1 capitalize">{article.ai_analyzer_label}</span>
                                </span>
                              </div>
                              <span className="text-sm font-medium text-gray-700">
                                Confidence: {formatConfidenceScore(article.ai_analyzer_score)}
                              </span>
                            </div>
                          </div>
                        )}

                        {/* Plagiarism Check */}
                        {article.plagiarism_checker_results && (
                          <div className="bg-gray-50 rounded-lg p-4">
                            <h4 className="font-semibold text-gray-800 mb-2 flex items-center">
                              <FileText className="w-4 h-4 mr-2" />
                              Plagiarism Analysis
                            </h4>
                            <div className="flex items-center justify-between">
                              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getPlagiarismColor(article.plagiarism_checker_results.result.score)}`}>
                                {article.plagiarism_checker_results.result.score}% Similarity
                              </span>
                              <span className="text-xs text-gray-500">
                                {article.plagiarism_checker_results.result.sourceCounts} sources checked
                              </span>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};