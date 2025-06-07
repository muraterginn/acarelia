import { 
  ScanResponse, 
  StatusResponse, 
  AIAnalyzeStatusResponse, 
  PlagiarismStatusResponse, 
  JobDataResponse 
} from '../types/api';

// Use relative URL for proxy
const API_BASE_URL = '/api';

export class ApiService {
  static async startScan(author: string): Promise<ScanResponse> {
    const response = await fetch(`${API_BASE_URL}/scan?author=${encodeURIComponent(author)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Scan request failed: ${response.statusText}`);
    }

    return response.json();
  }

  static async getStatus(jobId: string): Promise<StatusResponse> {
    const response = await fetch(`${API_BASE_URL}/status/${jobId}`, {
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Status request failed: ${response.statusText}`);
    }

    return response.json();
  }

  static async getAIAnalyzeStatus(jobId: string): Promise<AIAnalyzeStatusResponse> {
    const response = await fetch(`${API_BASE_URL}/ai_analyze_status/${jobId}`, {
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`AI analyze status request failed: ${response.statusText}`);
    }

    return response.json();
  }

  static async getPlagiarismStatus(jobId: string): Promise<PlagiarismStatusResponse> {
    const response = await fetch(`${API_BASE_URL}/plagiarism_check_status/${jobId}`, {
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Plagiarism status request failed: ${response.statusText}`);
    }

    return response.json();
  }

  static async getJobData(jobId: string): Promise<JobDataResponse> {
    const response = await fetch(`${API_BASE_URL}/job_data/${jobId}`, {
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Job data request failed: ${response.statusText}`);
    }

    return response.json();
  }
}