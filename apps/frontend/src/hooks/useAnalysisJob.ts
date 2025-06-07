import { useState, useEffect, useCallback } from 'react';
import { ApiService } from '../services/api';
import { JobData, ProcessStage } from '../types/api';

export const useAnalysisJob = () => {
  const [jobId, setJobId] = useState<string | null>(null);
  const [stage, setStage] = useState<ProcessStage>('idle');
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');
  const [jobData, setJobData] = useState<JobData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const getStageFromStatus = (status: string): { stage: ProcessStage; progress: number } => {
    const statusLower = status.toLowerCase();
    
    if (statusLower.includes('scraping started')) {
      return { stage: 'scraping', progress: 10 };
    }
    if (statusLower.includes('scraper completed') || statusLower.includes('dois resolving')) {
      return { stage: 'resolving', progress: 25 };
    }
    if (statusLower.includes('dois resolved') || statusLower.includes('extract service started')) {
      return { stage: 'extracting', progress: 50 };
    }
    if (statusLower.includes('extract service finished successfully')) {
      return { stage: 'analyzing', progress: 75 };
    }
    if (statusLower.includes('error')) {
      return { stage: 'error', progress: 0 };
    }
    
    return { stage: 'scraping', progress: 5 };
  };

  const startAnalysis = useCallback(async (author: string) => {
    try {
      setIsLoading(true);
      setError(null);
      setStage('scraping');
      setProgress(0);
      setJobData(null);
      
      const response = await ApiService.startScan(author);
      setJobId(response.job_id);
      setStatusMessage('Analysis started...');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start analysis');
      setStage('error');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const pollStatus = useCallback(async (currentJobId: string) => {
    try {
      const statusResponse = await ApiService.getStatus(currentJobId);
      const { stage: newStage, progress: newProgress } = getStageFromStatus(statusResponse.status);
      
      setStage(newStage);
      setProgress(newProgress);
      setStatusMessage(statusResponse.status);

      // If extract service finished, start polling AI and plagiarism status
      if (statusResponse.status.includes('Extract service finished successfully')) {
        const [aiResponse, plagiarismResponse] = await Promise.all([
          ApiService.getAIAnalyzeStatus(currentJobId),
          ApiService.getPlagiarismStatus(currentJobId)
        ]);

        const aiFinished = aiResponse.ai_analyze_status.includes('successfully');
        const plagiarismFinished = plagiarismResponse.plagiarism_check_status.includes('successfully');

        if (aiFinished && plagiarismFinished) {
          setStage('completed');
          setProgress(100);
          setStatusMessage('Analysis completed successfully');
          
          // Fetch final job data
          const jobDataResponse = await ApiService.getJobData(currentJobId);
          setJobData(jobDataResponse.job_data);
          return true; // Stop polling
        } else {
          setProgress(85);
          setStatusMessage('Finalizing analysis...');
        }
      }

      return newStage === 'error';
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get status');
      setStage('error');
      return true; // Stop polling on error
    }
  }, []);

  useEffect(() => {
    if (!jobId || stage === 'completed' || stage === 'error') return;

    const interval = setInterval(async () => {
      const shouldStop = await pollStatus(jobId);
      if (shouldStop) {
        clearInterval(interval);
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [jobId, stage, pollStatus]);

  const reset = useCallback(() => {
    setJobId(null);
    setStage('idle');
    setProgress(0);
    setStatusMessage('');
    setJobData(null);
    setError(null);
    setIsLoading(false);
  }, []);

  return {
    jobId,
    stage,
    progress,
    statusMessage,
    jobData,
    error,
    isLoading,
    startAnalysis,
    reset
  };
};